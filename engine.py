    
# Engine

import pygame
import math
import numpy
import random
import os
import time
import copy

import pieces, settings

pygame.init()

STATE = 0

running = True # so we can turn the game loop on and off

BOARD_WIDTH_PX = settings.CELL_SIZE * settings.BOARD_WIDTH
BOARD_HEIGHT_PX = settings.CELL_SIZE * (settings.BOARD_HEIGHT - settings.BOARD_EXTRA_HEIGHT)

BOARD_PX_OFFSET_X = (settings.WINDOW_WIDTH - BOARD_WIDTH_PX)/2
BOARD_PX_OFFSET_Y = (settings.WINDOW_HEIGHT - BOARD_HEIGHT_PX-(settings.WINDOW_HEIGHT * 0.05))/2 - (settings.BOARD_EXTRA_HEIGHT * settings.CELL_SIZE)

script_dir = os.path.dirname(os.path.abspath(__file__))
skins_dir = os.path.join(script_dir, "skin")

# --- Load tetra skins (top-left column) ---
tetra_skins = []
    
# --- Load penta skins (top-right column) ---
penta_skins = []

other_skins = []


frametime_clock = pygame.time.Clock()
arr_clock = pygame.time.Clock()
das_clock = pygame.time.Clock()
sdr_clock = pygame.time.Clock()
das_reset_clock = pygame.time.Clock()
are_clock = pygame.time.Clock()
gravity_clock = pygame.time.Clock()
lockdown_clock = pygame.time.Clock()
onekf_prac_clock = pygame.time.Clock()
prevent_harddrop_clock = pygame.time.Clock()

lines_cleared, pieces_placed, pps, bag_count, history_index, last_move_dir = 0, 0, 0, 0, 0, 0
rng_seed = random.getstate()
rng_state = rng_seed
history_index = 0
das_timer, arr_timer, sdr_timer, das_reset_timer, onekf_prac_timer = 0, 0, 0, 0, 0
are_timer, gravity_timer, lockdown_timer, prevent_harddrop_timer = 0, 0, 0, 0
das_started, arr_started, sdr_started, das_reset_started, onekf_prac_started = False, False, False, False, False
prevent_harddrop_started = False
softdrop_overrides = True
game_state_changed = False
board_state_changed = False
queue_spawn_piece = True

piece_bags = [[],[]]
hold_pieces = []

# gamemode specific vars (defaults)
pieces_dict = pieces.tetra_dict
piece_inversions = pieces.TETRA_INVERSIONS
piece_gen_type = "BAG"
lockdown_type = "GUIDELINE"
next_queue_size = 4 # next pieces count is the user settings max
                    # next_queue_size will sometimes be smaller than the max depending on the gamemode
das_threshold = settings.DAS_THRESHOLD # 266.6666666
arr_threshold = settings.ARR_THRESHOLD # 100
sdr_threshold = settings.SDR_THRESHOLD # 33.33333333
allow_sonic_drop = True
allow_180 = True
allow_mirror = False
are_threshold = 1000
entry_delay = 0
hold_pieces_count = 0
spawn_y_offset = 0
infinite_holds = False
starting_gravity = 0 # measured in G (1g = 1 fall/frame, 20g = max speed at 60fps (should jump to like 200g though for more consistency)
piece_size = 4
piece_types = 7

holds_used = 0
current_gravity = starting_gravity
    
hold_boards = numpy.zeros((hold_pieces_count, 5, 5), dtype=numpy.int8)
next_boards = numpy.zeros((next_queue_size, 5, 5), dtype=numpy.int8)
topout_board = numpy.zeros((5, 5), dtype=numpy.int8)

onekf_key_array = numpy.zeros((4, 10), dtype=int) # int8 is too small

starting_x = 3
starting_y = 2
STARTING_ROTATION = 0

game_board = numpy.zeros((settings.BOARD_HEIGHT, settings.BOARD_WIDTH), numpy.int8)
game_history = [None] * settings.MAX_HISTORY
piece_board = numpy.zeros((piece_size, piece_size), numpy.int8)
ghost_board = numpy.zeros_like(piece_board)

piece_x, ghost_piece_x = starting_x, starting_x
piece_y, ghost_piece_y = starting_y, starting_y
piece_rotation = STARTING_ROTATION
lockdown_start_x = starting_x
lockdown_start_y = -settings.BOARD_EXTRA_HEIGHT
lockdown_start_rotation = STARTING_ROTATION
lockdown_resets = 15

