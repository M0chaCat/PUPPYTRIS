# Main

import pygame
import math
import numpy
from enum import Enum
import random
import pygame_gui
import os

import engine, ui, settings, skinloader

pygame.init()

pygame.display.set_caption("puppytris!!!!!")

if settings.WALLPAPER_PATH:
    settings.WALLPAPER = pygame.image.load(settings.WALLPAPER_PATH).convert_alpha()

# Text (top-left)
font_size = 24
try:
    font = pygame.font.Font(settings.font_dir, font_size)
except:
    font = pygame.font.SysFont(None, font_size)
    

while engine.running:
    engine.frametime_clock.tick(settings.MAX_FRAMERATE)
    frametime = engine.frametime_clock.get_time()
    keys = pygame.key.get_pressed()
    
    if not engine.current_bag: # generate the first bag
        engine.current_bag = engine.generate_bag()
    
    engine.handle_soft_drop(keys, frametime) # soft drop handled before gravity, because it has to override it
    engine.handle_events()
    engine.handle_gravity(frametime)
    engine.handle_movement(keys) # horizontal movement handled after gravity, because tetrio does it this way and it kinda makes sense
    
    if engine.spawn_new_piece:
        engine.spawn_piece(engine.current_bag)
        engine.spawn_new_piece = False
        
    ui.draw_background()
    ui.draw_board_extension()
    ui.draw_left_panel()
    ui.draw_right_panel()
    ui.draw_board_background()
    ui.draw_board(engine.game_board)
    ui.draw_board(engine.piece_board)
    ui.draw_grid_lines()
    
    fps = str(int(engine.frametime_clock.get_fps()))
    #pygame.display.set_caption(f"FPS: {fps}")
    
    fps_surf = font.render(fps, True, settings.TEXT_COLOR)
    ui.draw_rect(0, 0, 60, 40, settings.BOARD_COLOR, cut_corners=['bottom-right'], cut_size=10)
    engine.MAIN_SCREEN.blit(fps_surf, (10, 10))
    
    pygame.display.flip()
    
    if not engine.running: # wait for the main loop to finish running to quit properly

        pygame.quit()
