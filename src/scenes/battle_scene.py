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
        self.life = 60  # 存在 60幀
        self.offset_y = 0
        self.alpha = 255

    def update(self):
        self.life -= 1
        self.offset_y -= 1.5
        if self.life < 20:
            self.alpha = int((self.life / 20) * 255)

    def draw(self, screen):
        if self.life > 0:
            surf = self.font.render(self.text, True, self.color)
            surf.set_alpha(self.alpha)
            outline = self.font.render(self.text, True, (0,0,0))
            outline.set_alpha(self.alpha)
            screen.blit(outline, (self.x + 2, self.y + self.offset_y + 2))
            screen.blit(surf, (self.x, self.y + self.offset_y))

# =========================
# [特效 4] 投射物 (子彈/火球) 類別
# =========================
class Projectile:
    def __init__(self, start_pos, end_pos, color, on_hit_callback):
        self.pos = pg.Vector2(start_pos)
        self.target = pg.Vector2(end_pos)
        self.color = color
        self.on_hit_callback = on_hit_callback
        self.speed = 25
        self.arrived = False

        direction = self.target - self.pos
        if direction.length() > 0:
            self.velocity = direction.normalize() * self.speed
        else:
            self.velocity = pg.Vector2(0, 0)

    def update(self):
        remaining_distance = self.pos.distance_to(self.target)
        if remaining_distance < self.speed:
            self.pos = self.target
            self.arrived = True
            if self.on_hit_callback:
                self.on_hit_callback()
        else:
            self.pos += self.velocity

    def draw(self, screen):
        pg.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), 15)
        pg.draw.circle(screen, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), 7)

