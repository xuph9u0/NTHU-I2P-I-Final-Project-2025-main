# src/scenes/backpack_overlay.py
import os
import pygame as pg
from functools import partial  # 用於綁定按鈕點擊事件的參數

from src.utils import Logger, GameSettings
from src.sprites import Sprite
# 確保這裡的 import 路徑對應到你提供的 Button 檔案位置
from src.interface.components.button import Button 

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
        
        # 這裡假設你的 Button 放在 src.interface.components.button
        self.close_button = Button(
            "UI/button_x.png",
            "UI/button_x_hover.png",
            btn_x, btn_y, btn_w, btn_h,
            self.close_overlay
        )

        # 背包資料
        self.items = []
        self.monsters = []
        
        # [新增] 儲存道具按鈕的列表
        # 結構: list of tuple (Button_Instance, Item_Data_Dict)
        self.item_buttons = [] 

    def close_overlay(self):
        self.game_scene.close_overlay()

    def on_item_click(self, item_data):
        """[新增] 當道具按鈕被點擊時觸發"""
        Logger.info(f"Item clicked: {item_data['name']}")
        # 這裡可以加入使用道具的邏輯，例如：
        # self.game_scene.game_manager.use_item(item_data)

    def refresh_item_buttons(self):
        """[新增] 根據目前的 self.items 重新生成按鈕"""
        self.item_buttons = []
        
        grid_x = self.x + 320
        grid_y = self.y + 100
        cell_size = 60
        spacing = 10
        items_per_row = 3
        spacing_x = spacing
        spacing_y = spacing + 40 # 垂直間距保留文字空間

        for idx, item in enumerate(self.items):
            row = idx // items_per_row
            col = idx % items_per_row
            x = grid_x + col * (cell_size + spacing_x)
            y = grid_y + row * (cell_size + spacing_y)
            
            sprite_path = item.get("sprite_path", "")
            
            # 建立按鈕
            # 注意：如果不希望圖片有懸停變換效果，hover_path 可以傳入與原圖相同的路徑
            # 使用 partial 將 item 資料綁定到這個按鈕的 callback
            btn = Button(
                img_path=sprite_path,
                img_hovered_path=sprite_path, # 或是你有準備 "item_hover.png" 邊框
                x=x, y=y, 
                width=cell_size, height=cell_size,
                on_click=partial(self.on_item_click, item)
            )
            
            # 將按鈕與資料存入列表，方便 Draw 的時候取用文字資料
            self.item_buttons.append((btn, item))

    def sync_with_game_manager(self):
        """同步 JSON 資料到背包 Overlay"""
        gm = getattr(self.game_scene, "game_manager", None)
        if gm is None:
            return

        # 從 gm.bag 取得資料
        current_monsters = gm.bag._monsters_data
        current_items = gm.bag._items_data

        # 簡單檢查資料是否有變動 (這裡用長度判斷，若要更嚴謹需比對內容)
        # 只有在資料變動時才重新生成按鈕，避免每一幀都 new Button 造成效能浪費與點擊失效
        data_changed = (len(current_items) != len(self.items)) or (self.items != current_items)

        self.monsters = current_monsters
        self.items = current_items

        if data_changed:
            self.refresh_item_buttons()

    def update(self, dt: float):
        self.sync_with_game_manager()
        self.close_button.update(dt)
        
        # [新增] 更新所有道具按鈕
        for btn, _ in self.item_buttons:
            btn.update(dt)

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
        # 怪物區塊 (維持原樣)
        # -------------------
        monster_label = self.font_title.render("Monsters:", True, (0, 0, 0))
        screen.blit(monster_label, (self.x + 20, self.y + 60))

        grid_x = self.x + 20
        grid_y = self.y + 100
        cell_size = 60
        spacing = 10

        for idx, monster in enumerate(self.monsters):
            sprite_path = monster.get("sprite_path", "")
            # 這裡如果也要改成按鈕，邏輯同下方道具區塊
            monster_img = Sprite(sprite_path, (cell_size, cell_size))
            screen.blit(monster_img.image, (grid_x, grid_y + idx * (cell_size + spacing)))

            name_text = self.font_item.render(monster["name"], True, (0, 0, 0))
            hp_text = self.font_info.render(f"HP:{monster['hp']}/{monster['max_hp']} Lv:{monster['level']}", True, (0, 0, 0))
            screen.blit(name_text, (grid_x + cell_size + 10, grid_y + idx * (cell_size + spacing) + 5))
            screen.blit(hp_text, (grid_x + cell_size + 10, grid_y + idx * (cell_size + spacing) + 30))

        # -------------------
        # 道具區塊 (已修改為 Button)
        # -------------------
        item_label = self.font_title.render("Items:", True, (0, 0, 0))
        screen.blit(item_label, (self.x + 320, self.y + 60))

        # [修改] 迭代按鈕列表進行繪製
        for btn, item in self.item_buttons:
            # 1. 繪製按鈕 (處理了 hover 和點擊判定)
            btn.draw(screen)
            
            # 2. 根據按鈕的位置繪製文字 (Name, Count)
            # btn.hitbox 屬性包含了按鈕的 x, y, width, height
            x, y = btn.hitbox.x, btn.hitbox.y
            width, height = btn.hitbox.width, btn.hitbox.height

            name_text = self.font_item.render(item["name"], True, (0, 0, 0))
            count_text = self.font_info.render(f"x{item['count']}", True, (0, 0, 0))
            
            screen.blit(name_text, (x, y + height + 2))
            screen.blit(count_text, (x, y + height + 22))

        # -------------------
        # 關閉按鈕
        # -------------------
        self.close_button.draw(screen)