import pygame
import math
from settings import TILE_SIZE, COLORS
from pathfinding import a_star
import random 
import os
class CommandCenter:
    """
    Lớp đại diện cho Thành trì.
    Quản lý máu (HP), sức chứa tài nguyên, thợ mỏ, cấp độ nâng cấp và tháp canh bắn quái.
    """
    def __init__(self, col, row):
        """
        Khởi tạo Thành trì tại tọa độ (col, row).
        Thiết lập các thông số cơ bản như HP, kho chứa mặc định và các giới hạn ban đầu.
        """
        self.col, self.row = col, row
        self.max_hp = 10
        self.hp = 10
        self.inventory = {'wood': 25, 'stone': 10, 'coal': 0} 
        self.rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.active_workers = 0
        self.max_workers = 5
        self.decay_timer = 120 
        self.shoot_cooldown = 0 
        
        self.upgrade_level = 0
        self.attack_range = 2     # Tầm bắn & Tầm viền vàng ban đầu
        self.inventory_limit = 50

    def upgrade(self):
        """
        Nâng cấp Thành trì (Tối đa 3 cấp).
        Mỗi cấp tăng: Tầm bắn, Máu, Giới hạn lính, và Sức chứa tài nguyên (tăng dần 10 -> 15 -> 20).
        Trả về True nếu nâng cấp thành công, False nếu thiếu tài nguyên.
        """
        if getattr(self, 'upgrade_level', 0) < 3:
            # Chi phí tăng dần: Cấp 1 (x1), Cấp 2 (x2), Cấp 3 (x3)
            cost_multiplier = self.upgrade_level + 1
            req_wood = 10 * cost_multiplier
            req_stone = 5 * cost_multiplier
            req_coal = 5 * cost_multiplier
            
            if self.inventory['wood'] >= req_wood and self.inventory['stone'] >= req_stone and self.inventory['coal'] >= req_coal:
                # Trừ tiền
                self.inventory['wood'] -= req_wood
                self.inventory['stone'] -= req_stone
                self.inventory['coal'] -= req_coal
                capacity_bonus = [10, 15, 20]
                
                # Cộng giới hạn kho TRƯỚC KHI tăng upgrade_level
                self.inventory_limit += capacity_bonus[self.upgrade_level]
                
                # Cập nhật các chỉ số khác
                self.upgrade_level += 1
                self.attack_range += 2    # Tăng tầm nhìn / tầm bắn
                self.max_hp += 10
                self.hp += 10
                self.max_workers += 2     # Thêm 2 slot lính khai thác mỗi lần nâng cấp
                
                return True
        return False
    
    def update_decay(self):
        """
        Kiểm tra và giảm dần tài nguyên dư thừa trong kho.
        Nếu lượng tài nguyên vượt quá 20, mỗi 120 khung hình sẽ tự động giảm đi 1 đơn vị.
        """
        if any(val > 20 for val in self.inventory.values()):
            self.decay_timer -= 1
            if self.decay_timer <= 0:
                for res in self.inventory:
                    if self.inventory[res] > 20: self.inventory[res] -= 1
                self.decay_timer = 120 

    def draw(self, surface):
        """Vẽ thành trì và hiển thị thanh HP"""
        pygame.draw.rect(surface, COLORS['cc'], self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, (255, 0, 0), (self.rect.x, self.rect.y - 10, TILE_SIZE, 5))
        pygame.draw.rect(surface, (0, 255, 0), (self.rect.x, self.rect.y - 10, TILE_SIZE * hp_ratio, 5))

    def repair(self):
        """
        Tiêu hao tài nguyên để phục hồi HP cho Thành trì.
        """
        if self.hp < self.max_hp and self.inventory['wood'] >= 5 and self.inventory['stone'] >= 5:
            self.inventory['wood'] -= 5
            self.inventory['stone'] -= 5
            self.hp = min(self.hp + 3, self.max_hp)

