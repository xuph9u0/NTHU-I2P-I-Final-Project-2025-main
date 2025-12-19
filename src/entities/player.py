from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager
from src.utils import Position, PositionCamera, GameSettings, Logger
from src.core import GameManager
import math
from typing import override

class Player(Entity):
    # 類別變數預設值
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)

        # [新增] 自動導航變數
        self.path = [] 
        self.target_tile = None
        self.is_auto_moving = False
        self.speed = 200 # 確保實例變數有定義速度

    # [新增] 設定路徑的方法
    def set_path(self, path):
        self.path = path
        # 移除第一個點(起點)，因為那是玩家現在站的位置
        if len(self.path) > 0:
            self.path.pop(0)
        self.is_auto_moving = True

    def get_rect(self) -> pg.Rect:
        """獲取玩家的碰撞矩形"""
        return pg.Rect(
            self.position.x, 
            self.position.y, 
            GameSettings.TILE_SIZE, 
            GameSettings.TILE_SIZE
        )

    @override
    def update(self, dt: float) -> None:
        # [核心修改] 這裡進行分流：自動導航 vs 手動輸入
        if self.is_auto_moving:
            self.move_along_path(dt)
        else:
            # 如果沒有在導航，就執行原本的鍵盤控制邏輯
            self.handle_input(dt) 

        # 執行父類別更新 (處理動畫、渲染狀態等)
        super().update(dt)

    # [重構] 將原本 update 裡的邏輯提取到這裡
    def handle_input(self, dt: float) -> None:
        dis = Position(0, 0)
        
        # [TODO HACKATHON 2] - 保持不變 (輸入處理)
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= 1
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += 1
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= 1
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += 1
        
        # Normalize diagonal movement
        if dis.x != 0 and dis.y != 0:
            length = math.sqrt(dis.x * dis.x + dis.y * dis.y)
            dis.x = dis.x / length
            dis.y = dis.y / length
        
        # Apply speed and delta time
        dis.x *= self.speed * dt
        dis.y *= self.speed * dt
        
        # [TODO HACKATHON 4] - 碰撞檢測邏輯 (保持不變)
        
        # 保存原始位置
        original_x = self.position.x
        original_y = self.position.y
        
        # 1. 先更新 X 軸
        self.position.x += dis.x
        player_rect = self.get_rect()
        
        # 檢查與碰撞層的碰撞
        if self.game_manager.current_map.check_collision(player_rect):
            self.position.x = original_x
            self._snap_to_grid(axis='x')
        
        # 檢查與敵人的碰撞
        for enemy in self.game_manager.current_enemy_trainers:
            enemy_rect = enemy.get_rect() if hasattr(enemy, 'get_rect') else pg.Rect(
                enemy.position.x, enemy.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE
            )
            if player_rect.colliderect(enemy_rect):
                self.position.x = original_x
                self._snap_to_grid(axis='x')
                break
        
        # 2. 再更新 Y 軸
        self.position.y += dis.y
        player_rect = self.get_rect()
        
        # 檢查與碰撞層的碰撞
        if self.game_manager.current_map.check_collision(player_rect):
            self.position.y = original_y
            self._snap_to_grid(axis='y')
        
        # 檢查與敵人的碰撞
        for enemy in self.game_manager.current_enemy_trainers:
            enemy_rect = enemy.get_rect() if hasattr(enemy, 'get_rect') else pg.Rect(
                enemy.position.x, enemy.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE
            )
            if player_rect.colliderect(enemy_rect):
                self.position.y = original_y
                self._snap_to_grid(axis='y')
                break
        
        # Check teleportation - 保持不變
        tp = self.game_manager.current_map.check_teleport(self.position)
        if tp:
            dest = tp.destination
            self.game_manager.switch_map(dest)

    # [TODO HACKATHON 4] - 新增的輔助方法
    def _snap_to_grid(self, axis: str = 'both'):
        """將實體位置對齊到網格"""
        if axis in ['x', 'both']:
            self.position.x = round(self.position.x / GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE
        if axis in ['y', 'both']:
            self.position.y = round(self.position.y / GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)

    # [新增] 沿著路徑移動的邏輯
    def move_along_path(self, dt):
        if not self.path and not self.target_tile:
            self.is_auto_moving = False
            return

        # 如果目前沒有目標格子，就從路徑拿一個
        if not self.target_tile:
            if len(self.path) > 0:
                self.target_tile = self.path.pop(0)
            else:
                self.is_auto_moving = False
                return

        # 計算目標像素座標
        TS = GameSettings.TILE_SIZE
        target_x = self.target_tile[0] * TS
        target_y = self.target_tile[1] * TS

        # 計算移動向量
        dx = target_x - self.position.x
        dy = target_y - self.position.y

        distance = (dx**2 + dy**2) ** 0.5

        # 如果非常接近目標，就直接對齊並準備走下一格
        if distance < 5: 
            self.position.x = target_x
            self.position.y = target_y
            self.target_tile = None # 完成這一格
        else:
            # 正規化向量並移動
            move_x = (dx / distance) * self.speed * dt
            move_y = (dy / distance) * self.speed * dt
            self.position.x += move_x
            self.position.y += move_y

            # 設定角色朝向 (因為沒有 input_manager，必須手動設定給動畫系統用)
            if abs(dx) > abs(dy):
                self.direction = "right" if dx > 0 else "left"
            else:
                self.direction = "down" if dy > 0 else "up"