import pieces, skinloader

class pentomino_base():
    pieces_dict = pieces.penta_dict
    piece_types = pieces.PIECE_TYPES_PENTA
    piece_inversions = pieces.TETRA_INVERSIONS
    hold_pieces_count = 2
    piece_size = 5
    
class tetramino_base():
    pieces_dict = pieces.tetra_dict
    piece_types = pieces.PIECE_TYPES_TETRA
    piece_inversions = pieces.PENTA_INVERSIONS
    hold_pieces_count = 1   
    piece_size = 4
    