    
# Engine

import pygame
import math
import numpy
import random
import os
import time
import copy

import settings, pieces, skinloader

pygame.init()

STATE = 0

running = True # so we can turn the game loop on and off

# DISPLAY_WIDTH = 3440
# DISPLAY_HEIGHT = 1440 # implement this later!!!

PIECE_TYPES = 18 if settings.is_penta else 7 

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

frametime_clock = pygame.time.Clock()
arr_clock = pygame.time.Clock()
das_clock = pygame.time.Clock()
sdr_clock = pygame.time.Clock()
das_reset_clock = pygame.time.Clock()
gravity_clock = pygame.time.Clock()
lockdown_clock = pygame.time.Clock()
onekf_prac_clock = pygame.time.Clock()
prevent_harddrop_clock = pygame.time.Clock()

lines_cleared = 0
pieces_placed = 0
pps = 0
bag_count = 0
rng_seed = random.getstate()
rng_state = rng_seed
history_index = 0
das_timer = 0
arr_timer = 0
sdr_timer = 0
das_reset_timer = 0
gravity_timer = 0
lockdown_timer = 0
onekf_prac_timer = 0
prevent_harddrop_timer = 0
das_timer_started = False
arr_timer_started = False
sdr_timer_started = False
das_reset_timer_started = False
onekf_prac_timer_started = False
prevent_harddrop_timer_started = False
softdrop_overrides = True
game_state_changed = False
queue_spawn_piece = True

last_move_dir = 0
gravity_timer = 0
current_gravity = settings.STARTING_GRAVITY # measured in G (1g = 1 fall/frame, 20g = max speed at 60fps (should jump to like 200g though for more consistency))

piece_bags = [[],[]]
hold_pieces = []

pieces_dict = pieces.tetra_dict
piece_inversions = pieces.tetra_inversions
hold_pieces_count = settings.HOLD_PIECES_COUNT_TETRA
holds_left = hold_pieces_count
piece_gen_type = "CLASSIC"

# if pentas exist and should be active, switch
if skinloader.has_penta and settings.is_penta:
    pieces_dict = pieces.penta_dict
    piece_inversions = pieces.penta_inversions
    hold_pieces_count = settings.HOLD_PIECES_COUNT_PENTA
    
hold_boards = numpy.zeros((hold_pieces_count, 5, 5), dtype=numpy.int8)
next_boards = numpy.zeros((settings.NEXT_PIECES_COUNT, 5, 5), dtype=numpy.int8)
topout_board = numpy.zeros((5, 5), dtype=numpy.int8)

onekf_key_array = numpy.zeros((4, 10), dtype=int) # int8 is too small

piece_width = 4
starting_x = 3
starting_y = 2
STARTING_ROTATION = 0

game_board = numpy.zeros((settings.BOARD_HEIGHT, settings.BOARD_WIDTH), numpy.int8)
game_history = [None] * settings.MAX_HISTORY
piece_board = numpy.zeros((piece_width, piece_width), numpy.int8)
ghost_board = numpy.zeros_like(piece_board)

piece_x = starting_x
piece_y = starting_y
piece_rotation = STARTING_ROTATION
ghost_piece_x = starting_x
ghost_piece_y = starting_y
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
    global piece_width, piece_x, piece_y, starting_x, starting_y, piece_rotation
    piece_shape = pieces_dict[piece_bags[0][0]]["shapes"][STARTING_ROTATION]
    piece_width = piece_shape.shape[1]
    height_offset = numpy.where(numpy.any(piece_shape != 0, axis=1))[0][0]
    starting_x = (settings.BOARD_WIDTH - piece_width) // 2 # dynamically calculate starting position based on board and piece size.
    starting_y = settings.BOARD_EXTRA_HEIGHT - piece_width//5 - height_offset + settings.SPAWN_Y_OFFSET # need to subtract the blank space in the piece here
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
            piece = random.randint(1, PIECE_TYPES)
            generated_bag.append(piece)

    elif (type == "CLASSIC"):
        for i in range(7):
            if not piece_bags[0] and i == 0:
                prev_piece = -1
            elif i == 0:
                prev_piece = (piece_bags[0] + piece_bags[1])[0]
            else:
                prev_piece = generated_bag[0]
            piece = random.randint(0, PIECE_TYPES)
            if (piece == 0 or piece == prev_piece):
                piece = random.randint(1, PIECE_TYPES)
            generated_bag.insert(0, piece)

    return generated_bag

