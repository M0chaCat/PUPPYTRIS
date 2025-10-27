# Main

import pygame
import math
import numpy
from enum import Enum
import random
import pygame_gui
import os

import engine, ui, settings, skinloader, menu

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

#pre game stuff
    
def on_load():
    skinloader.set_other_skins()
    engine.piece_bags[0] = engine.generate_bag() # generate the first two bags
    engine.piece_bags[1] = engine.generate_bag()
    next_pieces = (engine.piece_bags[0] + engine.piece_bags[1])[1:settings.NEXT_PIECES_COUNT + 1] # gets a truncated next_pieces list
    engine.next_boards = engine.gen_ui_boards(engine.next_boards, next_pieces)
    engine.spawn_piece()
    engine.update_ghost_piece()
    engine.unpack_1kf_binds()
        
def menu_loop():
    menu.draw_menu()
    # handle menu input, maybe transition to next state
    pass
    
def card_screen_loop(): # doesnt exist :3
    engine.STATE -= 1
    #ui.draw_card_screen()
    pass
    
def go_back():
    engine.STATE -= 1
    
btn = menu.Button(10, 10, 50, 50, "X", color=settings.PANEL_COLOR, cut_corners=['top-left', 'bottom-left', 'top-right', 'bottom-right'], font=font, callback=lambda: go_back())
mouse_was_down = False

on_load()
    
do_something = True
first_frame = True

def game_loop():
    global mouse_was_down, do_something, first_frame
    
    frametime = engine.frametime_clock.get_time()
    keys = pygame.key.get_pressed()
    
    engine.handle_soft_drop(keys, frametime)
    
    did_events = engine.handle_events()
    engine.handle_gravity(frametime)
    did_movement = False
    if not settings.ONEKF_ENABLED:
        did_movement = engine.handle_movement(keys)
        
    do_something = did_events or did_movement

    if do_something or first_frame or engine.draw_from_das:
        screen = engine.MAIN_SCREEN
        screen.blit(ui.draw_background(), (0, 0))
        ui.draw_next_panel()
        ui.draw_hold_panel()
        ui.draw_score_panel(Level="99", Score="99,999")
        ui.draw_board_background()
        ui.draw_grid_lines()
        ui.draw_board(engine.game_board)
        ui.draw_topout_board()
        ui.draw_board(engine.piece_board)
        btn.draw(screen)
        
    mins_secs, dot_ms = engine.timer.split_strings()
    ui.draw_stats_panel(
        PPS='50.2',
        TIMES=mins_secs,
        TIMEMS=dot_ms,
        CLEARED=str(engine.total_lines_cleared)
    )
    
    first_frame = False
    
    mouse_down = pygame.mouse.get_pressed()[0]
    if mouse_down and not mouse_was_down and btn.rect.collidepoint(pygame.mouse.get_pos()):
        btn.callback()
        
    mouse_was_down = mouse_down
    
state_funcs = {
    0: menu_loop,
    1: card_screen_loop,
    2: game_loop,
}

engine.MAIN_SCREEN = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))

while engine.running:
    engine.frametime_clock.tick(settings.MAX_FRAMERATE)
    fps = str(int(engine.frametime_clock.get_fps()))
    
    # Run current state’s logic
    state_funcs[engine.STATE]()

    # Draw FPS (universal part)
    fps_surf = font.render(fps + " FPS", True, settings.TEXT_COLOR)
    ui.draw_rect(-10, settings.WINDOW_HEIGHT - 40, 120, 50, settings.BOARD_COLOR, cut_corners=['top-right'], cut_size=10, outline_color=settings.PANEL_OUTLINE)
    engine.MAIN_SCREEN.blit(fps_surf, (10, settings.WINDOW_HEIGHT-30))
    
    pygame.display.flip()

    if not engine.running: # wait for the main loop to finish running to quit properly
        pygame.quit()
    