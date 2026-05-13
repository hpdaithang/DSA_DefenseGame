"""
Module chính của trò chơi Try To Survive.
Quản lý vòng lặp game, xử lý sự kiện người dùng, hệ thống Camera 
và giao diện khởi đầu với hiệu ứng đồ họa động.
"""
import pygame
import sys
import random
import time
import math

from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, UI_HEIGHT, FPS, COLORS
from map import GameMap
from entities import CommandCenter, ResourceNode, Worker, TransportConvoy, Enemy, HomingProjectile, Wall, Soldier, Barracks
from pathfinding import a_star
from ui import UIManager
from screens import GameOverScreen
from leaderboard import Leaderboard

class MenuDecor:
    """Quản lý hiệu ứng các icon tài nguyên bay lơ lửng và xoay trên màn hình chờ. Quản lý hiệu ứng đồ họa nền"""
    
    def __init__(self, screen_w, screen_h):
        """Khởi tạo danh sách các icon trang trí."""
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.icons = []
        res_types = ['wood', 'stone', 'coal']
        
        # Tạo 15 icon ngẫu nhiên
        for _ in range(15):
            res_type = random.choice(res_types)
            self.icons.append({
                'type': res_type,
                'x': random.randint(0, screen_w),
                'y': random.randint(0, screen_h),
                'angle': random.randint(0, 360),
                'rotate_speed': random.uniform(0.5, 1.5),
                'float_offset': random.uniform(0, math.pi * 2),
                'speed_y': random.uniform(0.2, 0.7)
            })

    def update_and_draw(self, surface):
        """Cập nhật vị trí và vẽ các icon lên màn hình."""
        for icon in self.icons:
            icon['y'] -= icon['speed_y']
            if icon['y'] < -50: icon['y'] = self.screen_h + 50
            
            icon['float_offset'] += 0.02
            curr_x = icon['x'] + math.sin(icon['float_offset']) * 20
            icon['angle'] += icon['rotate_speed']
            
            base_img = ResourceNode.loaded_images.get(icon['type'])
            if base_img:
                rotated_surf = pygame.transform.rotate(base_img, icon['angle'])
                rect = rotated_surf.get_rect(center=(int(curr_x), int(icon['y'])))
                surface.blit(rotated_surf, rect)

def draw_dashed_line(surface, color, start_pos, end_pos, width=1, dash_length=10):
    """Vẽ đường đứt đoạn hỗ trợ hiển thị vùng tuần tra."""
    x1, y1 = start_pos
    x2, y2 = end_pos
    dl = math.hypot(x2 - x1, y2 - y1)
    if dl == 0: return
    dashs = int(dl / dash_length)
    if dashs % 2 != 0: dashs += 1 
    for i in range(dashs):
        if i % 2 == 0:
            start = (x1 + (x2 - x1) * i / dashs, y1 + (y2 - y1) * i / dashs)
            end = (x1 + (x2 - x1) * (i + 1) / dashs, y1 + (y2 - y1) * (i + 1) / dashs)
            pygame.draw.line(surface, color, start, end, width)