class ResourceNode:
    """
    Lớp đại diện cho mỏ tài nguyên (Gỗ, Đá, Than) trên bản đồ.
    """
    loaded_images = {}

    def __init__(self, col, row, res_type):
        
        """
        Khởi tạo mỏ tài nguyên và tự động nạp hình ảnh tương ứng với loại tài nguyên.
        """

        self.col, self.row, self.res_type = col, row, res_type
        self.amount = random.randint(50,100)
        self.rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)

        
        if self.res_type not in ResourceNode.loaded_images:
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                img_path = os.path.join(base_dir, "assets", f"{self.res_type}.png")
                
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                
                ResourceNode.loaded_images[self.res_type] = img
            except Exception as e:
                print(f"Khong tim thay file {self.res_type}.png, se dung khoi vuong mac dinh: {e}") # xử lí khi không tìm được file 
                ResourceNode.loaded_images[self.res_type] = None

    def draw(self, surface):
        """
        Vẽ mỏ tài nguyên lên màn hình (ưu tiên dùng hình ảnh, nếu lỗi sẽ dùng khối vuông màu).
        """
        img = ResourceNode.loaded_images.get(self.res_type)
        if img is not None:
            surface.blit(img, self.rect)
            hp_ratio = self.amount / 100.0
            pygame.draw.rect(surface, (0, 255, 0), (self.rect.x, self.rect.bottom - 4, TILE_SIZE * hp_ratio, 1))
        else:
            pygame.draw.rect(surface, COLORS[self.res_type], self.rect)