class Timer:
    def __init__(self):
        self.start_time = None
        self.running = False
        
    def start(self):
        self.start_time = time.perf_counter()
        self.running = True
        
    def stop(self):
        self.running = False
        
    def reset(self):
        self.start_time = time.perf_counter()
        
    def split_strings(self):
        """Return ('M:SS', '.XX') with hundredths of a second."""
        if not self.running or self.start_time is None:
            return "0:00", ".00"
        
        elapsed = time.perf_counter() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        hundredths = int((elapsed * 100) % 100)  # rounds to .XX
        
        return f"{minutes}:{seconds:02d}", f".{hundredths:02d}"
    
    def get_seconds(self):
        """Return the time in seconds as an integer"""
        if not self.running or self.start_time is None:
            return 0
        
        elapsed = time.perf_counter() - self.start_time

        return elapsed
    
timer = Timer()

def update_starting_coords():
    global piece_size, piece_x, piece_y, starting_x, starting_y, piece_rotation
    piece_shape = pieces_dict[piece_bags[0][0]]["shapes"][STARTING_ROTATION]
    piece_size = piece_shape.shape[1]
    height_offset = numpy.where(numpy.any(piece_shape != 0, axis=1))[0][0]
    starting_x = (settings.BOARD_WIDTH - piece_size) // 2 # dynamically calculate starting position based on board and piece size.
    starting_y = settings.BOARD_EXTRA_HEIGHT - piece_size//5 - height_offset + spawn_y_offset # need to subtract the blank space in the piece here
    piece_x = starting_x
    piece_y = starting_y
    piece_rotation = STARTING_ROTATION

def update_pps():
    global pps
    total_time = timer.get_seconds()
    pps = pieces_placed / total_time
    pps = round(pps, 2)

def generate_bag(type="BAG"):
    global bag_count
    bag_count += 1
    generated_bag = []
    
    if (type == "BAG"): 
        for piece, data in pieces_dict.items(): # put all the pieces in the bag
            # Skip if rare piece (x) and we're on an odd bag
            if data.get("rare", False) and bag_count % 2 == 1:
                continue
            generated_bag.append(piece)
        random.shuffle(generated_bag)

    elif (type == "RANDOM"):
        for i in range(7):
            piece = random.randint(1, piece_types)
            generated_bag.append(piece)

    elif (type == "CLASSIC"):
        for i in range(7):
            if not piece_bags[0] and i == 0:
                prev_piece = -1
            elif i == 0:
                prev_piece = (piece_bags[0] + piece_bags[1])[0]
            else:
                prev_piece = generated_bag[0]
            piece = random.randint(0, piece_types)
            if (piece == 0 or piece == prev_piece):
                piece = random.randint(1, piece_types)
            generated_bag.insert(0, piece)
    elif type.startswith("4MEMR"): # ANY 4 memory, reroll 6 times is TGM2 style
        reroll_count = int(type[-1]) # gets the last character
        prev_pieces = [1, 1, 1, 1] # placeholder
        for i in range(7):
            if not piece_bags[0] and i == 0:
                if piece_types == 7:
                    prev_pieces = [1,4,1,4]
                else: # assume piece_types must equal 18
                    prev_pieces = [14, 14, 14, 14] # temp placeholder
            elif i == 0:
                prev_pieces = (piece_bags[0] + piece_bags[1])[:4]
            else:
                print(generated_bag)
                prev_pieces.append(generated_bag[0])
                prev_pieces.pop(0)
            piece = random.randint(1, piece_types)
            for _ in range(reroll_count):
                if piece in prev_pieces:
                    piece = random.randint(1, piece_types)
                    print("rerolling")
            generated_bag.insert(0, piece)

    return generated_bag

def spawn_piece():
    global piece_x, piece_y, piece_rotation, next_boards, topout_board, piece_board, queue_spawn_piece, holds_used, game_state_changed
    queue_spawn_piece = False
    update_starting_coords()
    holds_used = 0
    game_state_changed = True
    
    piece_board = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation] * piece_bags[0][0]
    gen_next_boards()
    gen_topout_board()
    update_ghost_piece()
    # top-out check
    if check_collisions(0, 0, piece_board):
        top_out()

def update_game_board(new_board):
    global game_board, game_state_changed
    game_state_changed = True
    game_board = new_board.copy()

def update_history():
    global history_index, game_history

    history_index += 1
    if history_index == settings.MAX_HISTORY:
        history_index = 0

    game_history[history_index] = {
        "board": game_board.copy(),
        "pieces": pieces_placed,
        "lines": lines_cleared,
        "next": copy.deepcopy(piece_bags),
        "hold": copy.deepcopy(hold_pieces),
        "rng": rng_state,
        #"level": level,
        #"score": score,
        "bag_count": bag_count
    }

