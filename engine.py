    
# Engine

import pygame
import math
import numpy
from enum import Enum
import random
import pygame_gui
import os

import settings, pieces, skinloader

pygame.init()

running = True # so we can turn the game loop on and off

MAIN_SCREEN = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
GUI_manager = pygame_gui.UIManager((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))

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

game_board = numpy.zeros((settings.BOARD_HEIGHT, settings.BOARD_WIDTH), numpy.int8)
piece_board = numpy.zeros((settings.BOARD_HEIGHT, settings.BOARD_WIDTH), numpy.int8)

frametime_clock = pygame.time.Clock()
arr_clock = pygame.time.Clock()
das_clock = pygame.time.Clock()
sdr_clock = pygame.time.Clock()
das_reset_clock = pygame.time.Clock()
gravity_clock = pygame.time.Clock()
lockdown_clock = pygame.time.Clock()

bag_counter = 0
das_timer = 0
arr_timer = 0
sdr_timer = 0
das_reset_timer = 0
gravity_timer = 0
lockdown_timer = 0
das_timer_started = False
arr_timer_started = False
sdr_timer_started = False
das_reset_timer_started = False
softdrop_overrides = True

last_move_dir = 0
gravity_timer = 0
current_gravity = settings.STARTING_GRAVITY # measured in G (1g = 1 fall/frame, 20g = max speed at 60fps (should jump to like 200g though for more consistency))

piece_bags = [[],[]]
hold_pieces = []

pieces_dict = pieces.tetra_dict
piece_inversions = pieces.tetra_inversions
hold_pieces_count = settings.HOLD_PIECES_COUNT_TETRA

# if pentas exist and should be active, switch
if skinloader.has_penta and settings.is_penta:
    pieces_dict = pieces.penta_dict
    piece_inversions = pieces.penta_inversions
    hold_pieces_count = settings.HOLD_PIECES_COUNT_PENTA
    
hold_boards = numpy.zeros((hold_pieces_count, 5, 5), dtype=numpy.int8)
next_boards = numpy.zeros((settings.NEXT_PIECES_COUNT, 5, 5), dtype=numpy.int8)
topout_board = numpy.zeros((5, 5), dtype=numpy.int8)

PIECE_WIDTH = pieces_dict[1]["shapes"][0].shape[1] # gets the first shape of the first piece for reference.
PIECE_STARTING_X = (settings.BOARD_WIDTH//2) - (PIECE_WIDTH//2) # dynamically calculate starting position based on board and piece size.
PIECE_STARTING_Y = settings.BOARD_EXTRA_HEIGHT - (PIECE_WIDTH//5 + 1)
PIECE_STARTING_ROTATION = 0

piece_x = PIECE_STARTING_X
piece_y = PIECE_STARTING_Y
piece_rotation = PIECE_STARTING_ROTATION
ghost_piece_x = PIECE_STARTING_X
ghost_piece_y = PIECE_STARTING_Y

def generate_bag():
    global bag_counter
    bag_counter += 1
    
    generated_bag = []
    
    for piece, data in pieces_dict.items():
        # Skip if rare piece (x) and we're on an odd bag
        if data.get("rare", False) and bag_counter % 2 == 1:
            continue
        generated_bag.append(piece)
        
    random.shuffle(generated_bag)
    return generated_bag

def spawn_piece():
    global piece_x, piece_y, piece_rotation, next_boards, topout_board
    
    piece_x = PIECE_STARTING_X
    piece_y = PIECE_STARTING_Y
    piece_rotation = PIECE_STARTING_ROTATION
    
    current_shape = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation]
    next_pieces = (piece_bags[0] + piece_bags[1])[1:settings.NEXT_PIECES_COUNT + 1] # gets a truncated next_pieces list

    refresh_piece_board(current_shape)
    next_boards = gen_ui_boards(next_boards, next_pieces)
    fill_topboard(current_shape, next_pieces)

def fill_topboard(current_shape, next_pieces):
    global topout_board
    next_shape = pieces_dict[(piece_bags[0] + piece_bags[1])[1]]["shapes"][PIECE_STARTING_ROTATION]
    # --- Check top 5 rows for occupancy ---
    top_rows = game_board[:settings.BOARD_EXTRA_HEIGHT + 5, :]
    if numpy.any(top_rows != 0):
        topout_board = gen_topout_board(next_shape)
    else:
        topout_board = None
        
    # Normal top-out check
    if check_collisions(0, 0, current_shape):
        top_out()

def check_collisions(target_move_x, target_move_y, target_shape):
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
        if (game_board[coords[0] + new_y, coords[1] + new_x]): # check for collision with minos below the piece
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
    global piece_rotation, piece_board, piece_x, piece_y
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

    kick_list_right = [(0, 0), (0, 1), (-1, 1), (1, 1), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)] # checks left to right if kicking right
    kick_list_left = [(0, 0), (0, 1), (1, 1), (-1, 1), (1, 0), (-1, 0), (2, 0), (-2, 0), (0, -1)] # checks right to left if kicking left

    # there are some rotation states where using the biased lists wouldn't make sense, for example rotating a state 4 I piece to a state 1 or 3. 
    # it should be fine though because it only affects kick order, and if anything gives advanced players more control.

    # slightly weird i kick behaviour on edge with hole underneath platform like this iiii
    #                                                                                  ---
    if new_rotation == 0 and piece_bags[0][0] in (1, 3, 4, 5): # ensures the kick order is symmetrical for Z, S, O, I
        kick_list = kick_list_left
    else:
        kick_list = kick_list_right

    for kick in kick_list:
        kick_x, kick_y = kick
        if not check_collisions(kick_x, kick_y, new_shape): # continue if no collisions found
            piece_rotation = new_rotation
            # move the piece
            piece_x = piece_x + kick_x # update the position variables
            piece_y = piece_y + kick_y
            refresh_piece_board(new_shape)
            return
    
