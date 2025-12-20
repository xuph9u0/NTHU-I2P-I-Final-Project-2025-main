import pygame as pg 
import json
import random
from src.core import GameManager 
from src.scenes.backpack_overlay import BackpackOverlay
from src.scenes.setting_overlay import SettingOverlay
from src.core.services import scene_manager, input_manager
from src.utils import load_img

# =========================
# 按鈕類別
# =========================
class Button:
    """按鈕，滑鼠經過時會下壓"""
    def __init__(self, rect, text, callback):
        self.rect = pg.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = pg.font.SysFont(None, 28)
        self.offset_y = 0
        self.prev_pressed = False
    
    def update(self, enabled=True):
        mouse_pos = pg.mouse.get_pos()
        mouse_down = pg.mouse.get_pressed()[0]

        if not enabled:
            return

        hover = self.rect.collidepoint(mouse_pos)
        self.offset_y = 5 if hover else 0

        if hover and mouse_down and not self.prev_pressed:
            self.callback()

        self.prev_pressed = mouse_down

    def reset_press(self):
        self.prev_pressed = False

    def draw(self, screen):
        draw_rect = self.rect.copy()
        draw_rect.y += self.offset_y

        pg.draw.rect(screen, (255, 255, 255), draw_rect)
        pg.draw.rect(screen, (0, 0, 0), draw_rect, 2)

        text_surf = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)

# =========================
# 怪物類別
# =========================
class Monster:
    def __init__(self, data):
        self.name = data["name"]
        self.hp = data["hp"]
        self.max_hp = data["max_hp"]
        self.level = data["level"]
        # [新增] 隨機屬性邏輯
        if "element" in data:
            self.element = data["element"]
        else:
            self.element = random.choice(["Water", "Fire", "Grass"])
        self.sprite = load_img(data["sprite_path"])
        self.sprite = pg.transform.scale(self.sprite, (100, 100))