def undo(amount):
    global game_board, pieces_placed, lines_cleared, piece_bags, hold_pieces, rng_state, pps, bag_count
    global piece_x, piece_y, piece_rotation, holds_used, piece_board, queue_spawn_piece
    global game_state_changed, history_index
    if pieces_placed - amount >= 0:
        game_state_changed = True
        history_index -= amount
        if history_index < 0:
            history_index = settings.MAX_HISTORY - amount # make sure this doesn't miss one

        # revert history
        state = game_history[history_index]
        game_board = copy.deepcopy(state["board"])
        pieces_placed = state["pieces"]
        lines_cleared = state["lines"]
        piece_bags = copy.deepcopy(state["next"])
        hold_pieces = copy.deepcopy(state["hold"])
        rng_state = state["rng"]
        bag_count = state["bag_count"]

        # reset position
        update_starting_coords()
        holds_used = 0
        random.setstate(rng_state)

        piece_board = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation] * piece_bags[0][0] # update piece board early so it looks nice
        queue_spawn_piece = True
        board_state_changed = True
        # updating all these even thought spawn_piece does it for us because want it to update on frame 0
        gen_topout_board()
        gen_hold_boards()
        gen_next_boards()
        update_ghost_piece()

def gen_topout_board():
    global topout_board
    extra_height = settings.BOARD_EXTRA_HEIGHT
    topout_board = numpy.zeros((piece_size, piece_size), dtype=numpy.int8)
    next_shape = pieces_dict[(piece_bags[0] + piece_bags[1])[1]]["shapes"][STARTING_ROTATION]

    # create the two boards to compare
    top_rows = extra_height + math.floor(settings.BOARD_HEIGHT/8) + 2 # 1 row less for boards < 24 high, and 2 less for boards < 8 high
    top_rows = game_board[:top_rows].copy()
    top_mask = top_rows.copy()
    full_rows_index = extra_height + piece_size - 3 # min index of rows that should be all 1
    for i, row in enumerate(top_mask):
        if i < full_rows_index:
            top_mask[i] = 1
        else:
            top_mask[i][0:i-full_rows_index] = 0
            top_mask[i][i-full_rows_index:settings.BOARD_WIDTH-(i-full_rows_index)] = 1
            top_mask[i][settings.BOARD_WIDTH-(i-full_rows_index):settings.BOARD_WIDTH] = 0
    if numpy.any((top_rows != 0) & (top_mask != 0)):
        topout_board = next_shape
    else:
        topout_board = None

def update_ghost_piece(): # make sure piece_board has been updated before calling this function
    global ghost_piece_x, ghost_piece_y, ghost_board, piece_y
    if settings.ONEKF_ENABLED: # return an empty board if 1kf is enabled
        ghost_board = numpy.zeros_like(ghost_board)
        return
    # calculate the coords
    ghost_piece_x = piece_x
    ghost_piece_y = piece_y # STARTS at piece y and looks from there 
    for _ in range(piece_y, settings.BOARD_HEIGHT):
        if not check_collisions(0, 1, piece_board, ghost_piece=True): # fourth param for ghost pieces
            ghost_piece_y += 1
        else: break
    # update the board
    ghost_board = piece_board.copy()

def check_collisions(target_move_x, target_move_y, target_shape, ghost_piece = False):
    if ghost_piece:
        new_x = target_move_x + ghost_piece_x
        new_y = target_move_y + ghost_piece_y
    else:
        new_x = target_move_x + piece_x
        new_y = target_move_y + piece_y
    collided = False
    # make sure positions aren't out of bounds first
    for coords in numpy.argwhere(target_shape != 0): # returns a 1d numpy array of coordinates that meet the condition != 0
        if (coords[0] + new_y > settings.BOARD_HEIGHT - 1): # check for collision with the bottom of the board
            collided = True
            break
        if (coords[1] + new_x < 0 or coords[1] + new_x > settings.BOARD_WIDTH - 1): # check for collision with the sides of the board
            collided = True
            break
        if (game_board[coords[0] + new_y, coords[1] + new_x]): # check for collision with minos
            collided = True
            break
    if collided: return True
    else: return False

def check_touching_ground():
    piece_shape = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation]

    for coords in numpy.argwhere(piece_shape != 0):
        if coords[0] + piece_y + 1 > settings.BOARD_HEIGHT - 1: # check if its touching the bottom of the board
            return True # return true if it IS touching the ground
        elif game_board[coords[0] + piece_y + 1, piece_x + coords[1]]: # check if its touching any minos below it
            return True
    return False # return false if nothing found