class GameManager:
    """
    Trình quản lý trung tâm của trò chơi.
    Nắm giữ và điều phối mọi thực thể (công trình, lính, quái, tài nguyên) và xử lý logic các giai đoạn (Phase).
    """
    def __init__(self):
        """Khởi tạo giao diện trò chơi"""
        self.ui = UIManager()
        self.reset_game() 

    def reset_game(self):
        """
        Xóa toàn bộ dữ liệu cũ và khởi tạo lại trạng thái bản đồ, thực thể, bộ đếm cho ván chơi mới.
        """
        self.game_map = GameMap()
        self.buildings, self.resources, self.workers = [], [], []
        self.convoys, self.enemies, self.projectiles = [], [], []
        self.walls, self.barracks, self.soldiers = [], [], []
        
        self.enemy_spawn_timer = 180 
        self.coverage_map = [[False for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.barracks_coverage_map = [[False for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        
        self.is_dragging = False
        self.drag_start = (0, 0)
        self.drag_current = (0, 0)
        self.build_mode = None
        
        self.ui.selected_building = None
        self.ui.reset_transport()
        
        self.has_started = False
        self.is_game_over = False
        
        res_types = ['wood', 'wood', 'stone', 'stone', 'coal' , 'coal']
        num_res_types = random.randint(7, 12) 
        for _ in range(num_res_types):
            for res in res_types:
                c = random.randint(2, MAP_WIDTH - 3)
                r = random.randint(2, MAP_HEIGHT - 3)
                while self.game_map.grid[r][c] == 1:
                    c = random.randint(2, MAP_WIDTH - 3)
                    r = random.randint(2, MAP_HEIGHT - 3)
                self.resources.append(ResourceNode(c, r, res))
                
        self.phase = 1               
        self.base_spawn_timer = 200  
        self.enemy_spawn_timer = self.base_spawn_timer
        self.phase_message_timer = 0 

    def spawn_resources(self):
        """
            Hàm quản lí việc sinh tài nguyên
        """
        res_types = ['wood', 'wood', 'stone', 'stone', 'coal', 'coal']
        num_res = random.randint(7, 18) 
        for _ in range(num_res):
            res = random.choice(res_types)
            for _ in range(50): 
                c = random.randint(2, MAP_WIDTH - 3)
                r = random.randint(2, MAP_HEIGHT - 3)
                if self.game_map.grid[r][c] == 0: 
                    occupied = any(b.col == c and b.row == r for b in self.buildings + self.walls + self.resources + self.barracks)
                    if not occupied:
                        self.resources.append(ResourceNode(c, r, res))
                        break
    
    def add_command_center(self, col, row):
        """
        Xử lý logic đặt/xây dựng Thành trì mới trên lưới tọa độ.
        Kiểm tra va chạm, tài nguyên và cập nhật đường đi.
        """
        if self.game_map.grid[row][col] == 1:
            print("Lỗi: Không thể xây Trung tâm chỉ huy trên mặt nước!")
            return False

        if any(b.col == col and b.row == row for b in self.buildings + self.walls + self.barracks + self.resources): 
            return False
        
        is_free = len(self.buildings) < 2
        
        if not is_free:
            if not self.coverage_map[row][col]:
                return False
                
            owner_cc = min(self.buildings, key=lambda b: math.hypot(b.col - col, b.row - row))
            if owner_cc.inventory['wood'] >= 10 and owner_cc.inventory['stone'] >= 3 and owner_cc.inventory['coal'] >= 3:
                owner_cc.inventory['wood'] -= 10
                owner_cc.inventory['stone'] -= 3
                owner_cc.inventory['coal'] -= 3
            else:
                return False
        
        if self.buildings:
            nearest_cc = min(self.buildings, key=lambda b: math.hypot(b.col - col, b.row - row))
            buildings_pos = [(b.col, b.row) for b in self.buildings]
            path = a_star((col, row), (nearest_cc.col, nearest_cc.row), self.game_map.grid, buildings_pos, ignore_buildings=True)
            
            if path:
                for p_col, p_row in path[:-1]:
                    current_terrain = self.game_map.grid[p_row][p_col]
                    if current_terrain == 0:
                        self.game_map.grid[p_row][p_col] = 2 
                    elif current_terrain == 1:
                        self.game_map.grid[p_row][p_col] = 3 
                        
        new_cc = CommandCenter(col, row)
        self.buildings.append(new_cc)
        self.update_coverage_map()
        return True 

    def update_coverage_map(self):
        """
            Hàm update phạm vi ảnh hưởng 
        """
        self.coverage_map = [[False for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        for b in self.buildings:
            rng = getattr(b, 'attack_range', 2) 
            for r in range(b.row - rng, b.row + rng + 1):
                for c in range(b.col - rng, b.col + rng + 1):
                    if 0 <= r < MAP_HEIGHT and 0 <= c < MAP_WIDTH: self.coverage_map[r][c] = True

    def update_barracks_coverage_map(self):
        """
            Update khu vực ảnh hưởng của doanh trại
        """
        self.barracks_coverage_map = [[False for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        for b in self.barracks:
            for r in range(b.row - 7, b.row + 8):
                for c in range(b.col - 7, b.col + 8):
                    if 0 <= r < MAP_HEIGHT and 0 <= c < MAP_WIDTH:
                        self.barracks_coverage_map[r][c] = True

    def draw_borders(self, surface):
        """
            Vẽ viền
        """
        for r in range(MAP_HEIGHT):
            for c in range(MAP_WIDTH):
                if self.coverage_map[r][c]:
                    x, y = c * TILE_SIZE, r * TILE_SIZE
                    if r == 0 or not self.coverage_map[r-1][c]: pygame.draw.line(surface, COLORS['border'], (x, y), (x + TILE_SIZE, y), 3)
                    if r == MAP_HEIGHT-1 or not self.coverage_map[r+1][c]: pygame.draw.line(surface, COLORS['border'], (x, y+TILE_SIZE), (x+TILE_SIZE, y+TILE_SIZE), 3)
                    if c == 0 or not self.coverage_map[r][c-1]: pygame.draw.line(surface, COLORS['border'], (x, y), (x, y+TILE_SIZE), 3)
                    if c == MAP_WIDTH-1 or not self.coverage_map[r][c+1]: pygame.draw.line(surface, COLORS['border'], (x+TILE_SIZE, y), (x+TILE_SIZE, y+TILE_SIZE), 3)

    def draw_barracks_borders(self, surface):

        """
            Vẽ viền cho doanh trại
        """
        for r in range(MAP_HEIGHT):
            for c in range(MAP_WIDTH):
                if self.barracks_coverage_map[r][c]:
                    x, y = c * TILE_SIZE, r * TILE_SIZE
                    color = (0, 255, 0) 
                    if r == 0 or not self.barracks_coverage_map[r-1][c]: 
                        draw_dashed_line(surface, color, (x, y), (x + TILE_SIZE, y), 2)
                    if r == MAP_HEIGHT-1 or not self.barracks_coverage_map[r+1][c]: 
                        draw_dashed_line(surface, color, (x, y+TILE_SIZE), (x+TILE_SIZE, y+TILE_SIZE), 2)
                    if c == 0 or not self.barracks_coverage_map[r][c-1]: 
                        draw_dashed_line(surface, color, (x, y), (x, y+TILE_SIZE), 2)
                    if c == MAP_WIDTH-1 or not self.barracks_coverage_map[r][c+1]: 
                        draw_dashed_line(surface, color, (x+TILE_SIZE, y), (x+TILE_SIZE, y+TILE_SIZE), 2)

    def handle_selection_box(self):
        """Phân bổ đều thợ mỏ cho các loại tài nguyên khác nhau thuật toán Round-Robin"""
        x1, y1 = self.drag_start
        x2, y2 = self.drag_current
        left, top = min(x1, x2), min(y1, y2)
        width, height = abs(x1 - x2), abs(y1 - y2)
        selection_rect = pygame.Rect(left, top, width, height)

        if not self.buildings: return

        selected_resources = [res for res in self.resources if res.rect.colliderect(selection_rect)]
        if not selected_resources: return

        res_by_type = {}
        for res in selected_resources:
            if res.res_type not in res_by_type: res_by_type[res.res_type] = []
            res_by_type[res.res_type].append(res)
            
        available_types = list(res_by_type.keys())
        type_index = 0

        available_ccs = [cc for cc in self.buildings if cc.active_workers < cc.max_workers]
        buildings_pos = [(b.col, b.row) for b in self.buildings]

        fail_count = 0
        while available_ccs and available_types and fail_count < len(available_types):
            current_type = available_types[type_index % len(available_types)]
            
            if not res_by_type[current_type]:
                available_types.remove(current_type)
                continue
                
            target_res = res_by_type[current_type].pop(0)
            res_by_type[current_type].append(target_res)
            
            available_ccs.sort(key=lambda cc: abs(cc.col - target_res.col) + abs(cc.row - target_res.row)) 
            best_cc, path = None, None
            
            for cc in available_ccs:
                path = a_star((cc.col, cc.row), (target_res.col, target_res.row), self.game_map.grid, buildings_pos, ignore_buildings=True)
                if path:
                    best_cc = cc
                    break
                    
            if best_cc and path:
                self.workers.append(Worker(best_cc, target_res, path))
                best_cc.active_workers += 1
                if best_cc.active_workers >= best_cc.max_workers:
                    available_ccs.remove(best_cc)
                fail_count = 0
            else:
                fail_count += 1
                
            type_index += 1

    def update(self, survival_time): 

        """
            Vòng lặp logic cốt lõi.
            Cập nhật Giai đoạn (Phase), sinh quái, dọn dẹp các thực thể đã chết, và gọi update() của tất cả các đối tượng.
        """
        if self.is_game_over: return 
        
        for cc in self.buildings: cc.active_workers = 0
        for worker in self.workers:
            if worker.home_cc in self.buildings and worker.active and getattr(worker, 'state', '') != 'KAMIKAZE':
                worker.home_cc.active_workers += 1
        # tại đây quy định thời gian mỗi phase
        current_phase = (survival_time // 50) + 1
        if current_phase > self.phase:
            self.phase = current_phase
            self.base_spawn_timer = max(40, int(self.base_spawn_timer * 0.85)) 
            self.spawn_resources() 
            self.phase_message_timer = 180 

        buildings_pos = [(b.col, b.row) for b in self.buildings]
        
        wall_positions = {(w.col, w.row) for w in self.walls}
        for wall in self.walls[:]:
            wall.is_vertical = (wall.col, wall.row - 1) in wall_positions or (wall.col, wall.row + 1) in wall_positions
            
            if not hasattr(wall, 'underlying_terrain'):
                wall.underlying_terrain = self.game_map.grid[wall.row][wall.col]
            self.game_map.grid[wall.row][wall.col] = 4 
            if wall.hp <= 0:
                self.ui.add_log("Có một bức tường đã bị hủy!") 
                self.game_map.grid[wall.row][wall.col] = wall.underlying_terrain 
                self.walls.remove(wall)
        
        if self.buildings and survival_time >= 15:
            self.enemy_spawn_timer -= 1
            if self.enemy_spawn_timer <= 0:
                spawn_col = random.choice([0, MAP_WIDTH - 1]) 
                spawn_row = random.randint(0, MAP_HEIGHT - 1)
                self.enemies.append(Enemy(spawn_col, spawn_row, self.phase)) 
                self.enemy_spawn_timer = self.base_spawn_timer 

        for enemy in self.enemies[:]:
            if not self.buildings: break
            target_cc = min(self.buildings, key=lambda b: abs(b.col - enemy.col) + abs(b.row - enemy.row))
            enemy.update(self.game_map.grid, target_cc, buildings_pos, self.walls) 
            if enemy.hp <= 0: self.enemies.remove(enemy)

        for cc in self.buildings:
            cc.update_decay()
            if cc.shoot_cooldown > 0: cc.shoot_cooldown -= 1
            else:
                rng = getattr(cc, 'attack_range', 2) 
                shots_allowed = 1 + getattr(cc, 'upgrade_level', 0) 
                shots_fired = 0
                for enemy in self.enemies:
                    if abs(enemy.col - cc.col) <= rng and abs(enemy.row - cc.row) <= rng:
                        self.projectiles.append(HomingProjectile(cc.rect.centerx, cc.rect.centery, enemy))
                        shots_fired += 1
                        if shots_fired >= shots_allowed: break
                if shots_fired > 0: cc.shoot_cooldown = 45 
                        
        for proj in self.projectiles[:]:
            proj.update()
            if not proj.active: self.projectiles.remove(proj)

        for worker in self.workers[:]:
            worker.update(self.game_map.grid, self.buildings, self.enemies)
            if not worker.active: self.workers.remove(worker)
                
        for convoy in self.convoys[:]:
            convoy.update(self.game_map.grid, buildings_pos)
            if convoy.state == 'DONE': self.convoys.remove(convoy)

        for cc in self.buildings[:]:
            if cc.hp <= 0:
                self.ui.add_log(f"Thành trì tọa độ ({cc.col}, {cc.row}) đã bị phá hủy!") 
                self.buildings.remove(cc)
                self.update_coverage_map()
                if self.ui.selected_building == cc: self.ui.selected_building = None
                
        for res in self.resources[:]:
            if res.amount <= 0:
                r, c = res.row, res.col
                neighbors = []
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < MAP_HEIGHT and 0 <= nc < MAP_WIDTH:
                        neighbors.append(self.game_map.grid[nr][nc])
                if len(neighbors) == 4 and all(n in (2, 3) for n in neighbors): self.game_map.grid[r][c] = 2 
                else: self.game_map.grid[r][c] = 0 
                self.resources.remove(res)
                
        if self.has_started and len(self.buildings) == 0:
            self.is_game_over = True
        
        for b in self.barracks[:]:
            if not hasattr(b, 'underlying_terrain'):
                b.underlying_terrain = self.game_map.grid[b.row][b.col]
            
            self.game_map.grid[b.row][b.col] = 4 
            if not self.coverage_map[b.row][b.col]:
                if not hasattr(b, 'decay_timer'): b.decay_timer = 600 
                b.decay_timer -= 1
                if b.decay_timer <= 0:
                    b.hp -= 1
                    b.decay_timer = 600 
            else:
                b.decay_timer = 600 

            self.game_map.grid[b.row][b.col] = 4 
            
            if b.hp <= 0:
                self.ui.add_log(f"Doanh trại tọa độ ({b.col}, {b.row}) đã bị phá hủy!") 
                b.active = False 
                self.game_map.grid[b.row][b.col] = b.underlying_terrain
                self.barracks.remove(b)
                self.update_barracks_coverage_map() 
            else:
                b.spawned_soldiers = [s for s in getattr(b, 'spawned_soldiers', []) if s.active]
                if len(b.spawned_soldiers) < 5:
                    b.spawn_timer -= 1
                    if b.spawn_timer <= 0:
                        new_soldier = Soldier(b, phase=self.phase) 
                        b.spawned_soldiers.append(new_soldier)
                        self.soldiers.append(new_soldier)
                        b.spawn_timer = 120

        for s in self.soldiers[:]:
            s.update(self.game_map.grid, self.enemies, buildings_pos)
            if not s.active: self.soldiers.remove(s)

    def draw_world(self, surface, survival_time, world_mx, world_my):
        """
        Vẽ toàn bộ thế giới game (bản đồ, thực thể, hiệu ứng) lên một bề mặt (surface) ảo để hỗ trợ hệ thống Camera thu phóng.
        """
        self.game_map.draw(surface)
        for res in self.resources: res.draw(surface)
        for b in self.buildings: b.draw(surface)
        
        self.draw_borders(surface)
        self.draw_barracks_borders(surface)

        for wall in self.walls: wall.draw(surface)
        for b in self.barracks: b.draw(surface)
        
        for worker in self.workers: worker.draw(surface)
        for convoy in self.convoys: convoy.draw(surface)
        for enemy in self.enemies: enemy.draw(surface)
        for proj in self.projectiles: proj.draw(surface)
        for s in self.soldiers: s.draw(surface)
        
        if getattr(self, 'phase_message_timer', 0) > 0:
            self.phase_message_timer -= 1
            font_big = pygame.font.SysFont("tahoma", 60, bold=True)
            msg = font_big.render(f"GIAI ĐOẠN {self.phase} BẮT ĐẦU!", True, (255, 50, 50))
            bg_rect = msg.get_rect(center=(surface.get_width()//2, surface.get_height()//2 - 100))
            pygame.draw.rect(surface, (0, 0, 0), bg_rect.inflate(20, 20))
            pygame.draw.rect(surface, (255, 215, 0), bg_rect.inflate(20, 20), 3)
            surface.blit(msg, bg_rect)
        
        if self.is_dragging:
            x1, y1 = self.drag_start
            x2, y2 = self.drag_current
            left, top = min(x1, x2), min(y1, y2)
            width, height = abs(x1 - x2), abs(y1 - y2)
            rect = pygame.Rect(left, top, width, height)
            pygame.draw.rect(surface, COLORS['selection'], rect, 2)
            
        if self.build_mode == 'BARRACKS':
            mc, mr = world_mx // TILE_SIZE, world_my // TILE_SIZE
            x, y = (mc-7)*TILE_SIZE, (mr-7)*TILE_SIZE
            w, h = 15*TILE_SIZE, 15*TILE_SIZE
            draw_dashed_line(surface, (0, 255, 0), (x, y), (x+w, y), 2)
            draw_dashed_line(surface, (0, 255, 0), (x, y+h), (x+w, y+h), 2)
            draw_dashed_line(surface, (0, 255, 0), (x, y), (x, y+h), 2)
            draw_dashed_line(surface, (0, 255, 0), (x+w, y), (x+w, y+h), 2)

def main():
    """Hàm khởi chạy chính, bắt sự kiện gõ chữ tiếng Việt và xử lý Game Loop."""
    pygame.init()
    window_width = MAP_WIDTH * TILE_SIZE
    window_height = MAP_HEIGHT * TILE_SIZE + UI_HEIGHT
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Try To Survive")
    clock = pygame.time.Clock()
    
    leaderboard = Leaderboard()
    font_large = pygame.font.SysFont("tahoma", 56, bold=True)
    font_normal = pygame.font.SysFont("tahoma", 28)
    font_bold = pygame.font.SysFont("tahoma", 28, bold=True)
    font_small = pygame.font.SysFont("tahoma", 18, bold=True)
    font_tutorial = pygame.font.SysFont("tahoma", 22)
    font_tutorial_bold = pygame.font.SysFont("tahoma", 22, bold=True)


    game_state = "INPUT_NAME" 
    player_name = ""
    start_time = 0
    survival_time = 0
    
    camera_x, camera_y = 0.0, 0.0
    zoom = 1.0
    
    manager = None
    game_over_screen = GameOverScreen()
    
    # Load giả lập 1 node để kích hoạt Cache ảnh tài nguyên cho màn hình Menu
    ResourceNode(0, 0, 'wood')
    ResourceNode(0, 0, 'stone')
    ResourceNode(0, 0, 'coal')
    decor = MenuDecor(window_width, window_height)

    pygame.key.start_text_input()
    
    while True:
        if game_state == "PLAYING":
            keys = pygame.key.get_pressed()
            pan_speed = 15
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: camera_x += pan_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: camera_x -= pan_speed
            if keys[pygame.K_UP] or keys[pygame.K_w]: camera_y += pan_speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: camera_y -= pan_speed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if game_state == "INPUT_NAME":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(player_name.strip()) > 0:
                        pygame.key.stop_text_input() 
                        manager = GameManager()
                        start_time = time.time()
                        game_state = "PLAYING"
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                        
                elif event.type == pygame.TEXTINPUT:
                    if len(player_name) < 20: 
                        player_name += event.text
                        
                # Bắt sự kiện Click vào nút Hướng dẫn
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    btn_help_rect = pygame.Rect(window_width//2 - 450, 520, 400, 45)
                    if btn_help_rect.collidepoint(event.pos):
                        pygame.key.stop_text_input()
                        game_state = "HOW_TO_PLAY"
                        
            elif game_state == "HOW_TO_PLAY":
                # Nhấn ESC hoặc click nút Quay Lại để thoát
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    game_state = "INPUT_NAME"
                    pygame.key.start_text_input()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    btn_back_rect = pygame.Rect(30, 30, 150, 45)
                    if btn_back_rect.collidepoint(event.pos):
                        game_state = "INPUT_NAME"
                        pygame.key.start_text_input()
            
            elif game_state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: manager.build_mode = 'CC'
                    elif event.key == pygame.K_2: manager.build_mode = 'WALL'
                    elif event.key == pygame.K_3: manager.build_mode = 'BARRACKS' 
                    elif event.key == pygame.K_ESCAPE: manager.build_mode = None
                    
                    elif event.key == pygame.K_h and manager.ui.selected_building:
                        manager.ui.selected_building.repair()
                        manager.ui.add_log("Đã sử dụng phím tắt H để sửa chữa!")

                    elif event.key == pygame.K_u and manager.ui.selected_building:
                        if hasattr(manager.ui.selected_building, 'upgrade'):
                            if manager.ui.selected_building.upgrade():
                                manager.update_coverage_map()
                                manager.ui.add_log("Đã nâng cấp công trình thành công!")
                
                elif event.type == pygame.MOUSEWHEEL:
                    old_zoom = zoom
                    zoom += event.y * 0.1
                    zoom = max(1.0, min(zoom, 3.0)) 
                    
                    mx, my = pygame.mouse.get_pos()
                    if my < MAP_HEIGHT * TILE_SIZE: 
                        world_x = (mx - camera_x) / old_zoom
                        world_y = (my - camera_y) / old_zoom
                        camera_x = mx - world_x * zoom
                        camera_y = my - world_y * zoom

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    mx, my = pos
                    
                    btn_cc_rect = pygame.Rect(10, 10, 180, 40)
                    btn_wall_rect = pygame.Rect(200, 10, 180, 40)
                    btn_barracks_rect = pygame.Rect(390, 10, 180, 40)
                    
                    if event.button == 1:
                        if btn_cc_rect.collidepoint(pos):
                            manager.build_mode = 'CC'; continue
                        if btn_wall_rect.collidepoint(pos):
                            manager.build_mode = 'WALL'; continue
                        if btn_barracks_rect.collidepoint(pos):
                            manager.build_mode = 'BARRACKS'; continue
                                
                        if my >= MAP_HEIGHT * TILE_SIZE:
                            ui_action = manager.ui.handle_click(pos)
                            if ui_action == "CONFIRM_TRANSPORT":
                                source = manager.ui.selected_building
                                dest = manager.ui.transport_dest_cc
                                payload = manager.ui.transport_payload.copy()
                                for res, amount in payload.items(): source.inventory[res] -= amount
                                buildings_pos = [(b.col, b.row) for b in manager.buildings]
                                path = a_star((source.col, source.row), (dest.col, dest.row), manager.game_map.grid, buildings_pos, ignore_buildings=True)
                                manager.convoys.append(TransportConvoy(source, dest, payload, path))
                                manager.ui.reset_transport() 
                                continue
                            elif ui_action is True: continue
                        
                        world_x = (mx - camera_x) / zoom
                        world_y = (my - camera_y) / zoom
                        grid_c, grid_r = int(world_x // TILE_SIZE), int(world_y // TILE_SIZE)

                        if manager.ui.is_selecting_dest:
                            clicked_building = next((b for b in manager.buildings if b.rect.collidepoint(world_x, world_y) and b != manager.ui.selected_building), None)
                            if clicked_building:
                                manager.ui.transport_dest_cc = clicked_building
                                manager.ui.is_selecting_dest = False
                            continue 
                        
                        if manager.build_mode is not None:
                            if manager.build_mode == 'CC':
                                if manager.add_command_center(grid_c, grid_r):
                                    if not manager.has_started:
                                        manager.has_started = True
                                        start_time = time.time()
                                    
                            elif manager.build_mode == 'WALL':
                                if manager.buildings and manager.coverage_map[grid_r][grid_c] and manager.game_map.grid[grid_r][grid_c] != 1:
                                    if not any(b.col == grid_c and b.row == grid_r for b in manager.buildings + manager.walls + manager.barracks + manager.resources):
                                        owner_cc = min(manager.buildings, key=lambda b: math.hypot(b.col - grid_c, b.row - grid_r))
                                        if owner_cc.inventory['wood'] >= 2 and owner_cc.inventory['stone'] >= 1:
                                            owner_cc.inventory['wood'] -= 2
                                            owner_cc.inventory['stone'] -= 1
                                            manager.walls.append(Wall(grid_c, grid_r, owner_cc))
                                            
                            elif manager.build_mode == 'BARRACKS':
                                if manager.buildings and manager.coverage_map[grid_r][grid_c] and manager.game_map.grid[grid_r][grid_c] != 1:
                                    if not any(b.col == grid_c and b.row == grid_r for b in manager.buildings + manager.walls + manager.barracks + manager.resources):
                                        owner_cc = min(manager.buildings, key=lambda b: math.hypot(b.col - grid_c, b.row - grid_r))
                                        if getattr(owner_cc, 'upgrade_level', 0) >= 1: 
                                            if owner_cc.inventory['wood'] >= 10 and owner_cc.inventory['stone'] >= 2 and owner_cc.inventory['coal'] >= 3:
                                                owner_cc.inventory['wood'] -= 10
                                                owner_cc.inventory['stone'] -= 2
                                                owner_cc.inventory['coal'] -= 3
                                                manager.barracks.append(Barracks(grid_c, grid_r, owner_cc))
                                                manager.update_barracks_coverage_map() 
                            continue
                        
                        clicked_building = next((b for b in manager.buildings if b.rect.collidepoint(world_x, world_y)), None)
                        if clicked_building:
                            manager.ui.selected_building = clicked_building
                            manager.ui.mode = 'INFO'
                            continue
                            
                        clicked_wall = next((w for w in manager.walls if w.rect.collidepoint(world_x, world_y)), None)
                        if clicked_wall:
                            if clicked_wall.repair(): print("Đã sửa tường!")
                            continue
                            
                        clicked_barrack = next((b for b in manager.barracks if b.rect.collidepoint(world_x, world_y)), None)
                        if clicked_barrack:
                            if clicked_barrack.repair(): print("Đã sửa doanh trại!")
                            continue
                            
                        manager.ui.selected_building = None
                        manager.is_dragging = True
                        manager.drag_start = (world_x, world_y)
                        manager.drag_current = (world_x, world_y)
                        
                    elif event.button == 3:
                        manager.build_mode = None
                            
                elif event.type == pygame.MOUSEMOTION:
                    if manager.is_dragging:
                        mx, my = pygame.mouse.get_pos()
                        manager.drag_current = ((mx - camera_x) / zoom, (my - camera_y) / zoom)
                        
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and manager.is_dragging:
                        manager.is_dragging = False
                        manager.handle_selection_box()
            
            elif game_state == "GAME_OVER":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if game_over_screen.handle_click(pygame.mouse.get_pos()) == "RESTART":
                            player_name = "" 
                            game_state = "INPUT_NAME" 
                            pygame.key.start_text_input() 
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        player_name = ""
                        game_state = "INPUT_NAME"
                        pygame.key.start_text_input()
        # VẼ GIAO DIỆN 
        if game_state == "INPUT_NAME":
            screen.fill((240, 248, 255)) 
            decor.update_and_draw(screen) 
            
            input_box = pygame.Rect(window_width//2 - 450, 200, 400, 300)
            pygame.draw.rect(screen, (255, 255, 255), input_box, border_radius=15)
            pygame.draw.rect(screen, (70, 130, 180), input_box, 3, border_radius=15)
            
            title_surf = font_large.render("Try To Survive", True, (25, 25, 112))
            screen.blit(title_surf, (input_box.x + 20, 120))
            
            prompt_surf = font_normal.render("Nhập tên Chỉ Huy:", True, (50, 50, 50))
            screen.blit(prompt_surf, (input_box.x + 30, 230))
            
            name_rect = pygame.Rect(input_box.x + 30, 270, 340, 50)
            pygame.draw.rect(screen, (230, 230, 230), name_rect, border_radius=5)
            
            display_name = player_name + ("|" if time.time() % 1 > 0.5 else "")
            name_surf = font_normal.render(display_name, True, (0, 0, 0))
            screen.blit(name_surf, (name_rect.x + 10, name_rect.y + 10))
            
            hint_surf = font_normal.render("Ấn ENTER để bắt đầu !!", True, (100, 100, 100))
            screen.blit(hint_surf, (input_box.x + 50, 420))
            
            # [MỚI]: Nút Hướng Dẫn
            btn_help_rect = pygame.Rect(window_width//2 - 450, 520, 400, 45)
            pygame.draw.rect(screen, (70, 130, 180), btn_help_rect, border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), btn_help_rect, 2, border_radius=10)
            help_txt = font_normal.render("HƯỚNG DẪN TÂN BINH", True, (255, 255, 255))
            screen.blit(help_txt, (btn_help_rect.centerx - help_txt.get_width()//2, btn_help_rect.centery - help_txt.get_height()//2))

            score_box = pygame.Rect(window_width//2 + 50, 120, 400, 450)
            pygame.draw.rect(screen, (255, 255, 255, 200), score_box, border_radius=15)
            pygame.draw.rect(screen, (218, 165, 32), score_box, 3, border_radius=15)
            
            lb_title = font_bold.render("Bảng xếp hạng", True, (139, 69, 19))
            screen.blit(lb_title, (score_box.centerx - lb_title.get_width()//2, 140))
            
            for i, entry in enumerate(leaderboard.data[:10]):
                color = (40, 40, 40)
                rank_txt = font_normal.render(f"#{i+1}", True, (218, 165, 32) if i < 3 else color)
                name_txt = font_normal.render(f"{entry['name']}", True, color)
                time_txt = font_normal.render(f"{entry['time']}s", True, color)
                
                y_offset = 190 + i * 38
                screen.blit(rank_txt, (score_box.x + 20, y_offset))
                screen.blit(name_txt, (score_box.x + 80, y_offset))
                screen.blit(time_txt, (score_box.x + 300, y_offset))
        
        elif game_state == "HOW_TO_PLAY":
            screen.fill((240, 248, 255)) 
            decor.update_and_draw(screen) # Hiệu ứng dao diện chờ 
            
            panel = pygame.Rect(window_width//2 - 350, 100, 700, 500)
            pygame.draw.rect(screen, (255, 255, 255, 230), panel, border_radius=15)
            pygame.draw.rect(screen, (70, 130, 180), panel, 3, border_radius=15)
            
            title = font_large.render("Hướng dẫn tân binh", True, (25, 25, 112))
            screen.blit(title, (panel.centerx - title.get_width()//2, panel.y + 20))
            
            instructions = [
                "MỤC TIÊU:",
                "- Khai thác tài nguyên, xây dựng phòng tuyến và sống sót.",
                "- Nếu tất cả 'Thành trì' bị phá hủy điều này dẫn đến GAME OVER.",
                "",
                "ĐIỀU KHIỂN & CAMERA:",
                "- W/A/S/D hoặc Mũi tên: Lướt Camera khắp bản đồ.",
                "- Lăn chuột: Phóng to / Thu nhỏ.",
                "- Chuột trái (Kéo thả): Giao việc cho thợ mỏ thu thập tài nguyên.",
                "- Chuột phải: Hủy thao tác xây dựng.",
                "",
                "PHÍM TẮT CƠ BẢN:",
                "- [1]: Xây 'Thành trì'      - [2]: Xây Tường     - [3]: Doanh Trại",
                "- [U]: Nâng cấp công trình đang chọn",
                "- [H]: Sửa chữa công trình đang chọn",
                "- [ESC]: Hủy chọn công trình"
            ]
            
            y_offset = panel.y + 90
            for line in instructions:
                color = (180, 50, 50) if "MỤC TIÊU" in line or "ĐIỀU KHIỂN" in line or "PHÍM TẮT" in line else (30, 30, 30)
                
                font_to_use = font_tutorial_bold if color != (30, 30, 30) else font_tutorial
                
                if line.startswith("-"): line = "  " + line
                txt_surf = font_to_use.render(line, True, color)
                screen.blit(txt_surf, (panel.x + 40, y_offset))
                y_offset += 24 if line == "" else 22

            btn_back_rect = pygame.Rect(40, 40, 160, 45)
            pygame.draw.rect(screen, (200, 50, 50), btn_back_rect, border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), btn_back_rect, 2, border_radius=10)
            back_txt = font_tutorial_bold.render("<- QUAY LẠI", True, (255, 255, 255))
            screen.blit(back_txt, (btn_back_rect.centerx - back_txt.get_width()//2, btn_back_rect.centery - back_txt.get_height()//2))

        elif game_state == "PLAYING":
            if manager.has_started:
                survival_time = int(time.time() - start_time)
            else:
                survival_time = 0

            scaled_w = MAP_WIDTH * TILE_SIZE * zoom
            scaled_h = MAP_HEIGHT * TILE_SIZE * zoom
            view_h = window_height - UI_HEIGHT 
            
            camera_x = max(window_width - scaled_w, min(0, camera_x))
            camera_y = max(view_h - scaled_h, min(0, camera_y))

            manager.update(survival_time) 
            
            screen.fill((0, 0, 0))
            
            world_surface = pygame.Surface((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))
            world_surface.fill((30, 100, 30)) 
            
            mx, my = pygame.mouse.get_pos()
            world_x = (mx - camera_x) / zoom
            world_y = (my - camera_y) / zoom
            
            manager.draw_world(world_surface, survival_time, world_x, world_y)
            
            scaled_w = int(MAP_WIDTH * TILE_SIZE * zoom)
            scaled_h = int(MAP_HEIGHT * TILE_SIZE * zoom)
            scaled_world = pygame.transform.scale(world_surface, (scaled_w, scaled_h))
            screen.blit(scaled_world, (camera_x, camera_y))

            free_cc = len(manager.buildings) < 2
            manager.ui.draw(screen, manager.build_mode, free_cc)

            btn_cc_rect = pygame.Rect(10, 10, 180, 40)
            cc_color = (80, 180, 80) if manager.build_mode == 'CC' else (50, 50, 50)
            pygame.draw.rect(screen, cc_color, btn_cc_rect)
            pygame.draw.rect(screen, (255, 255, 255), btn_cc_rect, 2)
            screen.blit(font_small.render("Thành Trì [1]", True, (255,255,255)), (20, 20))

            btn_wall_rect = pygame.Rect(200, 10, 180, 40)
            wall_color = (80, 180, 80) if manager.build_mode == 'WALL' else (50, 50, 50)
            pygame.draw.rect(screen, wall_color, btn_wall_rect)
            pygame.draw.rect(screen, (255, 255, 255), btn_wall_rect, 2)
            screen.blit(font_small.render("Tường [2]", True, (255,255,255)), (210, 20))
            
            btn_barracks_rect = pygame.Rect(390, 10, 180, 40)
            barracks_color = (80, 180, 80) if manager.build_mode == 'BARRACKS' else (50, 50, 50)
            pygame.draw.rect(screen, barracks_color, btn_barracks_rect)
            pygame.draw.rect(screen, (255, 255, 255), btn_barracks_rect, 2)
            screen.blit(font_small.render("Doanh Trại [3]", True, (255,255,255)), (400, 20))

            timer_surf = font_normal.render(f"Thời gian: {survival_time}s", True, (255, 255, 255))
            screen.blit(timer_surf, (window_width - 300, 20))
            
            if manager.has_started and survival_time < 15:
                countdown = 15 - survival_time
                font_warn = pygame.font.SysFont("tahoma", 36, bold=True)
                msg_warn = font_warn.render(f"QUÁI VẬT ĐẾN SAU: {countdown}s", True, (255, 100, 100))
                bg_rect = msg_warn.get_rect(center=(screen.get_width()//2, 80))
                pygame.draw.rect(screen, (0, 0, 0), bg_rect.inflate(20, 10))
                pygame.draw.rect(screen, (255, 100, 100), bg_rect.inflate(20, 10), 2)
                screen.blit(msg_warn, bg_rect)

            if manager.is_game_over:
                leaderboard.add_score(player_name, survival_time)
                game_state = "GAME_OVER"

        elif game_state == "GAME_OVER":
            screen.fill((0, 0, 0))
            
            temp_surface = pygame.Surface((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))
            manager.draw_world(temp_surface, survival_time, 0, 0)
            screen.blit(temp_surface, (0,0))
            
            game_over_screen.draw(screen) 
            lb_bg = pygame.Rect(50, 50, 400, 500)
            bg_surface = pygame.Surface((400, 500))
            bg_surface.set_alpha(220)
            bg_surface.fill((20, 20, 20))
            screen.blit(bg_surface, (50, 50))
            pygame.draw.rect(screen, (255, 215, 0), lb_bg, 2)
            
            lb_title = font_normal.render("Bảng xếp hạng", True, (255, 215, 0))
            screen.blit(lb_title, (50 + 200 - lb_title.get_width()//2, 70))
            
            for i, entry in enumerate(leaderboard.data[:10]):
                color = (0, 255, 0) if entry['name'] == player_name and entry['time'] == survival_time else (255, 255, 255)
                rank_text = font_normal.render(f"#{i+1} {entry['name']}", True, color)
                time_text = font_normal.render(f"{entry['time']}s", True, color)
                screen.blit(rank_text, (70, 130 + i * 35))
                screen.blit(time_text, (350, 130 + i * 35))
                
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()