#!/usr/bin/env python3
import argparse
import math
from pathlib import Path


BEGIN_MARKER = "  # BEGIN GENERATED FUSION OUTLINE\n"
END_MARKER = "  # END GENERATED FUSION OUTLINE\n"


def parse_group_pairs(path):
    lines = path.read_text(errors="ignore").splitlines()
    pairs = []
    i = 0
    while i < len(lines) - 1:
        pairs.append((lines[i].strip(), lines[i + 1].strip()))
        i += 2
    return pairs


def parse_lwpolylines(path):
    pairs = parse_group_pairs(path)
    polylines = []
    i = 0
    while i < len(pairs):
        code, value = pairs[i]
        if code != "0" or value != "LWPOLYLINE":
            i += 1
            continue

        i += 1
        entity = []
        while i < len(pairs) and pairs[i][0] != "0":
            entity.append(pairs[i])
            i += 1

        points = []
        closed = False
        j = 0
        while j < len(entity):
            code, value = entity[j]
            if code == "70":
                closed = bool(int(value) & 1)
            elif code == "10":
                x = float(value)
                y = None
                bulge = 0.0
                k = j + 1
                while k < len(entity) and entity[k][0] != "10":
                    if entity[k][0] == "20":
                        y = float(entity[k][1])
                    elif entity[k][0] == "42":
                        bulge = float(entity[k][1])
                    k += 1
                if y is None:
                    raise ValueError(f"Malformed LWPOLYLINE in {path}: vertex without y value")
                points.append((x, y, bulge))
                j = k
                continue
            j += 1

        if points:
            polylines.append({"points": points, "closed": closed})

    if not polylines:
        raise ValueError(f"No LWPOLYLINE entities found in {path}")
    return polylines


def parse_arcs(path, max_segment):
    pairs = parse_group_pairs(path)
    arcs = []
    i = 0
    while i < len(pairs):
        code, value = pairs[i]
        if code != "0" or value != "ARC":
            i += 1
            continue

        i += 1
        data = {}
        while i < len(pairs) and pairs[i][0] != "0":
            if pairs[i][0] in {"10", "20", "40", "50", "51"}:
                data[pairs[i][0]] = float(pairs[i][1])
            i += 1

        missing = {"10", "20", "40", "50", "51"} - data.keys()
        if missing:
            raise ValueError(f"Malformed ARC in {path}: missing group code(s) {sorted(missing)}")

        cx = data["10"]
        cy = data["20"]
        radius = data["40"]
        start_angle = math.radians(data["50"])
        end_angle = math.radians(data["51"])
        while end_angle <= start_angle:
            end_angle += 2 * math.pi
        sweep = end_angle - start_angle
        steps = max(2, math.ceil(abs(radius * sweep) / max_segment))
        points = []
        for step in range(steps + 1):
            angle = start_angle + sweep * step / steps
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle), 0.0))
        arcs.append({"points": points, "closed": False})

    return arcs


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def stitch_polylines(polylines, tolerance):
    chains = [[(x, y, bulge) for x, y, bulge in poly["points"]] for poly in polylines]
    closed_chains = [chain for chain, poly in zip(chains, polylines) if poly["closed"]]
    open_chains = [chain for chain, poly in zip(chains, polylines) if not poly["closed"]]

    if closed_chains and open_chains:
        raise ValueError("DXF contains both closed and open polylines; keep only the board outline")
    if len(closed_chains) == 1:
        return closed_chains[0]
    if len(closed_chains) > 1:
        raise ValueError("DXF contains multiple closed polylines; keep only the board outline")

    chain = open_chains.pop(0)
    while open_chains:
        end = chain[-1]
        candidates = []
        for idx, other in enumerate(open_chains):
            candidates.append((dist(end, other[0]), idx, False))
            candidates.append((dist(end, other[-1]), idx, True))
        distance, idx, reverse = min(candidates, key=lambda item: item[0])
        if distance > tolerance:
            raise ValueError(
                f"Could not stitch DXF polylines: nearest endpoint is {distance:.3f}mm away "
                f"(tolerance {tolerance:.3f}mm)"
            )
        other = open_chains.pop(idx)
        if reverse:
            other = list(reversed(other))
        chain.extend(other[1:])

    if dist(chain[-1], chain[0]) > tolerance:
        raise ValueError(
            f"Stitched polyline is not closed: final endpoint is {dist(chain[-1], chain[0]):.3f}mm "
            f"from the start (tolerance {tolerance:.3f}mm)"
        )
    if dist(chain[-1], chain[0]) <= tolerance:
        chain = chain[:-1]
    return chain