def rotate_piece(amount):
    global piece_rotation, piece_board, piece_x, piece_y, game_state_changed
    kick_list = []

    new_rotation = (piece_rotation + amount) % 4
    new_shape = pieces_dict[piece_bags[0][0]]["shapes"][new_rotation]

    # offset pieces rotating from state 4 to make them kick more symetrically 
    # for example, think 180ing a state 4 z piece, will behave as if nothing happened

    # a problem with the bias system is that if an unbiased (state 2) rotation would collide and allow a kick to be performed,
    # and an biased (state 4) rotation simply won't collide at all when rotating, then it will perform asymmetrically 
    # if piece_rotation == 0 and piece_bags[0][0] in (1, 3, 4, 5): # covers pieces Z, S, O, I
    #     bias = -1
    # else:
    #     bias = 0

    # slightly weird i kick behaviour on edge with hole underneath platform like this iiii
    #                                                                                  ---
    if new_rotation == 0 and piece_bags[0][0] in (1, 3, 4, 5): # ensures the kick order is symmetrical for Z, S, O, I
        kick_list = pieces.kick_list_left
    else:
        kick_list = pieces.kick_list_right

    for kick in kick_list:
        kick_x, kick_y = kick
        if not check_collisions(kick_x, kick_y, new_shape): # continue if no collisions found
            piece_rotation = new_rotation
            # move the piece
            piece_x += kick_x # update the position variables
            piece_y += kick_y
            piece_board = new_shape * piece_bags[0][0]
            update_ghost_piece()
            game_state_changed = True
            return
    
def mirror_piece():
    global piece_board, piece_bags, game_state_changed, piece_x, piece_y
    
    mirrored_piece = piece_inversions[piece_bags[0][0]] # get the mirror
    new_shape = pieces_dict[mirrored_piece]["shapes"][piece_rotation] # get its shape

    kick_list = pieces.kick_list_mirror

    for kick in kick_list:
        kick_x, kick_y = kick
        if not check_collisions(kick_x, kick_y, new_shape):
            game_state_changed = True
            piece_x += kick_x # update the coordinates
            piece_y += kick_y
            piece_bags[0][0] = mirrored_piece # update the piece in the queue
            piece_board = new_shape * piece_bags[0][0] # update the piece board
            update_ghost_piece()
            break

def hold_piece(type, infinite):
    if type == "PUPPY":
        hold_puppy()
    elif type == "GUIDELINE":
        hold_guideline(infinite)

def hold_puppy():
    global piece_bags, hold_pieces, hold_boards, next_boards, piece_board, game_state_changed
    game_state_changed = True

    if len(hold_pieces) >= hold_pieces_count: # if hold bag is full
        new_shape = pieces_dict[hold_pieces[0]]["shapes"][piece_rotation] # returns the next piece in the hold queue
    else:
        new_shape = pieces_dict[(piece_bags[0] + piece_bags[1])[1]]["shapes"][piece_rotation] # returns the next piece in the next queue
    
    if not check_collisions(0, 0, new_shape):
        hold_pieces.append(piece_bags[0][0]) # take the current piece and add it to hold queue
        piece_bags[0].pop(0) # remove the current piece from piece bag
        
        # if hold queue is full (enforce max hold pieces)
        if len(hold_pieces) > hold_pieces_count:
            piece_bags[0].insert(0, hold_pieces[0]) # insert the next hold piece as the new current piece
            hold_pieces.pop(0) # remove the inserted hold piece from the hold queue
        else:
            # only ever necessary if the hold queue wasn't already full
            gen_next_boards()
    
    # regen bags if the bag is emptied because of hold
    if not piece_bags[0]:
        piece_bags[0] = piece_bags[1]
        piece_bags[1] = generate_bag(piece_gen_type)
        
    # refresh current active piece
    piece_board = pieces_dict[(piece_bags[0] + piece_bags[1])[0]]["shapes"][piece_rotation] * piece_bags[0][0] # gets the next piece, this implementation is required cause holding can sometimes empty bag 1
    update_ghost_piece()
    gen_hold_boards()

