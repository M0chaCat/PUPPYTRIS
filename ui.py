# UI

import pygame
import math
import numpy
from enum import Enum
import random
import pygame_gui
import os

import engine, settings

BLOCK_SIZE = engine.BOARD_WIDTH_PX // settings.BOARD_WIDTH

def draw_background():
    """Fill the screen with a wallpaper if set, else fallback to BACKGROUND_COLOR."""
    if hasattr(settings, "WALLPAPER") and settings.WALLPAPER:
        # Get window size
        win_w, win_h = settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT
        wp = settings.WALLPAPER
        wp_w, wp_h = wp.get_size()
        
        # Determine scale factor to cover window
        scale_factor = max(win_w / wp_w, win_h / wp_h)
        new_w = int(wp_w * scale_factor)
        new_h = int(wp_h * scale_factor)
        
        # Scale wallpaper
        scaled_wp = pygame.transform.smoothscale(wp, (new_w, new_h))
        
        # Center crop
        offset_x = (new_w - win_w) // 2
        offset_y = (new_h - win_h) // 2
        engine.MAIN_SCREEN.blit(scaled_wp, (-offset_x, -offset_y))
    else:
        engine.MAIN_SCREEN.fill(settings.BACKGROUND_COLOR)

def draw_board(current_board):
    """
    Draw pieces clipped to the visible board area (but don't skip the top cells).
    After drawing pieces, call draw_board_corners() to mask triangular cuts.
    """
    cell = settings.CELL_SIZE
    visible_start_y = engine.BOARD_PX_OFFSET_Y + (settings.BOARD_EXTRA_HEIGHT * cell)
    grid_start_x = engine.BOARD_PX_OFFSET_X
    width = engine.BOARD_WIDTH_PX
    height = engine.BOARD_HEIGHT_PX
    
    # draw pieces if they intersect visible area (so partially-visible pieces still draw)
    for row in range(settings.BOARD_HEIGHT):
        for col in range(settings.BOARD_WIDTH):
            val = current_board[row, col]
            if val == 0:
                continue
            x = grid_start_x + col * cell
            y = visible_start_y + (row - settings.BOARD_EXTRA_HEIGHT) * cell
            # draw if any part of the cell intersects the visible board rectangle
            if (y + cell > visible_start_y) and (y < visible_start_y + height):
                engine.MAIN_SCREEN.blit(engine.pieces_dict[val]["skin"], (x, y))
                
    # draw the triangular corner overlays (covers only the triangle area)
    draw_board_corner_masks(cut_size=cell)
    
    
def draw_board_corner_masks(cut_size=None):
    """
    Draw only the triangular corner masks (top-left & top-right).
    If a wallpaper is set, copy the corresponding wallpaper pixels for each triangle;
    otherwise fill with BACKGROUND_COLOR.
    """
    if cut_size is None:
        cut_size = settings.CELL_SIZE
        
    grid_start_x = engine.BOARD_PX_OFFSET_X
    grid_start_y = engine.BOARD_PX_OFFSET_Y + (settings.BOARD_EXTRA_HEIGHT * settings.CELL_SIZE)
    width = engine.BOARD_WIDTH_PX
    
    # helper to blit the wallpaper-triangle into screen at (dst_x, dst_y)
    def blit_wp_triangle(dst_x, dst_y, triangle_points):
        # Create a temporary surface for the cell area
        tri_w, tri_h = cut_size, cut_size
        tri_surf = pygame.Surface((tri_w, tri_h), flags=pygame.SRCALPHA)
        
        if hasattr(settings, "WALLPAPER") and settings.WALLPAPER:
            wp = settings.WALLPAPER
            wp_w, wp_h = wp.get_size()
            win_w, win_h = settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT
            
            # Map screen rect -> wallpaper source rect (handles wallpapers not equal to window size)
            src_x = int(dst_x * wp_w / win_w)
            src_y = int(dst_y * wp_h / win_h)
            src_w = max(1, int(tri_w * wp_w / win_w))
            src_h = max(1, int(tri_h * wp_h / win_h))
            src_rect = pygame.Rect(src_x, src_y, src_w, src_h)
            
            # Blit the corresponding wallpaper area into tri_surf (scaled if necessary)
            # If sizes differ, scale to tri_surf so the visual alignment matches screen.
            tmp = wp.subsurface(src_rect).copy()
            if (src_w, src_h) != (tri_w, tri_h):
                tmp = pygame.transform.smoothscale(tmp, (tri_w, tri_h))
            tri_surf.blit(tmp, (0, 0))
        else:
            # no wallpaper: fill with background color (we'll mask to triangle)
            tri_surf.fill(settings.BACKGROUND_COLOR + (255,))  # ensure alpha present
            
        # create a mask surface where only the triangle area is opaque
        mask = pygame.Surface((tri_w, tri_h), flags=pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))
        # polygon points need to be relative to tri_surf (shifted by dst_x,dst_y)
        rel_pts = [(px - dst_x, py - dst_y) for (px, py) in triangle_points]
        pygame.draw.polygon(mask, (255, 255, 255, 255), rel_pts)
        
        # multiply tri_surf by mask alpha so only triangle remains
        tri_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # finally blit the triangular surface onto the main screen
        engine.MAIN_SCREEN.blit(tri_surf, (dst_x, dst_y))
        
        
    # top-left triangle points (screen coords)
    tl_pts = [
        (grid_start_x, grid_start_y),
        (grid_start_x + cut_size, grid_start_y),
        (grid_start_x, grid_start_y + cut_size),
    ]
    blit_wp_triangle(grid_start_x, grid_start_y, tl_pts)
    
    # top-right triangle points (screen coords)
    tr_pts = [
        (grid_start_x + width, grid_start_y),
        (grid_start_x + width - cut_size, grid_start_y),
        (grid_start_x + width, grid_start_y + cut_size),
    ]
    blit_wp_triangle(grid_start_x + width - cut_size, grid_start_y, tr_pts)
    
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
            
