import pygame as pg
import json
import random
from src.core.services import scene_manager, input_manager
from src.utils import load_img
from src.scenes.scene import Scene

class Button:
    """按鈕，滑鼠經過時會下壓"""
    def __init__(self, rect, text, callback):
        self.rect = pg.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = pg.font.SysFont(None, 28)
        self.offset_y = 0  # 下壓偏移

    def update(self):
        mouse_pos = pg.mouse.get_pos()
        # 滑鼠經過按鈕就下壓
        if self.rect.collidepoint(mouse_pos):
            self.offset_y = 5
        else:
            self.offset_y = 0

        # 點擊事件
        if self.rect.collidepoint(mouse_pos) and pg.mouse.get_pressed()[0]:
            self.callback()

    def draw(self, screen):
        draw_rect = self.rect.copy()
        draw_rect.y += self.offset_y
        pg.draw.rect(screen, (255, 255, 255), draw_rect)
        pg.draw.rect(screen, (0, 0, 0), draw_rect, 2)
        text_surf = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)


class Monster:
    def __init__(self, data):
        self.name = data["name"]
        self.hp = data["hp"]
        self.max_hp = data["max_hp"]
        self.level = data["level"]
        # [新增 2] 隨機屬性邏輯
        # 如果 json 資料裡原本就有 element 就用原本的，沒有的話就隨機選一個
        if "element" in data:
            self.element = data["element"]
        else:
            self.element = random.choice(["Water", "Fire", "Grass"])
        self.sprite = load_img(data["sprite_path"])
        self.sprite = pg.transform.scale(self.sprite, (100, 100))