def hold_guideline(infinite_holds = False):
    global piece_bags, hold_pieces, hold_boards, next_boards, game_state_changed, holds_used
    global piece_x, piece_y, piece_rotation, piece_board
    game_state_changed = True

    if holds_used < hold_pieces_count or infinite_holds:
        hold_pieces.append(piece_bags[0][0]) # take the current piece and add it to hold queue
        piece_bags[0].pop(0) # remove the current piece from piece bag
            
        # if hold queue is full (enforce max hold pieces)
        if len(hold_pieces) > hold_pieces_count:
            piece_bags[0].insert(0, hold_pieces[0]) # insert the next hold piece as the new current piece
            hold_pieces.pop(0) # remove the inserted hold piece from the hold queue
        else:
            # only ever necessary if the hold queue wasn't already full
            gen_next_boards()
        
        # regen bags if the bag is emptied because of hold
        if not piece_bags[0]:
            piece_bags[0] = piece_bags[1]
            piece_bags[1] = generate_bag(piece_gen_type)
            
        # refresh current active piece
        piece_board = pieces_dict[(piece_bags[0] + piece_bags[1])[0]]["shapes"][STARTING_ROTATION] * piece_bags[0][0] # gets the next piece, this implementation is required cause holding can sometimes empty bag 1
        update_starting_coords()
        holds_used += 1

        update_ghost_piece()
        gen_hold_boards()

        # top-out check
        if check_collisions(0, 0, piece_board):
            top_out()
        
def move_piece(move_x, move_y):
    global piece_x, piece_y, piece_rotation, piece_board, game_state_changed
    current_shape = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation]
    move_dir_x = int((move_x > 0) - (move_x < 0)) # treats bools like integers then converts to int to get direction
    move_dir_y = int((move_y > 0) - (move_y < 0))
    steps_to_move = max(abs(move_x), abs(move_y), 1)
    remaining_steps = 0 # set to zero as default

    for step in range(steps_to_move): # loops over whichever number is farther from 0 (the most moves), min 1
        if not check_collisions(move_dir_x, move_dir_y, current_shape): # only goes through with the movement if no collisions occur
            piece_x = move_dir_x + piece_x # int(move_x > 0) returns 0 if move_x is 0, and 1 otherwise
            piece_y = move_dir_y + piece_y
            game_state_changed = True # this is set multiple times, but its fiiiine
        else: # break when first collision happens
            remaining_steps = steps_to_move - step
            break
    
    piece_board = current_shape * piece_bags[0][0]
    if move_x != 0: update_ghost_piece()
    return remaining_steps

def gen_next_boards():
    global next_boards
    
    next_boards = []
    next_list = (piece_bags[0] + piece_bags[1])[1:next_queue_size + 1] # gets a truncated next_pieces list

    print(next_list)
    for piece_id in next_list:
        piece_shape = pieces_dict[piece_id]["shapes"][0]
        board = numpy.zeros((5, 5), dtype=numpy.int8)  # 5x5 board for hold piece
        for coords in numpy.argwhere(piece_shape != 0):
            board[coords[0], coords[1]] = piece_id
        next_boards.append(board)

def gen_hold_boards():
    global hold_boards

    hold_boards = []

    for piece_id in hold_pieces:
        piece_shape = pieces_dict[piece_id]["shapes"][0]
        board = numpy.zeros((5, 5), dtype=numpy.int8)  # 5x5 board for hold piece
        for coords in numpy.argwhere(piece_shape != 0):
            board[coords[0], coords[1]] = piece_id
        hold_boards.append(board)
        
def clear_lines():
    global game_board, lines_cleared
    # returns a 1d array of booleans for each line, true if its completed, false if not
    lines_to_clear = numpy.all(game_board != 0, axis=1)
    line_clear_count = numpy.where(lines_to_clear)[0].size
    if line_clear_count > 0:
        lines_cleared += line_clear_count
        board_mask = game_board[~lines_to_clear] # masks the board, removing lines where the mask returned true
        new_lines = numpy.zeros((line_clear_count, settings.BOARD_WIDTH), dtype=numpy.int8)
        new_board = numpy.vstack((new_lines, board_mask), dtype=numpy.int8)
        update_game_board(new_board)

def lockdown(type, frametime):
    global lockdown_timer, prevent_harddrop_timer, prevent_harddrop_clock, prevent_harddrop_started
    global lockdown_start_x, lockdown_start_y, lockdown_start_rotation, lockdown_resets

    if current_gravity > 0.01:
        lockdown_threshold = settings.LOCKDOWN_THRESHOLD # default setting, won't be overriden for any mode but classic
    else: lockdown_threshold = math.inf

    if type == "GUIDELINE" or type == "STEP" and lockdown_timer == 0: # calculate starting coords for step and guideline style
        lockdown_start_x = piece_x
        lockdown_start_y = piece_y

    elif type == "CLASSIC": # calculate piece falling time for classic style
        if current_gravity == 0:
            lockdown_threshold = math.inf
        else:
            lockdown_threshold = 16.6666667/current_gravity

    lockdown_timer += frametime

    if type == "GUIDELINE": # update position if guideline type
        piece_moved = lockdown_start_x != piece_x or lockdown_start_y != piece_y or lockdown_start_rotation != piece_rotation
        if piece_moved and lockdown_resets > 0: # if the piece has moved at all
            lockdown_resets -= 1
            lockdown_timer = 0 # if the piece has moved, reset the timer
            lockdown_start_x = piece_x # reset the position variables
            lockdown_start_y = piece_y
            lockdown_start_rotation = piece_rotation

    elif type == "STEP":
        if lockdown_start_y < piece_y:
            lockdown_timer = 0 # if the piece has fallen, reset the timer
            lockdown_start_y = piece_y # reset the position variable

    if lockdown_timer >= lockdown_threshold:
        lockdown_resets = settings.LOCKDOWN_RESETS_COUNT
        prevent_harddrop_timer = 0 # start the harddrop delay timer
        prevent_harddrop_started = True
        prevent_harddrop_clock.tick()
        lock_piece()

