#!/usr/bin/env python3
import pcbnew
import argparse
from dataclasses import dataclass
from itertools import groupby
import json
from enum import Enum
"""

"""


class Side(Enum):
    Left = 0
    Right = 1


class SwitchKind(Enum):
    Switch = 0,
    Encoder = 1


@dataclass
class Switch:
    kind: SwitchKind
    row: int
    col: int
    x: float
    y: float


ENCODER_INDEX = 0


def footprint_iterator(board, prefix):
    index = 1
    while True:
        fp = board.FindFootprintByReference(f"{prefix}{index}")
        if type(fp) is pcbnew.FOOTPRINT:
            yield fp
        else:
            break
        index += 1


def diode_map(board):
    m = {}
    for d in footprint_iterator(board, "D"):
        [p1, p2] = set(map(lambda x: x.GetNetname(), d.Pads()))
        assert p1.startswith("ROW") or p2.startswith(
            "ROW"), f"No row net detected in pads: '{p1}' nor '{p2}"

        if p1.startswith("ROW"):
            row = p1
            inter = p2
        else:
            inter = p1
            row = p2

        m[inter] = row
    return m


def find_inter(pads, diode_map):
    inters = diode_map.keys()
    for pad in pads:
        if pad in inters:
            return pad
    return None


def get_switches(board_path, side):
    global ENCODER_INDEX
    board = pcbnew.LoadBoard(board_path)
    dm = diode_map(board)

    positions = []
    switches = list(footprint_iterator(board, "S"))
    encoders = list(footprint_iterator(board, "ROT"))
    for fp in switches + encoders:
        pads = list(map(lambda x: x.GetNetname(), fp.Pads().iterator()))

        col = next(filter(lambda x: x.startswith("COL"), pads))
        assert col != None, f"Not found the column net from the footprint: {pads}"

        inter = find_inter(pads, dm)
        assert inter != None, f"Not found the interconnection from the footprint: {pads}"

        row = dm[inter]
        assert row.startswith(
            "ROW"), f"The row net '{row}' does not start with ROW"
        assert col.startswith(
            "COL"), f"The column net '{col}' does not start with COL"
        row_num = int(row.replace("ROW", ""))
        col_num = int(col.replace("COL", ""))

        [x, y] = fp.GetPosition()
        positions.append(Switch(SwitchKind.Switch, row_num, col_num, x, y))

        if fp.GetReference().startswith("ROT"):
            ku = 19 * 1000000
            encoder_ccw = Switch(SwitchKind.Encoder,
                                 ENCODER_INDEX, 0, x, y - 2*ku)
            encoder_cw = Switch(SwitchKind.Encoder,
                                ENCODER_INDEX, 1, x, y - 1*ku)

            positions.append(encoder_cw)
            positions.append(encoder_ccw)
            ENCODER_INDEX += 1

    min_x = min(map(lambda s: s.x, positions))
    min_y = min(map(lambda s: s.y, positions))

    for s in positions:
        s.x = round((s.x - min_x)/1000000/19.0, 2)
        s.y = round((s.y - min_y)/1000000/19.0, 2)

    return positions


def build_vial_layout(left, right):
    sorted_switches = sorted(left + right, key=lambda s: s.y)
    grouped_lines = {y: list(switches) for y, switches in groupby(
        sorted_switches, key=lambda s: s.y)}
    vial_layout = []
    prev_y = None
    for y in sorted(grouped_lines.keys()):
        row = []
        prev_x = -1
        switches = grouped_lines[y]
        for s in sorted(switches, key=lambda s: s.x):
            shift = {
                "x": round(s.x - prev_x - 1, 2)
            }
            if prev_y != None:
                shift["y"] = round(-1 + (s.y - prev_y), 2)
            row.append(shift)
            if s.kind == SwitchKind.Switch:
                row.append(f"{s.row},{s.col}")
            elif s.kind == SwitchKind.Encoder:
                row.append(f"{s.row},{s.col}\n\n\n\n\n\n\n\n\ne")
            else:
                assert False, f"Unknown SwitchKind: {s.kind}"
            prev_x = s.x
            prev_y = None
        vial_layout.append(row)
        prev_y = y

    return vial_layout


def output_vial(left, right):
    vial_layout = build_vial_layout(left, right)

    # "pretty print" each entry to own row
    json_blobs = map(json.dumps, vial_layout)
    print("[\n  %s\n]" % ",\n  ".join(json_blobs))


def build_qmk_layout(left, right):
    def entry(s): return {
        "label": f"{s.row},{s.col}",
        "matrix": [s.row, s.col],
        "x": round(s.x, 2),
        "y": round(s.y, 2)
    }

    def key_func_left(s): return (s.row, s.col)
    def key_func_right(s): return (s.row, -s.col)
    def only_switch(s): return s.kind == SwitchKind.Switch

    # sort the rows as R0, R5, R1, R6, etc..,
    # and sort the columns from ASC for left side and DESC for right side
    sorted_left = groupby(sorted(filter(only_switch, left),
                          key=key_func_left), key=lambda s: s.row)
    sorted_right = groupby(
        sorted(filter(only_switch, right), key=key_func_right), key=lambda s: s.row)

    entries = [entry(s) for pair in zip(sorted_left, sorted_right)
               for (_, group) in pair for s in group]

    return entries


def output_qmk(left, right):
    entries = build_qmk_layout(left, right)

    # "pretty print" each entry to own row
    json_blobs = map(json.dumps, entries)
    print("[\n  %s\n]" % ",\n  ".join(json_blobs))


def get_split_switches(left_pcb, right_pcb):
    global ENCODER_INDEX
    ENCODER_INDEX = 0

    left_switches = get_switches(left_pcb, Side.Left)
    right_switches = get_switches(right_pcb, Side.Right)

    right_start_row = max(map(lambda x: x.row, left_switches)) + 1
    right_start_x = max(map(lambda x: x.x, left_switches)) + 4
    for i in right_switches:
        i.x += right_start_x
        if i.kind == SwitchKind.Switch:
            i.row += right_start_row

    return left_switches, right_switches


def main():
    parser = argparse.ArgumentParser(
        prog='pcb_to_qmk_matrix',
        description='Produces the QMK/vial matrix json array from the ergogen generated PCBs'
    )
    parser.add_argument('format', choices=[
                        'qmk', 'vial'], help="The output format")
    parser.add_argument('left_pcb',
                        help="The path to the left side pcb")
    parser.add_argument('right_pcb',
                        help="The path to the right side pcb")
    args = parser.parse_args()

    left_switches, right_switches = get_split_switches(args.left_pcb, args.right_pcb)

    if args.format == 'vial':
        output_vial(left_switches, right_switches)
    elif args.format == 'qmk':
        output_qmk(left_switches, right_switches)
    else:
        assert False, f"Unknown format argument: {args.format}"


if __name__ == "__main__":
    main()
