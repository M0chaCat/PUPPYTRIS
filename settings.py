# Settings

import pygame
import os
import json

DISPLAY_WIDTH = 3440 # for fullscreen? implement this later!!!
DISPLAY_HEIGHT = 1440

BOARD_WIDTH = 10
BOARD_MAIN_HEIGHT = 20
BOARD_EXTRA_HEIGHT = 4
BOARD_HEIGHT = BOARD_MAIN_HEIGHT + BOARD_EXTRA_HEIGHT

DESIGN_WINDOW_WIDTH = 1400 #DONT CHANGE!!!!!
DESIGN_WINDOW_HEIGHT = 1000 #ME NEITHER!!!! SPARE ME!!!!!

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 1000

SCALEX = DESIGN_WINDOW_WIDTH / WINDOW_WIDTH
SCALEY = DESIGN_WINDOW_HEIGHT / WINDOW_HEIGHT
SCALE = min(WINDOW_WIDTH / DESIGN_WINDOW_WIDTH, WINDOW_HEIGHT / DESIGN_WINDOW_HEIGHT)

MAX_FRAMERATE = 60

if BOARD_WIDTH / WINDOW_WIDTH < BOARD_HEIGHT / WINDOW_HEIGHT:
    CELL_SIZE = WINDOW_HEIGHT//(BOARD_HEIGHT - BOARD_EXTRA_HEIGHT + 5) # +5 so its not too zoomed in
else: # if the board is REALLY wide
    CELL_SIZE = WINDOW_WIDTH//(BOARD_WIDTH + 20) # TODO: improve the formula for calculating CELL_SIZE
    

# --- Config / constants ---
PIECE_TYPES_TETRA = 7
PIECE_TYPES_PENTA = 18
HOLD_PIECES_COUNT_TETRA = 1
HOLD_PIECES_COUNT_PENTA = 2
NEXT_PIECES_COUNT = 5
INFINITE_HOLDS = False

is_penta = False

DAS_THRESHOLD = 100
ARR_THRESHOLD = 0
SDR_THRESHOLD = 0 # SDR = soft drop rate
DAS_RESET_THRESHOLD = 0 # experimental mechanic that causes DAS to stay charged for the duration of the value in MS
PREVENT_HARDDROP_THRESHOLD = 300

STARTING_GRAVITY = 0
MAX_BOARD_HISTORY = 1000
LOCKDOWN_THRESHOLD = 1000 # not a user variable

ONEKF_ENABLED = False
ONEKF_PRACTICE = True
ONEKF_STRING = "1234567890qwertyuiopasdfghjkl;zxcvbnm,./"
ONEKF_HOLD = pygame.K_SPACE

MOVE_LEFT = pygame.K_LEFT
MOVE_RIGHT = pygame.K_RIGHT
MOVE_SOFTDROP = pygame.K_DOWN
MOVE_SONICDROP = pygame.K_UP
MOVE_HARDDROP = pygame.K_SPACE
ROTATE_CW = pygame.K_z
ROTATE_CCW = pygame.K_x
ROTATE_180 = pygame.K_a
KEY_HOLD = pygame.K_c
ROTATE_MIRROR = pygame.K_s
KEY_UNDO = pygame.K_z
KEY_RESET = pygame.K_r
KEY_EXIT = pygame.K_ESCAPE

TRANSPARENCY_MAIN = 230
TRANSPARENCY_BOARD = 220
TRANSPARENCY_TEXT = 250

BOARD_COLOR = (30, 30, 46, TRANSPARENCY_BOARD)
BACKGROUND_COLOR = (24, 24, 37)
PANEL_COLOR = (64, 66, 86, TRANSPARENCY_MAIN)
PANEL_COLOR_HOVER = (128, 132, 172, TRANSPARENCY_MAIN)
PANEL_OUTLINE = (108, 112, 134, TRANSPARENCY_MAIN)
GRID_COLOR = (88, 91, 112)
TEXT_COLOR = (250, 250, 250, TRANSPARENCY_TEXT)
CRUST_COLOR = (17, 17, 27, TRANSPARENCY_MAIN)
DRAW_COLOR = (205, 214, 244)
UI_COLOR = (203, 166, 247)
USE_SKIN = False
WALLPAPER = None  # will hold the loaded surface after pygame.init()

# load the settings
with open("settings.json", "r") as file:
    user_settings = json.load(file)
    globals().update(user_settings)

# load the font
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_dir = os.path.join(script_dir, "Konstruktor.otf")
except Exception as e:

    print("Font load failed:", e)
