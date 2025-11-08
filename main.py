# Main

import pygame

import engine
import menu
import settings
import skinloader
import ui

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
def load_game():  # all this stuff is done a second time when reset_game is called. it should be smarter.
    skinloader.set_other_skins()
    engine.piece_bags[0] = engine.generate_bag()  # generate the first two bags
    engine.piece_bags[1] = engine.generate_bag()
    engine.gen_next_boards()
    engine.spawn_piece()
    engine.update_ghost_piece()
    engine.unpack_1kf_binds()


def menu_loop():
    menu.draw_menu()
    # handle menu input, maybe transition to next state
    pass


def mod_screen_loop():  # doesnt exist :3
    engine.STATE -= 1
    # ui.draw_mod_screen()
    pass


def go_back():
    engine.STATE -= 1


load_game()
mouse_was_down = False
remaining_steps = 0  # remaining steps for gravity or soft-drop
engine.game_state_changed = True  # always true on the first frame
engine.MAIN_SCREEN = pygame.display.set_mode(
    (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
)
engine.timer.start()


def game_loop():
    global mouse_was_down
    frametime = engine.frametime_clock.get_time()
    keys = pygame.key.get_pressed()
    if engine.queue_spawn_piece:
        engine.spawn_piece()
    remaining_grav = engine.handle_soft_drop(keys, frametime)
    remaining_grav += engine.do_gravity(
        frametime
    )  # this logic works the same as max() would, since one of them is always bound to be zero
    engine.handle_events()

    if not engine.queue_spawn_piece:  # if no more piece, skip remaining movement logic
        if engine.check_touching_ground():
            engine.lockdown_step(frametime)
        if not settings.ONEKF_ENABLED:
            engine.handle_movement(keys)
        engine.do_leftover_gravity(remaining_grav)

    if engine.game_state_changed:
        screen = engine.MAIN_SCREEN
        screen.blit(ui.draw_background(), (0, 0))
        ui.draw_stats_panel_bg()
        ui.draw_next_panel()
        ui.draw_hold_panel()
        ui.draw_score_panel(Level="99", Score="99,999")
        ui.draw_board_background()
        ui.draw_grid_lines()
        ui.draw_ghost_board()
        ui.draw_board()
        ui.draw_piece_board()
        ui.draw_topout_board()
    engine.game_state_changed = False  # reset it for next frame

    mins_secs, dot_ms = engine.timer.split_strings()
    engine.update_pps()
    ui.draw_stats_panel_text(
        PPS=str(engine.pps),
        TIMES=mins_secs,
        TIMEMS=dot_ms,
        CLEARED=str(engine.lines_cleared),
    )


state_funcs = {
    0: menu_loop,
    1: mod_screen_loop,
    2: game_loop,
}

while engine.running:
    engine.frametime_clock.tick()
    fps = str(int(engine.frametime_clock.get_fps()))

    # Run current state’s logic
    state_funcs[engine.STATE]()

    # Draw FPS (universal part)
    fps_surf = font.render(fps + " FPS", True, settings.TEXT_COLOR)
    ui.draw_rect(
        -10,
        settings.WINDOW_HEIGHT - 40,
        120,
        50,
        settings.BOARD_COLOR,
        cut_corners=["top-right"],
        cut_size=10,
        outline_color=settings.PANEL_OUTLINE,
    )
    engine.MAIN_SCREEN.blit(fps_surf, (10, settings.WINDOW_HEIGHT - 30))

    pygame.display.flip()

    if not engine.running:  # wait for the main loop to finish running to quit properly
        pygame.quit()
