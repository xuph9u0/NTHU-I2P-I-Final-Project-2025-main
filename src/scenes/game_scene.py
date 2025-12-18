import pygame as pg
from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager, scene_manager, input_manager
from src.sprites import Sprite
from typing import override
from src.interface.components.button import Button
from .backpack_overlay import BackpackOverlay
from .setting_overlay import SettingOverlay
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
            pg.Rect(player_x - 7 * TS, player_y, TS, TS),
            pg.Rect(player_x + 11 * TS, player_y, TS, TS),
            pg.Rect(player_x + 7 * TS, player_y + 4 * TS, TS, TS),
            pg.Rect(player_x + 14 * TS, player_y, TS, TS),
            pg.Rect(player_x + 26 * TS, player_y - 1 * TS, TS, TS),
            pg.Rect(player_x + 28 * TS, player_y + 3 * TS, TS, TS),
            pg.Rect(player_x + 33 * TS, player_y + 1 * TS, TS, TS),
            pg.Rect(player_x + 35 * TS, player_y + 3 * TS, TS, TS),
            pg.Rect(player_x + 31 * TS, player_y + 6 * TS, TS, TS),
            pg.Rect(player_x + 7 * TS, player_y + 7 * TS, TS, TS)
        ]

        # ---------------------------
        # Shop NPC
        # ---------------------------
        self.shop_npcs = [
            ShopNPC(18, 30, "menu_sprites/menusprite1.png")  # tile 座標 + 圖片路徑
        ]

        # ---------------------------
        # Overlays
        # ---------------------------
        self.backpack_overlay = BackpackOverlay(self)
        self.setting_overlay = SettingOverlay(self)

        # ---------------------------
        # Buttons
        # ---------------------------
        btn_w, btn_h = 100, 100
        px = GameSettings.SCREEN_WIDTH - btn_w - 10
        py = 10

        self.setting_button = Button(
            "UI/button_setting.png",
            "UI/button_setting_hover.png",
            px, py, btn_w, btn_h,
            self.open_setting_overlay
        )

        self.backpack_button = Button(
            "UI/button_backpack.png",
            "UI/button_backpack_hover.png",
            px - 110, py, btn_w, btn_h,
            self.open_backpack_overlay
        )

        self.overlay_type = None
        self.back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            GameSettings.SCREEN_WIDTH // 2 - 50,
            GameSettings.SCREEN_HEIGHT // 2 + 100,
            100, 50,
            self.close_overlay
        )

        # ---------------------------
        # Online manager
        # ---------------------------
        self.online_manager = OnlineManager() if GameSettings.IS_ONLINE else None
        self.sprite_online = Sprite(
            "ingame_ui/options1.png",
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )

        # ---------------------------
        # Multi-NPC warning system
        # ---------------------------
        self.enemy_warnings = []
        self.closest_enemy = None

        # Exclamation mark
        font = pg.font.SysFont(None, 36)
        self.warning_img = font.render("!", True, (255, 0, 0))

    # ==============================
    # Overlay control
    # ==============================
    def open_setting_overlay(self):
        self.overlay_type = "setting"

    def open_backpack_overlay(self):
        self.overlay_type = "backpack"
        if self.backpack_overlay:
            self.backpack_overlay.visible = True

    def close_overlay(self):
        if self.overlay_type == "backpack" and self.backpack_overlay:
            self.backpack_overlay.visible = False
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
        # 按 E → 進入戰鬥、抓寶可夢或與 NPC 互動
        # ---------------------------
        if self.overlay_type is None and input_manager.key_pressed(pg.K_e):
            player_rect = pg.Rect(
                self.game_manager.player.position.x,
                self.game_manager.player.position.y,
                getattr(self.game_manager.player, "size", GameSettings.TILE_SIZE),
                getattr(self.game_manager.player, "size", GameSettings.TILE_SIZE)
            )

            # 與 ShopNPC 互動
            for npc in self.shop_npcs:
                if player_rect.colliderect(npc.rect):
                    npc.open_shop(self.game_manager.bag)
                    return


            # 靠近 enemy → battle
            if self.closest_enemy:
                scene_manager.change_scene("battle")
                return

            # 靠近灌木叢 → catch Pokemon
            for bush in self.bushes:
                if player_rect.colliderect(bush):
                    scene_manager.change_scene("catch_pokemon")
                    return

        # ---------------------------
        # Overlay update
        # ---------------------------
        if self.overlay_type is None:
            self.setting_button.update(dt)
            self.backpack_button.update(dt)
        else:
            if self.overlay_type == "backpack":
                self.backpack_overlay.update(dt)
            if self.overlay_type == "setting":
                self.setting_overlay.update(dt)
            self.back_button.update(dt)

        # ---------------------------
        # NPC warning & enemy logic
        # ---------------------------
        self.enemy_warnings = []
        self.closest_enemy = None
        min_dist_sq = float("inf")

        if self.game_manager.player:
            player = self.game_manager.player
            player_w = getattr(player, "size", None) or 50
            player_h = getattr(player, "size", None) or 50
            if hasattr(player, "image") and player.image:
                try:
                    player_w = player.image.get_width()
                    player_h = player.image.get_height()
                except Exception:
                    pass

            player_rect = pg.Rect(player.position.x, player.position.y, player_w, player_h)

            for enemy in self.game_manager.current_enemy_trainers:
                enemy_w, enemy_h = 50, 50
                if hasattr(enemy, "image") and enemy.image:
                    try:
                        enemy_w = enemy.image.get_width()
                        enemy_h = enemy.image.get_height()
                    except Exception:
                        pass
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

        # ---------------------------
        # Game logic
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

        # Enemies
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)

        # Shop NPCs
        for npc in self.shop_npcs:
            npc.draw(screen, camera)

        # Player bag UI
        self.game_manager.bag.draw(screen)

        # Online players
        if self.online_manager and self.game_manager.player:
            for p in self.online_manager.get_list_players():
                if p["map"] == self.game_manager.current_map.path_name:
                    pos = camera.transform_position_as_position(Position(p["x"], p["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)

        # NPC / enemy warnings
        for rect in self.enemy_warnings:
            screen.blit(self.warning_img, (rect.centerx - 10 - camera.x, rect.y - 40 - camera.y))

        # Overlay buttons
        if self.overlay_type is None:
            screen.blit(self.setting_button.img_button.image, self.setting_button.hitbox)
            screen.blit(self.backpack_button.img_button.image, self.backpack_button.hitbox)
            return

        # Overlay background
        overlay = pg.Surface(screen.get_size(), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        panel_rect = pg.Rect(screen.get_width() // 2 - 300, screen.get_height() // 2 - 250, 600, 500)
        pg.draw.rect(screen, (240, 240, 240), panel_rect, border_radius=12)

        # Back button
        screen.blit(self.back_button.img_button.image, self.back_button.hitbox)

        # Draw overlay pages
        if self.overlay_type == "backpack":
            self.backpack_overlay.draw(screen)
        elif self.overlay_type == "setting":
            self.setting_overlay.draw(screen)
