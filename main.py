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
    
def game_loop():
    global mouse_was_down
    frametime = engine.frametime_clock.get_time()
    keys = pygame.key.get_pressed()

    engine.handle_soft_drop(keys, frametime) # soft drop handled before gravity, because it has to override it
    engine.handle_events()
    engine.handle_gravity(frametime)
    if not settings.ONEKF_ENABLED: engine.handle_movement(keys) # horizontal movement handled after gravity, because tetrio does it this way and it kinda makes sense        
    engine.MAIN_SCREEN.blit(ui.draw_background(), (0, 0))
    ui.draw_score_panel(Level="50", Score="50,000") # dont forget da comma, and make sure the chars total 7 max (not incl the comma)
    ui.draw_next_panel()
    ui.draw_hold_panel()
    mins_secs, dot_ms = engine.timer.split_strings()
    ui.draw_stats_panel(PPS='50.2', TIMES=mins_secs, TIMEMS=dot_ms, CLEARED=str(engine.total_lines_cleared))
    ui.draw_board_background()
    ui.draw_grid_lines()
    ui.draw_board(engine.game_board)
    ui.draw_topout_board()
    ui.draw_board(engine.piece_board)
    
    btn.draw(engine.MAIN_SCREEN)
    
    mouse_down = pygame.mouse.get_pressed()[0] # all dis works perfectly but is JANKY!!!! pls rewrite me!!!!!!!!!!!!!!!!!!!!!!
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
    