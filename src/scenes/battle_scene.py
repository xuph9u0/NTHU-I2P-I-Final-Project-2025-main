import pygame as pg 
import json
import random
from src.core import GameManager 
from src.scenes.backpack_overlay import BackpackOverlay
from src.scenes.setting_overlay import SettingOverlay
from src.core.services import scene_manager, input_manager
from src.utils import load_img

# =========================
# [特效 1] 飄浮傷害數字類別
# =========================
class DamageText:
    def __init__(self, x, y, damage, color=(255, 0, 0)):
        self.x = x
        self.y = y
        self.text = str(damage)
        self.color = color
        self.font = pg.font.SysFont("Arial", 30, bold=True)
        self.life = 60  # 存在 60幀 (約1秒)
        self.offset_y = 0
        self.alpha = 255

    def update(self):
        self.life -= 1
        self.offset_y -= 1.5  # 慢慢往上飄
        if self.life < 20:    # 最後 20幀慢慢變透明
            self.alpha = int((self.life / 20) * 255)

    def draw(self, screen):
        if self.life > 0:
            surf = self.font.render(self.text, True, self.color)
            surf.set_alpha(self.alpha)
            # 描邊效果讓字更清楚
            outline = self.font.render(self.text, True, (0,0,0))
            outline.set_alpha(self.alpha)
            screen.blit(outline, (self.x + 2, self.y + self.offset_y + 2))
            screen.blit(surf, (self.x, self.y + self.offset_y))