def mirror_piece():
    global piece_board, piece_bags
    
    piece_bags[0][0] = piece_inversions[piece_bags[0][0]]
    new_shape = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation]

    if not check_collisions(0, 0, new_shape):
        refresh_piece_board(new_shape)
    else:
        piece_bags[0][0] = piece_inversions[piece_bags[0][0]] # revert it back if collision

def hold_piece(): # mechanics need rewrite to check collision
    global piece_bags, hold_pieces, hold_boards
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
        
    # refresh current active piece
    new_shape = pieces_dict[(piece_bags[0] + piece_bags[1])[0]]["shapes"][piece_rotation] # gets the next piece, this implementation is required cause holding can sometimes empty bag 1
    refresh_piece_board(new_shape)
    hold_boards = gen_ui_boards(hold_boards, hold_pieces)
        
def move_piece(move_x, move_y):
    global piece_x, piece_y, piece_rotation, piece_board
    current_shape = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation]
    move_dir_x = int((move_x > 0) - (move_x < 0))
    move_dir_y = int((move_y > 0) - (move_y < 0))
    
    for _ in range(max(abs(move_x), abs(move_y), 1)): # loops over whichever number is farther from 0 (the most moves), min 1
        if not check_collisions(move_dir_x, move_dir_y, current_shape): # only goes through with the movement if no collisions occur
            piece_x = move_dir_x + piece_x # int(move_x > 0) returns 0 if move_x is 0, and 1 otherwise
            piece_y = move_dir_y + piece_y
        else: # when first collision happens, return false. this only makes sense if a single collision is being checked.
            refresh_piece_board(current_shape)
            return False
    refresh_piece_board(current_shape)
    if move_x != 0: update_ghost_piece()
    return True
    
def update_ghost_piece():
    global ghost_piece_x, ghost_piece_y
    ghost_piece_x = piece_x
    ghost_piece_y = 0
    current_shape = pieces_dict[piece_bags[0][0]]["shapes"][piece_rotation]
    for _ in range(settings.BOARD_HEIGHT):
        if not check_collisions(0, 1, current_shape):
            ghost_piece_y += 1
        else:
            break

def refresh_piece_board(piece_shape):
    global piece_board

    piece_board = numpy.zeros_like(piece_board) # clear the board. NEEDS OPTIMIZATION

    for coords in numpy.argwhere(piece_shape != 0): # returns a 1d numpy array of coordinates that meet the condition != 0
        piece_board[piece_y + coords[0]][piece_x + coords[1]] = piece_bags[0][0]

