import pygame as pg
from typing import override

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager, scene_manager, input_manager
from src.sprites import Sprite
from src.interface.components.button import Button

# Overlays
from .backpack_overlay import BackpackOverlay
from .setting_overlay import SettingOverlay
from src.scenes.shop_overlay import ShopOverlay
from src.scenes.minimap import Minimap
# [修正] 確保這裡的 import 與你的檔案名稱一致，建議用 navigation_overlay
from src.scenes.navigation_overlay import NavigationOverlay 

from src.scenes.battle_scene import BattleScene
from src.scenes.catch_pokemon_scene import CatchPokemonScene
from src.entities.shop_npc import ShopNPC


class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite

    def __init__(self):
        super().__init__()

        # ---------------------------
        # Load save file
        # ---------------------------
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager

        # Player tile size
        TS = GameSettings.TILE_SIZE
        player = self.game_manager.player
        player_x = player.position.x
        player_y = player.position.y

        # ---------------------------
        # Bushes for catching Pokemon
        # ---------------------------
        self.bushes = [
            pg.Rect(player_x - 8 * TS, player_y + 1* TS, TS, TS)
        ]

        # ---------------------------
        # Shop NPC
        # ---------------------------
        self.shop_npcs = [
            ShopNPC(18, 30, "menu_sprites/menusprite1.png")
        ]

        # ---------------------------
        # Overlays Initialization
        # ---------------------------
        self.backpack_overlay = BackpackOverlay(self)
        self.setting_overlay = SettingOverlay(self)
        self.shop_overlay = ShopOverlay(self)
        self.minimap = Minimap(self)
        # [修正] 修正類別名稱
        self.show_nav = False
        self.nav_overlay = NavigationOverlay(self)

        self.overlay_type = None

        # ---------------------------
        # Buttons
        # ---------------------------
        # [修正] 先定義位置參數，再建立按鈕，避免變數未定義錯誤
        btn_w, btn_h = 100, 100
        px = GameSettings.SCREEN_WIDTH - btn_w - 10
        py = 10

        # 1. Setting Button (最右邊)
        self.setting_button = Button(
            "UI/button_setting.png",
            "UI/button_setting_hover.png",
            px, py, btn_w, btn_h,
            self.open_setting_overlay
        )

        # 2. Backpack Button (Setting 的左邊)
        backpack_x = px - 110
        self.backpack_button = Button(
            "UI/button_backpack.png",
            "UI/button_backpack_hover.png",
            backpack_x, py, btn_w, btn_h,
            self.open_backpack_overlay
        )

        # 3. [新增] Navigation Button (Backpack 的左邊)
        # 暫時用 save icon，建議之後換成 map icon
        self.nav_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            backpack_x - 110, py, btn_w, btn_h, # 放在背包左邊
            lambda: setattr(self, 'overlay_type', 'NAVIGATION')
        )

        # 4. Back Button (通用返回)
        self.back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            GameSettings.SCREEN_WIDTH // 2 - 50,
            GameSettings.SCREEN_HEIGHT // 2 + 100,
            100, 50,
            self.close_overlay
        )

        # 玩家與 NPC 互動範圍
        self.interaction_range = 300

        # ---------------------------
        # Online manager
        # ---------------------------
        self.online_manager = OnlineManager() if GameSettings.IS_ONLINE else None
        self.sprite_online = Sprite(
            "ingame_ui/options1.png",
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )

        # ---------------------------
        # Warnings System
        # ---------------------------
        self.enemy_warnings = []
        self.closest_enemy = None
        self.shop_warnings = [] 

        # Warning Images
        font = pg.font.SysFont(None, 36)
        self.warning_img = font.render("!", True, (255, 0, 0))
        
        font_shop = pg.font.SysFont(None, 20)
        self.shop_label_img = font_shop.render("SHOP", True, (100, 100, 255))

    # ==============================
    # Overlay control
    # ==============================
    def open_setting_overlay(self):
        self.overlay_type = "setting"

    def open_backpack_overlay(self):
        self.overlay_type = "backpack"
        if self.backpack_overlay:
            self.backpack_overlay.visible = True

    def open_nav_overlay(self):
        self.overlay_type = "navigation"

    def close_overlay(self):
        if self.overlay_type == "backpack" and self.backpack_overlay:
            self.backpack_overlay.visible = False
        elif self.overlay_type == "shop" and self.shop_overlay:  
            self.shop_overlay.visible = False
        elif self.overlay_type == "navigation" and self.nav_overlay:
            self.nav_overlay.visible = False
        
        # 關閉任何 overlay 都設為 None
        self.overlay_type = None

    # ==============================
    # Scene lifecycle
    # ==============================
    @override
    def enter(self):
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()

    @override
    def exit(self):
        if self.online_manager:
            self.online_manager.exit()

    # ==============================
    # Update
    # ==============================
    @override
    def update(self, dt: float):
        # ---------------------------
        # 按 E → 互動邏輯
        # ---------------------------
        if self.overlay_type is None and input_manager.key_pressed(pg.K_e):
            player_rect = pg.Rect(
                self.game_manager.player.position.x,
                self.game_manager.player.position.y,
                getattr(self.game_manager.player, "size", GameSettings.TILE_SIZE),
                getattr(self.game_manager.player, "size", GameSettings.TILE_SIZE)
            )       

            # ShopNPC
            for npc in self.shop_npcs:
                if player_rect.colliderect(npc.rect):
                    self.overlay_type = "shop"
                    self.shop_overlay.visible = True
                    return

            # Enemy
            if self.closest_enemy:
                scene_manager.change_scene("battle")
                return

            # Bushes
            for bush in self.bushes:
                if player_rect.colliderect(bush):
                    scene_manager.change_scene("catch_pokemon")
                    return

        # ---------------------------
        # UI & Overlay Update
        # ---------------------------
        if self.overlay_type is None:
            # [修正] 沒開介面時，更新所有按鈕
            self.setting_button.update(dt)
            self.backpack_button.update(dt)
            self.nav_button.update(dt) # [修正] 變數名稱與拼字
        else:
            # 依據類型更新對應介面
            if self.overlay_type == "backpack":
                self.backpack_overlay.update(dt)
            elif self.overlay_type == "setting":
                self.setting_overlay.update(dt)
            elif self.overlay_type == "shop":
                self.shop_overlay.update(dt)
            elif self.overlay_type == "NAVIGATION": # [修正] 統一用 NAVIGATION
                self.nav_overlay.update(dt)
            
            # 通用返回按鈕 (如果該介面沒有自己的關閉按鈕)
            if self.overlay_type == "setting": 
                self.back_button.update(dt)
            

        # ---------------------------
        # NPC warning & enemy logic
        # ---------------------------
        self.enemy_warnings = []
        self.shop_warnings = [] 
        self.closest_enemy = None
        min_dist_sq = float("inf")

        if self.game_manager.player:
            player = self.game_manager.player
            player_w = getattr(player, "size", 50)
            player_h = getattr(player, "size", 50)
            if hasattr(player, "image") and player.image:
                try:
                    player_w = player.image.get_width()
                    player_h = player.image.get_height()
                except Exception:
                    pass

            player_rect = pg.Rect(player.position.x, player.position.y, player_w, player_h)

            # Enemy Warnings
            for enemy in self.game_manager.current_enemy_trainers:
                enemy_w, enemy_h = 50, 50
                # ... (略過取得寬高的錯誤處理，維持原樣) ...
                enemy_rect = pg.Rect(enemy.position.x, enemy.position.y, enemy_w, enemy_h)
                
                dx = player_rect.centerx - enemy_rect.centerx
                dy = player_rect.centery - enemy_rect.centery
                dist_sq = dx * dx + dy * dy
                warning_radius = 120
                if dist_sq <= warning_radius ** 2:
                    self.enemy_warnings.append(enemy_rect)
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        self.closest_enemy = enemy

            # Shop Warnings
            for npc in self.shop_npcs:
                dx = player_rect.centerx - npc.rect.centerx
                dy = player_rect.centery - npc.rect.centery
                dist_sq = dx * dx + dy * dy
                if dist_sq <= 120 ** 2:
                    self.shop_warnings.append(npc.rect)

        # ---------------------------
        # Game logic (Map, Player, Net)
        # ---------------------------
        self.game_manager.try_switch_map()
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
        self.game_manager.bag.update(dt)

        if self.game_manager.player and self.online_manager:
            self.online_manager.update(
                self.game_manager.player.position.x,
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name
            )

    # ==============================
    # Draw
    # ==============================
    @override
    def draw(self, screen: pg.Surface):
        # 1. Draw Map & Entities
        if self.game_manager.player:
            screen_width, screen_height = screen.get_size()
            px = self.game_manager.player.position.x
            py = self.game_manager.player.position.y
            camera = PositionCamera(px - screen_width // 2, py - screen_height // 2)
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)

        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)

        for npc in self.shop_npcs:
            npc.draw(screen, camera)

        # 2. Draw Online Players
        if self.online_manager and self.game_manager.player:
            for p in self.online_manager.get_list_players():
                if p["map"] == self.game_manager.current_map.path_name:
                    pos = camera.transform_position_as_position(Position(p["x"], p["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)

        # 3. Draw Warnings
        for rect in self.enemy_warnings:
            screen.blit(self.warning_img, (rect.centerx - 10 - camera.x, rect.y - 40 - camera.y))
        for rect in self.shop_warnings:
            screen.blit(self.shop_label_img, (rect.centerx - 20 - camera.x, rect.y - 10 - camera.y))

        # 4. Draw UI Elements (Minimap & Buttons)
        # 只有在沒有 Overlay 時才畫這些
        if self.overlay_type is None:
            self.minimap.draw(screen)
            
            # [修正] 畫出三個按鈕 (原本漏掉 nav_button)
            # 使用 button 類別內建的 draw (如果你 button 類別有 draw 方法)
            self.setting_button.draw(screen)
            self.backpack_button.draw(screen)
            self.nav_button.draw(screen)
            
            # 如果 Button 類別沒有 draw 方法，請保留你原本的寫法：
            # screen.blit(self.setting_button.img_button.image, self.setting_button.hitbox)
            # ...
            return

        # 5. Draw Overlays
        # [修正] 清理了底部重複的程式碼，結構更清晰
        
        # 情況 A: 全螢幕覆蓋型 (自帶背景)
        if self.overlay_type == "shop":
            self.shop_overlay.draw(screen)
        
        elif self.overlay_type == "backpack":
            self.backpack_overlay.draw(screen)
            
        elif self.overlay_type == "NAVIGATION":
            self.nav_overlay.draw(screen)

        # 情況 B: 通用視窗型 (Setting) - 這裡才畫通用背景
        elif self.overlay_type == "setting":
            # 半透明黑底
            overlay = pg.Surface(screen.get_size(), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            # Setting 內容
            self.setting_overlay.draw(screen)
            # 通用返回按鈕
            screen.blit(self.back_button.img_button.image, self.back_button.hitbox)

    # ------------------------------------------------
    # [新增] 這是 NavigationOverlay 專門呼叫的關閉函式
    # ------------------------------------------------
    def close_nav_overlay(self):
        # 將狀態設為 None，遊戲就會回到原本畫面
        self.overlay_type = None
        # 如果你有用 visible 屬性，也要記得關掉 (看你的實作習慣，保險起見加這行)
        if self.nav_overlay:
            self.nav_overlay.visible = False