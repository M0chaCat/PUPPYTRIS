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

# pre game stuff
def load_game():
    skinloader.set_other_skins()
    engine.piece_bags[0] = engine.generate_bag() # generate the first two bags
    engine.piece_bags[1] = engine.generate_bag()
    next_pieces = (engine.piece_bags[0] + engine.piece_bags[1])[1:settings.NEXT_PIECES_COUNT + 1] # gets a truncated next_pieces list
    engine.next_boards = engine.gen_ui_boards(engine.next_boards, next_pieces)
    engine.spawn_piece()
    engine.refresh_ghost_board()
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
load_game()
mouse_was_down = False
remaining_steps = 0 # remaining steps for gravity or soft-drop
engine.game_state_changed = True # always true on the first frame

def game_loop():
    global mouse_was_down
    frametime = engine.frametime_clock.get_time()
    keys = pygame.key.get_pressed()
    if engine.queue_spawn_piece:
        engine.spawn_piece()
    remaining_steps = engine.handle_soft_drop(keys, frametime)
    remaining_steps += engine.handle_gravity(frametime) # this logic works the same as max() would, since one of them is always bound to be zero
    engine.handle_events()
    #engine.handle_lockdown
    if not engine.queue_spawn_piece: # if no more piece, skip remaining movement logic
        if not settings.ONEKF_ENABLED:
            engine.handle_movement(keys)
        engine.handle_leftover_gravity(remaining_steps)

    if engine.game_state_changed:
        screen = engine.MAIN_SCREEN
        screen.blit(ui.draw_background(), (0, 0))
        ui.draw_stats_panel_bg()
        ui.draw_next_panel()
        ui.draw_hold_panel()
        ui.draw_score_panel(Level="99", Score="99,999")
        ui.draw_board_background()
        ui.draw_grid_lines()
        ui.draw_board()
        #ui.draw_ghost_board()
        ui.draw_piece_board()
        ui.draw_topout_board()
        btn.draw(screen)
    engine.game_state_changed = False # reset it for next frame
    mins_secs, dot_ms = engine.timer.split_strings()
    ui.draw_stats_panel_text(
        PPS='50.2',
        TIMES=mins_secs,
        TIMEMS=dot_ms,
        CLEARED=str(engine.total_lines_cleared)
    )
    
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
    engine.frametime_clock.tick()
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
    
            