"""
ui.py initializes some UI stuff, and contains functions
for drawing and rendering everything in the game,
which are called by main.py.
"""

import pygame
import numpy

import engine, settings, pieces

MAIN_SCREEN = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
BACKGROUND_SURFACE = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
BOARD_SURFACE = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)

BOARD_WIDTH_PX = settings.CELL_SIZE * settings.BOARD_WIDTH
BOARD_HEIGHT_PX = settings.CELL_SIZE * (settings.BOARD_HEIGHT - settings.BOARD_EXTRA_HEIGHT)

BOARD_PX_OFFSET_X = (settings.WINDOW_WIDTH - BOARD_WIDTH_PX)/2
BOARD_PX_OFFSET_Y = (settings.WINDOW_HEIGHT - BOARD_HEIGHT_PX)/2

if settings.WALLPAPER_PATH:
    settings.WALLPAPER = pygame.image.load(settings.WALLPAPER_PATH).convert_alpha()

#print(pygame.display.list_modes())

# Text (top-left)
font_size = 24
try:
    font = pygame.font.Font(settings.font_dir, font_size)
except:
    font = pygame.font.SysFont(None, font_size)

fps_cache = {}

def draw_fps(fps):
    if fps not in fps_cache:
        fps_cache[fps] = font.render(fps + " FPS", True, settings.TEXT_COLOR)

    draw_rect(-10, settings.WINDOW_HEIGHT - 40, 120, 50, settings.BOARD_COLOR,
              cut_corners=['top-right'], cut_size=10, outline_color=settings.PANEL_OUTLINE)
    MAIN_SCREEN.blit(fps_cache[fps], (10, settings.WINDOW_HEIGHT-30))

def draw_rect(x, y, width, height, color=(200, 200, 200, 255),
              cut_corners=None, cut_size=10, outline_color=None):
    """
    Draw a rectangle with optional 45° cut corners and optional outline,
    supporting transparency, without turning the main screen black.
    """
    # Create temporary surface with per-pixel alpha
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    if not cut_corners:
        # Simple rectangle
        pygame.draw.rect(surface, color, (0, 0, width, height))
        if outline_color:
            pygame.draw.rect(surface, outline_color, (0, 0, width, height), 1)
    else:
        # Offset to keep 1px outline fully inside surface
        offset = 0.7
        points = [
            ((cut_size if 'top-left' in cut_corners else 0) + offset, 0 + offset),
            (width - (cut_size if 'top-right' in cut_corners else 0) - offset, 0 + offset),
            (width - offset, (cut_size if 'top-right' in cut_corners else 0) + offset),
            (width - offset, height - (cut_size if 'bottom-right' in cut_corners else 0) - offset),
            (width - (cut_size if 'bottom-right' in cut_corners else 0) - offset, height - offset),
            ((cut_size if 'bottom-left' in cut_corners else 0) + offset, height - offset),
            (0 + offset, height - (cut_size if 'bottom-left' in cut_corners else 0) - offset),
            (0 + offset, (cut_size if 'top-left' in cut_corners else 0) + offset)
        ]

        pygame.draw.polygon(surface, color, points)
        if outline_color:
            pygame.draw.polygon(surface, outline_color, points, 1)

    # Blit to main screen
    MAIN_SCREEN.blit(surface, (x, y))

