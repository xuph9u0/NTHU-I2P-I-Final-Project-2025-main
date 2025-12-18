import pygame as pg
from src.core.services import scene_manager, input_manager, sound_manager
from src.interface.components import Button


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
            self.checked = not self.checked  # toggle

    def draw(self, screen: pg.Surface):
        pg.draw.rect(screen, (255, 255, 255), self.rect, 2)
        if self.checked:
            pg.draw.line(screen, (255, 255, 255),
                         (self.x, self.y),
                         (self.x + self.size, self.y + self.size), 3)
            pg.draw.line(screen, (255, 255, 255),
                         (self.x + self.size, self.y),
                         (self.x, self.y + self.size), 3)

        text_surf = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(text_surf, (self.x + 40, self.y - 2))


# ========================================
# Slider UI（已更換為使用 pygame 滑鼠狀態，確保可拖曳）
# ========================================
class Slider:
    def __init__(self, x, y, width, min_value=0, max_value=100, default=50):
        self.x = x
        self.y = y
        self.width = width
        self.min_value = min_value
        self.max_value = max_value
        self.value = default

        self.knob_radius = 10
        self.dragging = False

        # 用於碰撞檢測的矩形（會每幀更新中心）
        self.knob_rect = pg.Rect(0, 0, self.knob_radius * 2, self.knob_radius * 2)

    @property
    def knob_x(self):
        # 計算 knob 的 x 座標
        return int(self.x + (self.value - self.min_value) /
                   (self.max_value - self.min_value) * self.width)

    def update(self, dt):
        # 使用 pygame 的滑鼠狀態（持續回傳）來處理拖曳
        mouse_pos = pg.mouse.get_pos()
        mouse_buttons = pg.mouse.get_pressed()  # (left, middle, right)
        left_down = mouse_buttons[0]

        # 每 frame 更新 knob 的 hitbox 位置
        self.knob_rect.center = (self.knob_x, self.y)

        # 如果目前沒有在拖曳，檢查是否要開始拖曳：
        #  - 點到 knob 開始拖
        #  - 或者點在 bar 範圍內（較寬的 y 範圍）也會把 knob 移到該位置並開始拖
        if not self.dragging:
            if left_down:
                # 點到 knob
                if self.knob_rect.collidepoint(mouse_pos):
                    self.dragging = True
                else:
                    # 點在 bar 的區域內時也直接跳到該位置並開始拖（方便使用）
                    bar_rect = pg.Rect(self.x, self.y - 10, self.width, 20)
                    if bar_rect.collidepoint(mouse_pos):
                        # 把 knob 移到滑鼠處（同時開始拖）
                        new_x = max(self.x, min(mouse_pos[0], self.x + self.width))
                        percent = (new_x - self.x) / self.width
                        self.value = int(self.min_value + percent * (self.max_value - self.min_value))
                        self.dragging = True
        else:
            # 正在拖曳中，如果放開滑鼠就結束拖曳
            if not left_down:
                self.dragging = False

        # 若正在拖曳，更新值（限制在 bar 範圍內）
        if self.dragging:
            new_x = max(self.x, min(mouse_pos[0], self.x + self.width))
            percent = (new_x - self.x) / self.width
            self.value = int(self.min_value + percent * (self.max_value - self.min_value))

    def draw(self, screen: pg.Surface):
        pg.draw.line(screen, (200, 200, 200),
                     (self.x, self.y), (self.x + self.width, self.y), 4)

        pg.draw.circle(screen, (255, 255, 255),
                       (self.knob_x, self.y), self.knob_radius)

        font = pg.font.SysFont(None, 28)
        text_surf = font.render(f"Volume: {self.value}", True, (255, 255, 255))
        screen.blit(text_surf, (self.x, self.y - 30))


# ========================================
# Setting Scene
# ========================================
class SettingScene:
    def __init__(self):
        self.buttons = []

        # Back button
        self.buttons.append(Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            300, 300, 150, 80,
            lambda: scene_manager.change_scene("menu")
        ))

        # UI components
        self.checkbox_mute = Checkbox(100, 100, "Mute Audio", default=False)
        self.slider_volume = Slider(100, 180, 200, 0, 100, 50)

        self.last_volume_before_mute = 50

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self, dt: float):

        # --- update buttons ---
        for btn in self.buttons:
            btn.update(dt)

        # --- update checkbox ---
        self.checkbox_mute.update(dt)

        # --- update slider ---
        self.slider_volume.update(dt)

        # ================================
        # 🔊 音量控制邏輯
        # ================================
        if self.checkbox_mute.checked:
            if self.slider_volume.value != 0:
                self.last_volume_before_mute = self.slider_volume.value
            sound_manager.set_volume(0)

        else:
            volume_float = self.slider_volume.value / 100
            sound_manager.set_volume(volume_float)

    def draw(self, screen: pg.Surface):
        screen.fill((50, 50, 50))

        for btn in self.buttons:
            btn.draw(screen)

        self.checkbox_mute.draw(screen)
        self.slider_volume.draw(screen)
