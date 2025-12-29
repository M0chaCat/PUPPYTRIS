"""
pieces.py defines a bunch of constants relating to pieces, including:
-shapes for all piece rotations
-piece names and skins (initialized to placeholders)
-piece mirror mappings (inversions)
-constants for amount piece types
-kick tables
"""

import numpy, skinloader

TETRA_INVERSIONS = {
    1: 4,
    2: 6,
    3: 3,
    4: 1,
    5: 5,
    6: 2,
    7: 7
}
PENTA_INVERSIONS = {
    1: 2,
    2: 1,
    3: 3,
    4: 5,
    5: 4,
    6: 7,
    7: 6,
    8: 9,
    9: 8,
    10: 10,
    11: 11,
    12: 12,
    13: 13,
    14: 14,
    15: 16,
    16: 15,
    17: 18,
    18: 17
}

PIECE_TYPES_TETRA = 7
PIECE_TYPES_PENTA = 18

tetra_dict = {
    1: {
        "name": "Z",
        "shapes": [
            numpy.array([
                [0,0,0],
                [1,1,0],
                [0,1,1]
            ]),
            numpy.array([
                [0,0,1],
                [0,1,1],
                [0,1,0]
            ]),
            numpy.array([
                [0,0,0],
                [1,1,0],
                [0,1,1]
            ]),
            numpy.array([
                [0,1,0],
                [1,1,0],
                [1,0,0]
            ])
        ],
        "color": (243, 139, 168),  # red
        "skin": 0
        },
    2: {
        "name": "L",
        "shapes": [
            numpy.array([
                [0,0,0],
                [0,0,1],
                [1,1,1]
            ]),
            numpy.array([
                [0,1,0],
                [0,1,0],
                [0,1,1]
            ]),
            numpy.array([
                [0,0,0],
                [1,1,1],
                [1,0,0]
            ]),
            numpy.array([
                [1,1,0],
                [0,1,0],
                [0,1,0]
            ])
        ],
        "color": (250, 179, 135),  # orange
        "skin": 1
    },
    3: {
        "name": "O",
        "shapes": [
            numpy.array([
                [0,0,0,0],
                [0,1,1,0],
                [0,1,1,0],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [0,1,1,0],
                [0,1,1,0],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [0,1,1,0],
                [0,1,1,0],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [0,1,1,0],
                [0,1,1,0],
                [0,0,0,0]
            ])
        ],
        "color": (249, 226, 175),  # yellow
        "skin": 2
    },
    4: {
        "name": "S",
        "shapes": [
            numpy.array([
                [0,0,0],
                [0,1,1],
                [1,1,0]
            ]),
            numpy.array([
                [0,1,0],
                [0,1,1],
                [0,0,1]
            ]),
            numpy.array([
                [0,0,0],
                [0,1,1],
                [1,1,0]
            ]),
            numpy.array([
                [1,0,0],
                [1,1,0],
                [0,1,0]
            ])
        ],
        "color": (166, 227, 161),  # green
        "skin": 3
    },
    5: {
        "name": "I",
        "shapes": [
            numpy.array([
                [0,0,0,0],
                [0,0,0,0],
                [1,1,1,1],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,0,1,0],
                [0,0,1,0],
                [0,0,1,0],
                [0,0,1,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [0,0,0,0],
                [1,1,1,1],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,1,0,0],
                [0,1,0,0],
                [0,1,0,0],
                [0,1,0,0]
            ])
        ],
        "color": (137, 220, 235),  # cyan
        "skin": 4
    },
    6: {
        "name": "J",
        "shapes": [
            numpy.array([
                [0,0,0],
                [1,0,0],
                [1,1,1]
            ]),
            numpy.array([
                [0,1,1],
                [0,1,0],
                [0,1,0]
            ]),
            numpy.array([
                [0,0,0],
                [1,1,1],
                [0,0,1]
            ]),
            numpy.array([
                [0,1,0],
                [0,1,0],
                [1,1,0]
            ])
        ],
        "color": (137, 180, 250),  # blue
        "skin": 5
    },
    7: {
        "name": "T",
        "shapes": [
            numpy.array([
                [0,1,0],
                [1,1,1],
                [0,0,0]
            ]),
            numpy.array([
                [0,1,0],
                [0,1,1],
                [0,1,0]
            ]),
            numpy.array([
                [0,0,0],
                [1,1,1],
                [0,1,0]
            ]),
            numpy.array([
                [0,1,0],
                [1,1,0],
                [0,1,0]
            ])
        ],
        "color": (203, 166, 247),  # purple
        "skin": 6
    }
}
penta_dict = {
    1: {
        "name": "F",
        "shapes": [
            numpy.array([
                [0,1,0],
                [1,1,1],
                [0,0,1],
            ]),
            numpy.array([
                [0,1,0],
                [0,1,1],
                [1,1,0]
            ]),
            numpy.array([
                [1,0,0],
                [1,1,1],
                [0,1,0]
            ]),
            numpy.array([
                [0,1,1],
                [1,1,0],
                [0,1,0]
            ])
        ],
        "color": (243, 139, 168),  # red
        "skin": 0 #red
        },
    2: {
        "name": "F", # mirror
        "shapes": [
            numpy.array([
                [0,1,0],
                [1,1,1],
                [1,0,0]
            ]),
            numpy.array([
                [1,1,0],
                [0,1,1],
                [0,1,0]
            ]),
            numpy.array([
                [0,0,1],
                [1,1,1],
                [0,1,0]
            ]),
            numpy.array([
                [0,1,0],
                [1,1,0],
                [0,1,1]
            ])
        ],
        "color": (243, 139, 168),  # red
        "skin": 1 # orang
        },
    3: {
        "name": "I",
        "shapes": [
            numpy.array([
                [0,0,0,0,0],
                [0,0,0,0,0],
                [1,1,1,1,1],
                [0,0,0,0,0],
                [0,0,0,0,0]
            ]),
            numpy.array([
                [0,0,1,0,0],
                [0,0,1,0,0],
                [0,0,1,0,0],
                [0,0,1,0,0],
                [0,0,1,0,0]
            ]),
            numpy.array([
                [0,0,0,0,0],
                [0,0,0,0,0],
                [1,1,1,1,1],
                [0,0,0,0,0],
                [0,0,0,0,0]
            ]),
            numpy.array([
                [0,0,1,0,0],
                [0,0,1,0,0],
                [0,0,1,0,0],
                [0,0,1,0,0],
                [0,0,1,0,0]
            ])
        ],
        "color": (250, 179, 135),  # orange
        "skin": 2 #orange yelo
    },
    4: {
        "name": "P",
        "shapes": [
            numpy.array([
                [0,0,0,0],
                [0,1,1,1],
                [0,1,1,0],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [0,1,1,0],
                [0,1,1,0],
                [0,0,1,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [0,1,1,0],
                [1,1,1,0],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,1,0,0],
                [0,1,1,0],
                [0,1,1,0],
                [0,0,0,0]
            ])
        ],
        "color": (249, 226, 175),  # yellow
        "skin": 3 #yelo
    },
    5: {
        "name": "P", # mirror
        "shapes": [
            numpy.array([
                [0,0,0,0],
                [0,1,1,0],
                [0,1,1,1],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [0,1,1,0],
                [0,1,1,0],
                [0,1,0,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [1,1,1,0],
                [0,1,1,0],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,0,1,0],
                [0,1,1,0],
                [0,1,1,0],
                [0,0,0,0]
            ])
        ],
        "color": (249, 226, 175),  # yellow
        "skin": 4 #lime
    },
    6: {
        "name": "L",
        "shapes": [
            numpy.array([
                [0,0,0,0],
                [1,1,1,1],
                [1,0,0,0],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,1,1,0],
                [0,0,1,0],
                [0,0,1,0],
                [0,0,1,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [0,0,0,1],
                [1,1,1,1],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,1,0,0],
                [0,1,0,0],
                [0,1,0,0],
                [0,1,1,0]
            ])
        ],
        "color": (166, 227, 161),  # green
        "skin": 5 #geen
    },
    7: {
        "name": "L", # mirror
        "shapes": [
            numpy.array([
                [0,0,0,0],
                [1,0,0,0],
                [1,1,1,1],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,1,1,0],
                [0,1,0,0],
                [0,1,0,0],
                [0,1,0,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [1,1,1,1],
                [0,0,0,1],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,0,1,0],
                [0,0,1,0],
                [0,0,1,0],
                [0,1,1,0]
            ])
        ],
        "color": (166, 227, 161),  # green
        "skin": 6 #geen
    },
    8: {
        "name": "N",
        "shapes": [
            numpy.array([
                [0,0,0,0],
                [1,1,0,0],
                [0,1,1,1],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,0,1,0],
                [0,1,1,0],
                [0,1,0,0],
                [0,1,0,0]
            ]),
            numpy.array([
                [0,0,0,0],
                [1,1,1,0],
                [0,0,1,1],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,0,1,0],
                [0,0,1,0],
                [0,1,1,0],
                [0,1,0,0]
            ]),
        ],
        "color": (137, 220, 235),  # cyan
        "skin": 7 # geenish blu
    },
    9: {
        "name": "N", #mirror
        "shapes": [
            numpy.array([
                [0,0,0,0],
                [0,0,1,1],
                [1,1,1,0],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,1,0,0],
                [0,1,0,0],
                [0,1,1,0],
                [0,0,1,0],
            ]),
            numpy.array([
                [0,0,0,0],
                [0,1,1,1],
                [1,1,0,0],
                [0,0,0,0]
            ]),
            numpy.array([
                [0,1,0,0],
                [0,1,1,0],
                [0,0,1,0],
                [0,0,1,0]
            ])
        ],
        "color": (137, 220, 235),  # cyan
        "skin": 8 # bluish geen
    },
    10: {
        "name": "T",
        "shapes": [
            numpy.array([
                [1,1,1],
                [0,1,0],
                [0,1,0]
            ]),
            numpy.array([
                [0,0,1],
                [1,1,1],
                [0,0,1]
            ]),
            numpy.array([
                [0,1,0],
                [0,1,0],
                [1,1,1]
            ]),
            numpy.array([
                [1,0,0],
                [1,1,1],
                [1,0,0]
            ])
        ],
        "color": (137, 180, 250),  # blue
        "skin": 9 #cyan
    },
    11: {
        "name": "U",
        "shapes": [
            numpy.array([
                [0,0,0],
                [1,1,1],
                [1,0,1]
            ]),
            numpy.array([
                [0,1,1],
                [0,0,1],
                [0,1,1]
            ]),
            numpy.array([
                [0,0,0],
                [1,0,1],
                [1,1,1]
            ]),
            numpy.array([
                [1,1,0],
                [1,0,0],
                [1,1,0]
            ])
        ],
        "color": (203, 166, 247),  # purple
        "skin": 10 #blue
    },
    12: {
        "name": "V",
        "shapes": [
            numpy.array([
                [1,1,1],
                [1,0,0],
                [1,0,0]
            ]),
            numpy.array([
                [1,1,1],
                [0,0,1],
                [0,0,1]
            ]),
            numpy.array([
                [0,0,1],
                [0,0,1],
                [1,1,1]
            ]),
            numpy.array([
                [1,0,0],
                [1,0,0],
                [1,1,1]
            ])
        ],
        "color": (203, 166, 247),  # purple
        "skin": 11 # dark blu
    },
    13: {
        "name": "W",
        "shapes": [
            numpy.array([
                [1,0,0],
                [1,1,0],
                [0,1,1]
            ]),
            numpy.array([
                [0,1,1],
                [1,1,0],
                [1,0,0]
            ]),
            numpy.array([
                [1,1,0],
                [0,1,1],
                [0,0,1]
            ]),
            numpy.array([
                [0,0,1],
                [0,1,1],
                [1,1,0]
            ])
        ],
        "color": (203, 166, 247),  # purple
        "skin": 12 # rly dark blu
    },
    14: {
        "name": "X",
        "rare": True,
        "shapes": [
            numpy.array([
                [0,1,0],
                [1,1,1],
                [0,1,0]
            ]),
            numpy.array([
                [0,0,1,0,0],
                [0,1,1,1,0],
                [0,0,1,0,0]
            ]),
            numpy.array([
                [0,1,0],
                [1,1,1],
                [0,1,0]
            ]),
            numpy.array([
                [0,1,0],
                [1,1,1],
                [0,1,0]
            ])
        ],
        "color": (203, 166, 247),  # purple
        "skin": 13 # urple
    },
    15: {
        "name": "Y",
        "shapes": [
            numpy.array([
                [0,0,0,0,0],
                [0,0,0,0,0],
                [0,1,1,1,1],
                [0,0,1,0,0],
                [0,0,0,0,0]
            ]),
            numpy.array([
                [0,0,0,0,0],
                [0,0,1,0,0],
                [0,1,1,0,0],
                [0,0,1,0,0],
                [0,0,1,0,0]
            ]),
            numpy.array([
                [0,0,0,0,0],
                [0,0,0,0,0],
                [0,0,1,0,0],
                [1,1,1,1,0],
                [0,0,0,0,0]
            ]),
            numpy.array([
                [0,0,0,0,0],
                [0,0,1,0,0],
                [0,0,1,0,0],
                [0,0,1,1,0],
                [0,0,1,0,0]
            ])
        ],
        "color": (203, 166, 247),  # purple
        "skin": 14 # urple-er
    },
    16: {
        "name": "Y", # mirror
        "shapes": [
            numpy.array([
                [0,0,0,0,0],
                [0,0,0,0,0],
                [0,0,1,0,0],
                [0,1,1,1,1],
                [0,0,0,0,0]
            ]),
            numpy.array([
                [0,0,0,0,0],
                [0,0,1,0,0],
                [0,0,1,1,0],
                [0,0,1,0,0],
                [0,0,1,0,0]
            ]),
            numpy.array([
                [0,0,0,0,0],
                [0,0,0,0,0],
                [1,1,1,1,0],
                [0,0,1,0,0],
                [0,0,0,0,0]
            ]),
            numpy.array([
                [0,0,0,0,0],
                [0,0,1,0,0],
                [0,0,1,0,0],
                [0,1,1,0,0],
                [0,0,1,0,0]
            ])
        ],
        "color": (203, 166, 247),  # purple
        "skin": 15 #pimk
    },
    17: {
        "name": "Z",
        "shapes": [
            numpy.array([
                [0,0,1],
                [1,1,1],
                [1,0,0]
            ]),
            numpy.array([
                [1,1,0],
                [0,1,0],
                [0,1,1]
            ]),
            numpy.array([
                [0,0,1],
                [1,1,1],
                [1,0,0]
            ]),
            numpy.array([
                [1,1,0],
                [0,1,0],
                [0,1,1]
            ])
        ],
        "color": (203, 166, 247),  # purple
        "skin": 16 # prety
    },
    18: {
        "name": "Z", # mirror
        "shapes": [
            numpy.array([
                [1,0,0],
                [1,1,1],
                [0,0,1]
            ]),
            numpy.array([
                [0,1,1],
                [0,1,0],
                [1,1,0]
            ]),
            numpy.array([
                [1,0,0],
                [1,1,1],
                [0,0,1]
            ]),
            numpy.array([
                [0,1,1],
                [0,1,0],
                [1,1,0]

            ])
        ],
        "color": (203, 166, 247),  # purple
        "skin": 17 # rubyish?
    }
}