def arc_points_from_bulge(start, end, bulge, max_segment):
    if abs(bulge) < 1e-12:
        return []

    x1, y1 = start
    x2, y2 = end
    chord = math.hypot(x2 - x1, y2 - y1)
    if chord == 0:
        return []

    theta = 4 * math.atan(bulge)
    radius = chord / (2 * math.sin(abs(theta) / 2))
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    ux = (x2 - x1) / chord
    uy = (y2 - y1) / chord
    normal = (-uy, ux)
    center_offset = chord / (2 * math.tan(abs(theta) / 2))
    sign = 1 if bulge > 0 else -1
    cx = mx + normal[0] * center_offset * sign
    cy = my + normal[1] * center_offset * sign

    start_angle = math.atan2(y1 - cy, x1 - cx)
    sweep = theta
    steps = max(2, math.ceil(abs(radius * sweep) / max_segment))
    return [
        (
            cx + radius * math.cos(start_angle + sweep * step / steps),
            cy + radius * math.sin(start_angle + sweep * step / steps),
        )
        for step in range(1, steps)
    ]


def flatten_bulges(vertices, max_segment):
    result = []
    count = len(vertices)
    for i, (x, y, bulge) in enumerate(vertices):
        result.append((x, y))
        nx, ny, _ = vertices[(i + 1) % count]
        result.extend(arc_points_from_bulge((x, y), (nx, ny), bulge, max_segment))
    return result


def simplify_points(points, tolerance):
    if tolerance <= 0:
        return points

    simplified = []
    for point in points:
        if not simplified or dist(point, simplified[-1]) > tolerance:
            simplified.append(point)
    if len(simplified) > 1 and dist(simplified[0], simplified[-1]) <= tolerance:
        simplified.pop()

    changed = True
    while changed and len(simplified) > 3:
        changed = False
        kept = []
        count = len(simplified)
        for i, point in enumerate(simplified):
            prev_point = simplified[(i - 1) % count]
            next_point = simplified[(i + 1) % count]
            line_len = dist(prev_point, next_point)
            if line_len == 0:
                continue
            area2 = abs(
                (next_point[0] - prev_point[0]) * (prev_point[1] - point[1])
                - (prev_point[0] - point[0]) * (next_point[1] - prev_point[1])
            )
            deviation = area2 / line_len
            if deviation > tolerance:
                kept.append(point)
            else:
                changed = True
        simplified = kept
    return simplified


def transform_points(points, scale, offset_x, offset_y, flip_y):
    transformed = []
    for x, y in points:
        tx = x * scale + offset_x
        ty = y * (-scale if flip_y else scale) + offset_y
        transformed.append((tx, ty))
    return transformed


def mirror_points(points, axis):
    return [(2 * axis - x, y) for x, y in reversed(points)]


def fmt_number(value):
    value = round(value, 4)
    if value == 0:
        value = 0
    return f"{value:g}"


def outline_yaml(name, points):
    lines = [
        f"  {name}:\n",
        "    - what: polygon\n",
        "      points:\n",
    ]
    previous = (0.0, 0.0)
    for x, y in points:
        dx = x - previous[0]
        dy = y - previous[1]
        lines.append(f"        - shift: [{fmt_number(dx)}, {fmt_number(dy)}]\n")
        previous = (x, y)
    return lines