class CatchPokemonScene(Scene):
    """抓寶可夢戰鬥場景"""
    def __init__(self):
        super().__init__()
        self.screen_size = pg.display.get_surface().get_size()
        self.background = load_img("backgrounds/background3.png")
        self.background = pg.transform.scale(self.background, self.screen_size)

        # 新增：要加入背包的怪物
        self.caught_monster = None

        # 讀取 saves/game0.json
        with open("saves/game0.json") as f:
            self.game_data = json.load(f)

        # 玩家第 6 隻 / 敵人第 2 隻（依你原本寫法完全保留）
        self.player_monster = Monster(self.game_data["bag"]["monsters"][5])
        self.enemy_monster = Monster(self.game_data["bag"]["monsters"][1])

        # 按鈕
        btn_w, btn_h = 120, 50
        margin = 20
        total_width = 4 * btn_w + 3 * margin
        start_x = (self.screen_size[0] - total_width) // 2
        y_pos = self.screen_size[1] - btn_h - 30

        self.buttons = [
            Button((start_x + i*(btn_w+margin), y_pos, btn_w, btn_h), text, getattr(self, f"{text.lower()}_action"))
            for i, text in enumerate(["Fight", "Item", "Switch", "Run"])
        ]

        self.font = pg.font.SysFont(None, 24)

    # -----------------------
    # 生命週期
    # -----------------------

    # [新增 3] 屬性相剋判斷函式
    def get_element_multiplier(self, attacker_elem, defender_elem):
        # 預設倍率 1.0
        multiplier = 1.0
        
        # 水剋火
        if attacker_elem == "Water" and defender_elem == "Fire":
            multiplier = 1.5
        # 火剋草
        elif attacker_elem == "Fire" and defender_elem == "Grass":
            multiplier = 1.5
        # 草剋水
        elif attacker_elem == "Grass" and defender_elem == "Water":
            multiplier = 1.5
            
        return multiplier

    def enter(self):
        print("Entering CatchPokemonScene")

    def exit(self):
        print("Exiting CatchPokemonScene")

    # -----------------------
    # 按鈕行為
    # -----------------------
    # -----------------------
    # 按鈕行為
    # -----------------------
    def fight_action(self):
        # 1. 計算屬性倍率
        multiplier = self.get_element_multiplier(self.player_monster.element, self.enemy_monster.element)
        
        # 2. 計算傷害 (基礎傷害 10 * 倍率)
        base_damage = 5 
        final_damage = int(base_damage * multiplier)
        
        self.enemy_monster.hp -= final_damage
        
        # 印出戰鬥訊息 (方便除錯)
        print(f"我方 {self.player_monster.element} 攻擊 敵方 {self.enemy_monster.element}")
        if multiplier > 1.0:
            print(f"效果絕佳！造成 {final_damage} 點傷害 (2倍)")
        else:
            print(f"造成 {final_damage} 點傷害")

        if self.enemy_monster.hp < 0:
            self.enemy_monster.hp = 0

        # 3. 敵人死亡 → 記錄要加入背包的怪物 (記得把屬性也存進去)
        if self.enemy_monster.hp == 0 and self.caught_monster is None:
            self.caught_monster = {
                "name": self.enemy_monster.name,
                "hp": self.enemy_monster.max_hp,
                "max_hp": self.enemy_monster.max_hp,
                "level": self.enemy_monster.level,
                "element": self.enemy_monster.element, # [重要] 儲存屬性
                "sprite_path": self.game_data["bag"]["monsters"][1]["sprite_path"]
            }

    def item_action(self):
        pass

    def switch_action(self):
        pass

    def run_action(self):
        scene_manager.change_scene("game")

    # -----------------------
    # 更新
    # -----------------------
    def update(self, dt):
        for btn in self.buttons:
            btn.update()

        keys = pg.key.get_pressed()

        # ENTER → 結束戰鬥
        if keys[pg.K_RETURN]:

            # 如果敵人死亡 → 把怪物加入背包 + 寫回 JSON
            if self.enemy_monster.hp <= 0 and self.caught_monster is not None:

                # 加入背包資料（你原本 game0 結構保留）
                self.game_data["bag"]["monsters"].append(self.caught_monster)

                # 寫回 game0.json
                with open("saves/game0.json", "w") as f:
                    json.dump(self.game_data, f, indent=4)

                print("怪物已成功加入背包並寫入存檔！")

            # 回到 game scene
            scene_manager.change_scene("game")

    # -----------------------
    # 繪製血量條
    # -----------------------
    def draw_health_bar(self, screen, x, y, w, h, hp, max_hp):
        # 灰色背景
        pg.draw.rect(screen, (150, 150, 150), (x, y, w, h))
        # 綠色血量
        green_width = int(w * hp / max_hp)
        pg.draw.rect(screen, (0, 255, 0), (x, y, green_width, h))
        # 黑色邊框
        pg.draw.rect(screen, (0, 0, 0), (x, y, w, h), 2)

    # -----------------------
    # 繪製怪物資訊文字
    # -----------------------
    def draw_monster_info(self, screen, monster, x, y):
        # 名字
        name_text = self.font.render(monster.name, True, (0,0,0))
        screen.blit(name_text, (x, y))

        # [新增 4] 繪製屬性文字 (用不同顏色區分)
        color_map = {"Water": (0, 0, 255), "Fire": (255, 0, 0), "Grass": (0, 150, 0)}
        elem_color = color_map.get(monster.element, (0, 0, 0))
        
        elem_text = self.font.render(monster.element, True, elem_color)
        screen.blit(elem_text, (x + 80, y)) # 畫在名字右邊

        # 等級和 HP
        lvl_text = self.font.render(f"Lv {monster.level}", True, (0,0,0))
        hp_text = self.font.render(f"{monster.hp}/{monster.max_hp} HP", True, (0,0,0))
        screen.blit(lvl_text, (x - 45, y + 25))
        screen.blit(hp_text, (x, y + 45))

    # -----------------------
    # 繪製場景
    # -----------------------
    def draw(self, screen):
        screen.blit(self.background, (0,0))

        # 玩家怪物
        player_pos = (150, self.screen_size[1]//2)
        screen.blit(self.player_monster.sprite, player_pos)
        self.draw_health_bar(screen, 50, self.screen_size[1]//2 + 110, 150, 20,
                             self.player_monster.hp, self.player_monster.max_hp)
        self.draw_monster_info(screen, self.player_monster, 50, self.screen_size[1]//2 + 90)

        # 敵人怪物
        enemy_pos = (self.screen_size[0]-250, self.screen_size[1]//2 - 50)
        screen.blit(self.enemy_monster.sprite, enemy_pos)
        self.draw_health_bar(screen, self.screen_size[0]-300, self.screen_size[1]//2 - 80, 150, 20,
                             self.enemy_monster.hp, self.enemy_monster.max_hp)
        self.draw_monster_info(screen, self.enemy_monster, self.screen_size[0]-300, self.screen_size[1]//2 - 100)

        # 按鈕
        for btn in self.buttons:
            btn.draw(screen)

        # 提示文字
        info_text = self.font.render(f"What will {self.player_monster.name} do?", True, (0, 0, 0))
        screen.blit(info_text, (50, self.screen_size[1]-100))