def spawn_piece():
    global piece_x, piece_y, piece_rotation, next_boards, topout_board, piece_board, queue_spawn_piece, holds_left, game_state_changed
    queue_spawn_piece = False
    update_starting_coords()
    holds_left = hold_pieces_count
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
    global piece_x, piece_y, piece_rotation, holds_left, piece_board, queue_spawn_piece
    global game_state_changed, history_index
    if pieces_placed - amount >= 0:
        game_state_changed = True
        history_index -= amount
        if history_index < 0:
            history_index = settings.MAX_HISTORY - amount # make sure this doesn't miss one

        # revert history
        print("1")
        state = game_history[history_index]
        print("2")
        game_board = copy.deepcopy(state["board"])
        print("3")
        pieces_placed = state["pieces"]
        print("4")
        lines_cleared = state["lines"]
        print("5")
        piece_bags = copy.deepcopy(state["next"])
        print("6")
        hold_pieces = copy.deepcopy(state["hold"])
        print("7")
        rng_state = state["rng"]
        print("8")
        bag_count = state["bag_count"]
        print("9")

        # reset position
        update_starting_coords()
        holds_left = hold_pieces_count
        random.setstate(rng_state)

        piece_board = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation] * piece_bags[0][0] # update piece board early so it looks nice
        queue_spawn_piece = True
        # updating all these even thought spawn_piece does it for us because want it to update on frame 0
        gen_topout_board()
        gen_hold_boards()
        gen_next_boards()
        update_ghost_piece()

def gen_topout_board():
    global topout_board
    next_width = pieces_dict[(piece_bags[0] + piece_bags[1])[1]]["shapes"][piece_rotation].shape[0]
    board_size = next_width
    topout_board = numpy.zeros((board_size, board_size), dtype=numpy.int8)
    next_shape = pieces_dict[(piece_bags[0] + piece_bags[1])[1]]["shapes"][STARTING_ROTATION]

    # --- Check top 4/5 rows for occupancy ---
    top_rows = settings.BOARD_EXTRA_HEIGHT + next_width + math.floor(settings.BOARD_HEIGHT/8) - 1 # 1 row less for boards < 24 high, and 2 less for boards < 8 high
    top_rows = game_board[:top_rows]
    if numpy.all(top_rows == 0):
        topout_board = None
    else:
        topout_board = next_shape

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
    global piece_bags, hold_pieces, hold_boards, next_boards, game_state_changed, holds_left
    global piece_x, piece_y, piece_rotation, piece_board
    game_state_changed = True

    if holds_left > 0 or infinite_holds:
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
        holds_left -= 1

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
    next_list = (piece_bags[0] + piece_bags[1])[1:settings.NEXT_PIECES_COUNT + 1] # gets a truncated next_pieces list

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
    global lockdown_timer, prevent_harddrop_timer, prevent_harddrop_clock, prevent_harddrop_timer_started
    global lockdown_start_x, lockdown_start_y, lockdown_start_rotation, lockdown_resets

    lockdown_threshold = settings.LOCKDOWN_THRESHOLD # default setting, won't be overriden for any mode but classic

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
        prevent_harddrop_timer_started = True
        prevent_harddrop_clock.tick()
        lock_piece()

