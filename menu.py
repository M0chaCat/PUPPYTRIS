"""
menu.py has UI functions and stuff for the menu I guess (kity put more info here?)
"""

import pygame
import math

import ui, engine, settings, gamemodes

from ui import draw_rect, draw_text

class Button:
    def __init__(self, x, y, width, height, text,
                 color=(80, 80, 200), hover_color=None, text_color=(255, 255, 255),
                 outline_color=None, cut_corners=None, font=None, callback=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color if hover_color else color
        self.text_color = text_color
        self.outline_color = outline_color
        self.cut_corners = cut_corners
        self.font = font or pygame.font.Font(None, 36)
        self.callback = callback

    def draw(self, surface):
        # Draw button rectangle
        mouse_pos = pygame.mouse.get_pos()
        current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        draw_rect(
            self.rect.x, self.rect.y, self.rect.width, self.rect.height,
            color=current_color, cut_corners=self.cut_corners, outline_color=self.outline_color
        )

        # --- Draw text centered manually ---
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect()
        text_rect.center = self.rect.center  # center inside the button
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.callback:
                self.callback()

def draw_menu(events):
    # --- Percentage of screen size for foreground---
    foreground_width_pct = 0.7
    foreground_height_pct = 0.8

    foreground_width = int(settings.WINDOW_WIDTH * foreground_width_pct)
    foreground_height = int(settings.WINDOW_HEIGHT * foreground_height_pct)

    # --- Center horizontally & vertically ---
    foreground_x = (settings.WINDOW_WIDTH - foreground_width) // 2
    foreground_y = (settings.WINDOW_HEIGHT - foreground_height) // 2

    panel_color = settings.BOARD_COLOR

    # wipe screen
    draw_rect(
        0, 0, settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT,
        color=settings.BACKGROUND_COLOR,
        cut_corners=[],
    )

    # Draw the menu panel
    draw_rect(
        foreground_x, foreground_y, foreground_width, foreground_height,
        color=panel_color,
        cut_corners=['top-left', 'bottom-left', 'top-right', 'bottom-right'],
        outline_color=settings.PANEL_OUTLINE,
        cut_size=30,
    )

    font = pygame.font.Font(None, 36)

    # --- Button setup ---
    button_width = 200
    button_height = 60
    button_spacing = 20  # vertical space between buttons

    def start_tetra():
        engine.reset_game()
        engine.load_gamemode(gamemodes.TetraminoBase)
        engine.STATE = 1

    def start_penta():
        engine.reset_game()
        engine.load_gamemode(gamemodes.PentominoBase)
        engine.STATE = 1

    button_data = [
        ("Start Tetris", start_tetra),
        ("Start Pentris", start_penta),
        ("Quit", pygame.quit)
    ]

    buttons = []

    # Compute vertical starting point to center all buttons in the panel
    total_height = len(button_data) * button_height + (len(button_data) - 1) * button_spacing
    start_y = foreground_y + (foreground_height - total_height) // 2

    for i, (label, callback) in enumerate(button_data):
        button_x = foreground_x + (foreground_width - button_width) // 2
        button_y = start_y + i * (button_height + button_spacing)

        btn = Button(
            button_x, button_y, button_width, button_height,
            text=label,
            color=settings.PANEL_COLOR,
            hover_color=settings.PANEL_COLOR_HOVER,
            text_color=settings.TEXT_COLOR,
            outline_color=settings.PANEL_OUTLINE,
            cut_corners=['top-left', 'bottom-left', 'top-right', 'bottom-right'],
            font=font,
            callback=callback
        )
        buttons.append(btn)

    for event in events:
        if event.type == pygame.QUIT:
            engine.running = False
        for btn in buttons:
            btn.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == settings.KEY_EXIT:
                if engine.STATE == 0: engine.running = False
                else: engine.STATE -= 1

    # Draw buttons
    for btn in buttons:
        btn.draw(ui.MAIN_SCREEN)

        
def draw_mod_screen(events):
    # --- Percentage of screen size for foreground---
    foreground_width_pct = 0.7
    foreground_height_pct = 0.8
    
    foreground_width = int(settings.WINDOW_WIDTH * foreground_width_pct)
    foreground_height = int(settings.WINDOW_HEIGHT * foreground_height_pct)
    
    # --- Center horizontally & vertically ---
    foreground_x = (settings.WINDOW_WIDTH - foreground_width) // 2
    foreground_y = (settings.WINDOW_HEIGHT - foreground_height) // 2
    
    panel_color = settings.BOARD_COLOR
    
    # wipe screen
    draw_rect(
        0, 0, settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT,
        color=settings.BACKGROUND_COLOR,
        cut_corners=[],
    )
    
    # Draw the menu panel
    draw_rect(
        foreground_x, foreground_y, foreground_width, foreground_height,
        color=panel_color,
        cut_corners=['top-left', 'bottom-left', 'top-right', 'bottom-right'],
        outline_color=settings.PANEL_OUTLINE,
        cut_size=30,
    )
    
    font = pygame.font.Font(None, 36)
    
    # --- Button grid config ---
    button_width = 200
    button_height = 60
    spacing_x = 20
    spacing_y = 20
    
    grid_cols = 3  # number of buttons per row
    
    def Default():
        engine.reset_game()
        engine.reset_gamemode()
        engine.STATE = 2
    
    def Guideline():
        engine.reset_game()
        engine.reset_gamemode()
        engine.load_gamemode(gamemodes.Guideline)
        engine.STATE = 2
        
    def Classic():
        engine.reset_game()
        engine.reset_gamemode()
        engine.load_gamemode(gamemodes.Classic)
        engine.STATE = 2
        
    def Arcade():
        engine.reset_game()
        engine.reset_gamemode()
        engine.load_gamemode(gamemodes.BetterArcade)
        engine.STATE = 2
        
    def Teeny():
        engine.reset_game()
        engine.reset_gamemode()
        engine.load_gamemode(gamemodes.Teeny)
        engine.STATE = 2
    
    button_data = [
        ("Default", Default),
        ("Guideline", Guideline),
        ("Classic", Classic),
        ("PPAM", Arcade), #Puppys Pretty Arcade Mode
        ("Teeny", Teeny),
    ]
    
    buttons = []
    
    # Auto-calc rows
    grid_rows = math.ceil(len(button_data) / grid_cols)
    
    # Total grid size
    grid_width = grid_cols * button_width + (grid_cols - 1) * spacing_x
    grid_height = grid_rows * button_height + (grid_rows - 1) * spacing_y
    
    # Center grid in panel
    start_x = foreground_x + (foreground_width - grid_width) // 2
    start_y = foreground_y + (foreground_height - grid_height) // 2
    
    for i, (label, callback) in enumerate(button_data):
        col = i % grid_cols
        row = i // grid_cols
        
        button_x = start_x + col * (button_width + spacing_x)
        button_y = start_y + row * (button_height + spacing_y)
        
        btn = Button(
            button_x, button_y,
            button_width, button_height,
            text=label,
            color=settings.PANEL_COLOR,
            hover_color=settings.PANEL_COLOR_HOVER,
            text_color=settings.TEXT_COLOR,
            outline_color=settings.PANEL_OUTLINE,
            cut_corners=['top-left', 'bottom-left', 'top-right', 'bottom-right'],
            font=font,
            callback=callback
        )
        buttons.append(btn)
        
    for event in events:
        if event.type == pygame.QUIT:
            engine.running = False
        for btn in buttons:
            btn.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == settings.KEY_EXIT:
                if engine.STATE == 0: engine.running = False
                else: engine.STATE -= 1
            
    # Draw buttons
    for btn in buttons:
        btn.draw(ui.MAIN_SCREEN)
        