def lock_piece():
    global game_board, piece_board, piece_bags, queue_spawn_piece, pieces_placed, lockdown_timer, history_index, board_state_changed
    new_board = game_board.copy()
    for coords in numpy.argwhere(piece_board != 0):
        new_board[piece_y + coords[0], piece_x + coords[1]] = piece_board[coords[0], coords[1]]
    piece_board = numpy.zeros_like(piece_board)
    piece_bags[0].pop(0)
    
    if not piece_bags[0]:
        piece_bags[0] = piece_bags[1]
        piece_bags[1] = generate_bag(piece_gen_type)

    lockdown_timer = 0
    pieces_placed += 1
    queue_spawn_piece = True
    board_state_changed = True
    
    # update the next piece early so it looks nice
    update_starting_coords()
    piece_board = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation] * piece_bags[0][0] # update piece board early so it looks nice

    update_game_board(new_board)
    clear_lines()
    update_ghost_piece()
    # this has to happen at the very end
    update_history()

def add_mino(x, y): # used for drawing directly on the board and other whatever else might add a single mino
    game_board[x, y] == -2
    
def handle_movement(keys):
    global running, das_timer, arr_timer, das_started, arr_started, das_reset_timer, das_reset_started, last_move_dir
    
    # find which horizontal input the user pressed (0 if none)
    if keys[settings.MOVE_LEFT] and not keys[settings.MOVE_RIGHT]:
        move_dir = -1
    elif keys[settings.MOVE_RIGHT] and not keys[settings.MOVE_LEFT]:
        move_dir = 1
    else:
        move_dir = 0
        
    # handle horizontal movement according to DAS and ARR rules
    if move_dir != 0:
        if (last_move_dir != move_dir and settings.DAS_RESET_THRESHOLD <= 0): # if switching movement direction (and DAS_RESET_THRESHOLD is set to 0), reset DAS and ARR
            das_timer = 0                                           # last_move_dir is set to 0 by default so it will reset for the first movement, but that doesn't matter because it starts that way anyways
            das_started = False
            arr_timer = 0
            arr_started = False
        
        last_move_dir = move_dir
        
        if not das_started:
            move_piece(move_dir, 0)
            das_started = True # start the DAS timer
            das_timer = 0
            das_clock.tick_busy_loop() # use tick_busy_loop for more precise ticking for das timer. causes performance issues
            
        else:
            das_timer += das_clock.tick_busy_loop() # use tick_busy_loop for more precise ticking for das timer. causes performance issues
            
            if (das_timer > das_threshold):
                if not arr_started and arr_threshold != 0:
                    move_piece(move_dir, 0)
                    arr_started = True # start the ARR timer
                    arr_timer = 0
                    arr_clock.tick()
                else:
                    arr_timer += arr_clock.tick()
                    if arr_timer >= arr_threshold:
                        if arr_threshold == 0: # avoids divide by 0 error
                            steps_to_move = settings.BOARD_WIDTH
                        else:
                            steps_to_move = int(arr_timer / arr_threshold)
                        move_piece(steps_to_move * move_dir, 0)
                        if arr_threshold == 0: # avoids divide by 0 error
                            arr_timer = 0
                        else:
                            arr_timer = arr_timer % arr_threshold
                            
    elif das_started: # saves performance by only checking this stuff when das_timer is still running
        if not das_reset_started:
            das_reset_timer = 0
            das_reset_clock.tick()
            das_reset_started = True
            
        else:
            das_reset_timer += das_reset_clock.tick()
            
        if (das_reset_timer >= settings.DAS_RESET_THRESHOLD): # if das reset timer goes through, then reset all timers
            das_timer = 0
            das_started = False
            das_reset_timer = 0
            das_reset_started = False
    
        arr_timer = 0 # reset the ARR timer only to keep things clean
        arr_started = False

