"""
main.py handles the main gameloop.
Loads the game, handles all gameloop functions in order, then does rendering.
"""

import os, pygame, ctypes, numpy
import engine, skinloader, ui, settings, menu, pieces

import time

os.environ['SDL_VIDEO_WINDOW_POS'] = str(settings.WINDOW_WIDTH / 2) + "," + str(settings.WINDOW_HEIGHT / 2)
os.environ['SDL_VIDEO_CENTERED'] = '1'
if os.name == "nt": ctypes.windll.shcore.SetProcessDpiAwareness(2) # disable shitty DPI scaling on Windows

pygame.init()
pygame.display.set_caption("puppytris!!!!!")
# trying all three things because what works depends on window manager?
pygame.display.set_window_position((settings.WINDOW_POS_X, settings.WINDOW_POS_Y)) 

def handle_events():
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == settings.KEY_EXIT:
                if engine.STATE == 0: engine.running = False
                else: engine.STATE -= 1
            if event.key == settings.KEY_FULLSCREEN:
                toggle_fullscreen(False)

            if not settings.ONEKF_ENABLED:
                if event.key == settings.KEY_HOLD:
                    engine.hold_guideline(engine.infinite_holds)
                if event.key == settings.ROTATE_180:
                    if engine.allow_180: engine.rotate_piece(2)
                if event.key == settings.ROTATE_CW:
                    engine.rotate_piece(1)
                if event.key == settings.ROTATE_CCW:
                    engine.rotate_piece(3)
                if event.key == settings.ROTATE_MIRROR:
                    if engine.allow_mirror: engine.mirror_piece()
                if event.key == settings.MOVE_HARDDROP:
                    engine.hard_drop()
                if event.key == settings.KEY_RESET:
                    engine.reset_game()
                if event.key == settings.KEY_UNDO: # TODO: NEED TO MAKE ALT UNDO KEYS AND RESET KEYS FOR 1KF
                    engine.undo(1)
            else:
                if numpy.isin(event.key, engine.onekf_key_array):
                    engine.handle_1kf(event.key)
                if event.key == settings.ONEKF_HOLD:
                    engine.hold_guideline()
        if event.type == pygame.QUIT:
            engine.running = False
        if event.type == pygame.ACTIVEEVENT:
            if event.state & pygame.APPACTIVE > 0 and event.gain == 1: # weird bitwise stuff because activity is represented as bits in an integer
                engine.game_state_changed = True
                engine.board_state_changed = True

def toggle_fullscreen(is_fullscreen):
    if is_fullscreen:
        new_width = settings.WINDOW_WIDTH
        new_height = settings.WINDOW_HEIGHT
    else:
        new_width = settings.DISPLAY_WIDTH
        new_height = settings.DISPLAY_HEIGHT
    # update the window dimensions
    settings.WINDOW_WIDTH = new_width
    settings.WINDOW_HEIGHT = new_height
    # update the coords
    settings.WINDOW_POS_X = (settings.DISPLAY_WIDTH / 2) - (new_width / 2)
    settings.WINDOW_POS_Y = (settings.DISPLAY_HEIGHT / 2) - (new_height / 2)
    # update the surfaces
    ui.MAIN_SCREEN = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
    ui.BACKGROUND_SURFACE = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
    ui.BOARD_SURFACE = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
    # move the window to the new coords
    pygame.display.set_window_position((settings.WINDOW_POS_X, settings.WINDOW_POS_Y))
    pygame.display.toggle_fullscreen()
    # update the cell size
    if settings.BOARD_WIDTH / new_width < settings.BOARD_HEIGHT / new_height:
        settings.CELL_SIZE = new_height//(settings.BOARD_HEIGHT - settings.BOARD_EXTRA_HEIGHT + settings.BOARD_PADDING) # +10 so its not too zoomed in
    else: # if the board is REALLY wide
        settings.CELL_SIZE = new_width//(settings.BOARD_WIDTH + 20) # TODO: improve the formula for calculating CELL_SIZE
    ui.BOARD_WIDTH_PX = settings.CELL_SIZE * settings.BOARD_WIDTH
    ui.BOARD_HEIGHT_PX = settings.CELL_SIZE * (settings.BOARD_HEIGHT - settings.BOARD_EXTRA_HEIGHT)
    # update these weird ui variables\
    ui.BOARD_PX_OFFSET_X = (settings.WINDOW_WIDTH - ui.BOARD_WIDTH_PX)/2
    ui.BOARD_PX_OFFSET_Y = (settings.WINDOW_HEIGHT - ui.BOARD_HEIGHT_PX-(settings.WINDOW_HEIGHT * 0.05))/2 - (settings.BOARD_EXTRA_HEIGHT * settings.CELL_SIZE)
    # update the skins
    pieces.init_skins()
    # make sure it draws everything
    engine.game_state_changed = True
    engine.board_state_changed = True
    ui.draw_background()

