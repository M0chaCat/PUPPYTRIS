"""
menu.py has UI functions and stuff for the menu I guess (kity put more info here?) TEST2
"""

import pygame

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

def draw_menu():
    # --- Percentage of screen size ---
    width_pct = 0.7
    height_pct = 0.8

    width = int(settings.WINDOW_WIDTH * width_pct)
    height = int(settings.WINDOW_HEIGHT * height_pct)

    # --- Center horizontally & vertically ---
    x = (settings.WINDOW_WIDTH - width) // 2
    y = (settings.WINDOW_HEIGHT - height) // 2

    panel_color = settings.BOARD_COLOR

    # wipe screen
    draw_rect(
        0, 0, settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT,
        color=settings.BACKGROUND_COLOR,
        cut_corners=[],
    )

    # Draw the menu panel
    draw_rect(
        x, y, width, height,
        color=panel_color,
        cut_corners=['top-left', 'bottom-left', 'top-right', 'bottom-right'],
        outline_color=settings.PANEL_OUTLINE,
        cut_size=30,
    )

    font = pygame.font.Font(None, 36)

    # --- Button setup ---
    button_width = 200
    button_height = 60
    spacing = 20  # vertical space between buttons

    def start_tetra():
        engine.reset_game()
        engine.load_gamemode(gamemodes.TetraminoBase)
        engine.STATE = 2

    def start_penta():
        engine.reset_game()
        engine.load_gamemode(gamemodes.PentominoBase)
        engine.STATE = 2

    button_data = [
        ("Start Tetris", start_tetra),
        ("Start Pentris", start_penta),
        ("Quit", pygame.quit)
    ]

    buttons = []

    # Compute vertical starting point to center all buttons in the panel
    total_height = len(button_data) * button_height + (len(button_data) - 1) * spacing
    start_y = y + (height - total_height) // 2

    for i, (label, cb) in enumerate(button_data):
        bx = x + (width - button_width) // 2
        by = start_y + i * (button_height + spacing)

        btn = Button(
            bx, by, button_width, button_height,
            text=label,
            color=settings.PANEL_COLOR,
            hover_color=settings.PANEL_COLOR_HOVER,
            text_color=settings.TEXT_COLOR,
            outline_color=settings.PANEL_OUTLINE,
            cut_corners=['top-left', 'bottom-left', 'top-right', 'bottom-right'],
            font=font,
            callback=cb
        )
        buttons.append(btn)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            engine.running = False
        for btn in buttons:
            btn.handle_event(event)

    # Draw buttons
    for btn in buttons:
        btn.draw(ui.MAIN_SCREEN)