def unpack_1kf_binds():
    global onekf_key_array
    for row, col in numpy.ndindex((4, 10)): # indexes through all coordinates in a 4x10 array
        string_index = (row * 10) + col
        onekf_key_array[row][col] = pygame.key.key_code(settings.ONEKF_STRING[string_index : string_index + 1])

def handle_1kf(key, keydir = "DOWN"):
    global piece_rotation, game_state_changed
    key_row, key_col = numpy.where(onekf_key_array == key)
    # converts keyboard rows into their rotation states
    match key_row:
        case 0:
            piece_rotation = 2
        case 1:
            piece_rotation = 3
        case 2:
            piece_rotation = 0
        case 3:
            piece_rotation = 1

    current_shape = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation]
    rightmost_point = numpy.max(numpy.where(current_shape != 0)[1]) # gets the distance between piece_x and the rightmost point of the piece
    leftmost_point = numpy.min(numpy.where(current_shape != 0)[1]) # this is usually 0, but needed for O piece

    if key_col < 5:
        steps_to_move = int(key_col - piece_x - leftmost_point) # cast to int since numpy.where always returns an array for some reason
    else:
        steps_to_move = int(key_col - piece_x - rightmost_point) # cast to int since numpy.where always returns an array for some reason
    
    game_state_changed = True
    move_piece(steps_to_move, 0) # done in two steps because otherwise it stops early when colliding with the wall
    move_piece(0, settings.BOARD_HEIGHT)
    lock_piece()
         
def top_out():
    # can add extra functionality later like displaying a score panel at the end
    reset_game()
    
def reset_game():
    global game_board, game_history, piece_board, piece_bags, hold_pieces, bag_count, holds_used
    global piece_x, piece_y, piece_rotation, hold_boards, next_boards
    global das_timer, arr_timer, sdr_timer, das_reset_timer, prevent_harddrop_timer
    global das_started, arr_started, sdr_started, das_reset_started, prevent_harddrop_started
    global last_move_dir, gravity_timer, softdrop_overrides, timer, lines_cleared, pieces_placed, queue_spawn_piece, STATE, board_state_changed, game_state_changed
    
    # Clear boards
    game_board = numpy.zeros_like(game_board)
    game_history = [None] * settings.MAX_HISTORY
    piece_board = numpy.zeros_like(piece_board)
    
    # Reset timers
    das_timer = arr_timer = sdr_timer = das_reset_timer = prevent_harddrop_timer = 0
    das_started = arr_started = sdr_started = das_reset_started = prevent_harddrop_started = False
    
    # Reset active piece
    piece_x = starting_x
    piece_y = starting_y
    piece_rotation = STARTING_ROTATION
    last_move_dir = 0
    gravity_timer = 0
    softdrop_overrides = True
    bag_count = 0
    queue_spawn_piece = True
    game_state_changed = True
    board_state_changed = True
    
    # Reset hold
    hold_boards = numpy.zeros((hold_pieces_count, 5, 5), dtype=numpy.int8)
    hold_pieces = []
    holds_used = 0
    
    # Reset piece bag, should usually be done again when loading gamemode
    piece_bags[0] = generate_bag(piece_gen_type)
    piece_bags[1] = generate_bag(piece_gen_type)
    
    # Reset stats
    timer.reset()
    lines_cleared = 0
    pieces_placed = 0
    STATE = 2

    gen_next_boards()
    update_ghost_piece()
    update_history()
    
def handle_sonic_drop(keys):
    global softdrop_overrides, game_state_changed
    if keys[settings.MOVE_SONICDROP and allow_sonic_drop]:
        softdrop_overrides = True
        return move_piece(0, settings.BOARD_HEIGHT)
    return 0

def handle_soft_drop(keys, frametime):
    global sdr_timer, sdr_started, softdrop_overrides
    if current_gravity > 0.001:
        softdrop_overrides = (sdr_threshold <= 16.666667 / current_gravity and keys[settings.MOVE_SOFTDROP]) # returns true if softdrop is pressed and is faster than gravity
    elif keys[settings.MOVE_SOFTDROP]:
        softdrop_overrides = True # returns true always if gravity is 0 (prevents divide by 0)
    else:
        softdrop_overrides = False
        
    if sdr_threshold == 0:
        steps_to_move = settings.BOARD_HEIGHT + 10
    else:
        steps_to_move = max(int(frametime / sdr_threshold), 1) # predicts how much softdrop should move for first button press
        
    if softdrop_overrides:
        if not sdr_started:
            sdr_timer = 0
            sdr_clock.tick()
            sdr_started = True
            return move_piece(0, steps_to_move) # returns remaining steps
        else:
            sdr_timer += sdr_clock.tick()
            if sdr_timer >= sdr_threshold:
                if sdr_threshold == 0: # avoids divide by 0 error
                    steps_to_move == settings.BOARD_HEIGHT + 10
                    sdr_timer = 0
                else:
                    steps_to_move = int(sdr_timer / sdr_threshold)
                    sdr_timer = sdr_timer % sdr_threshold

                return move_piece(0, steps_to_move) # returns remaining steps
    else:
        sdr_timer = 0
        sdr_started = False
    return 0
        