# Lính cảm tử (KAMIKAZE) :))))
class Worker:
    """
    Lớp đại diện cho Thợ mỏ.
    Xử lý logic di chuyển, khai thác tài nguyên, quay về Thành trì và trạng thái Kamikaze khi mất nhà.
    """

    def __init__(self, home_cc, target_res, path):
        """
        Khởi tạo Thợ mỏ với mục tiêu là mỏ tài nguyên và đường đi A* ban đầu.
        """
        self.home_cc, self.target_res = home_cc, target_res
        self.col, self.row = home_cc.col, home_cc.row
        self.pixel_x = self.col * TILE_SIZE + TILE_SIZE // 2
        self.pixel_y = self.row * TILE_SIZE + TILE_SIZE // 2
        self.path = path
        self.path_index = 0
        self.base_speed = 2.0 
        self.state = 'MOVING_TO_RESOURCE' 
        
        self.carrying_amount = 0
        self.max_carrying = 5
        self.carrying_type = target_res.res_type 
        self.mining_timer = 0
        
        self.active = True       
        self.orphaned = False    
        
        # Mặc định lính màu Trắng [255, 255, 255]
        self.current_color = list(COLORS['worker'])
        self.target_enemy = None
        self.repath_timer = 0

    def update(self, grid, buildings, enemies):

        """
        Cập nhật trạng thái của thợ mỏ theo từng frame.
        Bao gồm: Kiểm tra mất Thành trì, tìm mục tiêu Cảm tử, di chuyển theo đường A*, và thao tác đào tài nguyên.
        """

        if not self.active: return
        self.col = int(self.pixel_x // TILE_SIZE)
        self.row = int(self.pixel_y // TILE_SIZE)
        if self.home_cc not in buildings and not self.orphaned:
            self.orphaned = True
            self.mining_timer = 0 # Ngừng đào ngay lập tức
            
            # Quét xem có quái không
            if enemies:
                self.state = 'KAMIKAZE'
                self.target_enemy = min(enemies, key=lambda e: abs(e.col - self.col) + abs(e.row - self.row)) # thuật 
                self.repath_timer = 0
            else:
                self.state = 'ORPHANED_RETURNING'
                if buildings:
                    self.home_cc = min(buildings, key=lambda b: abs(b.col - self.col) + abs(b.row - self.row)) # thuật 
                    buildings_pos = [(b.col, b.row) for b in buildings]
                    self.path = a_star((self.col, self.row), (self.home_cc.col, self.home_cc.row), grid, buildings_pos, ignore_buildings=True)
                    self.path_index = 0
                else:
                    self.active = False # Hết nhà hết quái biến mất
                    return

        #Hiệu ứng đổi màu tức giận
        if self.orphaned:
            self.current_color[1] = max(140, self.current_color[1] - 4) # Giảm Green
            self.current_color[2] = max(0, self.current_color[2] - 8)   # Giảm Blue

        # KAMIKAZE
        if self.state == 'KAMIKAZE':
            # Nếu quái bị trụ bắn chết trước, reset lại cờ để vòng lặp sau tự quét mục tiêu mới
            if self.target_enemy not in enemies or self.target_enemy.hp <= 0:
                self.orphaned = False 
                return
            
            #cập nhật A* vì quái thường xuyên di chuyển
            self.repath_timer -= 1
            if self.repath_timer <= 0 or not self.path:
                buildings_pos = [(b.col, b.row) for b in buildings]
                self.path = a_star((self.col, self.row), (self.target_enemy.col, self.target_enemy.row), grid, buildings_pos, ignore_buildings=True)
                self.path_index = 0
                self.repath_timer = 15

            # Kiểm tra va chạm với quái
            dist_to_enemy = ((self.pixel_x - self.target_enemy.pixel_x)**2 + (self.pixel_y - self.target_enemy.pixel_y)**2)**0.5
            if dist_to_enemy <= TILE_SIZE: # Ở sát bên
                self.target_enemy.hp -= 15 # Dmg nổ khổng lồ (quái có 10 hp)
                self.active = False        # Lính hi sinh
                # print("Lính khai thác vừa kích nổ Cảm tử!")
                return

        if self.path and self.path_index < len(self.path):
            target_col, target_row = self.path[self.path_index]
            target_x = target_col * TILE_SIZE + TILE_SIZE // 2
            target_y = target_row * TILE_SIZE + TILE_SIZE // 2

            # Tính tốc độ gốc theo trạng thái (Cảm tử hoặc Đang mang vác)
            if self.state == 'KAMIKAZE':
                current_speed = self.base_speed * 1.5
                self.carrying_amount = 0 # Vứt đồ
            else:
                speed_penalty = 1.0 - (0.05 * self.carrying_amount)
                current_speed = self.base_speed * speed_penalty
            
            # cập nhật tốc độ dựa trên địa hình
            current_terrain = grid[int(self.pixel_y // TILE_SIZE)][int(self.pixel_x // TILE_SIZE)]
            
            if current_terrain == 1:       # Nước
                current_speed *= 0.5       # Bị chậm 50%
            elif current_terrain in (2, 3): # Đường bộ (2) hoặc Cầu gỗ (3)
                current_speed *= 1.3       # Được buff thêm 30% tốc độ!

            dx, dy = target_x - self.pixel_x, target_y - self.pixel_y
            dist = (dx**2 + dy**2)**0.5

            if dist < current_speed:
                self.pixel_x, self.pixel_y = target_x, target_y
                self.path_index += 1
            else:
                self.pixel_x += (dx / dist) * current_speed
                self.pixel_y += (dy / dist) * current_speed
        else:
            # đến đích
            if self.state == 'ORPHANED_RETURNING':
                if self.carrying_amount > 0 and self.home_cc in buildings:
                    self.home_cc.inventory[self.carrying_type] += self.carrying_amount
                self.active = False
                return

            buildings_pos = [(b.col, b.row) for b in buildings]
            if self.state == 'MOVING_TO_RESOURCE':
                self.state = 'MINING'
                self.mining_timer = 60 
            elif self.state == 'RETURNING':
                self.home_cc.inventory[self.carrying_type] += self.carrying_amount
                self.carrying_amount = 0
                
                # Kiểm tra xem mỏ còn hàng không trước khi quay lại
                if self.target_res.amount <= 0:
                    self.active = False # Nghỉ hưu vì mỏ đã cạn
                    self.home_cc.active_workers -= 1
                    return
                
                self.state = 'MOVING_TO_RESOURCE'
                # đi đào bằng A*
                self.path = a_star((self.home_cc.col, self.home_cc.row), (self.target_res.col, self.target_res.row), grid, buildings_pos, ignore_buildings=True)
                self.path_index = 0
        # trạng thái đào
        if self.state == 'MINING' and not self.orphaned:
            self.mining_timer -= 1
            if self.mining_timer <= 0:
                # Kiểm tra xem mỏ còn bao nhiêu, lấy số nhỏ hơn giữa (sức chứa) và (lượng còn lại)
                actual_mined = min(self.max_carrying, self.target_res.amount)
                
                self.carrying_amount = actual_mined
                self.target_res.amount -= actual_mined
                
                self.state = 'RETURNING'
                buildings_pos = [(b.col, b.row) for b in buildings]
                self.path = a_star((self.target_res.col, self.target_res.row), (self.home_cc.col, self.home_cc.row), grid, buildings_pos, ignore_buildings=True)
                self.path_index = 0

    def draw(self, surface):
        """Hàm vẽ các quân lính lao động"""
        # Vẽ màu động (sẽ tự động từ Trắng -> Cam)
        pygame.draw.circle(surface, tuple(self.current_color), (int(self.pixel_x), int(self.pixel_y)), TILE_SIZE // 3)
        if self.carrying_amount > 0 and self.state != 'KAMIKAZE':
            pygame.draw.circle(surface, COLORS[self.carrying_type], (int(self.pixel_x), int(self.pixel_y)), TILE_SIZE // 6)

class TransportConvoy:
    """
    Lớp đại diện cho Đoàn xe vận chuyển tài nguyên giữa các Thành trì.
    """
    def __init__(self, source_cc, dest_cc, payload, path):
        """Thiết lập thông số mặc định cho các đối tượng là lính vận chuyển tài nguyên"""
        self.source_cc, self.dest_cc, self.payload = source_cc, dest_cc, payload
        self.path = path
        self.path_index = 0
        self.state = 'DELIVERING' 
        self.pixel_x = source_cc.col * TILE_SIZE + TILE_SIZE // 2
        self.pixel_y = source_cc.row * TILE_SIZE + TILE_SIZE // 2
        self.speed = 2.5
        self.angle = 0 

    def update(self, grid, buildings_pos):
        """
        Cập nhật vị trí của đoàn xe dựa trên đường đi A* và tốc độ theo địa hình.
        Khi đến nơi sẽ chuyển tài nguyên vào kho đích và quay về.
        """
        self.angle += 0.1 
        if self.path_index < len(self.path):
            target_col, target_row = self.path[self.path_index]
            target_x = target_col * TILE_SIZE + TILE_SIZE // 2
            target_y = target_row * TILE_SIZE + TILE_SIZE // 2

            # logic tốc độ dựa trên địa hình
            current_terrain = grid[int(self.pixel_y // TILE_SIZE)][int(self.pixel_x // TILE_SIZE)]
            
            if current_terrain == 1:       # Nước
                current_speed = self.speed * 0.5
            elif current_terrain in (2, 3): # Đường bộ (2) hoặc Cầu gỗ (3)
                current_speed = self.speed * 1.3
            else:                          # Đất cỏ bình thường (0)
                current_speed = self.speed

            dx, dy = target_x - self.pixel_x, target_y - self.pixel_y
            dist = (dx**2 + dy**2)**0.5

            if dist < current_speed:
                self.pixel_x, self.pixel_y = target_x, target_y
                self.path_index += 1
            else:
                self.pixel_x += (dx / dist) * current_speed
                self.pixel_y += (dy / dist) * current_speed
        else:
            if self.state == 'DELIVERING':
                for res, amount in self.payload.items():
                    self.dest_cc.inventory[res] += amount
                self.payload = {'wood': 0, 'stone': 0, 'coal': 0}
                self.state = 'RETURNING'
                self.path = a_star((self.dest_cc.col, self.dest_cc.row), (self.source_cc.col, self.source_cc.row), grid, buildings_pos, ignore_buildings=True)
                self.path_index = 0
            elif self.state == 'RETURNING':
                self.state = 'DONE'


    def draw(self, surface):
        """
        Hàm vẽ quân lính vận chuyển
        """
        if self.state == 'DELIVERING':
            rect = pygame.Rect(self.pixel_x - 8, self.pixel_y - 8, 16, 16)
            pygame.draw.rect(surface, (255, 255, 0), rect)
        
        for i in range(3):
            offset_angle = self.angle + i * (2 * math.pi / 3)
            cx = self.pixel_x + math.cos(offset_angle) * 15
            cy = self.pixel_y + math.sin(offset_angle) * 15
            pygame.draw.circle(surface, (255, 255, 255), (int(cx), int(cy)), 4)

class Enemy:
    """
    Lớp đại diện cho Quái vật. Có khả năng tự tìm đường đến Thành trì gần nhất và phá hủy tường rào.
    """
    def __init__(self, col, row, phase=1, is_purple=False): 
        """Hàm khởi tạo cho các đối tượng là quái vật với các thông số cơ  bản"""
        self.col, self.row = col, row
        self.pixel_x = col * TILE_SIZE + TILE_SIZE // 2
        self.pixel_y = row * TILE_SIZE + TILE_SIZE // 2
        self.is_purple = is_purple
        
        base_hp = 10 + (phase - 1) * 5 
        base_speed = 1.0 + (phase - 1) * 0.15 
        base_dmg = 1 + (phase - 1) * 1  
        
        # quái tím mạnh hơn
        if self.is_purple:
            self.max_hp = int(base_hp * 1.5)
            self.speed = base_speed * 1.5
            self.damage = int(base_dmg * 1.5)
        else:
            self.max_hp = base_hp
            self.speed = base_speed
            self.damage = base_dmg
            
        self.hp = self.max_hp
        self.path = []
        self.path_index = 0
        self.attack_timer = 0
        self.repath_timer = 0

    def update(self, grid, target_cc, buildings_pos, walls):
        """
        Cập nhật logic của quái vật: Tìm đường bằng A*, di chuyển, tấn công Tường chặn đường và tấn công Thành trì.
        """
        self.col = int(self.pixel_x // TILE_SIZE)
        self.row = int(self.pixel_y // TILE_SIZE)
        
        dist_cols = abs(self.col - target_cc.col)
        dist_rows = abs(self.row - target_cc.row)
        
        if dist_cols <= 1 and dist_rows <= 1:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                target_cc.hp -= self.damage 
                self.attack_timer = 60
        else:
            self.repath_timer -= 1
            if self.repath_timer <= 0 or not self.path:
                self.path = a_star((self.col, self.row), (target_cc.col, target_cc.row), grid, buildings_pos, ignore_buildings=False, is_enemy=True)
                self.path_index = 0
                self.repath_timer = 30
                    
            if self.path and self.path_index < len(self.path):
                t_col, t_row = self.path[self.path_index]
                blocking_wall = next((w for w in walls if w.col == t_col and w.row == t_row), None)
                
                if blocking_wall:
                    # Nếu có tường, chuyển sang chế độ tấn công
                    self.attack_timer -= 1
                    if self.attack_timer <= 0:
                        blocking_wall.hp -= self.damage 
                        self.attack_timer = 60
                    return 

                target_x = t_col * TILE_SIZE + TILE_SIZE // 2
                target_y = t_row * TILE_SIZE + TILE_SIZE // 2

                current_terrain = grid[int(self.pixel_y // TILE_SIZE)][int(self.pixel_x // TILE_SIZE)]
                if current_terrain == 1:
                    current_speed = self.speed * 0.5 
                else:
                    current_speed = self.speed

                dx, dy = target_x - self.pixel_x, target_y - self.pixel_y
                dist = (dx**2 + dy**2)**0.5

                if dist < current_speed:
                    self.pixel_x, self.pixel_y = target_x, target_y
                    self.path_index += 1
                else:
                    self.pixel_x += (dx / dist) * current_speed
                    self.pixel_y += (dy / dist) * current_speed
    def draw(self, surface):
        """màu cho 2 loại quái"""
        color = (150, 0, 255) if self.is_purple else (200, 0, 0)
        pygame.draw.circle(surface, color, (int(self.pixel_x), int(self.pixel_y)), TILE_SIZE // 2 - 2)
        pygame.draw.rect(surface, (255, 0, 0), (self.pixel_x - 10, self.pixel_y - 15, 20, 3))
        pygame.draw.rect(surface, (0, 255, 0), (self.pixel_x - 10, self.pixel_y - 15, 20 * (self.hp / self.max_hp), 3))

class HomingProjectile:
    """
    Lớp đại diện cho Đạn tự động bám theo mục tiêu (Quái vật) do Thành trì bắn ra.
    """
    frames = []

    def __init__(self, x, y, target):
        """khởi tạo cho đòn tấn công của thành"""
        self.x = x
        self.y = y
        self.target = target
        self.speed = 4.0
        self.damage = 1
        self.active = True
        
        self.current_frame = 0
        self.anim_timer = 0
        self.anim_speed = 5
        if not HomingProjectile.frames:
            try:
                import os
                base_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Đọc 2 file ảnh
                img1 = pygame.image.load(os.path.join(base_dir, "assets", 'commandcenter_Attack1.png')).convert_alpha()
                img2 = pygame.image.load(os.path.join(base_dir, "assets", 'commandcenter_Attack2.png')).convert_alpha()
                img1 = pygame.transform.scale(img1, (20, 20))
                img2 = pygame.transform.scale(img2, (20, 20))
                
                HomingProjectile.frames = [img1, img2]
            except Exception as e:
                print(f"Khong load duoc anh dan: {e}")
                HomingProjectile.frames = [None, None]

    def update(self):
        """
        Cập nhật hướng bay của viên đạn đến mục tiêu và xử lý sát thương khi chạm đích.
        Chuyển đổi các khung hình (frames) để tạo hoạt ảnh.
        """
        if not self.active: return
        
        # Kiểm tra xem quái mục tiêu còn sống không
        if self.target.hp <= 0 or not getattr(self.target, 'active', True):
            self.active = False
            return

        # Tính toán góc bay tới mục tiêu
        dx = self.target.pixel_x - self.x
        dy = self.target.pixel_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist < self.speed:
            self.target.hp -= self.damage
            self.active = False
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        self.anim_timer += 1
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            # Công thức đổi qua lại giữa số 0 và 1 cực kỳ nhanh
            self.current_frame = 1 - self.current_frame 

    def draw(self, surface):
        """Vẽ hình ảnh tấn công"""
        # Nếu đã load ảnh thành công thì vẽ ảnh
        if HomingProjectile.frames and HomingProjectile.frames[self.current_frame] is not None:
            img = HomingProjectile.frames[self.current_frame]
            rect = img.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(img, rect)
        else:
            pygame.draw.circle(surface, (0, 255, 255), (int(self.x), int(self.y)), 5)

class Wall:
    """
    Lớp đại diện cho Tường phòng thủ do người chơi xây dựng.
    """
    loaded_images = {}

    def __init__(self, col, row, home_cc):
        """Khởi tạo các giá trị mặc định cho mỗi công trình là tường"""
        self.col, self.row = col, row
        self.home_cc = home_cc 
        self.hp = 5
        self.max_hp = 5
        self.rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        
        self.is_vertical = False

        if 'wall_h' not in Wall.loaded_images:
            try:
                import os
                base_dir = os.path.dirname(os.path.abspath(__file__))
                img_path = os.path.join(base_dir, "wall.png")
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                
                Wall.loaded_images['wall_h'] = img
                # Tự động lật ảnh 90 độ để làm tường dọc
                Wall.loaded_images['wall_v'] = pygame.transform.rotate(img, 90)
            except Exception as e:
                print(f"Khong tim thay file wall.png: {e}")
                Wall.loaded_images['wall_h'] = None
                Wall.loaded_images['wall_v'] = None

    def repair(self):
        if self.home_cc.inventory['wood'] >= 1 and self.hp < self.max_hp:
            self.home_cc.inventory['wood'] -= 1
            self.hp = min(self.max_hp, self.hp + 3)
            return True
        return False

    def draw(self, surface):
        """
            Vẽ hình ảnh của tường
        """
        # Chọn ảnh dọc hoặc ngang tùy vào vị trí
        img_key = 'wall_v' if self.is_vertical else 'wall_h'
        img = Wall.loaded_images.get(img_key)
        
        if img is not None:
            surface.blit(img, self.rect)
        else:
            pygame.draw.rect(surface, (139, 69, 19), self.rect) 
            pygame.draw.rect(surface, (100, 50, 10), self.rect, 2)
            
        if self.hp < self.max_hp:
            health_bar_width = (self.hp / self.max_hp) * (TILE_SIZE - 4)
            pygame.draw.rect(surface, (255, 0, 0), (self.rect.x + 2, self.rect.y + 2, TILE_SIZE - 4, 4))
            pygame.draw.rect(surface, (0, 255, 0), (self.rect.x + 2, self.rect.y + 2, health_bar_width, 4))

class Soldier:
    """
    Lớp đại diện cho Lính bảo vệ sinh ra từ Doanh trại. 
    Tự động tuần tra và tiêu diệt quái vật.
    """
    def __init__(self, home_barracks, path=None, phase=1):
        self.home_barracks = home_barracks
        self.pixel_x = home_barracks.col * TILE_SIZE + TILE_SIZE // 2
        self.pixel_y = home_barracks.row * TILE_SIZE + TILE_SIZE // 2
        self.col, self.row = home_barracks.col, home_barracks.row
        self.path = path
        self.path_index = 0
        enemy_speed = 1.0 + (phase - 1) * 0.15
        self.speed = enemy_speed * 1.5
        
        self.hp = 5       
        self.max_hp = 5
        self.state = 'IDLE' 
        self.target_enemy = None
        self.active = True

    def update(self, grid, enemies, buildings_pos):
        """Hàm cập nhật liên tục với các hành vi của quân lính (huiting, returning)"""
        if not self.active: return
        self.col = int(self.pixel_x // TILE_SIZE)
        self.row = int(self.pixel_y // TILE_SIZE)

        if not self.home_barracks.active:
            self.active = False
            return

        if self.state == 'IDLE':
            targets = [e for e in enemies if abs(e.col - self.home_barracks.col) <= 7 and abs(e.row - self.home_barracks.row) <= 7]
            if targets:
                self.target_enemy = min(targets, key=lambda e: abs(e.col - self.col) + abs(e.row - self.row))
                self.state = 'HUNTING'

        elif self.state == 'HUNTING':
            # check Quái cũ bị chết HOẶC chạy ra khỏi vùng 15x15
            if not self.target_enemy or self.target_enemy.hp <= 0 or \
               abs(self.target_enemy.col - self.home_barracks.col) > 7 or \
               abs(self.target_enemy.row - self.home_barracks.row) > 7:
                # kiểm tra trước khi quay lại
                targets = [e for e in enemies if abs(e.col - self.home_barracks.col) <= 7 and abs(e.row - self.home_barracks.row) <= 7]
                
                if targets:
                    # Nếu còn, target ngay con gần lính nhất và tiếp tục đi săn
                    self.target_enemy = min(targets, key=lambda e: abs(e.col - self.col) + abs(e.row - self.row))
                else:
                    # Nếu dọn dẹp sạch sẽ rồi mới đi về
                    self.state = 'RETURNING'
                    self.path = a_star((self.col, self.row), (self.home_barracks.col, self.home_barracks.row), grid, buildings_pos, ignore_buildings=True)
                    self.path_index = 0
                    return

            dx = self.target_enemy.pixel_x - self.pixel_x
            dy = self.target_enemy.pixel_y - self.pixel_y
            dist = (dx**2 + dy**2)**0.5
            
            if dist <= TILE_SIZE: 
                self.target_enemy.hp -= 2
                self.hp -= 1
                if self.hp <= 0: self.active = False
            else:
                if pygame.time.get_ticks() % 500 < 20: 
                    self.path = a_star((self.col, self.row), (self.target_enemy.col, self.target_enemy.row), grid, buildings_pos, ignore_buildings=True)
                    self.path_index = 0
                
                if self.path and self.path_index < len(self.path):
                    t_col, t_row = self.path[self.path_index]
                    target_x = t_col * TILE_SIZE + TILE_SIZE // 2
                    target_y = t_row * TILE_SIZE + TILE_SIZE // 2
                    step_dx, step_dy = target_x - self.pixel_x, target_y - self.pixel_y
                    step_dist = (step_dx**2 + step_dy**2)**0.5
                    if step_dist < self.speed: self.path_index += 1
                    else:
                        self.pixel_x += (step_dx/step_dist)*self.speed
                        self.pixel_y += (step_dy/step_dist)*self.speed

        elif self.state == 'RETURNING':
            if self.path and self.path_index < len(self.path):
                t_col, t_row = self.path[self.path_index]
                target_x = t_col * TILE_SIZE + TILE_SIZE // 2
                target_y = t_row * TILE_SIZE + TILE_SIZE // 2
                dx, dy = target_x - self.pixel_x, target_y - self.pixel_y
                dist = (dx**2 + dy**2)**0.5
                if dist < self.speed: self.path_index += 1
                else:
                    self.pixel_x += (dx/dist)*self.speed
                    self.pixel_y += (dy/dist)*self.speed
            else:
                self.state = 'IDLE'
                self.hp = self.max_hp 

    def draw(self, surface):
        """Vẽ quân lính"""
        pygame.draw.circle(surface, (50, 200, 50), (int(self.pixel_x), int(self.pixel_y)), TILE_SIZE // 3)


class Barracks:
    """
    Lớp đại diện cho Doanh trại lính.
    Sản sinh Lính bảo vệ theo thời gian và duy trì vùng an toàn tuần tra.
    """
    def __init__(self, col, row, home_cc):
        """
            Khởi tạo các giá trị mặc định cho mỗi công trình là doanh trại
        """
        self.col, self.row = col, row
        self.home_cc = home_cc 
        self.hp = 5
        self.max_hp = 5
        self.rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.active = True
        
        # Quản lý danh sách 5 lính và thời gian sinh lính nhanh hơn
        self.spawn_timer = 120 # Cứ 3 giây sinh 1 lính (60 fps * 2)
        self.spawned_soldiers = [] 

    def draw(self, surface):
        """
            Hàm dùng để vẽ thanh máu cho doanh trại
        """
        pygame.draw.rect(surface, (34, 139, 34), self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, (255, 0, 0), (self.rect.x, self.rect.y - 5, TILE_SIZE, 3))
        pygame.draw.rect(surface, (0, 255, 0), (self.rect.x, self.rect.y - 5, TILE_SIZE * hp_ratio, 3))

    def repair(self):
        """
            Hàm xủ lí hành vi sửa chữa cho doanh trại
        """
        if self.home_cc.inventory['wood'] >= 1 and self.hp < self.max_hp:
            self.home_cc.inventory['wood'] -= 1
            self.hp = min(self.max_hp, self.hp + 3)
            return True
        return False
    
# class SecretBlock:
#     loaded_image = None
    
#     def __init__(self, pixel_x, pixel_y):
#         self.x = pixel_x
#         self.y = -50 # Rơi từ mép trên
#         self.target_y = pixel_y
#         self.rect = pygame.Rect(self.x, self.y, 30, 30)
#         self.landed = False

#         if SecretBlock.loaded_image is None:
#             try:
#                 import os
#                 base_dir = os.path.dirname(os.path.abspath(__file__))
#                 img_path = os.path.join(base_dir, "serect.png")
#                 img = pygame.image.load(img_path).convert_alpha()
#                 SecretBlock.loaded_image = pygame.transform.scale(img, (30, 30))
#             except Exception as e:
#                 print("Khong tim thay serect.png, dung block vang-den.")
#                 SecretBlock.loaded_image = False # Dùng False để đánh dấu là vẽ thủ công

#     def update(self):
#         if self.y < self.target_y:
#             self.y += 4
#             self.rect.y = int(self.y)
#         else:
#             self.landed = True

#     def draw(self, surface):
#         if SecretBlock.loaded_image:
#             surface.blit(SecretBlock.loaded_image, self.rect)
#         else:
#             pygame.draw.rect(surface, (255, 215, 0), self.rect)
#             pygame.draw.line(surface, (0, 0, 0), (self.rect.left, self.rect.top), (self.rect.right, self.rect.bottom), 4)
#             pygame.draw.line(surface, (0, 0, 0), (self.rect.right, self.rect.top), (self.rect.left, self.rect.bottom), 4)
#             pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)