def generated_block(left_points, right_points):
    lines = [BEGIN_MARKER]
    lines.extend(outline_yaml("_fusion_outline_left", left_points))
    lines.extend(outline_yaml("_fusion_outline_right", right_points))
    lines.append(END_MARKER)
    return "".join(lines)


def replace_between(text, start, end, replacement):
    start_index = text.find(start)
    if start_index == -1:
        return None
    end_index = text.find(end, start_index)
    if end_index == -1:
        return None
    end_index += len(end)
    while text.startswith(end, end_index):
        end_index += len(end)
    return text[:start_index] + replacement + text[end_index:]


def update_generated_outline_block(config_text, block):
    replaced = replace_between(config_text, BEGIN_MARKER, END_MARKER, block)
    if replaced is not None:
        return replaced

    legacy_start = "  # Custom outline extensions"
    insertion_point = "  # Mounting holes\n"
    legacy_start_index = config_text.find(legacy_start)
    insertion_index = config_text.find(insertion_point)
    if legacy_start_index != -1 and insertion_index != -1 and legacy_start_index < insertion_index:
        return config_text[:legacy_start_index] + block + config_text[insertion_index:]

    if insertion_index == -1:
        raise ValueError("Could not find '# Mounting holes' insertion point in config")
    return config_text[:insertion_index] + block + config_text[insertion_index:]


def update_board_outline_block(config_text):
    start = "  # Board outlines\n"
    end = "  board_left:"
    replacement = (
        "  # Board outlines\n"
        "  board_outline_left:\n"
        "    - what: outline\n"
        "      name: _fusion_outline_left\n"
        "  board_outline_right:\n"
        "    - what: outline\n"
        "      name: _fusion_outline_right\n"
    )
    start_index = config_text.find(start)
    end_index = config_text.find(end, start_index)
    if start_index == -1 or end_index == -1:
        raise ValueError("Could not find board_outline_left/right block in config")
    return config_text[:start_index] + replacement + config_text[end_index:]


def main():
    parser = argparse.ArgumentParser(
        description="Update Ergogen board outlines from novum/outline/left.dxf LWPOLYLINE geometry."
    )
    parser.add_argument("--dxf", default="novum/outline/left.dxf", type=Path)
    parser.add_argument("--config", default="novum/ergogen/config.yaml", type=Path)
    parser.add_argument("--join-tolerance", default=0.5, type=float)
    parser.add_argument("--simplify-tolerance", default=0.0, type=float)
    parser.add_argument("--arc-segment", default=0.5, type=float)
    parser.add_argument("--scale", default=1.0, type=float)
    parser.add_argument("--offset-x", default=0.0, type=float)
    parser.add_argument("--offset-y", default=0.0, type=float)
    parser.add_argument("--flip-y", action="store_true")
    parser.add_argument("--mirror-axis", default=202.25, type=float)
    args = parser.parse_args()

    polylines = parse_lwpolylines(args.dxf)
    polylines.extend(parse_arcs(args.dxf, args.arc_segment))
    stitched = stitch_polylines(polylines, args.join_tolerance)
    points = flatten_bulges(stitched, args.arc_segment)
    points = simplify_points(points, args.simplify_tolerance)
    left_points = transform_points(points, args.scale, args.offset_x, args.offset_y, args.flip_y)
    right_points = mirror_points(left_points, args.mirror_axis)

    config_text = args.config.read_text()
    config_text = update_generated_outline_block(config_text, generated_block(left_points, right_points))
    config_text = update_board_outline_block(config_text)
    args.config.write_text(config_text)

    print(
        f"Updated {args.config} from {args.dxf}: "
        f"{len(polylines)} polylines stitched into {len(left_points)} points "
        f"(mirror axis x={fmt_number(args.mirror_axis)})"
    )


if __name__ == "__main__":
    main()
