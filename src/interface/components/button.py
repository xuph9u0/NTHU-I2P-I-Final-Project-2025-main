from __future__ import annotations
import pygame as pg

from src.sprites import Sprite
from src.core.services import input_manager
from src.utils import Logger
from typing import Callable, override
from .component import UIComponent

class Button(UIComponent):
    img_button: Sprite
    img_button_default: Sprite
    img_button_hover: Sprite
    hitbox: pg.Rect
    on_click: Callable[[], None] | None
    _was_clicked: bool  # 防止連續觸發點擊

    def __init__(
        self,
        img_path: str, img_hovered_path:str,
        x: int, y: int, width: int, height: int,
        on_click: Callable[[], None] | None = None
    ):
        self.img_button_default = Sprite(img_path, (width, height))
        self.img_button_hover = Sprite(img_hovered_path, (width, height))
        self.hitbox = pg.Rect(x, y, width, height)
        
        # 設置當前顯示的圖片（初始為默認圖片）
        self.img_button = self.img_button_default
        
        # 保存點擊回調函數
        self.on_click = on_click
        
        # 防止連續點擊的標誌
        self._was_clicked = False

    @override
    def update(self, dt: float) -> None:
        # 檢查鼠標是否在按鈕上
        mouse_pos = input_manager.mouse_pos
        mouse_pressed = input_manager.mouse_pressed(1)  # 左鍵點擊
        
        if self.hitbox.collidepoint(mouse_pos):
            # 切換到懸停圖片
            self.img_button = self.img_button_hover
            
            # 檢查是否被點擊（防止連續觸發）
            if mouse_pressed and not self._was_clicked:
                self._was_clicked = True
                if self.on_click is not None:
                    Logger.debug(f"Button clicked! Calling on_click function")
                    self.on_click()
        else:
            # 切換回默認圖片
            self.img_button = self.img_button_default
            
        # 重置點擊狀態
        if not mouse_pressed:
            self._was_clicked = False
    
    @override
    def draw(self, screen: pg.Surface) -> None:
        # 繪製當前圖片（可能是默認或懸停狀態）
        screen.blit(self.img_button.image, self.hitbox)


def main():
    import sys
    import os
    
    pg.init()

    WIDTH, HEIGHT = 800, 800
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption("Button Test")
    clock = pg.time.Clock()
    
    bg_color = (0, 0, 0)
    def on_button_click():
        nonlocal bg_color
        if bg_color == (0, 0, 0):
            bg_color = (255, 255, 255)
        else:
            bg_color = (0, 0, 0)
        Logger.debug(f"Button clicked! Background color changed to {bg_color}")
        
    button = Button(
        img_path="UI/button_play.png",
        img_hovered_path="UI/button_play_hover.png",
        x=WIDTH // 2 - 50,
        y=HEIGHT // 2 - 50,
        width=100,
        height=100,
        on_click=on_button_click
    )
    
    running = True
    dt = 0
    
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            input_manager.handle_events(event)
        
        dt = clock.tick(60) / 1000.0
        button.update(dt)
        
        input_manager.reset()
        
        screen.fill(bg_color)
        button.draw(screen)
        
        pg.display.flip()
    
    pg.quit()


if __name__ == "__main__":
    main()