def lock_piece():
    global game_board, piece_board, piece_bags, queue_spawn_piece, pieces_placed, lockdown_timer, history_index
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
    
    # update the next piece early so it looks nice
    update_starting_coords()
    piece_board = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation] * piece_bags[0][0] # update piece board early so it looks nice

    update_game_board(new_board)
    clear_lines()
    update_ghost_piece()
    # this has to happen at the very end
    update_history()
    
def handle_movement(keys):
    global running, das_timer, arr_timer, das_timer_started, arr_timer_started, das_reset_timer, das_reset_timer_started, last_move_dir
    
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
            das_timer_started = False
            arr_timer = 0
            arr_timer_started = False
        
        last_move_dir = move_dir
        
        if not das_timer_started:
            move_piece(move_dir, 0)
            das_timer_started = True # start the DAS timer
            das_timer = 0
            das_clock.tick_busy_loop() # use tick_busy_loop for more precise ticking for das timer. causes performance issues
            
        else:
            das_timer += das_clock.tick_busy_loop() # use tick_busy_loop for more precise ticking for das timer. causes performance issues
            
            if (das_timer > settings.DAS_THRESHOLD):
                if not arr_timer_started and settings.ARR_THRESHOLD != 0:
                    move_piece(move_dir, 0)
                    arr_timer_started = True # start the ARR timer
                    arr_timer = 0
                    arr_clock.tick()
                else:
                    arr_timer += arr_clock.tick()
                    if arr_timer >= settings.ARR_THRESHOLD:
                        if settings.ARR_THRESHOLD == 0: # avoids divide by 0 error
                            steps_to_move = settings.BOARD_WIDTH
                        else:
                            steps_to_move = int(arr_timer / settings.ARR_THRESHOLD)
                        move_piece(steps_to_move * move_dir, 0)
                        if settings.ARR_THRESHOLD == 0: # avoids divide by 0 error
                            arr_timer = 0
                        else:
                            arr_timer = arr_timer % settings.ARR_THRESHOLD
                            
    elif das_timer_started: # saves performance by only checking this stuff when das_timer is still running
        if not das_reset_timer_started:
            das_reset_timer = 0
            das_reset_clock.tick()
            das_reset_timer_started = True
            
        else:
            das_reset_timer += das_reset_clock.tick()
            
        if (das_reset_timer >= settings.DAS_RESET_THRESHOLD): # if das reset timer goes through, then reset all timers
            das_timer = 0
            das_timer_started = False
            das_reset_timer = 0
            das_reset_timer_started = False
    
        arr_timer = 0 # reset the ARR timer only to keep things clean
        arr_timer_started = False

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
    global game_board, game_history, piece_board, piece_bags, hold_pieces, bag_count, holds_left
    global piece_x, piece_y, piece_rotation, hold_boards, next_boards
    global das_timer, arr_timer, sdr_timer, das_reset_timer, prevent_harddrop_timer
    global das_timer_started, arr_timer_started, sdr_timer_started, das_reset_timer_started, prevent_harddrop_timer_started
    global last_move_dir, gravity_timer, softdrop_overrides, timer, lines_cleared, pieces_placed, queue_spawn_piece, STATE, game_state_changed
    
    # Clear boards
    game_board = numpy.zeros_like(game_board)
    game_history = [None] * settings.MAX_HISTORY
    piece_board = numpy.zeros_like(piece_board)
    
    # Reset timers
    das_timer = arr_timer = sdr_timer = das_reset_timer = prevent_harddrop_timer = 0
    das_timer_started = arr_timer_started = sdr_timer_started = das_reset_timer_started = prevent_harddrop_timer_started = False
    
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
    
    # Reset hold
    hold_boards = numpy.zeros((hold_pieces_count, 5, 5), dtype=numpy.int8)
    hold_pieces = []
    holds_left = hold_pieces_count
    
    # Reset piece bag
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
    if keys[settings.MOVE_SONICDROP]:
        softdrop_overrides = True
        return move_piece(0, settings.BOARD_HEIGHT)
    return 0

