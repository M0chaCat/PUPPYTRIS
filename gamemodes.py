"""
gamemodes.py defines classes containing
all the data for their respective gamemodes.
Gamemodes are usually stacked. For example,
tetramino_base is loaded, then guideline is loaded.
"""

import pieces

class PentominoBase():
    pieces_dict = pieces.penta_dict
    piece_types = pieces.PIECE_TYPES_PENTA
    piece_inversions = pieces.PENTA_INVERSIONS
    hold_pieces_count = 2
    piece_size = 5
    allow_mirror = True

class TetraminoBase():
    pieces_dict = pieces.tetra_dict
    piece_types = pieces.PIECE_TYPES_TETRA
    piece_inversions = pieces.TETRA_INVERSIONS
    hold_pieces_count = 1
    piece_size = 4
    allow_mirror = False

class Guideline():
    piece_gen_type = "BAG"
    lockdown_type = "GUIDELINE"
    next_queue_size = 4
    das_threshold = 166.6666666
    arr_threshold = 33.3333333
    entry_delay = 100
    sdr_threshold = 33.333333
    allow_sonic_drop = False
    allow_180 = False

class Classic():
    piece_gen_type = "CLASSIC"
    lockdown_type = "CLASSIC"
    next_queue_size = 1
    das_threshold = 266.666666
    arr_threshold = 100
    entry_delay = 233 # PLACEHOLDER, ARE in nestris is more complicated than this
    sdr_threshold = 33.33333
    allow_sonic_drop = False
    allow_180 = False

class BetterArcade():
    piece_gen_type = "4MEMR6"
    next_queue_size = 2
    das_threshold = 233 # PLACEHOLDER, DAS in TGM is framerate dependent
    arr_threshold = 16.6666666
    sdr_threshold = 16.6666666
    entry_delay = 350
    allow_sonic_drop = False