def gen_ui_boards(boards_list, pieces_list):
    boards_list = [] # clear previous
    for piece_id in pieces_list:
        piece_shape = pieces_dict[piece_id]["shapes"][0]
        board = numpy.zeros((5, 5), dtype=numpy.int8)  # 5x5 board for hold piece
        for coords in numpy.argwhere(piece_shape != 0):
            board[coords[0], coords[1]] = piece_id
        boards_list.append(board)
    return boards_list

def gen_topout_board(shape):
    """Return a 5×5 board with the shape centered."""
    board_size = 5
    board = numpy.zeros((board_size, board_size), dtype=int)
    shape_rows, shape_cols = shape.shape
    off_x = (board_size - shape_cols) // 2
    off_y = (board_size - shape_rows) // 2
    for r in range(shape_rows):
        for c in range(shape_cols):
            val = shape[r, c]
            if val:
                board[off_y + r, off_x + c] = val
    return board

def find_completed_lines():
    # returns a 1d array of booleans for each line, true if its completed, false if not
    lines_to_clear = numpy.all(game_board != 0, axis=1)
    if lines_to_clear.size > 0:
        clear_lines(lines_to_clear)
        
def clear_lines(lines_to_clear):
    global game_board
    lines_cleared = numpy.where(lines_to_clear)[0].size
    new_board = game_board[~lines_to_clear] # masks the board, removing lines where the mask returned true
    new_lines = numpy.zeros((lines_cleared, settings.BOARD_WIDTH), dtype=numpy.int8)
    game_board = numpy.vstack((new_lines, new_board), dtype=numpy.int8)
    
def handle_piece_lockdown(): # NEED TO IMPLEMENT PIECE FLASHING
    # the way this function is called causes a lot of issues!!! REWRITE IT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    global lockdown_timer
    lockdown_clock.tick()
    lockdown_timer += lockdown_clock.get_time()
    if (lockdown_timer >= math.inf): #LOCKDOWN_THRESHOLD):                  TEMPORARILY DISABLED BECAUSE THIS SUCKS
        lockdown_timer = 0
        lock_to_board()
    
def lock_to_board():
    global game_board, piece_board, piece_bags
    game_board[piece_board != 0] = piece_board[piece_board != 0]
    piece_board = numpy.zeros_like(piece_board)
    piece_bags[0].pop(0)
    
    if not piece_bags[0]:
        piece_bags[0] = piece_bags[1]
        piece_bags[1] = generate_bag()
        
    find_completed_lines()
    spawn_piece()
    
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
            das_clock.tick() # use tick_busy_loop for more precise ticking for das timer. causes performance issues
            
        else:
            das_clock.tick() # use tick_busy_loop for more precise ticking for das timer. causes performance issues
            das_timer += das_clock.get_time()
            
            if (das_timer > settings.DAS_THRESHOLD):
                if not arr_timer_started and settings.ARR_THRESHOLD != 0:
                    move_piece(move_dir, 0)
                    arr_timer_started = True # start the ARR timer
                    arr_timer = 0
                    arr_clock.tick()
                else:
                    arr_clock.tick()
                    arr_timer += arr_clock.get_time()
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
            das_reset_clock.tick()
            das_reset_timer += das_reset_clock.get_time()
            
        if (das_reset_timer >= settings.DAS_RESET_THRESHOLD): # if das reset timer goes through, then reset all timers
            das_timer = 0
            das_timer_started = False
            das_reset_timer = 0
            das_reset_timer_started = False
    
        arr_timer = 0 # reset the ARR timer only to keep things clean
        arr_timer_started = False

def top_out():
    # can add extra functionality later like displaying a score panel at the end
    reset_game()
    