def handle_soft_drop(keys, frametime):
    global sdr_timer, sdr_timer_started, softdrop_overrides
    if current_gravity > 0.001:
        softdrop_overrides = (settings.SDR_THRESHOLD <= 16.666667 / current_gravity and keys[settings.MOVE_SOFTDROP]) # returns true if softdrop is pressed and is faster than gravity
    elif keys[settings.MOVE_SOFTDROP]:
        softdrop_overrides = True # returns true always if gravity is 0 (prevents divide by 0)
    else:
        softdrop_overrides = False
        
    if settings.SDR_THRESHOLD == 0:
        steps_to_move = settings.BOARD_HEIGHT + 10
    else:
        steps_to_move = max(int(frametime / settings.SDR_THRESHOLD), 1) # predicts how much softdrop should move for first button press
        
    if softdrop_overrides:
        if not sdr_timer_started:
            sdr_timer = 0
            sdr_clock.tick()
            sdr_timer_started = True
            return move_piece(0, steps_to_move) # returns remaining steps
        else:
            sdr_timer += sdr_clock.tick()
            if sdr_timer >= settings.SDR_THRESHOLD:
                if settings.SDR_THRESHOLD == 0: # avoids divide by 0 error
                    steps_to_move == settings.BOARD_HEIGHT + 10
                    sdr_timer = 0
                else:
                    steps_to_move = int(sdr_timer / settings.SDR_THRESHOLD)
                    sdr_timer = sdr_timer % settings.SDR_THRESHOLD

                return move_piece(0, steps_to_move) # returns remaining steps
    else:
        sdr_timer = 0
        sdr_timer_started = False
    return 0
        
def hard_drop():
    global prevent_harddrop_clock, prevent_harddrop_timer, prevent_harddrop_timer_started, prevent_harddrop_clock
    prevent_harddrop_timer += prevent_harddrop_clock.tick()
    if not prevent_harddrop_timer_started or prevent_harddrop_timer >= settings.PREVENT_HARDDROP_THRESHOLD:
        move_piece(0, settings.BOARD_HEIGHT + 10)
        lock_piece()

    prevent_harddrop_timer = 0 # reset either way, because it only applies to the first hard drop after lockdown
    prevent_harddrop_clock.tick()
    prevent_harddrop_timer_started = False # remove the timer flag
    
def handle_events():
    global running, STATE, game_state_changed
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if not settings.ONEKF_ENABLED:
                if event.key == settings.KEY_HOLD:
                    hold_guideline(settings.INFINITE_HOLDS)
                if event.key == settings.ROTATE_180:
                    rotate_piece(2)
                if event.key == settings.ROTATE_CW:
                    rotate_piece(1)
                if event.key == settings.ROTATE_CCW:
                    rotate_piece(3)
                if event.key == settings.ROTATE_MIRROR:
                    mirror_piece()
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

def swap_mode(usepenta):
    global pieces_dict, piece_inversions, hold_pieces_count, holds_left
    if not skinloader.has_penta and usepenta:
        print("Your skin does not support pentaminos!")
        return
    global PIECE_TYPES, pieces_dict, piece_inversions
    settings.is_penta = usepenta
    PIECE_TYPES = settings.PIECE_TYPES_PENTA if settings.is_penta else settings.PIECE_TYPES_TETRA
    pieces_dict = pieces.tetra_dict
    piece_inversions = pieces.tetra_inversions
    hold_pieces_count = settings.HOLD_PIECES_COUNT_TETRA
    holds_left = settings.HOLD_PIECES_COUNT_TETRA
    
    # if pentas exist and should be active, switch
    if skinloader.has_penta and settings.is_penta:
        pieces_dict = pieces.penta_dict
        piece_inversions = pieces.penta_inversions
        hold_pieces_count = settings.HOLD_PIECES_COUNT_PENTA

        holds_left = settings.HOLD_PIECES_COUNT_TETRA
