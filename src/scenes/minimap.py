import pygame as pg
from src.utils import GameSettings, PositionCamera

class Minimap:
    def __init__(self, game_scene):
        self.game_scene = game_scene
        self.game_manager = game_scene.game_manager

        # --- 設定小地圖外觀 ---
        self.width = 200   # 固定寬度 200 px
        self.height = 100  # 初始高度 (之後會根據地圖自動調整)
        self.x = 20        # 距離左邊界
        self.y = 20        # 距離上邊界
        self.border_color = (200, 200, 200)

        # --- 縮圖相關變數 ---
        self.cached_map_surface = None
        self.last_map_name = None
        self.scale = 1.0

    def _generate_scaled_map_image(self, current_map):
        """ 生成縮圖，並自動調整小地圖的高度以完美貼合 """
        print("Generating fitted minimap image...")

        # 1. 取得地圖真實的總像素寬高
        if hasattr(current_map, "tmx_data"):
            real_map_w = current_map.tmx_data.width * current_map.tmx_data.tilewidth
            real_map_h = current_map.tmx_data.height * current_map.tmx_data.tileheight
        else:
            real_map_w = getattr(current_map, "width", 67) * GameSettings.TILE_SIZE
            real_map_h = getattr(current_map, "height", 38) * GameSettings.TILE_SIZE

        # 2. 繪製完整的大地圖到暫存畫布
        large_surface = pg.Surface((real_map_w, real_map_h)).convert()
        dummy_camera = PositionCamera(0, 0)
        current_map.draw(large_surface, dummy_camera)

        # ==========================================
        # [核心修改] 動態調整高度
        # ==========================================
        # 3. 固定寬度為 self.width (200)，計算縮放比例
        self.scale = self.width / real_map_w
        
        # 4. 根據比例算出「完美高度」
        new_h = int(real_map_h * self.scale)
        
        # [關鍵步驟] 更新小地圖的高度設定，讓框框變小
        self.height = new_h 

        # 5. 進行縮放
        scaled_surface = pg.transform.smoothscale(large_surface, (self.width, self.height))
        scaled_surface.set_alpha(220) # 設定半透明

        return scaled_surface

    def draw(self, screen: pg.Surface):
        current_map = self.game_manager.current_map
        if not current_map:
            return

        # 檢查是否需要重新生成縮圖
        current_map_name = getattr(current_map, "path_name", "unknown")
        if self.cached_map_surface is None or current_map_name != self.last_map_name:
            # 重新生成並更新高度
            self.cached_map_surface = self._generate_scaled_map_image(current_map)
            self.last_map_name = current_map_name

        # ==========================================
        # 開始繪製
        # ==========================================

        # 1. 繪製地圖縮圖 (現在不需要偏移量了，因為框框大小剛好等於圖片大小)
        if self.cached_map_surface:
            screen.blit(self.cached_map_surface, (self.x, self.y))

        # 2. 繪製邊框 (使用更新後的 self.height)
        pg.draw.rect(screen, self.border_color, (self.x, self.y, self.width, self.height), 2)

        # --- 座標轉換小幫手函式 ---
        def get_mini_pos(world_x, world_y):
            # 公式簡化：世界座標 * 縮放比 + 小地圖起始點
            mx = world_x * self.scale + self.x
            my = world_y * self.scale + self.y
            return int(mx), int(my)

        # 3. 繪製玩家 (綠點帶黑邊)
        player = self.game_manager.player
        if player:
            mini_pos = get_mini_pos(player.position.x, player.position.y)
            pg.draw.circle(screen, (0, 0, 0), mini_pos, 5) # 黑邊
            pg.draw.circle(screen, (0, 255, 0), mini_pos, 4) # 綠底

        # 4. 繪製敵人 (紅點)
        for enemy in self.game_manager.current_enemy_trainers:
            mini_pos = get_mini_pos(enemy.position.x, enemy.position.y)
            pg.draw.circle(screen, (255, 0, 0), mini_pos, 3)

        # 5. 繪製商店 NPC (藍點)
        # 確保 game_scene 裡有 shop_npcs 這個列表
        if hasattr(self.game_scene, "shop_npcs"):
            for npc in self.game_scene.shop_npcs:
                # 取得 NPC 的世界座標 (相容 rect 或 position 屬性)
                if hasattr(npc, "rect"):
                    world_x, world_y = npc.rect.centerx, npc.rect.centery
                elif hasattr(npc, "position"):
                    world_x, world_y = npc.position.x, npc.position.y
                else:
                    continue 

                mini_pos = get_mini_pos(world_x, world_y)
                pg.draw.circle(screen, (0, 0, 255), mini_pos, 3)