import pygame as pg
from src.utils import GameSettings
from src.interface.components.button import Button
from src.sprites import Sprite

class ShopOverlay:
    def __init__(self, game_scene):
        self.game_scene = game_scene
        self.visible = False

        # --- 面板設定 ---
        self.width = 600
        self.height = 500
        self.x = (GameSettings.SCREEN_WIDTH - self.width) // 2
        self.y = (GameSettings.SCREEN_HEIGHT - self.height) // 2

        # --- 字體 ---
        self.font_title = pg.font.SysFont("arial", 28, bold=True)
        self.font_item = pg.font.SysFont("arial", 22)
        self.font_price = pg.font.SysFont("arial", 20, bold=True)
        self.font_msg = pg.font.SysFont("arial", 18, italic=True) # 顯示購買訊息用

        # --- 商店商品清單 ---
        self.shop_items = [
            {
                "name": "Potion", 
                "price": 1, 
                "sprite_path": "ingame_ui/potion.png"
            },
            {
                "name": "Pokeball",
                "price": 1,
                "sprite_path": "ingame_ui/ball.png"
            }
        ]

        # 購買狀態訊息 (例如: "Bought Potion!", "Not enough coins!")
        self.message = ""
        self.message_timer = 0

        # --- UI 元件容器 ---
        self.buttons = []
        self.sprites = {} # 用來快取圖片 Sprite 物件

        # 1. 初始化商品按鈕與圖片
        self.init_shop_items()

        # 2. 關閉按鈕
        btn_w, btn_h = 100, 50
        self.close_button = Button(
            "UI/button_back.png",       
            "UI/button_back_hover.png", 
            self.x + self.width // 2 - 50, # 置中下方
            self.y + self.height - 70,
            btn_w, btn_h,
            self.close_overlay
        )
        self.buttons.append(self.close_button)

    def init_shop_items(self):
        """ 初始化商品列表的圖片與購買按鈕 """
        start_y = self.y + 80
        item_height = 80
        spacing = 10

        # 按鈕圖片
        buy_img = "UI/button_shop.png"         # 建議改成 button_buy.png
        buy_hover_img = "UI/button_shop_hover.png" 

        for idx, item in enumerate(self.shop_items):
            current_y = start_y + idx * (item_height + spacing)
            
            # (A) 載入圖片
            path = item.get("sprite_path", "")
            try:
                self.sprites[idx] = Sprite(path, (60, 60))
            except Exception as e:
                print(f"Error loading image {path}: {e}")
                self.sprites[idx] = None

            # (B) 建立購買按鈕
            btn = Button(
                buy_img, 
                buy_hover_img,
                self.x + self.width - 140, # x 位置 (靠右)
                current_y + 10,            # y 位置
                100, 50,                   # 寬高
                lambda i=idx: self.buy_item(i) # callback
            )
            self.buttons.append(btn)

    def buy_item(self, item_index):
        """ 購買邏輯：檢查金幣 -> 扣款 -> 加道具 """
        # 1. 取得要買的商品資訊
        shop_item = self.shop_items[item_index]
        item_name = shop_item['name']
        item_price = shop_item['price']
        
        # 2. 取得玩家背包資料 (這裡是關鍵)
        # 我們假設 game_manager.bag 有 exposed 出 items (或是 _items_data)
        # 為了保險，我們嘗試取得列表
        gm = self.game_scene.game_manager
        
        # 這裡根據你的架構，可能是 gm.bag.items 或 gm.bag._items_data
        # 我們先嘗試讀取 items，如果沒有就讀取 _items_data (根據你 backpack overlay 的寫法)
        player_items = getattr(gm.bag, "items", None)
        if player_items is None:
            player_items = getattr(gm.bag, "_items_data", [])

        # 3. 尋找玩家身上的 Coins
        coin_entry = None
        for item in player_items:
            if item['name'] == "Coins":
                coin_entry = item
                break
        
        # 4. 判斷是否買得起
        if coin_entry and coin_entry['count'] >= item_price:
            # --- 交易成功 ---
            
            # (A) 扣錢
            coin_entry['count'] -= item_price
            
            # (B) 增加道具
            target_item_entry = None
            for item in player_items:
                if item['name'] == item_name:
                    target_item_entry = item
                    break
            
            if target_item_entry:
                # 已經有這個道具，直接加數量
                target_item_entry['count'] += 1
            else:
                # 沒有這個道具，新增一筆資料
                new_item = {
                    "name": item_name,
                    "count": 1,
                    "sprite_path": shop_item['sprite_path']
                }
                player_items.append(new_item)

            self.set_message(f"Bought {item_name}!", (0, 150, 0))
            print(f"Success: Bought {item_name}. Coins left: {coin_entry['count']}")
        
        else:
            # --- 交易失敗 ---
            self.set_message("Not enough Coins!", (200, 0, 0))
            print("Failed: Not enough coins.")

    def set_message(self, text, color):
        """ 設定顯示在介面上的暫時訊息 """
        self.message = text
        self.message_color = color
        self.message_timer = 2.0 # 訊息顯示 2 秒

    def close_overlay(self):
        self.visible = False
        if self.game_scene:
            self.game_scene.close_overlay()

    def update(self, dt: float):
        if not self.visible:
            return
        
        # 更新按鈕
        for btn in self.buttons:
            btn.update(dt)

        # 更新訊息計時器
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer < 0:
                self.message_timer = 0
                self.message = ""

    def draw(self, screen: pg.Surface):
        if not self.visible:
            return

        # 1. 半透明背景
        overlay_bg = pg.Surface(screen.get_size(), pg.SRCALPHA)
        overlay_bg.fill((0, 0, 0, 180))
        screen.blit(overlay_bg, (0, 0))

        # 2. 商店面板
        panel_rect = pg.Rect(self.x, self.y, self.width, self.height)
        pg.draw.rect(screen, (240, 240, 240), panel_rect, border_radius=12)
        pg.draw.rect(screen, (50, 50, 50), panel_rect, 3, border_radius=12)

        # 3. 標題
        title = self.font_title.render("Item Shop", True, (0, 0, 0))
        screen.blit(title, (self.x + 30, self.y + 20))

        # 4. 顯示玩家目前的錢 (從 GM 抓取)
        gm = self.game_scene.game_manager
        player_items = getattr(gm.bag, "items", []) or getattr(gm.bag, "_items_data", [])
        current_coins = 0
        for item in player_items:
            if item['name'] == "Coins":
                current_coins = item['count']
                break
        
        coin_text = self.font_item.render(f"Your Coins: {current_coins}", True, (100, 100, 100))
        screen.blit(coin_text, (self.x + 350, self.y + 25))

        # 5. 繪製商品列表
        start_y = self.y + 80
        item_height = 80
        spacing = 10

        for idx, item in enumerate(self.shop_items):
            current_y = start_y + idx * (item_height + spacing)
            
            # (A) 商品圖
            sprite = self.sprites.get(idx)
            if sprite and sprite.image:
                screen.blit(sprite.image, (self.x + 40, current_y))
            else:
                pg.draw.rect(screen, (255, 100, 100), (self.x + 40, current_y, 60, 60))

            # (B) 名稱與價格
            name_text = self.font_item.render(item["name"], True, (20, 20, 20))
            screen.blit(name_text, (self.x + 120, current_y + 10))

            price_text = self.font_price.render(f"$ {item['price']}", True, (200, 150, 0))
            screen.blit(price_text, (self.x + 120, current_y + 35))

            # 分隔線
            pg.draw.line(screen, (200, 200, 200), 
                         (self.x + 20, current_y + item_height + 5), 
                         (self.x + self.width - 20, current_y + item_height + 5))

        # 6. 繪製訊息 (購買成功/失敗)
        if self.message:
            msg_surf = self.font_msg.render(self.message, True, self.message_color)
            # 顯示在面板下方中間
            screen.blit(msg_surf, (self.x + 30, self.y + self.height - 40))

        # 7. 繪製按鈕
        for btn in self.buttons:
            btn.draw(screen)