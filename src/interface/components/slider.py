# src/interface/components/slider.py
import pygame as pg
from typing import Callable

class Slider:
    def __init__(self, x: int, y: int, width: int, min_value: int, max_value: int, 
                 initial_value: int = 50, on_change: Callable[[int], None] | None = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.on_change = on_change

        self.handle_radius = 10
        self.dragging = False

        # 計算 handle 初始位置
        self.handle_x = self.x + (self.value - self.min_value) / (self.max_value - self.min_value) * self.width

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if (mx - self.handle_x) ** 2 + (my - (self.y + self.height//2)) ** 2 <= self.handle_radius ** 2:
                self.dragging = True
        elif event.type == pg.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pg.MOUSEMOTION and self.dragging:
            mx = event.pos[0]
            self.handle_x = max(self.x, min(self.x + self.width, mx))
            self.value = round(self.min_value + (self.handle_x - self.x) / self.width * (self.max_value - self.min_value))
            if self.on_change:
                self.on_change(self.value)

    def draw(self, screen: pg.Surface):
        # Draw line
        pg.draw.line(screen, (200, 200, 200), (self.x, self.y + self.height//2), (self.x + self.width, self.y + self.height//2), 4)
        # Draw handle
        pg.draw.circle(screen, (100, 100, 250), (int(self.handle_x), self.y + self.height//2), self.handle_radius)
