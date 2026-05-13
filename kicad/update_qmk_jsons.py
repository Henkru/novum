#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from pcb_to_qmk_matrix import build_qmk_layout, build_vial_layout, get_split_switches


def matrix_key(entry):
    return tuple(entry["matrix"])


def read_json(path):
    with path.open("r") as file:
        return json.load(file)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=4) + "\n")


def reorder_keymap_layers(path, old_layout, new_layout):
    keymap = read_json(path)
    old_order = [matrix_key(entry) for entry in old_layout]
    new_order = [matrix_key(entry) for entry in new_layout]

    updated_layers = []
    for layer_index, layer in enumerate(keymap["layers"]):
        if len(layer) != len(old_order):
            raise ValueError(
                f"{path}: layer {layer_index} has {len(layer)} keycodes, "
                f"but keyboard layout has {len(old_order)} keys"
            )

        old_keycodes = dict(zip(old_order, layer))
        missing = [matrix for matrix in new_order if matrix not in old_keycodes]
        if missing:
            formatted = ", ".join(f"{row},{col}" for row, col in missing)
            raise ValueError(
                f"{path}: new layout contains matrix key(s) without existing keycodes: "
                f"{formatted}. Add keycodes manually before re-running this step."
            )

        updated_layers.append([old_keycodes[matrix] for matrix in new_order])

    keymap["layers"] = updated_layers
    write_json(path, keymap)


def main():
    parser = argparse.ArgumentParser(
        description="Update QMK/Vial physical layout JSON from generated KiCad PCBs."
    )
    parser.add_argument("--left-pcb", default="out/novum/pcbs/left.kicad_pcb", type=Path)
    parser.add_argument("--right-pcb", default="out/novum/pcbs/right.kicad_pcb", type=Path)
    parser.add_argument("--qmk-root", default="novum/qmk", type=Path)
    parser.add_argument("--rev", default="rev2")
    parser.add_argument("--keymap", action="append")
    args = parser.parse_args()

    rev_root = args.qmk_root / args.rev
    keyboard_path = rev_root / "keyboard.json"
    vial_path = rev_root / "keymaps/vial/vial.json"

    left_switches, right_switches = get_split_switches(args.left_pcb, args.right_pcb)
    qmk_layout = build_qmk_layout(left_switches, right_switches)
    vial_layout = build_vial_layout(left_switches, right_switches)

    keyboard = read_json(keyboard_path)
    old_layout = keyboard["layouts"]["LAYOUT"]["layout"]

    keymaps = args.keymap or ["default", "vial"]
    for keymap in keymaps:
        reorder_keymap_layers(rev_root / f"keymaps/{keymap}/keymap.json", old_layout, qmk_layout)

    keyboard["layouts"]["LAYOUT"]["layout"] = qmk_layout
    write_json(keyboard_path, keyboard)

    vial = read_json(vial_path)
    vial["layouts"]["keymap"] = vial_layout
    write_json(vial_path, vial)

    print(
        f"Updated QMK JSONs for {args.rev}: "
        f"{len(qmk_layout)} layout keys, {len(vial_layout)} Vial rows"
    )


if __name__ == "__main__":
    main()
