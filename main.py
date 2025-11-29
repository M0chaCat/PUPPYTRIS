# Main

import pygame

import engine, ui, settings, skinloader, menu

pygame.init()

pygame.display.set_caption("puppytris!!!!!")

# pre game stuff
def load_game(): # all this stuff is done a second time when reset_game is called. it should be smarter.
    skinloader.set_other_skins()
    engine.piece_bags[0] = engine.generate_bag(engine.piece_gen_type) # generate the first two bags
    engine.piece_bags[1] = engine.generate_bag(engine.piece_gen_type)
    engine.gen_next_boards()
    engine.spawn_piece()
    engine.update_ghost_piece()
    engine.unpack_1kf_binds()
    engine.update_history()
        
def menu_loop():
    menu.draw_menu()
    # handle menu input, maybe transition to next state
    pass
    
def mod_screen_loop(): # doesnt exist :3
    engine.STATE -= 1
    #ui.draw_mod_screen()
    pass
    
def go_back():
    engine.STATE -= 1

load_game()
mouse_was_down = False
remaining_steps = 0 # remaining steps for gravity or soft-drop
engine.game_state_changed = True # always true on the first frame
ui.draw_background()

engine.timer.start()

def game_loop():
    global mouse_was_down
    frametime = engine.frametime_clock.get_time()
    keys = pygame.key.get_pressed()
    if engine.queue_spawn_piece:
        engine.spawn_piece()
    remaining_grav = engine.handle_soft_drop(keys, frametime)
    remaining_grav += engine.handle_sonic_drop(keys)
    remaining_grav += engine.do_gravity(frametime) # this logic works the same as max() would, since one of them is always bound to be zero
    engine.handle_events()
    if engine.check_touching_ground():
        engine.lockdown("STEP", frametime)

    if not engine.queue_spawn_piece: # if no more piece, skip remaining movement logic
        if not settings.ONEKF_ENABLED:
            engine.handle_movement(keys)
        engine.do_leftover_gravity(remaining_grav)
    else:
        ui.draw_board() # if the board state has changed, update the board surface

    if engine.game_state_changed:
        ui.MAIN_SCREEN.blit(ui.BACKGROUND_SURFACE)
        ui.draw_board_background()
        ui.draw_grid_lines()
        ui.draw_ghost_board()
        ui.MAIN_SCREEN.blit(ui.BOARD_SURFACE)
        ui.draw_piece_board()
        ui.draw_topout_board()
        ui.draw_stats_panel_bg()
        ui.draw_next_panel()
        ui.draw_hold_panel()
        ui.draw_score_panel(Level="99", Score="99,999")
    engine.game_state_changed = False # reset it for next frame

    mins_secs, dot_ms = engine.timer.split_strings()
    engine.update_pps()
    ui.draw_stats_panel_text(
        PPS=str(engine.pps),
        TIMES=mins_secs,
        TIMEMS=dot_ms,
        CLEARED=str(engine.lines_cleared)
    )

state_funcs = {
    0: menu_loop,
    1: mod_screen_loop,
    2: game_loop,
}

while engine.running:
    engine.frametime_clock.tick(settings.MAX_FRAMERATE)
    fps = str(int(engine.frametime_clock.get_fps()))
    
    # Run current state’s logic
    state_funcs[engine.STATE]()

    # Draw FPS (universal part)
    ui.draw_fps(fps)
    
    pygame.display.flip()

    if not engine.running: # wait for the main loop to finish running to quit properly

        pygame.quit()
