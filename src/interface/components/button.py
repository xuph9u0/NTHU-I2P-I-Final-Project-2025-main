# src/interface/components/button.py (或其他存放 Button 的路徑)
from __future__ import annotations
import pygame as pg

from src.sprites import Sprite
from src.core.services import input_manager
from src.utils import Logger
from typing import Callable, override
# 假設 Component 在這裡，如果不是請自行調整 import
from .component import UIComponent 

class Button(UIComponent):
    img_button: Sprite
    img_button_default: Sprite
    img_button_hover: Sprite
    hitbox: pg.Rect
    on_click: Callable[[], None] | None
    _was_clicked: bool
    
    # [新增] 追蹤懸停狀態和偏移量設定
    is_hovered: bool
    hover_offset_x: int
    hover_offset_y: int

    def __init__(
        self,
        img_path: str, img_hovered_path: str,
        x: int, y: int, width: int, height: int,
        on_click: Callable[[], None] | None = None,
        # [新增] 可選參數：設定懸停時的偏移量，預設向下移動 3px
        hover_offset_x: int = 0,
        hover_offset_y: int = 3 
    ):
        self.img_button_default = Sprite(img_path, (width, height))
        # 如果沒有特別準備 hover 圖片，可以使用同一張，單純靠位移來製造效果
        self.img_button_hover = Sprite(img_hovered_path if img_hovered_path else img_path, (width, height))
        self.hitbox = pg.Rect(x, y, width, height)
        
        self.img_button = self.img_button_default
        self.on_click = on_click
        self._was_clicked = False

        # [新增] 初始化狀態
        self.is_hovered = False
        self.hover_offset_x = hover_offset_x
        self.hover_offset_y = hover_offset_y

    @override
    def update(self, dt: float) -> None:
        mouse_pos = input_manager.mouse_pos
        mouse_pressed = input_manager.mouse_pressed(1)
        
        if self.hitbox.collidepoint(mouse_pos):
            # [新增] 標記為懸停狀態
            self.is_hovered = True
            # 切換到懸停圖片
            self.img_button = self.img_button_hover
            
            # 檢查是否被點擊
            if mouse_pressed and not self._was_clicked:
                self._was_clicked = True
                if self.on_click is not None:
                    Logger.debug(f"Button clicked!")
                    self.on_click()
        else:
            # [新增] 標記為非懸停狀態
            self.is_hovered = False
            # 切換回默認圖片
            self.img_button = self.img_button_default
            
        # 重置點擊狀態
        if not mouse_pressed:
            self._was_clicked = False
    
    @override
    def draw(self, screen: pg.Surface) -> None:
        # [修改] 計算實際繪製位置
        draw_x = self.hitbox.x
        draw_y = self.hitbox.y

        # 如果懸停，加上偏移量
        if self.is_hovered:
            draw_x += self.hover_offset_x
            draw_y += self.hover_offset_y

        # [修改] 在計算後的位置繪製圖片，而不是直接畫在 hitbox 上
        screen.blit(self.img_button.image, (draw_x, draw_y))

# ==========================================
# 以下是測試用的 main (不需要包含在正式專案檔案中)
# ==========================================
def main():
    # ... (省略前面的 pygame init 設定) ...
    WIDTH, HEIGHT = 800, 800
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    input_manager.init() # 假設你的 input_manager 需要 init

    # 測試用假 Sprite 類別 (因為我沒有你的檔案)
    class MockSprite:
        def __init__(self, color, size):
            self.image = pg.Surface(size)
            self.image.fill(color)

    # 替換 Button 裡的 Sprite (為了測試運行)
    global Sprite
    Sprite = lambda path, size: MockSprite((100, 100, 200) if "hover" not in path else (150, 150, 250), size)

    def on_button_click():
        print("Clicked!")
        
    # 建立按鈕，這裡使用了預設的下壓效果 (y=3)
    button = Button(
        img_path="UI/button_play.png",
        img_hovered_path="UI/button_play_hover.png",
        x=WIDTH // 2 - 50,
        y=HEIGHT // 2 - 50,
        width=100,
        height=100,
        on_click=on_button_click,
        # 你可以嘗試修改這裡看看不同效果，例如向右下壓:
        # hover_offset_x=4, hover_offset_y=4
    )
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pg.event.get():
            if event.type == pg.QUIT: running = False
            input_manager.handle_events(event) # 假設你有這個

        button.update(dt)
        input_manager.reset() # 假設你有這個
        
        screen.fill((50, 50, 50))
        button.draw(screen)
        pg.display.flip()
    pg.quit()

if __name__ == "__main__":
    # 如果要測試，需要確保 input_manager 和 Sprite 能正常運作
    # main()
    pass