def draw_rect(x, y, width, height, color=(200, 200, 200), cut_corners=None, cut_size=10):
    """
    Draw a rectangle on the main screen with optional 45deg cuts on specified corners.

    :param x: X position
    :param y: Y position
    :param width: Width of rectangle
    :param height: Height of rectangle
    :param color: RGB color tuple
    :param cut_corners: List of corners to cut (e.g., ['top-left', 'bottom-right'])
    :param cut_size: Size of the corner cut in pixels
    """
    if not cut_corners:
        pygame.draw.rect(engine.MAIN_SCREEN, color, (x, y, width, height))
        return
    
    # Define polygon points clockwise, starting top-left
    points = [
        (x + (cut_size if 'top-left' in cut_corners else 0), y),  # top-left
        (x + width - (cut_size if 'top-right' in cut_corners else 0), y),  # top-right
        (x + width, y + (cut_size if 'top-right' in cut_corners else 0)),  # top-right vertical
        (x + width, y + height - (cut_size if 'bottom-right' in cut_corners else 0)),  # bottom-right
        (x + width - (cut_size if 'bottom-right' in cut_corners else 0), y + height),  # bottom-right horizontal
        (x + (cut_size if 'bottom-left' in cut_corners else 0), y + height),  # bottom-left
        (x, y + height - (cut_size if 'bottom-left' in cut_corners else 0)),  # bottom-left vertical
        (x, y + (cut_size if 'top-left' in cut_corners else 0))  # back to top-left vertical
    ]
    
    pygame.draw.polygon(engine.MAIN_SCREEN, color, points)
    
        
def draw_board_extension(text="SCORE: 0"):
    """Draw a rectangular section aligned to the bottom of the board with text."""
    panel_height = int(settings.WINDOW_HEIGHT * 0.05)
    total_board_px = settings.CELL_SIZE * settings.BOARD_HEIGHT
    x = engine.BOARD_PX_OFFSET_X
    y = engine.BOARD_PX_OFFSET_Y + total_board_px
    width = engine.BOARD_WIDTH_PX
    height = panel_height
    
    # Draw the panel rectangle
    draw_rect(x, y, width, height, settings.CRUST_COLOR, cut_corners=['bottom-left', 'bottom-right'])
    
    # Load font
    padding = 5
    font_size = height - 2 * padding
    try:
        font = pygame.font.Font(settings.font_dir, font_size)
    except:
        font = pygame.font.SysFont(None, font_size)
        
    # Render text
    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect()
    text_rect.topleft = (x + padding, y + padding)  # Add some padding
    engine.MAIN_SCREEN.blit(text_surf, text_rect)
    

def draw_left_panel():
    text = "Next"
    total_board_px = settings.CELL_SIZE * settings.BOARD_HEIGHT
    left_width = int(engine.BOARD_WIDTH_PX * 0.4)
    left_height = int(total_board_px * 0.6)
    
    left_x = engine.BOARD_PX_OFFSET_X - left_width
    left_y = engine.BOARD_PX_OFFSET_Y + (total_board_px - left_height) // 1.09
    
    panel_color = settings.OVERLAY_COLOR
    draw_rect(left_x, left_y, left_width, left_height, color=panel_color, cut_corners=['top-left', 'bottom-left'])
    
    # Text (top-right)
    font_size = 24
    try:
        font = pygame.font.Font(settings.font_dir, font_size)
    except:
        font = pygame.font.SysFont(None, font_size)
        
    text_surf = font.render(text, True, (255, 255, 255))
    padding = 10
    text_rect = text_surf.get_rect(topright=(left_x + left_width - padding, left_y + padding))
    engine.MAIN_SCREEN.blit(text_surf, text_rect)
    
    
def draw_right_panel():
    text = "Hold"
    total_board_px = settings.CELL_SIZE * settings.BOARD_HEIGHT
    right_width = int(engine.BOARD_WIDTH_PX * 0.4)
    right_height = total_board_px / 7
    
    right_x = engine.BOARD_PX_OFFSET_X + engine.BOARD_WIDTH_PX
    right_y = engine.BOARD_PX_OFFSET_Y + (total_board_px - right_height) // 2.14
    
    panel_color = settings.OVERLAY_COLOR
    draw_rect(right_x, right_y, right_width, right_height, color=panel_color, cut_corners=['top-right', 'bottom-right'])
    
    # Text (top-left)
    font_size = 24
    try:
        font = pygame.font.Font(settings.font_dir, font_size)
    except:
        font = pygame.font.SysFont(None, font_size)
        
    text_surf = font.render(text, True, (255, 255, 255))
    padding = 10
    text_rect = text_surf.get_rect(topleft=(right_x + padding, right_y + padding))
    engine.MAIN_SCREEN.blit(text_surf, text_rect)
    
