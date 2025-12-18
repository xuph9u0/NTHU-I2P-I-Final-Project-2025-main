import pygame as pg 
import json
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

        self.font = pg.font.SysFont(None, 24)

        # 回合：player 或 enemy
        self.turn = "player"

    # ----------------------------
    # 重新初始化戰鬥資料
    # ----------------------------
    def enter(self):
        print("Entering BattleScene")

        # 每次進入戰鬥都重新讀取怪物資料
        with open("saves/game0.json") as f:
            game_data = json.load(f)

        self.player_monster = Monster(game_data["bag"]["monsters"][5])
        self.enemy_monster = Monster(game_data["bag"]["monsters"][1])

        # 重置回合
        self.turn = "player"

        # 重置按鈕狀態
        
        for btn in self.buttons:
            btn.reset_press()
            
        self.battle_over = False

    def exit(self):
        print("Exiting BattleScene")

    # ----------------------------
    # 事件處理（玩家與敵人共用）
    # ----------------------------
    def handle_action(self, text):

        if text == "Fight":
            if self.turn == "player":
                self.enemy_monster.hp -= 10
                
            else:
                self.player_monster.hp -= 10
            

                 

        elif text == "Item":
            if self.turn == "player":
                self.player_monster.hp = min(self.player_monster.hp + 10,
                                             self.player_monster.max_hp)
            else:
                self.enemy_monster.hp = min(self.enemy_monster.hp + 10,
                                            self.enemy_monster.max_hp)

        elif text == "Switch":
            pass  # 你可在這裡加換怪邏輯

        elif text == "Run":
            # 切換回遊戲場景，下次進入 BattleScene 會重新初始化
            scene_manager.change_scene("game")
            return

        # 回合切換
        self.turn = "enemy" if self.turn == "player" else "player"

        

    # -------------------------------------------------
    # 更新
    # -------------------------------------------------
    def update(self, dt):
        if not self.battle_over:
            for btn in self.buttons:
                btn.update(enabled=True)

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

        # 提示文字（完全保留）
        if self.turn == "player":
            txt = f"What will {self.player_monster.name} do?"
        else:
            txt = f"What will {self.enemy_monster.name} do?"

        info_text = self.font.render(txt, True, (0, 0, 0))
        screen.blit(info_text, (50, self.screen_size[1]-100))