def hard_drop():
    global prevent_harddrop_clock, prevent_harddrop_timer, prevent_harddrop_started, prevent_harddrop_clock
    prevent_harddrop_timer += prevent_harddrop_clock.tick()
    if not prevent_harddrop_started or prevent_harddrop_timer >= settings.PREVENT_HARDDROP_THRESHOLD:
        move_piece(0, settings.BOARD_HEIGHT + 10)
        lock_piece()

    prevent_harddrop_timer = 0 # reset either way, because it only applies to the first hard drop after lockdown
    prevent_harddrop_clock.tick()
    prevent_harddrop_started = False # remove the timer flag
    
def handle_events():
    global running, STATE, game_state_changed
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if not settings.ONEKF_ENABLED:
                if event.key == settings.KEY_HOLD:
                    hold_guideline(infinite_holds)
                if event.key == settings.ROTATE_180:
                    if allow_180: rotate_piece(2)
                if event.key == settings.ROTATE_CW:
                    rotate_piece(1)
                if event.key == settings.ROTATE_CCW:
                    rotate_piece(3)
                if event.key == settings.ROTATE_MIRROR:
                    if allow_mirror: mirror_piece()
                if event.key == settings.MOVE_HARDDROP:
                    hard_drop()
                if event.key == settings.KEY_RESET:
                    reset_game()
                if event.key == settings.KEY_EXIT:
                    STATE -= 1
                if event.key == settings.KEY_UNDO:
                    undo(1)
            else:
                if numpy.isin(event.key, onekf_key_array):
                    handle_1kf(event.key)
                if event.key == settings.ONEKF_HOLD:
                    hold_guideline()

        if event.type == pygame.QUIT:
            running = False
            
def do_gravity(frametime):
    global gravity_timer, current_gravity, game_state_changed
    
    if current_gravity >= 15.8: # make instant drop at 20g regardless of framerate
        remaining_steps = move_piece(0, settings.BOARD_HEIGHT + 10)
        return remaining_steps
    
    elif current_gravity <= 0.0001: # disable gravity if too low
        return 0
    
    elif not softdrop_overrides: # only process gravity this frame if user isn't pressing the softdrop key
        gravity_timer += frametime # use frametime clock because precision is not necessary, only consistent pacing is
        if (gravity_timer >= 16.666667 / current_gravity):
            steps_to_move = int(gravity_timer / (16.666667 / current_gravity))
            remaining_steps = move_piece(0, steps_to_move)
            gravity_timer = gravity_timer % (16.666667 / current_gravity)
            return remaining_steps
    return 0
            
def do_leftover_gravity(remaining_steps): # for when a piece falls, touches the ground, then loses ground inside the same frame. prevents hanging for a frame.
    if remaining_steps != 0: # check if the piece can move at all
        move_piece(0, remaining_steps) # move the piece by the leftover amount from this frame

def handle_entry_delay(frametime, threshold = are_threshold): # currently buggy. need to fix
    global are_timer, queue_spawn_piece
    if threshold == 0 or not queue_spawn_piece: # if piece not spawning 
        return
    elif queue_spawn_piece and are_timer == 0: # if timer not started
        are_timer += frametime*0.9 # estimate of this frame's frametime inbetween locking and spawning pieces will be
    elif are_timer < threshold: # if timer not ready
        are_timer += frametime
    elif are_timer >= threshold:
        print(are_timer, "spawning")
        are_timer = 0
        queue_spawn_piece = False
        spawn_piece()

def load_gamemode(gamemode):
    global das_threshold, arr_threshold, sdr_threshold, are_threshold
    global pieces_dict, piece_types, piece_inversions, piece_size
    global hold_pieces_count 
    for attr, value in vars(gamemode).items():
        globals()[attr] = value
    # regenerate the bags
    piece_bags[0] = generate_bag(piece_gen_type)
    piece_bags[1] = generate_bag(piece_gen_type)
    
    