# pre game stuff
def load_game(): # all this stuff is done twice after reset_game has called. it should be smarter.
    pieces.init_skins()
    engine.piece_bags[0] = engine.generate_bag(engine.piece_gen_type) # generate the first two bags
    engine.piece_bags[1] = engine.generate_bag(engine.piece_gen_type)
    engine.gen_next_boards()
    engine.spawn_piece() # later want delayed spawn first piece mechanic
    engine.update_ghost_piece()
    engine.unpack_1kf_binds()
    engine.update_history()

load_game()
mouse_was_down = False
remaining_steps = 0 # remaining steps for gravity or soft-drop
engine.game_state_changed = True # always true on the first frame
ui.draw_background()

engine.timer.start()

engine.game_board[9][0] = 1

def game_loop():
    global mouse_was_down
    frametime = engine.frametime_clock.get_time()
    keys = pygame.key.get_pressed()
    if engine.queue_spawn_piece:
        engine.spawn_piece()
    remaining_grav = engine.handle_soft_drop(keys, frametime)
    remaining_grav += engine.handle_sonic_drop(keys)
    remaining_grav += engine.do_gravity(frametime) # this logic works the same as max() would, since one of them is always bound to be zero
    handle_events()
    if engine.check_touching_ground():
        engine.lockdown(engine.lockdown_type, frametime)

    if not engine.queue_spawn_piece: # if no more piece, skip remaining movement logic
        if not settings.ONEKF_ENABLED:
            engine.handle_movement(keys)
        engine.do_leftover_gravity(remaining_grav)

    if engine.board_state_changed:
        ui.draw_board() # if the board state has changed, update the board surface
    if engine.game_state_changed:
        ui.MAIN_SCREEN.blit(ui.BACKGROUND_SURFACE) # TODO: offset is being drawn into the surface itself, instead of using blit(cordx, cordy, surface)
        ui.draw_board_background()
        ui.draw_grid_lines()
        ui.draw_ghost_board()
        ui.MAIN_SCREEN.blit(ui.BOARD_SURFACE)
        ui.draw_piece_board()
        ui.draw_topout_board()
        ui.draw_stats_panel_bg()
        ui.draw_next_panel()
        if engine.hold_pieces_count > 0: ui.draw_hold_panel()
        ui.draw_score_panel(level="99", score="99,999")
    engine.game_state_changed = False # reset it for next frame
    engine.board_state_changed = False

    mins_secs, dot_ms = engine.timer.split_strings()
    engine.update_pps()
    ui.draw_stats_panel_text(
        PPS=str(engine.pps),
        TIME_S=mins_secs,
        TIME_MS=dot_ms,
        CLEARED=str(engine.lines_cleared)
    )

def menu_loop():
    handle_events() # make sure this doesn't break anything!!!
    menu.draw_menu()
    # handle menu input, maybe transition to next state

def mod_screen_loop(): # doesnt exist :3
    #engine.STATE -= 1
    menu.draw_mod_screen()

def go_back():
    engine.STATE -= 1

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
