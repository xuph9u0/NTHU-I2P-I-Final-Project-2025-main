import pygame as pg
from src.core.services import input_manager, sound_manager
from src.interface.components.button import Button
from src.core.managers.game_manager import GameManager


# ========================================
# Checkbox UI
# ========================================
class Checkbox:
    def __init__(self, x, y, label, default=False):
        self.x = x
        self.y = y
        self.size = 30
        self.checked = default
        self.label = label
        self.font = pg.font.SysFont(None, 32)
        self.rect = pg.Rect(x, y, self.size, self.size)

    def update(self, dt):
        mouse_pos = input_manager.mouse_pos
        mouse_click = input_manager.mouse_pressed(1)
        if self.rect.collidepoint(mouse_pos) and mouse_click:
            self.checked = not self.checked

    def draw(self, screen: pg.Surface):
        pg.draw.rect(screen, (50, 50, 50), self.rect)
        pg.draw.rect(screen, (255, 255, 255), self.rect, 2)

        if self.checked:
            pg.draw.line(screen, (255, 255, 255),
                         (self.x, self.y),
                         (self.x + self.size, self.y + self.size), 3)
            pg.draw.line(screen, (255, 255, 255),
                         (self.x + self.size, self.y),
                         (self.x, self.y + self.size), 3)

        text_surf = self.font.render(self.label, True, (0, 0, 0))
        screen.blit(text_surf, (self.x + 40, self.y - 2))


# ========================================
# Slider UI (可正常滑動版本)
# ========================================
class Slider:
    def __init__(self, x, y, width, min_value=0, max_value=100, default=50):
        self.x = x
        self.y = y
        self.width = width
        self.min_value = min_value
        self.max_value = max_value
        self.value = default
        self.knob_radius = 12

        self.dragging = False
        self.knob_rect = pg.Rect(0, 0, self.knob_radius*2, self.knob_radius*2)

    @property
    def knob_x(self):
        return int(self.x + (self.value - self.min_value) /
                   (self.max_value - self.min_value) * self.width)

    def update(self, dt):
        mouse_pos = pg.mouse.get_pos()
        mouse_pressed = pg.mouse.get_pressed()[0]

        self.knob_rect.center = (self.knob_x, self.y)

        # 開始拖曳
        if mouse_pressed:
            if self.knob_rect.collidepoint(mouse_pos) and not self.dragging:
                self.dragging = True
        else:
            self.dragging = False

        # 拖曳中：更新滑桿值
        if self.dragging:
            new_x = max(self.x, min(mouse_pos[0], self.x + self.width))
            percent = (new_x - self.x) / self.width
            self.value = int(self.min_value + percent * (self.max_value - self.min_value))

    def draw(self, screen: pg.Surface):
        # bar
        pg.draw.line(screen, (120, 120, 120), (self.x, self.y),
                     (self.x + self.width, self.y), 6)

        # knob
        pg.draw.circle(screen, (255, 255, 255),
                       (self.knob_x, self.y), self.knob_radius)

        # text
        font = pg.font.SysFont(None, 28)
        text_surf = font.render(f"Volume: {self.value}", True, (0, 0, 0))
        screen.blit(text_surf, (self.x, self.y - 30))


# ========================================
# Setting Overlay
# ========================================
class SettingOverlay:
    def __init__(self, game_scene):
        self.game_scene = game_scene

        # Overlay UI
        self.checkbox_mute = Checkbox(480, 230, "Mute Audio", default=False)
        self.slider_volume = Slider(480, 300, 300, 0, 100, 50)
        self.last_volume_before_mute = 50

        # Buttons
        self.buttons = []

        self.save_button = Button(
            "UI/button_save.png", "UI/button_save_hover.png",
            530, 380, 120, 50,
            self.save_game
        )
        self.load_button = Button(
            "UI/button_load.png", "UI/button_load_hover.png",
            680, 380, 120, 50,
            self.load_game
        )
        self.back_button = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            605, 460, 120, 50,
            self.close_overlay
        )

        self.buttons.extend([self.save_button, self.load_button, self.back_button])

    def save_game(self):
        if self.game_scene.game_manager:
            self.game_scene.game_manager.save("saves/game0.json")
            

    def load_game(self):
        gm = GameManager.load("saves/game0.json")
        if gm:
            self.game_scene.game_manager = gm
            

    def close_overlay(self):
        self.game_scene.overlay_type = None

    def update(self, dt):
        for btn in self.buttons:
            btn.update(dt)

        self.checkbox_mute.update(dt)
        self.slider_volume.update(dt)

        # --- 音量邏輯 ---
        if self.checkbox_mute.checked:
            if self.slider_volume.value != 0:
                self.last_volume_before_mute = self.slider_volume.value
            sound_manager.set_volume(0)
        else:
            volume_float = self.slider_volume.value / 100
            sound_manager.set_volume(volume_float)

    def draw(self, screen: pg.Surface):
        # 背景半透明
        overlay = pg.Surface(screen.get_size(), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 白色面板
        panel_rect = pg.Rect(screen.get_width()//2 - 280,
                             screen.get_height()//2 - 250,
                             600, 500)
        pg.draw.rect(screen, (240, 240, 240), panel_rect, border_radius=12)

        # Buttons
        for btn in self.buttons:
            btn.draw(screen)

        # UI Components
        self.checkbox_mute.draw(screen)
        self.slider_volume.draw(screen)