# =========================
# 按鈕類別
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
        self.attack = data.get("attack", 20) 
        self.atk_mult = 1.0 
        self.def_mult = 1.0
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
        
        self.damage_texts = []        
        self.projectiles = [] 

        self.overlay_type = None 
        self.backpack_overlay = BackpackOverlay(self)
        self.setting_overlay = SettingOverlay(self)

        self.shake_offset = [0, 0]
        self.shake_timer = 0
        
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
        self.enemy_next_action_time = 0

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

    def enter(self):
        print("Entering BattleScene")
        if not hasattr(self, "game_manager") or self.game_manager is None:
            class DummyGM: pass
            self.game_manager = DummyGM()

        self.player_monster = None
        self.enemy_monster = None

        try:
            print("【系統】嘗試直接讀取 saves/game0.json ...")
            with open("saves/game0.json", "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            monster_list = raw_data["bag"]["monsters"]
            item_list = raw_data["bag"]["items"]

            if len(monster_list) > 5:
                p_data = monster_list[5]
                e_data = monster_list[1]
                self.player_monster = Monster(p_data)
                self.enemy_monster = Monster(e_data)
            else:
                print("【錯誤】JSON 裡的怪物不夠多！")

            # ★ [修正] QuickBag 補上遺失的屬性，防止 Overlay 報錯
            class QuickBag:
                def __init__(self, m_list, i_list):
                    self.monsters = m_list
                    self.items = i_list
                    # 這裡是為了滿足 BackpackOverlay 的檢查
                    self._monsters_data = m_list
                    self._items_data = i_list
                    self.pokemon = m_list
                    self.data = {"monsters": m_list, "items": i_list}

            self.game_manager.bag = QuickBag(monster_list, item_list)

        except Exception as e:
            print(f"【嚴重錯誤】讀檔失敗: {e}")

        if self.player_monster is None:
            dummy_data = {
                "name": "Backup", "hp": 100, "max_hp": 100, "level": 1, 
                "sprite_path": "menu_sprites/menusprite1.png", "element": "Water", "attack": 20
            }
            self.player_monster = Monster(dummy_data)
            dummy_data["name"] = "Enemy"
            self.enemy_monster = Monster(dummy_data)

        self.turn = "player"
        self.damage_texts = [] 
        self.projectiles = []
        
        for btn in self.buttons: btn.reset_press()
        self.btn_setting.reset_press()
        self.btn_backpack.reset_press()
        self.battle_over = False
        self.overlay_type = None
        
        self.has_evolved = False      
        self.evo_press_count = 0      
        self.last_press_time = 0      

        self.enemy_next_action_time = 0 

        print(f"★ 戰鬥開始 -> P: {self.player_monster.hp}, E: {self.enemy_monster.hp}")

    def exit(self):
        print("Exiting BattleScene")
        if hasattr(self, "has_evolved") and self.has_evolved:
            monster = self.player_monster
            monster.name = monster.name.replace("Mega ", "")
            monster.max_hp = int(monster.max_hp / 1.5)
            monster.attack = int(monster.attack / 2)
            if monster.hp > monster.max_hp: monster.hp = monster.max_hp
            self.has_evolved = False
            
    # ----------------------------
    # 事件處理
    # ----------------------------
    def handle_action(self, text):
        if len(self.projectiles) > 0:
            return

        if text == "Fight":
            player_center = (150 + 50, self.screen_size[1]//2 + 50)
            enemy_center = (self.screen_size[0]-250 + 50, self.screen_size[1]//2 - 50 + 50)

            def apply_damage(attacker, defender, is_player_atk):
                base_damage = attacker.attack
                if is_player_atk:
                    multiplier = self.get_element_multiplier(attacker.element, defender.element)
                    final_damage = int(base_damage * multiplier * attacker.atk_mult / defender.def_mult)
                    dmg_x, dmg_y = self.screen_size[0]-250, self.screen_size[1]//2 - 100
                    txt_color = (255, 50, 50)
                    print(f"[玩家] 造成傷害: {final_damage}")
                else:
                    multiplier = self.get_element_multiplier(defender.element, attacker.element)
                    final_damage = int(base_damage * multiplier * attacker.atk_mult / defender.def_mult)
                    dmg_x, dmg_y = 150, self.screen_size[1]//2
                    txt_color = (255, 100, 0)
                    print(f"[敵人] 造成傷害: {final_damage}")

                if final_damage < 1: final_damage = 1
                defender.hp -= final_damage
                
                self.shake_timer = 10
                defender.hit_flash_timer = 10
                self.damage_texts.append(DamageText(dmg_x, dmg_y, final_damage, txt_color))

                self.turn = "enemy" if self.turn == "player" else "player"
                self.enemy_next_action_time = 0

            if self.turn == "player":
                on_hit = lambda: apply_damage(self.player_monster, self.enemy_monster, True)
                proj = Projectile(start_pos=player_center, end_pos=enemy_center, 
                                  color=(0, 191, 255), on_hit_callback=on_hit)
                self.projectiles.append(proj)
                print("玩家發射水彈！")

            else:
                on_hit = lambda: apply_damage(self.enemy_monster, self.player_monster, False)
                proj = Projectile(start_pos=enemy_center, end_pos=player_center, 
                                  color=(255, 69, 0), on_hit_callback=on_hit)
                self.projectiles.append(proj)
                print("敵人發射火球！")

        elif text == "Item":
            if self.turn == "player":
                self.player_monster.hp = min(self.player_monster.hp + 10, self.player_monster.max_hp)
            else:
                self.enemy_monster.hp = min(self.enemy_monster.hp + 10, self.enemy_monster.max_hp)
            self.turn = "enemy" if self.turn == "player" else "player"
            self.enemy_next_action_time = 0

        elif text == "Switch":
            pass 

        elif text == "Run":
            scene_manager.change_scene("game")
            return

    def perform_evolution(self):
        if getattr(self, "has_evolved", False): return
        monster = self.player_monster
        target_sprite = "menu_sprites/sprite10.png" 
        try:
            loaded_image = pg.image.load(target_sprite).convert_alpha()
            new_image = pg.transform.scale(loaded_image, (350, 350))
            monster.sprite = new_image
        except:
            tint = pg.Surface(monster.sprite.get_size(), flags=pg.SRCALPHA)
            tint.fill((255, 215, 0, 100))
            monster.sprite.blit(tint, (0, 0), special_flags=pg.BLEND_RGBA_ADD)
            w, h = monster.sprite.get_size()
            monster.sprite = pg.transform.scale(monster.sprite, (int(w*1.5), int(h*1.5)))

        monster.max_hp = int(monster.max_hp * 1.5)
        monster.hp = monster.max_hp 
        monster.attack = int(monster.attack * 2)
        monster.name = f"Mega {monster.name}"
        self.has_evolved = True
        print(f"★ 進化成功! ATK: {monster.attack}")

    # -------------------------------------------------
    # 更新邏輯
    # -------------------------------------------------
    def update(self, dt):
        if getattr(self, "overlay_type", None) == "backpack":
            self.backpack_overlay.update(dt)
            return 
        elif getattr(self, "overlay_type", None) == "setting":
            self.setting_overlay.update(dt)
            if pg.key.get_pressed()[pg.K_ESCAPE]: self.close_overlay()
            return

        if self.player_monster.hp <= 0 or self.enemy_monster.hp <= 0:
            self.battle_over = True

        if not self.battle_over:
            is_player_turn = (self.turn == "player" and len(self.projectiles) == 0)
            for btn in self.buttons: 
                if btn.text in ["Run", "Switch"]: btn.update(enabled=True)
                else: btn.update(enabled=is_player_turn)
            self.btn_setting.update(enabled=True)
            self.btn_backpack.update(enabled=True)

            if self.turn == "enemy" and len(self.projectiles) == 0:
                current_time = pg.time.get_ticks()
                if self.enemy_next_action_time == 0:
                    self.enemy_next_action_time = current_time + 1000
                    print("【系統】敵人正在思考中...")

                if current_time >= self.enemy_next_action_time:
                    print("【系統】敵人發動攻擊！")
                    self.handle_action("Fight")
                    self.enemy_next_action_time = 0 
            else:
                self.enemy_next_action_time = 0

        keys = pg.key.get_pressed()
        if keys[pg.K_e]:
            current_time = pg.time.get_ticks()
            if not hasattr(self, "last_press_time"): self.last_press_time = 0
            if current_time - self.last_press_time > 500:
                if not getattr(self, "has_evolved", False):
                    self.evo_press_count += 1
                    self.last_press_time = current_time 
                    if self.evo_press_count >= 2: self.perform_evolution()

        for proj in self.projectiles:
            proj.update()
        self.projectiles = [p for p in self.projectiles if not p.arrived]

        if self.shake_timer > 0:
            self.shake_timer -= 1
            magnitude = 5
            self.shake_offset = [random.randint(-magnitude, magnitude), random.randint(-magnitude, magnitude)]
        else:
            self.shake_offset = [0, 0]

        for dt_txt in self.damage_texts: dt_txt.update()
        self.damage_texts = [t for t in self.damage_texts if t.life > 0] 

        if self.player_monster.hit_flash_timer > 0: self.player_monster.hit_flash_timer -= 1
        if self.enemy_monster.hit_flash_timer > 0: self.enemy_monster.hit_flash_timer -= 1

        if keys[pg.K_RETURN]:
            try:
                from src.core.managers.scene_manager import scene_manager
                scene_manager.change_scene("game")
            except: pass

    # -------------------------------------------------
    # 畫面
    # -------------------------------------------------
    def draw_health_bar(self, screen, x, y, w, h, hp, max_hp):
        ratio = hp / max_hp if max_hp > 0 else 0
        if ratio > 0.5: bar_color = (0, 255, 0)
        elif ratio > 0.2: bar_color = (255, 215, 0)
        else: bar_color = (220, 20, 60)
        pg.draw.rect(screen, (50, 50, 50), (x, y, w, h)) 
        pg.draw.rect(screen, bar_color, (x, y, int(w * ratio), h))
        pg.draw.rect(screen, (0, 0, 0), (x, y, w, h), 2)

    def draw_monster_info(self, screen, monster, x, y):
        name_text = self.font.render(monster.name, True, (0,0,0))
        screen.blit(name_text, (x, y))
        color_map = {"Water": (0, 0, 255), "Fire": (255, 0, 0), "Grass": (0, 150, 0)}
        elem_text = self.font.render(monster.element, True, color_map.get(monster.element, (0, 0, 0)))
        screen.blit(elem_text, (x + 100, y + 50))
        #atk_text = self.font.render(f"ATK: {monster.attack}", True, (100, 0, 0))
        #screen.blit(atk_text, (x + 100, y + 70))
        hp_text = self.font.render(f"{monster.hp}/{monster.max_hp} HP", True, (0,0,0))
        screen.blit(hp_text, (x, y + 45))

    def draw_monster_sprite(self, screen, monster, x, y):
        draw_x = x + self.shake_offset[0]
        draw_y = y + self.shake_offset[1]
        sprite_w, sprite_h = monster.sprite.get_size()
        offset_x = (100 - sprite_w) // 2
        offset_y = (100 - sprite_h) // 2
        screen.blit(monster.sprite, (draw_x + offset_x, draw_y + offset_y))
        if monster.hit_flash_timer > 0:
            mask = monster.sprite.copy()
            mask.fill((255, 255, 255, 150), special_flags=pg.BLEND_RGB_ADD) 
            screen.blit(mask, (draw_x + offset_x, draw_y + offset_y))

    def draw(self, screen):
        screen.blit(self.background, (self.shake_offset[0], self.shake_offset[1]))

        self.draw_monster_sprite(screen, self.player_monster, 150, self.screen_size[1]//2)
        self.draw_health_bar(screen, 50, self.screen_size[1]//2 + 110, 150, 20, self.player_monster.hp, self.player_monster.max_hp)
        self.draw_monster_info(screen, self.player_monster, 50, self.screen_size[1]//2 + 90)

        self.draw_monster_sprite(screen, self.enemy_monster, self.screen_size[0]-250, self.screen_size[1]//2 - 50)
        self.draw_health_bar(screen, self.screen_size[0]-300, self.screen_size[1]//2 - 80, 150, 20, self.enemy_monster.hp, self.enemy_monster.max_hp)
        self.draw_monster_info(screen, self.enemy_monster, self.screen_size[0]-300, self.screen_size[1]//2 - 100)

        for proj in self.projectiles: proj.draw(screen)
        for dt_txt in self.damage_texts: dt_txt.draw(screen)

        for btn in self.buttons: btn.draw(screen)
        self.btn_setting.draw(screen)
        self.btn_backpack.draw(screen)

        txt = f"What will {self.player_monster.name if self.turn == 'player' else self.enemy_monster.name} do?"
        screen.blit(self.font.render(txt, True, (0, 0, 0)), (50, self.screen_size[1]-100))

        if self.overlay_type == "backpack": self.backpack_overlay.draw(screen)
        elif self.overlay_type == "setting":
            overlay = pg.Surface(screen.get_size(), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            self.setting_overlay.draw(screen)