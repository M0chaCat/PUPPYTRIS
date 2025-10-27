# UI

import pygame
import math
import numpy
from enum import Enum
import random
import pygame_gui
import os

import engine, settings, skinloader

BLOCK_SIZE = engine.BOARD_WIDTH_PX // settings.BOARD_WIDTH

def draw_rect(x, y, width, height, color=(200, 200, 200, 255),
              cut_corners=None, cut_size=10, outline_color=None):
    """
    Draw a rectangle with optional 45° cut corners and optional outline,
    supporting transparency, without turning the main screen black.
    """
    import pygame
    # Create temporary surface with per-pixel alpha
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    
    if not cut_corners:
        # Simple rectangle
        pygame.draw.rect(surf, color, (0, 0, width, height))
        if outline_color:
            pygame.draw.rect(surf, outline_color, (0, 0, width, height), 1)
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
        
        pygame.draw.polygon(surf, color, points)
        if outline_color:
            pygame.draw.polygon(surf, outline_color, points, 1)
            
    # Blit to main screen
    engine.MAIN_SCREEN.blit(surf, (x, y))
    
def draw_text(surface, text, font, color, x, y, line_spacing=4):
    """Draw text with \n newlines manually handled and transparent background."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        text_surf = font.render(line, True, color)  # True = antialias, no background
        text_surf.set_colorkey((0, 0, 0))  # optional if your font surface has black bg
        surface.blit(text_surf, (x, y + i * (text_surf.get_height() + line_spacing)))
        
def draw_background():
    """Return a surface with the background drawn, scaled wallpaper or color."""
    win_w, win_h = settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT
    background_surf = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
    
    if hasattr(settings, "WALLPAPER") and settings.WALLPAPER:
        wp = settings.WALLPAPER
        wp_w, wp_h = wp.get_size()
        scale_factor = max(win_w / wp_w, win_h / wp_h)
        new_w = int(wp_w * scale_factor)
        new_h = int(wp_h * scale_factor)
        scaled_wp = pygame.transform.smoothscale(wp, (new_w, new_h))
        offset_x = (new_w - win_w) // 2
        offset_y = (new_h - win_h) // 2
        
        # Draw wallpaper onto our surface
        background_surf.blit(scaled_wp, (-offset_x, -offset_y))
    else:
        background_surf.fill(settings.BACKGROUND_COLOR)
        
    return background_surf

def draw_board(current_board):
    """
    Draw the full board including the extra hidden rows (no clipping).
    After drawing pieces, call draw_board_corners() to mask triangular cuts.
    """
    cell = settings.CELL_SIZE
    grid_start_x = engine.BOARD_PX_OFFSET_X
    grid_start_y = engine.BOARD_PX_OFFSET_Y
    total_rows = current_board.shape[0]
    total_cols = current_board.shape[1]
    
    for row in range(total_rows):
        for col in range(total_cols):
            val = current_board[row, col]
            if val == 0:
                continue
            
            x = grid_start_x + col * cell
            y = grid_start_y + row * cell
            
            engine.MAIN_SCREEN.blit(engine.pieces_dict[val]["skin"], (x, y))
            
def draw_board_background(cut_size=None):
        """Draw board background with top-left & top-right cut by `cut_size`.
                If cut_size is None, use one full cell (so a full corner cell is cut).
        """
        if cut_size is None:
                cut_size = settings.CELL_SIZE
            
        grid_start_x = engine.BOARD_PX_OFFSET_X
        grid_start_y = engine.BOARD_PX_OFFSET_Y + (settings.BOARD_EXTRA_HEIGHT * settings.CELL_SIZE)
        width = engine.BOARD_WIDTH_PX
        height = engine.BOARD_HEIGHT_PX
    
        draw_rect(grid_start_x, grid_start_y, width, height,
                            color=settings.BOARD_COLOR,
                            cut_corners=['top-left', 'top-right'],
                            cut_size=cut_size)
    
def draw_grid_lines():
        """Draw grid lines for the board with top-left/top-right cut,
            including a diagonal line across each cut.
        """
        grid_start_x = engine.BOARD_PX_OFFSET_X
        grid_start_y = engine.BOARD_PX_OFFSET_Y + (settings.BOARD_EXTRA_HEIGHT * settings.CELL_SIZE)
        width = engine.BOARD_WIDTH_PX
        height = engine.BOARD_HEIGHT_PX
        cell = settings.CELL_SIZE
        cut = cell  # full cell cut

        # Vertical lines
        for col in range(0, settings.BOARD_WIDTH + 1):
            x = grid_start_x + col * cell
            y0 = grid_start_y
            
            if x <= grid_start_x + cut:
                y0 = grid_start_y + (cut - (x - grid_start_x))
            elif x >= grid_start_x + width - cut:
                dx = (grid_start_x + width) - x
                y0 = grid_start_y + (cut - dx)
                
            if y0 < grid_start_y:
                y0 = grid_start_y
            pygame.draw.line(engine.MAIN_SCREEN, settings.GRID_COLOR,
                            (x, y0),
                            (x, grid_start_y + height))
            
        # Horizontal lines
        max_rows = settings.BOARD_HEIGHT + 1 - settings.BOARD_EXTRA_HEIGHT
        for row in range(0, max_rows):
            y = grid_start_y + row * cell
            x0 = grid_start_x
            x1 = grid_start_x + width
            
            if y <= grid_start_y + cut:
                offset = cut - (y - grid_start_y)
                x0 = grid_start_x + offset
                x1 = grid_start_x + width - offset
                
            if x0 < grid_start_x:
                x0 = grid_start_x
            if x1 > grid_start_x + width:
                x1 = grid_start_x + width
                
            pygame.draw.line(engine.MAIN_SCREEN, settings.GRID_COLOR,
                            (x0, y),
                            (x1, y))
            
        # Diagonal lines across the top-left and top-right cuts
        # top-left
        pygame.draw.line(engine.MAIN_SCREEN, settings.GRID_COLOR,
                        (grid_start_x, grid_start_y + cut),
                        (grid_start_x + cut, grid_start_y))
        # top-right
        pygame.draw.line(engine.MAIN_SCREEN, settings.GRID_COLOR,
                        (grid_start_x + width - cut, grid_start_y),
                        (grid_start_x + width, grid_start_y + cut))
            
def draw_topout_board():
    """Draw the top-out piece directly on the main board, aligned to the grid, shifted up/right 1 cell."""
    if not hasattr(engine, "topout_board") or engine.topout_board is None:
        return
    
    board = engine.topout_board
    cell = settings.CELL_SIZE
    board_rows, board_cols = board.shape
    
    # Main board top-left (include extra hidden rows if any)
    grid_start_x = engine.BOARD_PX_OFFSET_X
    grid_start_y = engine.BOARD_PX_OFFSET_Y + settings.BOARD_EXTRA_HEIGHT * cell
    
    # Compute horizontal alignment in board cells
    main_cols = settings.BOARD_WIDTH
    start_col = engine.PIECE_STARTING_X # piece_starting x is the regular piece offset
    start_row = -1  # shift up 1 cell (negative y)
    
    # Draw each block aligned to main board's grid
    for row in range(board_rows):
        for col in range(board_cols):
            val = board[row, col]
            if val == 0:
                continue
            skin = skinloader.other_skins[4]  # semi-transparent topout piece
            x = grid_start_x + (start_col + col) * cell
            y = grid_start_y + (start_row + row) * cell
            engine.MAIN_SCREEN.blit(skin, (x, y))
            
def draw_next_panel():
    text = "Next"
    total_board_px = settings.CELL_SIZE * settings.DRAWN_BOARD_HEIGHT
    next_width = int(total_board_px * 0.2)
    next_height_per_piece = total_board_px / 7
    next_height_top = total_board_px / 19
    next_height = (next_height_per_piece * settings.NEXT_PIECES_COUNT) + next_height_top
    
    # --- Horizontal alignment: stick to the board ---
    next_x = engine.BOARD_PX_OFFSET_X + engine.BOARD_WIDTH_PX
    
    # --- Vertical alignment: start at a % down the board ---
    vertical_pct = 0.3  # change this: 0.0 = top of board, 1.0 = bottom
    next_y = engine.BOARD_PX_OFFSET_Y + int(vertical_pct * total_board_px)
    
    panel_color = settings.PANEL_COLOR
    draw_rect(next_x, next_y, next_width, next_height, color=panel_color, cut_corners=['top-right', 'bottom-right'], outline_color=settings.PANEL_OUTLINE)
    
    # --- Draw label ---
    font_size = 24
    try:
        font = pygame.font.Font(settings.font_dir, font_size)
    except:
        font = pygame.font.SysFont(None, font_size)
        
    text_surf = font.render(text, True, settings.TEXT_COLOR)
    padding = 10
    text_rect = text_surf.get_rect(topleft=(next_x + padding, next_y + padding))
    engine.MAIN_SCREEN.blit(text_surf, text_rect)
    
    # --- Draw next pieces ---
    if hasattr(engine, "next_boards") and engine.next_boards is not None:
        cell = settings.CELL_SIZE
        base_scale = 0.8  # original piece scale
        shrink_factor = 0.95  # shrink entire area by 5%
        spacing = -40  # space between stacked hold pieces
        
        # precompute scaled cell size
        cell_scaled = int(cell * base_scale * shrink_factor)
        
        for i, board in enumerate(engine.next_boards):
            board_rows, board_cols = board.shape
            
            # x/y of the top-left of this board area (stacked)
            area_start_x = next_x + (next_width - board_cols * cell_scaled) // 2
            area_start_y = next_y + 20 + i * (board_rows * cell_scaled + spacing)
            
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
            offset_x = ((board_cols - piece_cols) * cell_scaled) // 2 - min_col * cell_scaled
            offset_y = ((board_rows - piece_rows) * cell_scaled) // 2 - min_row * cell_scaled
            
            for row in range(board_rows):
                for col in range(board_cols):
                    val = board[row, col]
                    if val == 0:
                        continue
                    x = area_start_x + col * cell_scaled + offset_x
                    y = area_start_y + row * cell_scaled + offset_y
                    piece_skin = engine.pieces_dict[val]["skin"]
                    piece_skin_scaled = pygame.transform.smoothscale(piece_skin, (cell_scaled, cell_scaled))
                    engine.MAIN_SCREEN.blit(piece_skin_scaled, (x, y))
    
def draw_hold_panel():
    text = "Hold"
    total_board_px = settings.CELL_SIZE * settings.DRAWN_BOARD_HEIGHT
    hold_width = int(total_board_px * 0.2)
    hold_height_per_piece = total_board_px / 7
    hold_height_top = total_board_px / 19
    hold_height = (hold_height_per_piece * engine.hold_pieces_count) + hold_height_top
    
    # --- Horizontal alignment: stick to the left of the board ---
    hold_x = engine.BOARD_PX_OFFSET_X - hold_width
    
    # --- Vertical alignment: start at a % down the board ---
    vertical_pct = 0.3  # 0.0 = top, 1.0 = bottom
    hold_y = engine.BOARD_PX_OFFSET_Y + int(vertical_pct * total_board_px)
    
    panel_color = settings.PANEL_COLOR
    draw_rect(hold_x, hold_y, hold_width, hold_height, color=panel_color, cut_corners=['top-left', 'bottom-left'], outline_color=settings.PANEL_OUTLINE)
    
    # --- Draw label ---
    font_size = 24
    try:
        font = pygame.font.Font(settings.font_dir, font_size)
    except:
        font = pygame.font.SysFont(None, font_size)
        
    text_surf = font.render(text, True, settings.TEXT_COLOR)
    padding = 10
    text_rect = text_surf.get_rect(topright=(hold_x + hold_width - padding, hold_y + padding))
    engine.MAIN_SCREEN.blit(text_surf, text_rect)
    
    # --- Draw held pieces ---
    if hasattr(engine, "hold_boards") and engine.hold_boards is not None:
        cell = settings.CELL_SIZE
        base_scale = 0.8  # original piece scale
        shrink_factor = 0.95  # shrink entire area by 5%
        spacing = -40  # space between stacked hold pieces
        
        # precompute scaled cell size
        cell_scaled = int(cell * base_scale * shrink_factor)
        
        for i, board in enumerate(engine.hold_boards):
            board_rows, board_cols = board.shape
            
            # x/y of the top-left of this board area (stacked)
            area_start_x = hold_x + (hold_width - board_cols * cell_scaled) // 2
            area_start_y = hold_y + 10 + i * (board_rows * cell_scaled + spacing)
            
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
            offset_x = ((board_cols - piece_cols) * cell_scaled) // 2 - min_col * cell_scaled
            offset_y = ((board_rows - piece_rows) * cell_scaled) // 2 - min_row * cell_scaled
            
            for row in range(board_rows):
                for col in range(board_cols):
                    val = board[row, col]
                    if val == 0:
                        continue
                    x = area_start_x + col * cell_scaled + offset_x
                    y = area_start_y + row * cell_scaled + offset_y
                    piece_skin = engine.pieces_dict[val]["skin"]
                    piece_skin_scaled = pygame.transform.smoothscale(piece_skin, (cell_scaled, cell_scaled))
                    engine.MAIN_SCREEN.blit(piece_skin_scaled, (x, y))
                    
                    
def draw_stats_panel(PPS='50.2', TIMES='3:28', TIMEMS='3:28', CLEARED="69"):
    total_board_px = settings.CELL_SIZE * settings.DRAWN_BOARD_HEIGHT
    stats_width = int(total_board_px * 0.18)
    stats_height = total_board_px / 2.6
    
    # --- Horizontal alignment: stick to the left of the board ---
    stats_x = engine.BOARD_PX_OFFSET_X - stats_width
    
    # --- Vertical alignment: start at a % down the board ---
    vertical_pct = 0.7  # 0.0 = top, 1.0 = bottom
    stats_y = engine.BOARD_PX_OFFSET_Y + int(vertical_pct * total_board_px)
    
    panel_color = settings.CRUST_COLOR
    draw_rect(stats_x, stats_y, stats_width, stats_height, color=panel_color, cut_corners=['top-left', 'bottom-left'], outline_color=settings.PANEL_OUTLINE)
    
    fontbig = pygame.font.Font(settings.font_dir, 40)
    font = pygame.font.Font(settings.font_dir, 24)
    fontsmall = pygame.font.Font(settings.font_dir, 19)
    draw_text(engine.MAIN_SCREEN, "PPS:", font, settings.TEXT_COLOR, stats_x + 10, stats_y + 20)
    draw_text(engine.MAIN_SCREEN, "Time:", font, settings.TEXT_COLOR, stats_x + 10, stats_y + 120)
    draw_text(engine.MAIN_SCREEN, "Lines", fontsmall, settings.TEXT_COLOR, stats_x + 10, stats_y + 200)
    draw_text(engine.MAIN_SCREEN, "Cleared:", font, settings.TEXT_COLOR, stats_x + 10, stats_y + 220)
    
    draw_text(engine.MAIN_SCREEN, PPS, fontbig, settings.TEXT_COLOR, stats_x + 20, stats_y + 50)
    draw_text(engine.MAIN_SCREEN, TIMES, fontbig, settings.TEXT_COLOR, stats_x + 20, stats_y + 150)
    draw_text(engine.MAIN_SCREEN, TIMEMS, fontsmall, settings.TEXT_COLOR, stats_x + 22 + fontbig.size(TIMES)[0], stats_y + 141 + (fontbig.size(TIMES)[1] - fontsmall.size(TIMEMS)[1]))
    
    draw_text(engine.MAIN_SCREEN, CLEARED, fontbig, settings.TEXT_COLOR, stats_x + 20, stats_y + 250)
    
def draw_score_panel(Level="50", Score="50,000"):
    """Draw a rectangular section aligned to the bottom of the board with text."""
    panel_height = int(settings.WINDOW_HEIGHT * 0.05)
    total_board_px = settings.CELL_SIZE * settings.BOARD_HEIGHT
    x = engine.BOARD_PX_OFFSET_X
    y = engine.BOARD_PX_OFFSET_Y + total_board_px
    width = engine.BOARD_WIDTH_PX
    height = panel_height
    
    # Draw the panel rectangle
    draw_rect(x, y, width, height, settings.CRUST_COLOR, cut_size=25, cut_corners=['bottom-left', 'bottom-right'], outline_color=settings.PANEL_OUTLINE)
    
    fontbig = pygame.font.Font(settings.font_dir, 50)
    font = pygame.font.Font(settings.font_dir, 20)
    
    draw_text(engine.MAIN_SCREEN, "Level:", font, settings.TEXT_COLOR, x + 5, y + 5)
    draw_text(engine.MAIN_SCREEN, Level, fontbig, settings.TEXT_COLOR, x + 70, y + 5)
    
    line_offset = font.size("Level:")[0] +  fontbig.size(Level)[0] + 15
    pygame.draw.line(engine.MAIN_SCREEN, settings.PANEL_OUTLINE, (x + line_offset, y), (x+line_offset+40, y + height), 2)
    
    draw_text(engine.MAIN_SCREEN, "Score:", font, settings.TEXT_COLOR, x + line_offset + 25, y + 5)
    draw_text(engine.MAIN_SCREEN, Score, fontbig, settings.TEXT_COLOR, x + width - 30 - fontbig.size(Score)[0], y + 5)
    
    