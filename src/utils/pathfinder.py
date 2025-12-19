import collections

def find_path(start_pos, end_pos, game_map):
    """
    使用 BFS 尋找路徑
    start_pos: (x, y) tuple, 單位是 tile (格子座標)
    end_pos: (x, y) tuple, 單位是 tile (格子座標)
    game_map: 用來檢查障礙物
    """
    # 佇列，用來存待檢查的格子
    queue = collections.deque([start_pos])
    
    # 記錄路徑來源：came_from[下一個點] = 當前點
    came_from = {start_pos: None}
    
    found = False
    
    while queue:
        current = queue.popleft()
        
        # 如果找到終點了
        if current == end_pos:
            found = True
            break
            
        # 檢查上下左右四個鄰居
        neighbors = [
            (current[0] + 1, current[1]), # 右
            (current[0] - 1, current[1]), # 左
            (current[0], current[1] + 1), # 下
            (current[0], current[1] - 1)  # 上
        ]
        
        for next_node in neighbors:
            # 1. 檢查是否在邊界內 (假設地圖最大 100x100，你可以根據實際地圖大小調整)
            if not (0 <= next_node[0] < 100 and 0 <= next_node[1] < 100):
                continue
                
            # 2. 檢查是否是障礙物 (這是最重要的一步！)
            # 這裡我們假設 game_map 有一個方法叫 check_wall 或是透過 tmx_data 判斷
            # 如果你之前是用 obstacles 列表，要寫在這裡
            if is_blocked(game_map, next_node):
                continue

            # 3. 如果這個點還沒走過
            if next_node not in came_from:
                queue.append(next_node)
                came_from[next_node] = current

    # 如果沒找到路徑
    if not found:
        print("No path found!")
        return []

    # 回溯路徑：從終點倒著推回起點
    path = []
    current = end_pos
    while current != start_pos:
        path.append(current)
        current = came_from[current]
    path.reverse() # 翻轉成 正確順序
    return path

def is_blocked(game_map, tile_pos):
    """
    檢查該格子是否為障礙物
    這裡需要根據你的 Map 實作來修改
    """
    x, y = tile_pos
    
    # 方法 A: 如果你的 Map 有 obstacles 列表 (Rect 列表)
    # 我們把 tile 座標轉成 pixel 座標來檢查碰撞
    # TILE_SIZE = 16 (假設)
    # test_rect = pg.Rect(x * 16, y * 16, 16, 16)
    # index = test_rect.collidelist(game_map.obstacles)
    # return index != -1

    # 方法 B: 簡單檢查 (假設 tmx_data)
    # 如果該層沒有瓦片，或者該瓦片屬性是牆壁
    # 這裡先暫時回傳 False (代表所有路都能走)，等你測試成功再把障礙物判斷加進來
    # 為了測試，你可以先不改，讓人物能穿牆導航，之後再修
    return False