# =========================
# 按鈕類別 (保持不變)
# =========================
class Button:
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

        if not enabled: return

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
        
        # 戰鬥屬性加成
        self.atk_mult = 1.0 
        self.def_mult = 1.0

        # [特效 3] 受擊閃爍計時器
        self.hit_flash_timer = 0 

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

        # Overlays
        self.overlay_type = None 
        self.backpack_overlay = BackpackOverlay(self)
        self.setting_overlay = SettingOverlay(self)

        # [特效 2] 畫面震動偏移量與計時器
        self.shake_offset = [0, 0]
        self.shake_timer = 0
        
        # [特效 1] 傷害數字列表
        self.damage_texts = []

        # 按鈕設定
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

        # 右上角功能按鈕
        top_btn_w, top_btn_h = 60, 40
        top_margin = 10
        self.btn_setting = Button(
            (self.screen_size[0] - top_btn_w - top_margin, top_margin, top_btn_w, top_btn_h),
            "Set", self.open_setting
        )
        self.btn_backpack = Button(
            (self.screen_size[0] - top_btn_w * 2 - top_margin * 2, top_margin, top_btn_w, top_btn_h),
            "Bag", self.open_backpack
        )

        self.font = pg.font.SysFont(None, 24)
        self.turn = "player"

    def open_setting(self):
        self.overlay_type = "setting"

    def open_backpack(self):
        self.overlay_type = "backpack"
        self.backpack_overlay.visible = True

    def close_overlay(self):
        self.overlay_type = None
        self.backpack_overlay.visible = False

    def get_element_multiplier(self, attacker_elem, defender_elem):
        multiplier = 1.0
        if attacker_elem == "Water" and defender_elem == "Fire": multiplier = 1.5
        elif attacker_elem == "Fire" and defender_elem == "Grass": multiplier = 1.5
        elif attacker_elem == "Grass" and defender_elem == "Water": multiplier = 1.5
        elif attacker_elem == "Water" and defender_elem == "Grass": multiplier = 1.0
        elif attacker_elem == "Fire" and defender_elem == "Water": multiplier = 1.0
        elif attacker_elem == "Grass" and defender_elem == "Fire": multiplier = 1.0
        return multiplier

    # ----------------------------
    # 重新初始化戰鬥資料 (偵錯與修復版)
    # ----------------------------
    
    def enter(self):
        print("Entering BattleScene")
        self.game_manager = GameManager.load("saves/game0.json")

        # 1. 初始化背包介面
        self.backpack_overlay = BackpackOverlay(self)
        
        self.player_monster = None
        self.enemy_monster = None

        # 2. 嘗試讀取存檔
        if self.game_manager:
            try:
                # 嘗試取得列表，不管它叫 monsters 還是 pokemon
                bag = self.game_manager.bag
                monster_list = []
                
                if hasattr(bag, "monsters"):
                    monster_list = bag.monsters
                elif hasattr(bag, "pokemon"):
                    monster_list = bag.pokemon
                elif hasattr(bag, "data"):
                    monster_list = bag.data

                # 確保有足夠的怪物
                if len(monster_list) > 5:
                    self.player_monster = Monster(monster_list[5])
                    self.enemy_monster = Monster(monster_list[1])
                else:
                    print("【警告】存檔內的怪物數量不足，將使用預設怪物")

            except Exception as e:
                print(f"【讀取失敗】無法從存檔載入怪物: {e}")

        # 3. [保底機制] 如果上面失敗，建立假怪物 (防止當機)
        if self.player_monster is None:
            print("【系統】使用預設測試怪物 (Test Mode)")
            dummy_data = {
                "name": "Player", "hp": 100, "max_hp": 100, "level": 1, 
                "sprite_path": "menu_sprites/menusprite1.png", 
                "element": "Water" # 這裡寫什麼不重要，下面會覆蓋
            }
            try:
                self.player_monster = Monster(dummy_data)
                
                dummy_data["name"] = "Enemy"
                self.enemy_monster = Monster(dummy_data)
            except:
                print("【嚴重錯誤】連預設圖片都讀不到")

        # ==========================================
        # [關鍵修改] 無論如何，這裡強制隨機屬性
        # ==========================================
        elements = ["Water", "Fire", "Grass"]
        
        if self.player_monster:
            self.player_monster.element = random.choice(elements)
        
        if self.enemy_monster:
            self.enemy_monster.element = random.choice(elements)

        print(f"★ 戰鬥開始! 屬性重置: 玩家[{self.player_monster.element}] vs 敵人[{self.enemy_monster.element}]")
        # ==========================================

        # 重置變數
        self.turn = "player"
        self.damage_texts = [] 
        for btn in self.buttons: btn.reset_press()
        self.btn_setting.reset_press()
        self.btn_backpack.reset_press()
        self.battle_over = False
        self.overlay_type = None

    def exit(self):
        print("Exiting BattleScene")

    # ----------------------------
    # 事件處理
    # ----------------------------
    def handle_action(self, text):
        if text == "Fight":
            base_damage = 10 
            
            # --- 玩家攻擊敵人 ---
            if self.turn == "player":
                multiplier = self.get_element_multiplier(self.player_monster.element, self.enemy_monster.element)
                final_damage = int(base_damage * multiplier * self.player_monster.atk_mult / self.enemy_monster.def_mult)
                if final_damage < 1: final_damage = 1

                self.enemy_monster.hp -= final_damage
                
                # [特效觸發] 震動 + 飄字 + 敵人閃白
                self.shake_timer = 10
                self.enemy_monster.hit_flash_timer = 10
                self.damage_texts.append(DamageText(self.screen_size[0]-250, self.screen_size[1]//2 - 100, final_damage, (255, 50, 50)))

                print(f"[玩家回合] 傷害: {final_damage}")

            # --- 敵人攻擊玩家 ---
            else:
                multiplier = self.get_element_multiplier(self.enemy_monster.element, self.player_monster.element)
                final_damage = int(base_damage * multiplier * self.enemy_monster.atk_mult / self.player_monster.def_mult)
                if final_damage < 1: final_damage = 1

                self.player_monster.hp -= final_damage

                # [特效觸發] 震動 + 飄字 + 玩家閃白
                self.shake_timer = 10
                self.player_monster.hit_flash_timer = 10
                self.damage_texts.append(DamageText(150, self.screen_size[1]//2, final_damage, (255, 100, 0)))

                print(f"[敵人回合] 傷害: {final_damage}")

        elif text == "Item":
            if self.turn == "player":
                self.player_monster.hp = min(self.player_monster.hp + 10, self.player_monster.max_hp)
            else:
                self.enemy_monster.hp = min(self.enemy_monster.hp + 10, self.enemy_monster.max_hp)

        elif text == "Switch":
            pass 

        elif text == "Run":
            scene_manager.change_scene("game")
            return

        self.turn = "enemy" if self.turn == "player" else "player"

    # -------------------------------------------------
    # 更新
    # -------------------------------------------------
    def update(self, dt):
        if self.overlay_type == "backpack":
            self.backpack_overlay.update(dt)
            return
        elif self.overlay_type == "setting":
            self.setting_overlay.update(dt)
            if pg.key.get_pressed()[pg.K_ESCAPE]:
                self.close_overlay()
            return

        if not self.battle_over:
            for btn in self.buttons: btn.update(enabled=True)
            self.btn_setting.update(enabled=True)
            self.btn_backpack.update(enabled=True)

        if self.player_monster.hp <= 0 or self.enemy_monster.hp <= 0:
            self.battle_over = True
        
        # [特效更新] 處理震動
        if self.shake_timer > 0:
            self.shake_timer -= 1
            magnitude = 5
            self.shake_offset = [random.randint(-magnitude, magnitude), random.randint(-magnitude, magnitude)]
        else:
            self.shake_offset = [0, 0]

        # [特效更新] 處理飄字
        for dt_txt in self.damage_texts:
            dt_txt.update()
        self.damage_texts = [t for t in self.damage_texts if t.life > 0] # 移除消失的

        # [特效更新] 處理怪物受傷閃白計時
        if self.player_monster.hit_flash_timer > 0: self.player_monster.hit_flash_timer -= 1
        if self.enemy_monster.hit_flash_timer > 0: self.enemy_monster.hit_flash_timer -= 1

        if pg.key.get_pressed()[pg.K_RETURN]:
            scene_manager.change_scene("game")

    # -------------------------------------------------
    # 畫面
    # -------------------------------------------------
    def draw_health_bar(self, screen, x, y, w, h, hp, max_hp):
        # [特效 4] 動態血條顏色
        ratio = hp / max_hp
        if ratio > 0.5:
            bar_color = (0, 255, 0)      # 綠
        elif ratio > 0.2:
            bar_color = (255, 215, 0)    # 黃
        else:
            bar_color = (220, 20, 60)    # 紅

        pg.draw.rect(screen, (50, 50, 50), (x, y, w, h)) # 深灰底色看起來更有質感
        green_width = int(w * ratio)
        if green_width > 0:
            pg.draw.rect(screen, bar_color, (x, y, green_width, h))
        pg.draw.rect(screen, (0, 0, 0), (x, y, w, h), 2)

    def draw_monster_info(self, screen, monster, x, y):
        name_text = self.font.render(monster.name, True, (0,0,0))
        screen.blit(name_text, (x, y))

        color_map = {"Water": (0, 0, 255), "Fire": (255, 0, 0), "Grass": (0, 150, 0)}
        elem_color = color_map.get(monster.element, (0, 0, 0))
        elem_text = self.font.render(monster.element, True, elem_color)
        screen.blit(elem_text, (x + 80, y))

        # [特效 5] 狀態 Buff 顯示
        buff_str = ""
        if monster.atk_mult > 1.0: buff_str += " ATK UP!"
        if monster.def_mult > 1.0: buff_str += " DEF UP!"
        
        if buff_str:
            buff_text = self.font.render(buff_str, True, (255, 0, 255)) # 紫色提示
            # 讓字閃爍
            if (pg.time.get_ticks() // 500) % 2 == 0:
                screen.blit(buff_text, (x + 160, y))

        lvl_text = self.font.render(f"Lv {monster.level}", True, (0,0,0))
        hp_text = self.font.render(f"{monster.hp}/{monster.max_hp} HP", True, (0,0,0))
        screen.blit(lvl_text, (x - 45, y + 25))
        screen.blit(hp_text, (x, y + 45))

    def draw_monster_sprite(self, screen, monster, x, y):
        """[特效 3 輔助函式] 處理怪物繪製與受擊閃白"""
        draw_x = x + self.shake_offset[0]
        draw_y = y + self.shake_offset[1]
        
        screen.blit(monster.sprite, (draw_x, draw_y))
        
        # 如果正在受傷閃爍，畫一個白色的遮罩
        if monster.hit_flash_timer > 0:
            mask = monster.sprite.copy()
            mask.fill((255, 255, 255, 150), special_flags=pg.BLEND_RGB_ADD) # 變白
            screen.blit(mask, (draw_x, draw_y))

    def draw(self, screen):
        # [特效 2 應用] 整個背景跟著震動
        bg_x = self.shake_offset[0]
        bg_y = self.shake_offset[1]
        screen.blit(self.background, (bg_x, bg_y))

        # 玩家 (使用新的繪製函式)
        player_pos = (150, self.screen_size[1]//2)
        self.draw_monster_sprite(screen, self.player_monster, player_pos[0], player_pos[1])
        
        # 為了不讓 UI 跟著震動，UI 座標不加 offset
        self.draw_health_bar(screen, 50, self.screen_size[1]//2 + 110, 150, 20,
                             self.player_monster.hp, self.player_monster.max_hp)
        self.draw_monster_info(screen, self.player_monster, 50, self.screen_size[1]//2 + 90)

        # 敵人 (使用新的繪製函式)
        enemy_pos = (self.screen_size[0]-250, self.screen_size[1]//2 - 50)
        self.draw_monster_sprite(screen, self.enemy_monster, enemy_pos[0], enemy_pos[1])
        
        self.draw_health_bar(screen, self.screen_size[0]-300, self.screen_size[1]//2 - 80, 150, 20,
                             self.enemy_monster.hp, self.enemy_monster.max_hp)
        self.draw_monster_info(screen, self.enemy_monster, self.screen_size[0]-300, self.screen_size[1]//2 - 100)

        # [特效 1 應用] 繪製傷害數字 (在怪物和UI之上)
        for dt_txt in self.damage_texts:
            dt_txt.draw(screen)

        # UI 按鈕
        for btn in self.buttons: btn.draw(screen)
        self.btn_setting.draw(screen)
        self.btn_backpack.draw(screen)

        if self.turn == "player":
            txt = f"What will {self.player_monster.name} do?"
        else:
            txt = f"What will {self.enemy_monster.name} do?"
        info_text = self.font.render(txt, True, (0, 0, 0))
        screen.blit(info_text, (50, self.screen_size[1]-100))

        if self.overlay_type == "backpack":
            self.backpack_overlay.draw(screen)
        elif self.overlay_type == "setting":
            overlay = pg.Surface(screen.get_size(), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            self.setting_overlay.draw(screen)