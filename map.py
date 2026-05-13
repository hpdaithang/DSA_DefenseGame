import pygame
import random
from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, COLORS

class GameMap:
    def __init__(self):
        # 0: Cỏ, 1: Nước, 2: Đường đất (trên cỏ), 3: Cầu ván gỗ (trên nước)
        self.grid = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        
        # Lưới random cho đường đất (4 mảnh)
        self.road_random_grid = [[random.randint(0, 3) for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        # Lưới random để xoay Cầu ván gỗ (0: Dọc, 1: Ngang)
        self.bridge_orient_grid = [[random.randint(0, 1) for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        
        self.has_grass_graphics = False
        self.has_road_graphics = False
        self.has_bridge_graphics = False
        self.has_water_graphics = False

        self.setup_environment()
        self.load_graphics()

    def load_graphics(self):
        """
            Tải hình ảnh cho các yếu tố môi trường 
        """
        try:
            sheet = pygame.image.load(r"TryToSurvive/assets/grass.png").convert_alpha()
            sheet_w, sheet_h = sheet.get_size()
            self.full_grass_tile = pygame.transform.scale(sheet, (TILE_SIZE, TILE_SIZE))
            cell_w, cell_h = sheet_w // 3, sheet_h // 3

            self.grass_tiles = [[None for _ in range(3)] for _ in range(3)]
            for r in range(3):
                for c in range(3):
                    surf = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
                    surf.blit(sheet, (0, 0), (c * cell_w, r * cell_h, cell_w, cell_h))
                    self.grass_tiles[r][c] = pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE))
            self.has_grass_graphics = True
        except Exception: pass

        try:
            road_sheet = pygame.image.load(r"TryToSurvive/assets/road.png").convert_alpha()
            rw, rh = road_sheet.get_size()
            cell_w, cell_h = rw // 2, rh // 2
            
            self.road_tiles = []
            for r in range(2):
                for c in range(2):
                    surf = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
                    surf.blit(road_sheet, (0, 0), (c * cell_w, r * cell_h, cell_w, cell_h))
                    self.road_tiles.append(pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE)))
            self.has_road_graphics = True
        except Exception: pass

        try:
            bridge_img = pygame.image.load(r"TryToSurvive/assets/road_water.png").convert_alpha()
            
            self.bridge_v_tile = pygame.transform.scale(bridge_img, (TILE_SIZE, TILE_SIZE))
            
            self.bridge_h_tile = pygame.transform.rotate(self.bridge_v_tile, 90)
            
            self.has_bridge_graphics = True
        except Exception as e: 
            print(f"Chưa tải được ván gỗ road_water.png: {e}")

        try:
            sheet = pygame.image.load(r"TryToSurvive/assets/water.png").convert_alpha()
            sheet_w, sheet_h = sheet.get_size()
            cell_w, cell_h = sheet_w // 3, sheet_h // 3 
            
            surf = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), (1 * cell_w, 1 * cell_h, cell_w, cell_h))
            self.water_base_tile = pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE))
            self.has_water_graphics = True
        except Exception: pass

    def setup_environment(self):
        """
        Sử dụng thuật toán ngẫu nhiên để tạo các hồ nước (Water) trên bề mặt lưới.
        """
        num_lakes = random.randint(7,15)
        for _ in range(num_lakes):
            start_c = random.randint(2, MAP_WIDTH - 3)
            start_r = random.randint(2, MAP_HEIGHT - 3)
            lake_size = random.randint(40, 80) 
            
            r, c = start_r, start_c
            for _ in range(lake_size):
                if 0 <= r < MAP_HEIGHT and 0 <= c < MAP_WIDTH:
                    self.grid[r][c] = 1 
                direction = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                r += direction[0]
                c += direction[1]

    def get_grass_texture(self, r, c):
        def is_land(row, col):
            if 0 <= row < MAP_HEIGHT and 0 <= col < MAP_WIDTH:
                return self.grid[row][col] == 0 
            return True 

        top, bottom = is_land(r - 1, c), is_land(r + 1, c)
        left, right = is_land(r, c - 1), is_land(r, c + 1)

        if (not top and not bottom) or (not left and not right):
            return self.full_grass_tile

        tex_r = 1 if (top and bottom) else (2 if top else (0 if bottom else 1))
        tex_c = 1 if (left and right) else (2 if left else (0 if right else 1))
        return self.grass_tiles[tex_r][tex_c]

    def draw(self, surface):
        """
        Vẽ toàn bộ lưới địa hình lên màn hình theo các lớp (layer): Đáy (Nước) -> Lót nền -> Đường/Cầu -> Đỉnh (Cỏ bo viền).
        """
        for r in range(MAP_HEIGHT):
            for c in range(MAP_WIDTH):
                terrain_val = self.grid[r][c]
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                if terrain_val == 1 or terrain_val == 3:
                    if self.has_water_graphics:
                        surface.blit(self.water_base_tile, (c * TILE_SIZE, r * TILE_SIZE))
                    else:
                        pygame.draw.rect(surface, COLORS['water'], rect)
                
                if terrain_val == 0 or terrain_val == 2:
                    is_near_water = False
                    for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < MAP_HEIGHT and 0 <= nc < MAP_WIDTH and self.grid[nr][nc] == 1:
                            is_near_water = True
                            break
                    if is_near_water and self.has_grass_graphics:
                        surface.blit(self.grass_tiles[1][1], (c * TILE_SIZE, r * TILE_SIZE))
                    elif not is_near_water:
                        pygame.draw.rect(surface, COLORS['grass'], rect)

                if terrain_val == 2:
                    if self.has_road_graphics:
                        random_index = self.road_random_grid[r][c]
                        surface.blit(self.road_tiles[random_index], (c * TILE_SIZE, r * TILE_SIZE))
                    else:
                        pygame.draw.rect(surface, COLORS['road_grass'], rect)

                if terrain_val == 3:
                    if self.has_bridge_graphics:
                        is_vertical = self.bridge_orient_grid[r][c] == 0
                        bridge_img = self.bridge_v_tile if is_vertical else self.bridge_h_tile
                        surface.blit(bridge_img, (c * TILE_SIZE, r * TILE_SIZE))
                    else:
                        pygame.draw.rect(surface, COLORS['road_water'], rect)

                if terrain_val == 0:
                    if self.has_grass_graphics:
                        surface.blit(self.get_grass_texture(r, c), (c * TILE_SIZE, r * TILE_SIZE))