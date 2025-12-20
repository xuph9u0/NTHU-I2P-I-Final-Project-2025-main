import pygame as pg
from src.scenes.scene import Scene
from src.utils import GameSettings, Logger
from src.utils.pathfinder import find_path

# --- 定義一個專用的簡易按鈕類別 (包含下壓效果) ---
class SimpleNavButton:
    def __init__(self, x, y, width, height, text, font, action_func, action_arg):
        self.rect = pg.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action_func = action_func
        self.action_arg = action_arg
        
        # 狀態
        self.is_hovered = False
        self.is_pressed = False
        self.was_mouse_down = False

        # 顏色設定
        self.color_normal = (255, 255, 255) # 白底
        self.color_hover = (240, 240, 240)  # 稍微灰一點
        self.color_text = (0, 0, 0)         # 黑字
        self.color_shadow = (50, 50, 50)    # 陰影顏色

    def update(self):
        mouse_pos = pg.mouse.get_pos()
        mouse_buttons = pg.mouse.get_pressed()
        is_left_down = mouse_buttons[0]

        self.is_hovered = self.rect.collidepoint(mouse_pos)

        # 判斷點擊邏輯 (下壓效果)
        if self.is_hovered:
            if is_left_down:
                self.is_pressed = True
            else:
                # 如果剛剛是按下的，現在放開了 -> 觸發事件
                if self.is_pressed:
                    self.action_func(self.action_arg)
                self.is_pressed = False
        else:
            self.is_pressed = False
            
    def draw(self, screen):
        # 繪製陰影 (總是畫在原始位置的右下角)
        shadow_offset = 5
        shadow_rect = self.rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pg.draw.rect(screen, self.color_shadow, shadow_rect, border_radius=8)

        # 決定按鈕本體的位置 (如果有按下，就往右下移動，產生下壓感)
        draw_rect = self.rect.copy()
        if self.is_pressed:
            draw_rect.x += shadow_offset
            draw_rect.y += shadow_offset
            current_bg = self.color_hover
        else:
            current_bg = self.color_hover if self.is_hovered else self.color_normal

        # 繪製按鈕本體
        pg.draw.rect(screen, current_bg, draw_rect, border_radius=8)
        pg.draw.rect(screen, (0, 0, 0), draw_rect, 3, border_radius=8) # 黑色邊框

        # 繪製文字
        text_surf = self.font.render(self.text, True, self.color_text)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)

# ----------------------------------------------------

class NavigationOverlay(Scene):
    def __init__(self, game_scene):
        super().__init__()
        self.screen = pg.display.get_surface()
        self.game_scene = game_scene
        self.game_manager = getattr(game_scene, "game_manager", None)

        # 使用粗體字型會好看一點
        self.font = pg.font.SysFont("arial", 40, bold=True)
        
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        btn_width, btn_height = 240, 70
        center_x = self.screen.get_width() // 2
        start_y = 150
        gap = 30  # 按鈕間距

        # 定義按鈕列表
        # action_arg 是傳給導航函式的參數
        items = [
            {"label": "HOME", "target": "HOME"},
            {"label": "SHOP", "target": "SHOP"},
            {"label": "GYM",  "target": "GYM"},
        ]

        for i, item in enumerate(items):
            btn = SimpleNavButton(
                x=center_x - btn_width // 2,
                y=start_y + i * (btn_height + gap),
                width=btn_width,
                height=btn_height,
                text=item["label"],
                font=self.font,
                action_func=self.start_navigation,
                action_arg=item["target"]
            )
            self.buttons.append(btn)

        # 關閉按鈕 (放在最下面)
        close_btn = SimpleNavButton(
            x=center_x - btn_width // 2,
            y=start_y + len(items) * (btn_height + gap) + 40,
            width=btn_width,
            height=btn_height,
            text="CLOSE",
            font=self.font,
            action_func=self.close_overlay,
            action_arg=None
        )
        # 讓關閉按鈕顏色稍微不同 (紅色系)
        close_btn.color_normal = (255, 200, 200)
        self.buttons.append(close_btn)

    def start_navigation(self, target_name):
        """
        處理導航邏輯
        """
        if not self.game_manager:
            return

        gm = self.game_manager
        current_map = gm.current_map
        player = gm.player
        TS = GameSettings.TILE_SIZE

        target_tile = None

        # --- [重點] 設定你的座標 ---
        if target_name == "HOME":
            # 獲取地圖生成點
            target_tile = (int(current_map.spawn.x // TS), int(current_map.spawn.y // TS))
            
        elif target_name == "SHOP":
            # [請修改] Shop 的座標 (網格座標 x, y)
            target_tile = (int(current_map.spawn.x // TS)+2, int(current_map.spawn.y // TS)+1)
            
        elif target_name == "GYM":
            # [請修改] Gym 的座標 (網格座標 x, y)
            target_tile = (int(current_map.spawn.x // TS)+9, int(current_map.spawn.y // TS)-6)

        print(f"Navigating to {target_name}: {target_tile}")

        if target_tile:
            start_tile = (int(player.position.x // TS), int(player.position.y // TS))
            try:
                path = find_path(start_tile, target_tile, current_map)
                if path:
                    player.set_path(path)
                    self.close_overlay(None)
                else:
                    print("No path found!")
            except Exception as e:
                print(f"Navigation Error: {e}")

    def update(self, dt):
        for btn in self.buttons:
            btn.update()

    def draw(self, screen):
        # 畫半透明黑色背景
        overlay = pg.Surface(screen.get_size(), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # 標題
        title_surf = self.font.render("Where to go?", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen.get_width()//2, 80))
        screen.blit(title_surf, title_rect)

        # 畫所有按鈕
        for btn in self.buttons:
            btn.draw(screen)

    def close_overlay(self, _):
        self.game_scene.close_nav_overlay()