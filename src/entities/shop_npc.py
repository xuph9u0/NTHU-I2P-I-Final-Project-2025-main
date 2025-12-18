import pygame as pg
from src.utils import Position, GameSettings
from src.sprites import Sprite


class ShopNPC:
    """
    A simple stationary NPC for shop interaction.
    - Does NOT move
    - Does NOT battle
    - Only used for proximity interaction
    """

    def __init__(self, x: float, y: float, sprite_path: str):
        """
        x, y: tile-based position (NOT pixel)
        sprite_path: path under assets/
        """
        # Convert tile position to pixel position
        self.position = Position(
            x * GameSettings.TILE_SIZE,
            y * GameSettings.TILE_SIZE
        )

        self.size = GameSettings.TILE_SIZE

        # Visual
        self.sprite = Sprite(
            sprite_path,
            (self.size, self.size)
        )

        # Collision / interaction rect
        self.rect = pg.Rect(
            self.position.x,
            self.position.y,
            self.size,
            self.size
        )

    def update(self, dt: float):
        """
        Shop NPC is stationary; nothing to update for now.
        """
        pass

    def draw(self, screen: pg.Surface, camera):
        """
        Draw NPC with camera offset
        """
        pos = camera.transform_position_as_position(self.position)
        self.sprite.update_pos(pos)
        self.sprite.draw(screen)

    def is_player_near(self, player_rect: pg.Rect, distance: int = 50) -> bool:
        """
        Check if player is close enough to interact
        """
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        return dx * dx + dy * dy <= distance * distance
