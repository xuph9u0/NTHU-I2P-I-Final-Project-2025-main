import pygame as pg
import pytmx

from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport

class Map:
    # Map Properties
    path_name: str
    tmxdata: pytmx.TiledMap
    # Position Argument
    spawn: Position
    teleporters: list[Teleport]
    # Rendering Properties
    _surface: pg.Surface
    _collision_map: list[pg.Rect]

    def __init__(self, path: str, tp: list[Teleport], spawn: Position):
        self.path_name = path
        self.tmxdata = load_tmx(path)
        self.spawn = spawn
        self.teleporters = tp

        pixel_w = self.tmxdata.width * GameSettings.TILE_SIZE
        pixel_h = self.tmxdata.height * GameSettings.TILE_SIZE

        # Prebake the map
        self._surface = pg.Surface((pixel_w, pixel_h), pg.SRCALPHA)
        self._render_all_layers(self._surface)
        # Prebake the collision map
        self._collision_map = self._create_collision_map()

    def update(self, dt: float):
        return

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        screen.blit(self._surface, camera.transform_position(Position(0, 0)))
        
        # Draw the hitboxes collision map
        if GameSettings.DRAW_HITBOXES:
            for rect in self._collision_map:
                pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(rect), 1)
        
    def check_collision(self, rect: pg.Rect) -> bool:
        '''
        [TODO HACKATHON 4]
        Return True if collide if rect param collide with self._collision_map
        '''
        for collision_rect in self._collision_map:
            if rect.colliderect(collision_rect):
                return True
        return False
        
    def check_teleport(self, pos: Position) -> Teleport | None:
        """
        [TODO HACKATHON 6]
        Teleportation: Player can enter a building by walking into certain tiles defined in saves/*.json.
        This function only detects and returns the Teleport object if player steps on a teleport tile.
        The actual map switching should be performed by GameManager / Player (to avoid circular imports).

        Args:
            pos: The player's position (x, y) in pixel coordinates.
        """
        
        for teleport in self.teleporters:
            if teleport.pos.x//GameSettings.TILE_SIZE!=pos.x//GameSettings.TILE_SIZE:
                continue 
            if teleport.pos.y//GameSettings.TILE_SIZE!=pos.y//GameSettings.TILE_SIZE:
                continue 
            return teleport

    def _render_all_layers(self, target: pg.Surface) -> None:
        for layer in self.tmxdata.visible_layers:
            # pytmx exposes TiledTileLayer as pytmx.TiledTileLayer
            if isinstance(layer, pytmx.TiledTileLayer):
                self._render_tile_layer(target, layer)
            # image layers handled by pytmx if needed (left commented out like original)
            # elif isinstance(layer, pytmx.TiledImageLayer) and layer.image:
            #        target.blit(layer.image, (layer.x or 0, layer.y or 0))
    
    def _render_tile_layer(self, target: pg.Surface, layer: pytmx.TiledTileLayer) -> None:
        for x, y, gid in layer:
            if gid == 0:
                continue
            image = self.tmxdata.get_tile_image_by_gid(gid)
            if image is None:
                continue

            image = pg.transform.scale(image, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
            target.blit(image, (x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE))
    
    def _create_collision_map(self) -> list[pg.Rect]:
        rects = []
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and ("collision" in layer.name.lower() or "house" in layer.name.lower()):
                for x, y, gid in layer:
                    if gid != 0:
                        rect = pg.Rect(
                            x * GameSettings.TILE_SIZE,
                            y * GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE
                        )
                        rects.append(rect)
        return rects

    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        tp = [Teleport.from_dict(t) for t in data.get("teleport", [])]
        pos = Position(data["player"]["x"] * GameSettings.TILE_SIZE, data["player"]["y"] * GameSettings.TILE_SIZE)
        return cls(data["path"], tp, pos)

    def to_dict(self):
        return {
            "path": self.path_name,
            "teleport": [t.to_dict() for t in self.teleporters],
            "player": {
                "x": self.spawn.x // GameSettings.TILE_SIZE,
                "y": self.spawn.y // GameSettings.TILE_SIZE,
            }
        }