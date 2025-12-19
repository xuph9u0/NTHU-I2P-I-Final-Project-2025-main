import heapq
import pygame as pg
from src.utils import GameSettings, Logger

class Node:
    def __init__(self, x, y, parent=None):
        self.x = x
        self.y = y
        self.parent = parent
        self.g = 0
        self.h = 0
        self.f = 0

    def __lt__(self, other):
        return self.f < other.f

def find_path(start_pos, end_pos, game_map):
    """
    A* 尋路演算法
    """
    # 0. 預先檢查：如果目標點本身就是牆壁，直接放棄，不用浪費時間運算
    if not is_walkable(game_map, end_pos[0], end_pos[1]):
        Logger.warning(f"Target {end_pos} is a wall or obstacle! Pathfinding aborted.")
        return None
    
    # 如果起點跟終點一樣
    if start_pos == end_pos:
        return []

    start_node = Node(start_pos[0], start_pos[1])
    end_node = Node(end_pos[0], end_pos[1])

    open_list = []
    closed_list = set()

    heapq.heappush(open_list, start_node)

    max_iterations = 3000 #稍微調高一點上限
    iterations = 0

    while open_list:
        iterations += 1
        if iterations > max_iterations:
            Logger.warning(f"Pathfinding timeout. Searched {len(closed_list)} tiles.")
            return None

        current_node = heapq.heappop(open_list)
        closed_list.add((current_node.x, current_node.y))

        # 找到終點
        if current_node.x == end_node.x and current_node.y == end_node.y:
            path = []
            curr = current_node
            while curr is not None:
                path.append((curr.x, curr.y))
                curr = curr.parent
            return path[::-1]

        neighbors = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        for offset in neighbors:
            neighbor_pos = (current_node.x + offset[0], current_node.y + offset[1])

            if neighbor_pos in closed_list:
                continue

            # 檢查鄰居是否可走
            if not is_walkable(game_map, neighbor_pos[0], neighbor_pos[1]):
                continue

            neighbor = Node(neighbor_pos[0], neighbor_pos[1], current_node)
            neighbor.g = current_node.g + 1
            neighbor.h = abs(neighbor.x - end_node.x) + abs(neighbor.y - end_node.y)
            neighbor.f = neighbor.g + neighbor.h

            existing_node = next((n for n in open_list if n.x == neighbor.x and n.y == neighbor.y), None)
            if existing_node and existing_node.g < neighbor.g:
                continue

            heapq.heappush(open_list, neighbor)

    return None

def is_walkable(game_map, x, y):
    """
    判斷該座標是否可以行走 (更加寬容的版本)
    """
    # 1. 邊界檢查
    map_w, map_h = 0, 0
    if hasattr(game_map, 'map_data') and len(game_map.map_data) > 0:
        map_h = len(game_map.map_data)
        map_w = len(game_map.map_data[0])
    elif hasattr(game_map, 'width'):
        map_w = game_map.width
        map_h = game_map.height
    else:
        map_w, map_h = 9999, 9999 # Fallback

    if x < 0 or y < 0 or x >= map_w or y >= map_h:
        return False

    # 2. 障礙物檢查
    ts = GameSettings.TILE_SIZE
    
    # [關鍵修改]：縮小檢查範圍
    # 我們不檢查完整的 32x32 格子，而是檢查中間的 24x24 區域
    # 這樣可以避免因為 "擦到牆壁邊緣" 就被判定為死路
    margin = 4 # 每一邊縮減 4 pixels
    virtual_rect = pg.Rect(x * ts + margin, y * ts + margin, ts - margin*2, ts - margin*2)

    try:
        if hasattr(game_map, 'check_collision'):
            # 如果這格裡面有任何碰撞物，就回傳 False (不可走)
            if game_map.check_collision(virtual_rect):
                return False 
    except Exception:
        return False 

    return True