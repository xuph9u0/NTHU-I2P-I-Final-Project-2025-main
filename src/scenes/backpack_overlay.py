# src/scenes/backpack_overlay.py
import os
import pygame as pg
from src.utils import Logger, GameSettings
from src.interface.components.button import Button
from src.sprites import Sprite

# -------------------
# load_image 函式
# -------------------
def load_image(path: str) -> pg.Surface:
    """載入圖片並轉換 alpha，找不到檔案回傳透明表面"""
    if not os.path.isfile(path):
        Logger.warning(f"Image not found: {path}")
        return pg.Surface((50, 50), pg.SRCALPHA)
    return pg.image.load(path).convert_alpha()


class BackpackOverlay:
    def __init__(self, game_scene):
        self.game_scene = game_scene
        self.visible = True

        # 面板尺寸與位置
        self.width = 600
        self.height = 600
        self.x = (GameSettings.SCREEN_WIDTH - self.width) // 2
        self.y = (GameSettings.SCREEN_HEIGHT - self.height) // 2

        # 字體
        self.font_title = pg.font.SysFont("arial", 28, bold=True)
        self.font_item = pg.font.SysFont("arial", 22)
        self.font_info = pg.font.SysFont("arial", 18)

        # 關閉按鈕
        btn_w, btn_h = 100, 50
        btn_x = self.x + self.width - btn_w - 20
        btn_y = self.y + self.height - btn_h - 20
        self.close_button = Button(
            "UI/button_x.png",
            "UI/button_x_hover.png",
            btn_x, btn_y, btn_w, btn_h,
            self.close_overlay
        )

        # 背包資料
        self.items = []
        self.monsters = []

    def close_overlay(self):
        self.game_scene.close_overlay()

    def sync_with_game_manager(self):
        """同步 JSON 資料到背包 Overlay"""
        gm = getattr(self.game_scene, "game_manager", None)
        if gm is None:
            return

        # 從 gm.bag 取得資料
        self.monsters = gm.bag._monsters_data
        self.items = gm.bag._items_data

    def update(self, dt: float):
        self.sync_with_game_manager()
        self.close_button.update(dt)

    def draw(self, screen: pg.Surface):
        if not self.visible:
            return

        # -------------------
        # 半透明背景
        # -------------------
        overlay_bg = pg.Surface(screen.get_size(), pg.SRCALPHA)
        overlay_bg.fill((0, 0, 0, 180))
        screen.blit(overlay_bg, (0, 0))

        # -------------------
        # 面板
        # -------------------
        panel_rect = pg.Rect(self.x, self.y, self.width, self.height)
        pg.draw.rect(screen, (240, 240, 240), panel_rect, border_radius=12)
        pg.draw.rect(screen, (0, 0, 0), panel_rect, 2, border_radius=12)

        # 標題
        title_text = self.font_title.render("Backpack", True, (0, 0, 0))
        screen.blit(title_text, (self.x + 20, self.y + 15))

        # -------------------
        # 怪物區塊
        # -------------------
        monster_label = self.font_title.render("Monsters:", True, (0, 0, 0))
        screen.blit(monster_label, (self.x + 20, self.y + 60))

        grid_x = self.x + 20
        grid_y = self.y + 100
        cell_size = 60
        spacing = 10

        for idx, monster in enumerate(self.monsters):
            Logger.info(monster["sprite_path"])
            # 載入圖片
            sprite_path = monster.get("sprite_path", "")
            monster_img = Sprite(sprite_path, (cell_size, cell_size))
            screen.blit(monster_img.image, (grid_x, grid_y + idx * (cell_size + spacing)))

            # 名稱與等級/血量
            name_text = self.font_item.render(monster["name"], True, (0, 0, 0))
            hp_text = self.font_info.render(f"HP:{monster['hp']}/{monster['max_hp']} Lv:{monster['level']}", True, (0, 0, 0))
            screen.blit(name_text, (grid_x + cell_size + 10, grid_y + idx * (cell_size + spacing) + 5))
            screen.blit(hp_text, (grid_x + cell_size + 10, grid_y + idx * (cell_size + spacing) + 30))

        # -------------------
        # 道具區塊
        # -------------------
        item_label = self.font_title.render("Items:", True, (0, 0, 0))
        screen.blit(item_label, (self.x + 320, self.y + 60))

        grid_x = self.x + 320
        grid_y = self.y + 100
        items_per_row = 3

        for idx, item in enumerate(self.items):
            row = idx // items_per_row
            col = idx % items_per_row
            x = grid_x + col * (cell_size + spacing)
            y = grid_y + row * (cell_size + spacing)

            # 載入圖片
            sprite_path = item.get("sprite_path", "")
            item_img = Sprite(sprite_path, (cell_size, cell_size))
            # 修正：使用 x, y 放置圖片
            screen.blit(item_img.image, (x, y))

            # 顯示名稱與數量
            name_text = self.font_item.render(item["name"], True, (0, 0, 0))
            count_text = self.font_info.render(f"x{item['count']}", True, (0, 0, 0))
            screen.blit(name_text, (x, y + cell_size + 2))
            screen.blit(count_text, (x, y + cell_size + 22))

        # -------------------
        # 關閉按鈕
        # -------------------
        self.close_button.draw(screen)