def draw_text(surface, text, font, color, x, y, line_spacing=4):
    """Draw text with \n newlines manually handled and transparent background."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        text_surface = font.render(line, True, color)  # True = antialias, no background
        text_surface.set_colorkey((0, 0, 0))  # optional if your font surface has black bg
        surface.blit(text_surface, (x, y + i * (text_surface.get_height() + line_spacing)))

def draw_background():
    """Return a surface with the background drawn, scaled wallpaper or color."""
    window_width, window_height = settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT

    if hasattr(settings, "WALLPAPER") and settings.WALLPAPER:
        wallpaper = settings.WALLPAPER
        wallpaper_width, wallpaper_height = wallpaper.get_size()
        scale_factor = max(window_width / wallpaper_width, window_height / wallpaper_height)
        new_width = int(wallpaper_width * scale_factor)
        new_height = int(wallpaper_height * scale_factor)
        scaled_wallpaper = pygame.transform.smoothscale(wallpaper, (new_width, new_height)).convert()
        offset_x = (new_width - window_width) // 2
        offset_y = (new_height - window_height) // 2

        # Draw wallpaper onto our surface
        BACKGROUND_SURFACE.blit(scaled_wallpaper, (-offset_x, -offset_y))
    else:
        BACKGROUND_SURFACE.fill(settings.BACKGROUND_COLOR)

def draw_board():
    """
    Draw the full board including the extra hidden rows.
    """

    BOARD_SURFACE.fill((0, 0, 0, 0)) # clear the board

    cell_size = settings.CELL_SIZE
    grid_start_x = BOARD_PX_OFFSET_X
    grid_start_y = BOARD_PX_OFFSET_Y - (settings.BOARD_EXTRA_HEIGHT * settings.CELL_SIZE)
    board_rows = engine.game_board.shape[0]
    board_cols = engine.game_board.shape[1]

    for row in range(board_rows):
        for col in range(board_cols):
            if engine.game_board[row, col] != 0:
                x = grid_start_x + col * cell_size
                y = grid_start_y + row * cell_size
                BOARD_SURFACE.blit(engine.pieces_dict[engine.game_board[row, col]]["skin"], (x, y))

def draw_piece_board():
    """
    Draw the current piece, which is a small board layered on top of the regular board
    """
    cell_size= settings.CELL_SIZE
    grid_start_x = BOARD_PX_OFFSET_X + (engine.piece_x * cell_size)
    grid_start_y = BOARD_PX_OFFSET_Y + (engine.piece_y * cell_size)  - (settings.BOARD_EXTRA_HEIGHT * settings.CELL_SIZE)
    total_rows = engine.piece_board.shape[0]
    total_cols = engine.piece_board.shape[1]

    for row in range(total_rows):
        for col in range(total_cols):
            if engine.piece_board[row, col] != 0:
                x = grid_start_x + col * cell_size
                y = grid_start_y + row * cell_size
                MAIN_SCREEN.blit(engine.pieces_dict[engine.piece_board[row, col]]["skin"], (x, y))

def draw_board_background(cut_size=None):
    """Draw board background with top-left & top-right cut by `cut_size`.
            If cut_size is None, use one full cell (so a full corner cell is cut).
    """
    if cut_size is None:
        cut_size = settings.CELL_SIZE

    grid_start_x = BOARD_PX_OFFSET_X
    grid_start_y = BOARD_PX_OFFSET_Y

    draw_rect(grid_start_x, grid_start_y, BOARD_WIDTH_PX, BOARD_HEIGHT_PX,
                        color=settings.BOARD_COLOR,
                        cut_corners=['top-left', 'top-right'],
                        cut_size=cut_size)

def draw_grid_lines():
    """Draw grid lines for the board with top-left/top-right cut,
        including a diagonal line across each cut.
    """
    board_px_offset_x = BOARD_PX_OFFSET_X
    board_px_offset_y = BOARD_PX_OFFSET_Y
    cell_size = settings.CELL_SIZE
    cut_size = cell_size # full cell cut

    # Vertical lines
    for col in range(0, settings.BOARD_WIDTH + 1):
        line_x = board_px_offset_x + col * cell_size
        line_y = board_px_offset_y

        if line_x <= board_px_offset_x + cut_size:
            line_y = board_px_offset_y + (cut_size - (line_x - board_px_offset_x))
        elif line_x >= board_px_offset_x + BOARD_WIDTH_PX - cut_size:
            line_x_diff = (board_px_offset_x + BOARD_WIDTH_PX) - line_x
            line_y = board_px_offset_y + (cut_size - line_x_diff)

        if line_y < board_px_offset_y:
            line_y = board_px_offset_y
        pygame.draw.line(MAIN_SCREEN, settings.GRID_COLOR,
                        (line_x, line_y),
                        (line_x, board_px_offset_y + BOARD_HEIGHT_PX))

    # Horizontal lines
    max_rows = settings.BOARD_HEIGHT + 1 - settings.BOARD_EXTRA_HEIGHT
    for row in range(0, max_rows):
        line_y = board_px_offset_y + row * cell_size
        line_start_x = board_px_offset_x
        line_end_x = board_px_offset_x + BOARD_WIDTH_PX

        if line_y <= board_px_offset_y + cut_size:
            offset = cut_size - (line_y - board_px_offset_y)
            line_start_x = board_px_offset_x + offset
            line_end_x = board_px_offset_x + BOARD_WIDTH_PX - offset

        if line_start_x < board_px_offset_x:
            line_start_x = board_px_offset_x
        if line_end_x > board_px_offset_x + BOARD_WIDTH_PX:
            line_end_x = board_px_offset_x + BOARD_WIDTH_PX

        pygame.draw.line(MAIN_SCREEN, settings.GRID_COLOR,
                        (line_start_x, line_y),
                        (line_end_x, line_y))

    # Diagonal lines across the top-left and top-right cuts
    # top-left
    pygame.draw.line(MAIN_SCREEN, settings.GRID_COLOR,
                    (board_px_offset_x, board_px_offset_y + cut_size),
                    (board_px_offset_x + cut_size, board_px_offset_y))
    # top-right
    pygame.draw.line(MAIN_SCREEN, settings.GRID_COLOR,
                    (board_px_offset_x + BOARD_WIDTH_PX - cut_size, board_px_offset_y),
                    (board_px_offset_x + BOARD_WIDTH_PX, board_px_offset_y + cut_size))

def draw_ghost_board():
    """Draw the top-out piece directly on the main board, aligned to the grid, shifted up/right 1 cell."""
    if not hasattr(engine, "ghost_board") or engine.ghost_board is None:
        return

    board = engine.ghost_board
    cell_size= settings.CELL_SIZE
    board_rows, board_cols = board.shape

    # Main board top-left (include extra hidden rows if any)
    grid_start_x = BOARD_PX_OFFSET_X
    grid_start_y = BOARD_PX_OFFSET_Y - (settings.BOARD_EXTRA_HEIGHT * settings.CELL_SIZE)

    # Compute horizontal alignment in board cells
    start_col = engine.ghost_piece_x # piece_starting x is the regular piece offset
    start_row = engine.ghost_piece_y  # shift up 1 cell (negative y)

    # Draw each block aligned to main board's grid
    for row in range(board_rows):
        for col in range(board_cols):
            if board[row, col] != 0:
                skin = pieces.other_skins[0]  # semi-transparent ghost piece
                x = grid_start_x + (start_col + col) * cell_size
                y = grid_start_y + (start_row + row) * cell_size
                MAIN_SCREEN.blit(skin, (x, y))

def draw_topout_board():
    """Draw the top-out piece directly on the main board, aligned to the grid, shifted up/right 1 cell."""
    if not hasattr(engine, "topout_board") or engine.topout_board is None:
        return

    board = engine.topout_board
    cell_size= settings.CELL_SIZE
    board_rows, board_cols = board.shape

    # Main board top-left (include extra hidden rows if any)
    grid_start_x = BOARD_PX_OFFSET_X
    grid_start_y = BOARD_PX_OFFSET_Y
    
    # Calculate the piece spawning offset (code copied from engine.py)
    next_piece = (engine.piece_bags[0] + engine.piece_bags[1])[1]
    piece_shape = engine.pieces_dict[next_piece]["shapes"][engine.STARTING_ROTATION]
    piece_width = piece_shape.shape[1]
    height_offset = numpy.where(numpy.any(piece_shape != 0, axis=1))[0][0]
    start_col = (settings.BOARD_WIDTH - piece_width) // 2 # dynamically calculate starting position based on board and piece size.
    start_row = piece_width//5 - height_offset + engine.spawn_y_offset # need to subtract the blank space in the piece here.

    # Draw each block aligned to main board's grid
    for row in range(board_rows):
        for col in range(board_cols):
            if board[row, col] != 0:
                skin = pieces.other_skins[4]  # semi-transparent topout piece
                x = grid_start_x + (start_col + col) * cell_size
                y = grid_start_y + (start_row + row) * cell_size
                MAIN_SCREEN.blit(skin, (x, y))

def draw_next_panel():
    cell_size= settings.CELL_SIZE
    base_scale = 0.8  # original piece scale
    shrink_factor = 0.95  # shrink entire area by 5%

    # precompute scaled cell size
    cell_size_scaled = int(cell_size * base_scale * shrink_factor)

    board_width_px = BOARD_WIDTH_PX
    board_height_px = settings.CELL_SIZE * settings.BOARD_MAIN_HEIGHT

    next_width = int(cell_size_scaled * (engine.mino_count + 1))

    next_height_per_piece = cell_size_scaled * 3
    next_height_top = cell_size_scaled * 1
    # next_height = (next_height_per_piece * engine.next_queue_size) + next_height_top
    next_height = (len(engine.next_boards) * cell_size_scaled * engine.mino_count) + next_height_top
    panel_color = settings.PANEL_COLOR

    too_big = False

    if (next_height >= board_height_px):
        # --- Horizontal alignment: next to board ---
        next_x = BOARD_PX_OFFSET_X + board_width_px + 50

        # --- Vertical alignment: center of screen ---
        next_y = (settings.WINDOW_HEIGHT - next_height) / 2

        draw_rect(next_x, next_y, next_width, next_height, color=panel_color, cut_size=20, cut_corners=['top-left', 'bottom-left', 'top-right', 'bottom-right'], outline_color=settings.PANEL_OUTLINE)

        too_big = True
    else:
        # --- Horizontal alignment: stick to the board ---
        next_x = BOARD_PX_OFFSET_X + board_width_px

        # --- Vertical alignment: start at a % down the board ---
        vertical_pct = 0.3  # 0.0 = top of board, 1.0 = bottom
        next_y = BOARD_PX_OFFSET_Y + int(vertical_pct * board_height_px)

        draw_rect(next_x, next_y, next_width, next_height, color=panel_color, cut_size=20, cut_corners=['top-right', 'bottom-right'], outline_color=settings.PANEL_OUTLINE)

    # --- Draw label ---
    font_size = int(cell_size_scaled / 1.5)
    try:
        font = pygame.font.Font(settings.font_dir, font_size)
    except:
        font = pygame.font.SysFont(None, font_size)

    text_surface = font.render("Next", True, settings.TEXT_COLOR)

    paddingy = cell_size_scaled / 3
    paddingx = cell_size_scaled / 3

    text_rect = text_surface.get_rect()

    if too_big:
        text_rect.centerx = next_x + next_width / 2
        text_rect.top = next_y + paddingy
    else:
        text_rect.topleft = (next_x + paddingx, next_y + paddingy)

    MAIN_SCREEN.blit(text_surface, text_rect)

    # --- Draw next pieces ---
    if hasattr(engine, "next_boards") and engine.next_boards is not None:
        spacing = cell_size_scaled * -1 # space between stacked pieces (1 next cell)
        for i, board in enumerate(engine.next_boards):
            board_rows, board_cols = board.shape

            # x/y of the top-left of this board area (stacked)
            area_start_x = next_x + (next_width - board_cols * cell_size_scaled) // 2
            area_start_y = next_y + 20 + i * (board_rows * cell_size_scaled + spacing)

            # compute bounding box of non-zero cells
            rows_nonzero = numpy.any(board != 0, axis=1)
            cols_nonzero = numpy.any(board != 0, axis=0)
            if not rows_nonzero.any() or not cols_nonzero.any():
                continue  # empty board

            min_row, max_row = numpy.where(rows_nonzero)[0][[0, -1]]
            min_col, max_col = numpy.where(cols_nonzero)[0][[0, -1]]

            piece_rows = max_row - min_row + 1
            piece_cols = max_col - min_col + 1

            # offset to center the piece in the board area
            offset_x = ((board_cols - piece_cols) * cell_size_scaled) // 2 - min_col * cell_size_scaled
            offset_y = ((board_rows - piece_rows) * cell_size_scaled) // 2 - min_row * cell_size_scaled

            for row in range(board_rows):
                for col in range(board_cols):
                    if board[row, col] != 0:
                        x = area_start_x + col * cell_size_scaled + offset_x
                        y = area_start_y + row * cell_size_scaled + offset_y
                        piece_skin = engine.pieces_dict[board[row, col]]["skin"]
                        piece_skin_scaled = pygame.transform.smoothscale(piece_skin, (cell_size_scaled, cell_size_scaled))
                        MAIN_SCREEN.blit(piece_skin_scaled, (x, y))

def draw_hold_panel():
    cell_size= settings.CELL_SIZE
    base_scale = 0.8  # original piece scale
    shrink_factor = 0.95  # shrink entire area by 5%

    # precompute scaled cell size
    cell_size_scaled = int(cell_size* base_scale * shrink_factor)

    total_board_px = settings.CELL_SIZE * settings.BOARD_MAIN_HEIGHT
    board_width_px = BOARD_WIDTH_PX
    board_height_px = settings.CELL_SIZE * settings.BOARD_MAIN_HEIGHT # vertical pixels

    hold_width = int(cell_size_scaled * (engine.mino_count + 0.5))

    hold_height_per_piece = cell_size_scaled * 3
    hold_height_top = cell_size_scaled * 1
    hold_height = (engine.hold_pieces_count * cell_size_scaled * engine.mino_count) + hold_height_top

    too_big = False

    if ((hold_height + (10 * cell_size_scaled)) >= board_height_px):
        # --- Horizontal alignment: stick to the left of the board ---
        hold_x = BOARD_PX_OFFSET_X - hold_width - 50

        # --- Vertical alignment: start at a % down the screen ---
        vertical_pct = 0.3  # 0.0 = top, 1.0 = bottom
        hold_y = int(vertical_pct * board_height_px)

        panel_color = settings.PANEL_COLOR
        draw_rect(hold_x, hold_y, hold_width, hold_height, color=panel_color, cut_size=20, cut_corners=['top-left', 'bottom-left', 'top-right', 'bottom-right'], outline_color=settings.PANEL_OUTLINE)
        too_big = True
    elif (hold_height < board_height_px):
        # --- Horizontal alignment: stick to the left of the board ---
        hold_x = BOARD_PX_OFFSET_X - hold_width

        # --- Vertical alignment: start at a % down the board ---
        vertical_pct = 0.3  # 0.0 = top, 1.0 = bottom
        hold_y = BOARD_PX_OFFSET_Y + int(vertical_pct * board_height_px)

        panel_color = settings.PANEL_COLOR
        draw_rect(hold_x, hold_y, hold_width, hold_height, color=panel_color, cut_size=20, cut_corners=['top-left', 'bottom-left'], outline_color=settings.PANEL_OUTLINE)

    # --- Draw label ---
    font_size = int(cell_size_scaled / 1.5)
    try:
        font = pygame.font.Font(settings.font_dir, font_size)
    except:
        font = pygame.font.SysFont(None, font_size)

    text_surface = font.render("Hold", True, settings.TEXT_COLOR)
    text_rect = text_surface.get_rect()
    paddingy = cell_size_scaled / 3
    paddingx = cell_size_scaled / 3
    if too_big:
        text_rect.centerx = hold_x + hold_width / 2
        text_rect.top = hold_y + paddingy
    else:
        text_rect.topright=(hold_x + hold_width - paddingx, hold_y + paddingy)

    MAIN_SCREEN.blit(text_surface, text_rect)

    # --- Draw held pieces ---
    if hasattr(engine, "hold_boards") and engine.hold_boards is not None:
        cell_size= settings.CELL_SIZE
        base_scale = 0.8  # original piece scale
        shrink_factor = 0.95  # shrink entire area by 5%
        spacing = -40  # space between stacked hold pieces

        # precompute scaled cell size
        cell_size_scaled = int(cell_size* base_scale * shrink_factor)

        for i, board in enumerate(engine.hold_boards):
            board_rows, board_cols = board.shape

            # x/y of the top-left of this board area (stacked)
            area_start_x = hold_x + (hold_width - board_cols * cell_size_scaled) // 2
            area_start_y = hold_y + 10 + i * (board_rows * cell_size_scaled + spacing)

            # compute bounding box of non-zero cells
            rows_nonzero = numpy.any(board != 0, axis=1)
            cols_nonzero = numpy.any(board != 0, axis=0)
            if not rows_nonzero.any() or not cols_nonzero.any():
                continue  # empty board

            min_row, max_row = numpy.where(rows_nonzero)[0][[0, -1]]
            min_col, max_col = numpy.where(cols_nonzero)[0][[0, -1]]

            piece_rows = max_row - min_row + 1
            piece_cols = max_col - min_col + 1

            # offset to center the piece in the board area
            offset_x = ((board_cols - piece_cols) * cell_size_scaled) // 2 - min_col * cell_size_scaled
            offset_y = ((board_rows - piece_rows) * cell_size_scaled) // 2 - min_row * cell_size_scaled

            for row in range(board_rows):
                for col in range(board_cols):
                    if board[row, col] != 0:
                        x = area_start_x + col * cell_size_scaled + offset_x
                        y = area_start_y + row * cell_size_scaled + offset_y
                        piece_skin = engine.pieces_dict[board[row, col]]["skin"]
                        piece_skin_scaled = pygame.transform.smoothscale(piece_skin, (cell_size_scaled, cell_size_scaled))
                        MAIN_SCREEN.blit(piece_skin_scaled, (x, y))

# Precompute panel rect for later use
stats_panel_rect = None
saved_stats_bg = None

def draw_stats_panel_bg():
    cell_size= settings.CELL_SIZE
    base_scale = 0.8  # original piece scale
    shrink_factor = 0.95  # shrink entire area by 5%

    # precompute scaled cell size
    cell_size_scaled = int(cell_size* base_scale * shrink_factor)
    total_board_px = settings.CELL_SIZE * settings.BOARD_MAIN_HEIGHT

    """Draw just the stats panel background and save it for later text updates."""
    global stats_panel_rect, saved_stats_bg
    total_board_px = settings.CELL_SIZE * settings.BOARD_MAIN_HEIGHT

    board_width_px = BOARD_WIDTH_PX
    stats_width = int(cell_size_scaled * 5)
    stats_height = int(cell_size_scaled * 10)

    vertical_pct = 0.7
    stats_y = BOARD_PX_OFFSET_Y + int(vertical_pct * total_board_px)
    stats_x = BOARD_PX_OFFSET_X - stats_width
    hold_height = (engine.hold_pieces_count * cell_size_scaled * 4) + (cell_size_scaled)
    panel_color = settings.CRUST_COLOR

    if ((hold_height + stats_height) >= total_board_px):
        vertical_pct = 0.7 + (0.15 * engine.hold_pieces_count)
        stats_x = stats_x - 50
        stats_y = int(vertical_pct * total_board_px)
        stats_panel_rect = pygame.Rect(stats_x, stats_y, stats_width, stats_height)

        draw_rect(stats_x, stats_y, stats_width, stats_height,
                            cut_size=20, color=panel_color,
                            cut_corners=['top-left', 'bottom-left', 'top-right', 'bottom-right'],
                            outline_color=settings.PANEL_OUTLINE)
    elif ((hold_height + stats_height) < total_board_px):
        stats_panel_rect = pygame.Rect(stats_x, stats_y, stats_width, stats_height)

        draw_rect(stats_x, stats_y, stats_width, stats_height,
                            cut_size=20, color=panel_color,
                            cut_corners=['top-left', 'bottom-left'],
                            outline_color=settings.PANEL_OUTLINE)

    # Save the background so we can restore it before updating text
    saved_stats_bg = MAIN_SCREEN.subsurface(stats_panel_rect).copy()

def draw_stats_panel_text(PPS='50.2', TIME_S='3:28', TIME_MS='3:28', CLEARED="69"):
    """Draw only the stats text, restoring background first."""
    if saved_stats_bg:
        MAIN_SCREEN.blit(saved_stats_bg, stats_panel_rect.topleft)

    stats_x, stats_y = stats_panel_rect.topleft
    panel_height = stats_panel_rect.height

    # Fonts relative to panel height
    fontbig   = pygame.font.Font(settings.font_dir, max(1, int(panel_height * 0.12)))
    font      = pygame.font.Font(settings.font_dir, max(1, int(panel_height * 0.08)))
    fontsmall = pygame.font.Font(settings.font_dir, max(1, int(panel_height * 0.06)))

    # Vertical positions as % of panel height
    y_PPS_label      = stats_y + int(panel_height * 0.10)
    y_PPS_value      = stats_y + int(panel_height * 0.20)
    y_time_label     = stats_y + int(panel_height * 0.40)
    y_time_value     = stats_y + int(panel_height * 0.50)
    y_lines_label    = stats_y + int(panel_height * 0.68)
    y_cleared_label  = stats_y + int(panel_height * 0.73)
    y_cleared_value  = stats_y + int(panel_height * 0.83)

    # Draw labels
    draw_text(MAIN_SCREEN, "PPS:", font, settings.TEXT_COLOR, stats_x + 0.1*stats_panel_rect.width, y_PPS_label)
    draw_text(MAIN_SCREEN, "Time:", font, settings.TEXT_COLOR, stats_x + 0.1*stats_panel_rect.width, y_time_label)
    draw_text(MAIN_SCREEN, "Lines", fontsmall, settings.TEXT_COLOR, stats_x + 0.1*stats_panel_rect.width, y_lines_label)
    draw_text(MAIN_SCREEN, "Cleared:", font, settings.TEXT_COLOR, stats_x + 0.1*stats_panel_rect.width, y_cleared_label)

    # Draw values
    draw_text(MAIN_SCREEN, PPS, fontbig, settings.TEXT_COLOR, stats_x + 0.2*stats_panel_rect.width, y_PPS_value)
    draw_text(MAIN_SCREEN, TIME_S, fontbig, settings.TEXT_COLOR, stats_x + 0.2*stats_panel_rect.width, y_time_value)
    draw_text(MAIN_SCREEN, TIME_MS, fontsmall, settings.TEXT_COLOR,
                        stats_x + 0.2*stats_panel_rect.width + fontbig.size(TIME_S)[0],
                        y_time_value + fontbig.get_ascent() - fontsmall.get_ascent())

    draw_text(MAIN_SCREEN, CLEARED, fontbig, settings.TEXT_COLOR, stats_x + 0.2*stats_panel_rect.width, y_cleared_value)

def draw_score_panel(level="50", score="50,000"):
    """Draw a rectangular section aligned to the bottom of the board with text."""
    panel_height = int(settings.CELL_SIZE * 1.5)
    total_board_px = settings.CELL_SIZE * settings.BOARD_HEIGHT
    x = BOARD_PX_OFFSET_X
    y = BOARD_PX_OFFSET_Y + total_board_px - (settings.BOARD_EXTRA_HEIGHT * settings.CELL_SIZE)
    width = BOARD_WIDTH_PX
    height = panel_height

    # Draw the panel rectangle
    draw_rect(
        x, y, width, height, settings.CRUST_COLOR,
        cut_size=int(panel_height * 0.5),
        cut_corners=['bottom-left', 'bottom-right'],
        outline_color=settings.PANEL_OUTLINE
    )

    padding_x = int(0.02 * width)  # 2% of panel width
    right_padding_x = int(0.08 * width)
    padding_y = int(0.15 * height)  # 10% of panel height from top

    # Fonts relative to panel height
    # start with default font sizes
    big_size = max(1, int(panel_height * 1.07))
    small_size = max(1, int(panel_height * 0.35))

    fontbig = pygame.font.Font(settings.font_dir, big_size)
    font = pygame.font.Font(settings.font_dir, small_size)

    # shrink fonts if text doesn't fit
    def total_text_width():
        return (
            padding_x +
            font.size("Level:")[0] + 5 +
            fontbig.size(level)[0] +
            padding_x +
            int(0.3 * height) +  # separator width
            padding_x +
            font.size("Score:")[0] + 5 +
            fontbig.size(score)[0] +
            right_padding_x
        )

    while total_text_width() > width and big_size > 1:
        big_size -= 1
        small_size = max(1, int(big_size * 0.35))
        fontbig = pygame.font.Font(settings.font_dir, big_size)
        font = pygame.font.Font(settings.font_dir, small_size)

    # Draw Level
    draw_text(MAIN_SCREEN, "Level:", font, settings.TEXT_COLOR, x + padding_x, y + padding_y)
    draw_text(MAIN_SCREEN, level, fontbig, settings.TEXT_COLOR, x + padding_x + font.size("Level:")[0] + 5, y + padding_y)

    # Vertical line separator
    line_offset = x + padding_x + font.size("Level:")[0] + fontbig.size(level)[0] + int(0.02 * width)
    pygame.draw.line(
        MAIN_SCREEN, settings.PANEL_OUTLINE,
        (line_offset, y),
        (line_offset + int(0.3 * height), y + height), # 0.3 is the width the line takes up
        1
    )

    # Draw score
    draw_text(MAIN_SCREEN, "Score:", font, settings.TEXT_COLOR, line_offset + int(0.03 * width), y + padding_y)
    score_width = fontbig.size(score)[0]
    draw_text(MAIN_SCREEN, score, fontbig, settings.TEXT_COLOR, x + width - right_padding_x - score_width, y + padding_y)
