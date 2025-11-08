# Skin-Loader

import pygame
import os

import settings

script_dir = os.path.dirname(os.path.abspath(__file__))
skins_dir = os.path.join(script_dir, "skin")

# Load first PNG in skins dir
sprite_file = next(file for file in os.listdir(skins_dir) if file.lower().endswith(".png"))
sprite_sheet = pygame.image.load(os.path.join(skins_dir, sprite_file))

sheet_width, sheet_height = sprite_sheet.get_size()

def is_solid_red(color, tol=5):
    r, g, b, a = color
    return abs(r - 255) <= tol and g <= tol and b <= tol and a >= 250

top_right_pixel = sprite_sheet.get_at((sheet_width-1, 0))
has_penta = is_solid_red(top_right_pixel)

# Determine cell size
if has_penta:
    cell_size_tetra = sheet_height // 2
    cell_size_penta = sheet_height // 2
else:
    cell_size_tetra = sheet_height
    cell_size_penta = None  # ignored
    
cell_spacing = 1

# --- Load tetra skins (top-left column) ---
tetra_skins = []
for i in range(settings.PIECE_TYPES_TETRA):
    cell_x = (cell_size_tetra + cell_spacing) * i
    cell_rect = pygame.Rect((cell_x, 0), (cell_size_tetra, cell_size_tetra))
    raw_skin = sprite_sheet.subsurface(cell_rect)
    scaled_skin = pygame.transform.scale(raw_skin, (settings.CELL_SIZE, settings.CELL_SIZE))
    tetra_skins.append(scaled_skin)

# --- Load penta skins (top-right column) ---
penta_skins = []
if has_penta:
    for i in range(settings.PIECE_TYPES_PENTA):
        # second column: x = cell_size_penta + spacing?
        cell_x = (cell_size_penta + cell_spacing) * i
        cell_y = cell_size_penta + cell_spacing  # second row
        cell_rect = pygame.Rect((cell_x, cell_y), (cell_size_penta, cell_size_penta))
        raw_skin = sprite_sheet.subsurface(cell_rect)
        scaled_skin = pygame.transform.scale(raw_skin, (settings.CELL_SIZE, settings.CELL_SIZE))
        penta_skins.append(scaled_skin)
        
# --- Load other skins (right of top-left column) preserving original transparency ---
other_skins = []

def set_other_skins():
    for i in range(5):
        cell_x = (cell_size_tetra + cell_spacing) * (settings.PIECE_TYPES_TETRA + i)  # skip tetraminos
        cell_rect = pygame.Rect((cell_x, 0), (cell_size_tetra, cell_size_tetra))
        
        # Extract and scale the sprite
        raw_skin = sprite_sheet.subsurface(cell_rect)
        scaled_skin = pygame.transform.scale(raw_skin, (settings.CELL_SIZE, settings.CELL_SIZE))
        
        # Keep per-pixel alpha from PNG
        scaled_skin = scaled_skin.convert_alpha()
        
        other_skins.append(scaled_skin)
        

script_dir = os.path.dirname(os.path.abspath(__file__))
wallpaper_dir = os.path.join(script_dir, "wallpaper")

# Find the first image in /wallpaper/ and store its path
wallpaper_file = next(
    (f for f in os.listdir(wallpaper_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))),
    None
)

settings.WALLPAPER_PATH = os.path.join(wallpaper_dir, wallpaper_file) if wallpaper_file else None