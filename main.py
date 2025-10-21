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

if settings.WALLPAPER_PATH:
    settings.WALLPAPER = pygame.image.load(settings.WALLPAPER_PATH).convert_alpha()

while engine.running:
    #frametime_clock.tick(MAX_FRAMERATE)
    frametime = engine.frametime_clock.get_time()
    keys = pygame.key.get_pressed()
    
    if not engine.current_bag: # generate the first bag
        engine.current_bag = engine.generate_bag()
    
    engine.handle_soft_drop(keys) # soft drop handled before gravity, because it has to override it
    engine.handle_events()
    engine.handle_gravity()
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
    
    pygame.display.flip()
    #fps = int(engine.frametime_clock.get_fps())
    #pygame.display.set_caption(f"FPS: {fps}")
    
    pygame.display.set_caption("puppytris!!!!!")
    
    if not engine.running: # wait for the main loop to finish running to quit properly
        pygame.quit()