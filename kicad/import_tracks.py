#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import pcbnew
import json
"""
Import tracks from a JSON file

Usage: import_tracks.py <board_file> <track_file>
"""


class TrackImportError(Exception):
    pass


def vec(x, y):
    return pcbnew.VECTOR2I(x, y)


def get_net_code(board, netname, board_file, track_file, kind, index):
    try:
        return board.GetNetcodeFromNetname(netname)
    except (IndexError, KeyError):
        raise TrackImportError(
            f"{track_file}: {kind} #{index} references missing net "
            f"{netname!r} in {board_file}"
        ) from None


def main(argv):
    board_file = argv[0]
    track_file = argv[1]
    tracks = json.load(open(track_file, 'r'))
    board = pcbnew.LoadBoard(board_file)

    for index, info in enumerate(tracks['tracks'], start=1):
        track = pcbnew.PCB_TRACK(board)
        try:
            track.SetNetCode(
                get_net_code(board, info[0], board_file, track_file, "track", index)
            )
            track.SetStart(vec(info[1], info[2]))
            track.SetEnd(vec(info[3], info[4]))
            track.SetWidth(info[5])
            track.SetLayer(info[6])
            board.Add(track)
        except TrackImportError as e:
            print(e)
            continue

    for index, info in enumerate(tracks['vias'], start=1):
        try:
            pcb_via = pcbnew.PCB_VIA(board)
            pcb_via.SetNetCode(
                get_net_code(board, info[0], board_file, track_file, "via", index)
            )
            pcb_via.SetPosition(vec(info[1], info[2]))
            pcb_via.SetWidth(info[3])
            pcb_via.SetDrill(info[4])
            board.Add(pcb_via)
        except TrackImportError as e:
            print(e)
            continue

    board.Save(board_file)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except TrackImportError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
