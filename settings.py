# Settings

import pygame
import math
import numpy
from enum import Enum
import random
import pygame_gui
import os

# DISPLAY_WIDTH = 3440
# DISPLAY_HEIGHT = 1440 # implement this later!!!

BOARD_EXTRA_HEIGHT = 10
BOARD_WIDTH = 10
BOARD_HEIGHT = 20 + BOARD_EXTRA_HEIGHT

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 1000
MAX_FRAMERATE = 60

#if BOARD_WIDTH / WINDOW_WIDTH < BOARD_HEIGHT / WINDOW_HEIGHT:
CELL_SIZE = WINDOW_HEIGHT//(BOARD_HEIGHT - BOARD_EXTRA_HEIGHT + 5) # +2 so its not too zoomed in
#else: # if the board is REALLY wide # kity note: dis seems useless? # pupy note: is not :3 jus need to get it workying
    #CELL_SIZE = WINDOW_WIDTH//(BOARD_HEIGHT - BOARD_EXTRA_HEIGHT + 2)
    

# --- Config / constants ---
PIECE_TYPES_TETRA = 7
PIECE_TYPES_PENTA = 18
HOLD_PIECES_AMOUNT_TETRA = 1
HOLD_PIECES_AMOUNT_PENTA = 2

is_penta = False

DAS_THRESHOLD = 150
ARR_THRESHOLD = 33
SDR_THRESHOLD = 0 # SDR = soft drop rate
DAS_RESET_THRESHOLD = 0
STARTING_GRAVITY = 0

LOCKDOWN_THRESHOLD = 2000 # not a user variable

MOVE_LEFT = pygame.K_LEFT
MOVE_RIGHT = pygame.K_RIGHT
MOVE_SOFTDROP = pygame.K_DOWN
MOVE_HARDDROP = pygame.K_SPACE
ROTATE_CW = pygame.K_x
ROTATE_CCW = pygame.K_z
ROTATE_180 = pygame.K_c
ROTATE_MIRROR = pygame.K_a
KEY_HOLD = pygame.K_v
KEY_SWAP = pygame.K_q
KEY_RESET = pygame.K_r

BOARD_COLOR = (30, 30, 46)
BACKGROUND_COLOR = (24, 24, 37)
GRID_COLOR = (88, 91, 112)
TEXT_COLOR = (205, 214, 244)
CRUST_COLOR = (17, 17, 27)
OVERLAY_COLOR = (108, 112, 134)
GRID_COLOR_LEGIT = (205, 214, 244, 0.5) # make this the real one and make rgba work!!!
DRAW_COLOR = (205, 214, 244)
UI_COLOR = (203, 166, 247)
USE_SKIN = False
WALLPAPER = None  # will hold the loaded surface after pygame.init()

# load the font
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(script_dir, "Konstruktor.otf")
except Exception as e:
    print("Font load failed:", e)