def reset_game():
    global game_board, piece_board, piece_bags, hold_pieces, bag_counter
    global piece_x, piece_y, piece_rotation
    global das_timer, arr_timer, sdr_timer, das_reset_timer
    global das_timer_started, arr_timer_started, sdr_timer_started, das_reset_timer_started
    global last_move_dir, gravity_timer, softdrop_overrides
    global hold_boards, next_boards
    
    # Clear boards
    game_board = numpy.zeros((settings.BOARD_HEIGHT, settings.BOARD_WIDTH), numpy.int8)
    piece_board = numpy.zeros((settings.BOARD_HEIGHT, settings.BOARD_WIDTH), numpy.int8)
    
    # Reset timers
    das_timer = arr_timer = sdr_timer = das_reset_timer = 0
    das_timer_started = arr_timer_started = sdr_timer_started = das_reset_timer_started = False
    
    # Reset active piece
    piece_x = PIECE_STARTING_X
    piece_y = PIECE_STARTING_Y
    piece_rotation = PIECE_STARTING_ROTATION
    last_move_dir = 0
    gravity_timer = 0
    softdrop_overrides = True
    bag_counter = 0
    
    # Reset hold
    hold_boards = numpy.zeros((hold_pieces_count, 5, 5), dtype=numpy.int8)
    hold_pieces = []
    
    # Reset piece bag
    piece_bags[0] = generate_bag()
    piece_bags[1] = generate_bag()

    # generate the next boards
    next_pieces = (piece_bags[0] + piece_bags[1])[1:settings.NEXT_PIECES_COUNT + 1] # gets a truncated next_pieces list
    next_boards = gen_ui_boards(next_boards, next_pieces)

    spawn_piece()
    update_ghost_piece()
    
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
            move_piece(0, steps_to_move)
        else:
            sdr_clock.tick()
            sdr_timer += sdr_clock.get_time()
            if sdr_timer >= settings.SDR_THRESHOLD:
                if settings.SDR_THRESHOLD == 0: # avoids divide by 0 error
                    steps_to_move == settings.BOARD_HEIGHT + 10
                    sdr_timer = 0
                else:
                    steps_to_move = int(sdr_timer / settings.SDR_THRESHOLD)
                    sdr_timer = sdr_timer % settings.SDR_THRESHOLD
                move_piece(0, steps_to_move)
    else:
        sdr_timer = 0
        sdr_timer_started = False
        
def handle_hard_drop():
    move_piece(0, settings.BOARD_HEIGHT + 10)
    lock_to_board()
    
def handle_events():
    global running
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == settings.KEY_HOLD:
                hold_piece()
            if event.key == settings.ROTATE_180:
                rotate_piece(2)
            if event.key == settings.ROTATE_CW:
                rotate_piece(1)
            if event.key == settings.ROTATE_CCW:
                rotate_piece(3)
            if event.key == settings.ROTATE_MIRROR:
                mirror_piece()
            if event.key == settings.MOVE_HARDDROP:
                handle_hard_drop()
            if event.key == settings.KEY_RESET:
                reset_game()
            if event.key == settings.KEY_SWAP:
                handle_swap_mode()
        if event.type == pygame.QUIT:
            running = False
            
def handle_gravity(frametime):
    global gravity_timer, current_gravity
    if current_gravity >= 19.8: # make instant drop at 20g regardless of framerate
        move_piece(0, settings.BOARD_HEIGHT + 10) 
    elif current_gravity <= 0.0001: # disable gravity if too low
        return  
    elif not softdrop_overrides: # only process gravity this frame if user isn't pressing the softdrop key
        gravity_timer += frametime # use frametime clock because precision is not necessary, only consistent pacing is
        if (gravity_timer >= 16.666667 / current_gravity):
            steps_to_move = int(gravity_timer / (16.666667 / current_gravity))
            move_piece(0, steps_to_move)
            gravity_timer = gravity_timer % (16.666667 / current_gravity)
            
def handle_swap_mode():
    global pieces_dict, piece_inversions, hold_pieces_count
    if skinloader.has_penta == False:
        print("Your skin does not support pentaminos!")
        return
    global PIECE_TYPES, pieces_dict, piece_inversions
    settings.is_penta = not settings.is_penta
    PIECE_TYPES = 18 if settings.is_penta else 7
    pieces_dict = pieces.tetra_dict
    piece_inversions = pieces.tetra_inversions
    hold_pieces_count = settings.HOLD_PIECES_COUNT_TETRA
    
    # if pentas exist and should be active, switch
    if skinloader.has_penta and settings.is_penta:
        pieces_dict = pieces.penta_dict
        piece_inversions = pieces.penta_inversions
        hold_pieces_count = settings.HOLD_PIECES_COUNT_PENTA
        
    reset_game()