other_skins = []

def init_skins():
    """
    Lazy loader for skin textures.
    Replaces placeholders with surfaces from the arrays already declared in skinloader.py
    """
    global other_skins 
    other_skins = [] # clear the list
    skinloader.set_tetra_skins()
    skinloader.set_penta_skins()
    skinloader.set_other_skins()

    for i, piece in penta_dict.items():
        piece["skin"] = skinloader.penta_skins[i-1]
    for i, piece in tetra_dict.items():
        piece["skin"] = skinloader.tetra_skins[i-1]
    for skin in skinloader.other_skins:
        other_skins.append(skin)

# checks left to right if kicking right
kick_list_right = [(0, 0), (0, 1), (-1, 1), (1, 1), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)]
# checks right to left if kicking left
kick_list_left = [(0, 0), (0, 1), (1, 1), (-1, 1), (1, 0), (-1, 0), (2, 0), (-2, 0), (0, -1)]
# there are some rotation states where using the biased lists wouldn't make sense, for example rotating a state 4 I piece to a state 1 or 3.
# it should be fine though because it only affects kick order, and if anything gives advanced players more control.

kick_list_mirror = [(0, 0), (0, 1), (1, 1), (-1, 1), (1, 0), (-1, 0), (2, 0), (-2, 0), (0, -1)]