# =========================
# BattleScene
# =========================
class BattleScene:
    def __init__(self):
        self.screen_size = pg.display.get_surface().get_size()
        self.background = load_img("backgrounds/background2.png")
        self.background = pg.transform.scale(self.background, self.screen_size)
        self.battle_over = False
        self.game_manager = None

        # ---------------------------
        # Overlays 初始化
        # ---------------------------
        self.overlay_type = None # 用來判斷當前開啟哪個介面 (None, 'backpack', 'setting')
        self.backpack_overlay = BackpackOverlay(self)
        self.setting_overlay = SettingOverlay(self)

        btn_w, btn_h = 120, 50
        margin = 20
        total_width = 4 * btn_w + 3 * margin
        start_x = (self.screen_size[0] - total_width) // 2
        y_pos = self.screen_size[1] - btn_h - 30

        self.buttons = [
            Button((start_x + i*(btn_w+margin), y_pos, btn_w, btn_h),
                   text,
                   lambda t=text: self.handle_action(t))
            for i, text in enumerate(["Fight", "Item", "Switch", "Run"])
        ]

        # ---------------------------
        # [新增] 右上角功能按鈕 (Bag, Set)
        # ---------------------------
        top_btn_w, top_btn_h = 60, 40
        top_margin = 10
        # 設定按鈕 (最右邊)
        self.btn_setting = Button(
            (self.screen_size[0] - top_btn_w - top_margin, top_margin, top_btn_w, top_btn_h),
            "Set",
            self.open_setting
        )
        # 背包按鈕 (在設定按鈕左邊)
        self.btn_backpack = Button(
            (self.screen_size[0] - top_btn_w * 2 - top_margin * 2, top_margin, top_btn_w, top_btn_h),
            "Bag",
            self.open_backpack
        )

        self.font = pg.font.SysFont(None, 24)

        # 回合：player 或 enemy
        self.turn = "player"

    # [新增] 開啟介面的 Callback
    def open_setting(self):
        self.overlay_type = "setting"

    def open_backpack(self):
        self.overlay_type = "backpack"
        self.backpack_overlay.visible = True

    # [新增] 關閉介面 (給 Overlay 使用)
    def close_overlay(self):
        self.overlay_type = None
        self.backpack_overlay.visible = False

    # [新增] 屬性相剋判斷函式 (跟 CatchPokemonScene 一樣)
    def get_element_multiplier(self, attacker_elem, defender_elem):
        multiplier = 1.0
        
        # 2.0 倍 (效果絕佳)
        if attacker_elem == "Water" and defender_elem == "Fire":
            multiplier = 2.0
        elif attacker_elem == "Fire" and defender_elem == "Grass":
            multiplier = 2.0
        elif attacker_elem == "Grass" and defender_elem == "Water":
            multiplier = 2.0
            
        # 0.5 倍 (效果不好)
        elif attacker_elem == "Water" and defender_elem == "Grass":
            multiplier = 0.5
        elif attacker_elem == "Fire" and defender_elem == "Water":
            multiplier = 0.5
        elif attacker_elem == "Grass" and defender_elem == "Fire":
            multiplier = 0.5
            
        return multiplier

    # ----------------------------
    # 重新初始化戰鬥資料
    # ----------------------------
    def enter(self):
        print("Entering BattleScene")

        # 1. 使用 GameManager 讀取存檔 (修正舊的 json.load 寫法)
        self.game_manager = GameManager.load("saves/game0.json")
        
        # 防呆：如果讀取失敗
        if self.game_manager is None:
            print("【錯誤】無法讀取 saves/game0.json，請確認檔案存在。")
            return

        # ==========================================
        # [關鍵修正] 重新初始化 BackpackOverlay
        # ==========================================
        # 因為現在 game_manager 才有資料，這時候建立背包介面，
        # 它才能讀到正確的道具列表。
        self.backpack_overlay = BackpackOverlay(self)

        # 2. 設定戰鬥怪物 (使用物件屬性 .bag 而非 ["bag"])
        try:
            # 確保你的存檔裡有足夠的怪物
            player_data = self.game_manager.bag.monsters[5] 
            enemy_data = self.game_manager.bag.monsters[1]

            self.player_monster = Monster(player_data)
            self.enemy_monster = Monster(enemy_data)
        except Exception as e:
            print(f"【資料錯誤】設定怪物失敗: {e}")
            # 如果出錯，建立假怪物防止當機 (測試用)
            self.player_monster = Monster({"name": "ErrMon", "hp": 100, "max_hp": 100, "level": 1, "sprite_path": "menu_sprites/menusprite1.png", "element": "Water"})
            self.enemy_monster = Monster({"name": "ErrMon", "hp": 100, "max_hp": 100, "level": 1, "sprite_path": "menu_sprites/menusprite1.png", "element": "Fire"})

        # 重置回合
        self.turn = "player"

        # 重置按鈕狀態
        for btn in self.buttons:
            btn.reset_press()
        self.btn_setting.reset_press()
        self.btn_backpack.reset_press()
            
        self.battle_over = False
        self.overlay_type = None # 重置介面狀態
    def exit(self):
        print("Exiting BattleScene")

    # ----------------------------
    # 事件處理（玩家與敵人共用）
    # ----------------------------
    def handle_action(self, text):

        if text == "Fight":
            base_damage = 10  # 基礎傷害

            # --- 玩家攻擊敵人 ---
            if self.turn == "player":
                # 計算倍率：玩家 vs 敵人
                multiplier = self.get_element_multiplier(self.player_monster.element, self.enemy_monster.element)
                final_damage = int(base_damage * multiplier)
                if final_damage < 1: final_damage = 1 # 至少 1 點傷害

                self.enemy_monster.hp -= final_damage
                
                print(f"[玩家回合] {self.player_monster.element} -> {self.enemy_monster.element} (x{multiplier}) 傷害: {final_damage}")

            # --- 敵人攻擊玩家 ---
            else:
                # 計算倍率：敵人 vs 玩家
                multiplier = self.get_element_multiplier(self.enemy_monster.element, self.player_monster.element)
                final_damage = int(base_damage * multiplier)
                if final_damage < 1: final_damage = 1

                self.player_monster.hp -= final_damage

                print(f"[敵人回合] {self.enemy_monster.element} -> {self.player_monster.element} (x{multiplier}) 傷害: {final_damage}")


        elif text == "Item":
            # ... (保持原樣) ...
            if self.turn == "player":
                self.player_monster.hp = min(self.player_monster.hp + 10, self.player_monster.max_hp)
            else:
                self.enemy_monster.hp = min(self.enemy_monster.hp + 10, self.enemy_monster.max_hp)

        elif text == "Switch":
            pass 

        elif text == "Run":
            scene_manager.change_scene("game")
            return

        # 回合切換
        self.turn = "enemy" if self.turn == "player" else "player"

        

    # -------------------------------------------------
    # 更新
    # -------------------------------------------------
    def update(self, dt):

        # [新增] 如果有開啟 Overlay，只更新 Overlay，不更新戰鬥
        if self.overlay_type == "backpack":
            self.backpack_overlay.update(dt)
            return
        elif self.overlay_type == "setting":
            self.setting_overlay.update(dt)
            # 設定頁面通常需要一個返回按鈕，這裡簡單偵測 ESC 或點擊外部來關閉
            keys = pg.key.get_pressed()
            if keys[pg.K_ESCAPE]:
                self.close_overlay()
            return

        # --- 以下是原本的戰鬥邏輯 ---
        if not self.battle_over:
            for btn in self.buttons:
                btn.update(enabled=True)

            # [新增] 更新右上角按鈕
            self.btn_setting.update(enabled=True)
            self.btn_backpack.update(enabled=True)

        if self.player_monster.hp <= 0 or self.enemy_monster.hp <= 0:
            self.battle_over = True

        
        keys = pg.key.get_pressed()
        if keys[pg.K_RETURN]:
            scene_manager.change_scene("game")
        

    # -------------------------------------------------
    # 畫面
    # -------------------------------------------------
    def draw_health_bar(self, screen, x, y, w, h, hp, max_hp):
        pg.draw.rect(screen, (150, 150, 150), (x, y, w, h))
        green_width = int(w * hp / max_hp)
        pg.draw.rect(screen, (0, 255, 0), (x, y, green_width, h))
        pg.draw.rect(screen, (0, 0, 0), (x, y, w, h), 2)

    def draw_monster_info(self, screen, monster, x, y):
        name_text = self.font.render(monster.name, True, (0,0,0))
        screen.blit(name_text, (x, y))

        # [新增] 繪製屬性文字
        color_map = {"Water": (0, 0, 255), "Fire": (255, 0, 0), "Grass": (0, 150, 0)}
        elem_color = color_map.get(monster.element, (0, 0, 0))
        
        elem_text = self.font.render(monster.element, True, elem_color)
        screen.blit(elem_text, (x + 80, y)) # 畫在名字右邊

        lvl_text = self.font.render(f"Lv {monster.level}", True, (0,0,0))
        hp_text = self.font.render(f"{monster.hp}/{monster.max_hp} HP", True, (0,0,0))
        screen.blit(lvl_text, (x - 45, y + 25))
        screen.blit(hp_text, (x, y + 45))

    def draw(self, screen):
        screen.blit(self.background, (0,0))

        # 玩家
        player_pos = (150, self.screen_size[1]//2)
        screen.blit(self.player_monster.sprite, player_pos)
        self.draw_health_bar(screen, 50, self.screen_size[1]//2 + 110, 150, 20,
                             self.player_monster.hp, self.player_monster.max_hp)
        self.draw_monster_info(screen, self.player_monster, 50, self.screen_size[1]//2 + 90)

        # 敵人
        enemy_pos = (self.screen_size[0]-250, self.screen_size[1]//2 - 50)
        screen.blit(self.enemy_monster.sprite, enemy_pos)
        self.draw_health_bar(screen, self.screen_size[0]-300, self.screen_size[1]//2 - 80, 150, 20,
                             self.enemy_monster.hp, self.enemy_monster.max_hp)
        self.draw_monster_info(screen, self.enemy_monster, self.screen_size[0]-300, self.screen_size[1]//2 - 100)

        # UI 按鈕
        for btn in self.buttons:
            btn.draw(screen)

        # [新增] 繪製右上角按鈕
        self.btn_setting.draw(screen)
        self.btn_backpack.draw(screen)

        # 提示文字（完全保留）
        if self.turn == "player":
            txt = f"What will {self.player_monster.name} do?"
        else:
            txt = f"What will {self.enemy_monster.name} do?"

        info_text = self.font.render(txt, True, (0, 0, 0))
        screen.blit(info_text, (50, self.screen_size[1]-100))

        # 3. [新增] 繪製 Overlay (畫在最上層)
        if self.overlay_type == "backpack":
            self.backpack_overlay.draw(screen)
        elif self.overlay_type == "setting":
            # 畫一個半透明黑底
            overlay = pg.Surface(screen.get_size(), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            self.setting_overlay.draw(screen)
