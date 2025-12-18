from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager
from src.utils import Position, PositionCamera, GameSettings, Logger
from src.core import GameManager
import math
from typing import override

class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)

    def get_rect(self) -> pg.Rect:
        """獲取玩家的碰撞矩形"""
        # 假設玩家大小是一個圖塊的大小
        return pg.Rect(
            self.position.x, 
            self.position.y, 
            GameSettings.TILE_SIZE, 
            GameSettings.TILE_SIZE
        )

    @override
    def update(self, dt: float) -> None:
        dis = Position(0, 0)
        
        # [TODO HACKATHON 2] - 保持不變
        # Calculate the distance change, and then normalize the distance
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= 1
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += 1
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= 1
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += 1
        
        # Normalize diagonal movement so it's not faster than straight movement
        if dis.x != 0 and dis.y != 0:
            # If moving diagonally, normalize the vector to maintain consistent speed
            length = math.sqrt(dis.x * dis.x + dis.y * dis.y)
            dis.x = dis.x / length
            dis.y = dis.y / length
        
        # Apply speed and delta time
        dis.x *= self.speed * dt
        dis.y *= self.speed * dt
        
        # [TODO HACKATHON 4] - 新增碰撞檢測
        # Check if there is collision, if so try to make the movement smooth
        # Hint #1 : use entity.py _snap_to_grid function or create a similar function
        # Hint #2 : Beware of glitchy teleportation, you must do
        #             1. Update X
        #             2. If collide, snap to grid
        #             3. Update Y
        #             4. If collide, snap to grid
        #           instead of update both x, y, then snap to grid
        
        # 保存原始位置
        original_x = self.position.x
        original_y = self.position.y
        
        # 1. 先更新 X 軸
        self.position.x += dis.x
        player_rect = self.get_rect()
        
        # 檢查與碰撞層的碰撞
        if self.game_manager.current_map.check_collision(player_rect):
            # 如果碰撞，恢復 X 軸位置並對齊到網格
            self.position.x = original_x
            self._snap_to_grid(axis='x')
        
        # 檢查與敵人的碰撞
        for enemy in self.game_manager.current_enemy_trainers:
            enemy_rect = enemy.get_rect() if hasattr(enemy, 'get_rect') else pg.Rect(
                enemy.position.x, enemy.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE
            )
            if player_rect.colliderect(enemy_rect):
                # 如果與敵人碰撞，恢復 X 軸位置
                self.position.x = original_x
                self._snap_to_grid(axis='x')
                break
        
        # 2. 再更新 Y 軸
        self.position.y += dis.y
        player_rect = self.get_rect()
        
        # 檢查與碰撞層的碰撞
        if self.game_manager.current_map.check_collision(player_rect):
            # 如果碰撞，恢復 Y 軸位置並對齊到網格
            self.position.y = original_y
            self._snap_to_grid(axis='y')
        
        # 檢查與敵人的碰撞
        for enemy in self.game_manager.current_enemy_trainers:
            enemy_rect = enemy.get_rect() if hasattr(enemy, 'get_rect') else pg.Rect(
                enemy.position.x, enemy.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE
            )
            if player_rect.colliderect(enemy_rect):
                # 如果與敵人碰撞，恢復 Y 軸位置
                self.position.y = original_y
                self._snap_to_grid(axis='y')
                break
        
        # Check teleportation - 保持不變
        tp = self.game_manager.current_map.check_teleport(self.position)
        if tp:
            dest = tp.destination
            self.game_manager.switch_map(dest)
                
        super().update(dt)

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