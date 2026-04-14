import pygame
import random
import time
from core.pathfinding import bfs


class Enemy:
    def __init__(self, grid_size):
        self.x, self.y = self.spawn_edge(grid_size)

        self.hp = 5
        self.damage = 1
        self.alive = True

        # ===== MOVE =====
        self.move_delay = 0.3
        self.last_move = time.time()

        # ===== ATTACK =====
        self.attack_delay = 1.0
        self.last_attack = time.time()

        # ===== PATH =====
        self.path = []
        self.path_index = 0

        self.repath_delay = 1.0
        self.last_repath = time.time()

    # =========================
    # SPAWN
    # =========================
    def spawn_edge(self, size):
        side = random.choice(["top", "bottom", "left", "right"])

        if side == "top":
            return random.randint(0, size - 1), 0
        elif side == "bottom":
            return random.randint(0, size - 1), size - 1
        elif side == "left":
            return 0, random.randint(0, size - 1)
        else:
            return size - 1, random.randint(0, size - 1)

    # =========================
    # TARGET PRIORITY
    # =========================
    def choose_target(self, buildings):
        hqs = [b for b in buildings if b.__class__.__name__ == "HQ"]
        farms = [b for b in buildings if b.__class__.__name__ == "Farm"]
        walls = [b for b in buildings if b.__class__.__name__ == "Building"]

        if hqs:
            return min(hqs, key=lambda b: abs(b.x - self.x) + abs(b.y - self.y))

        if farms:
            return min(farms, key=lambda b: abs(b.x - self.x) + abs(b.y - self.y))

        if walls:
            return min(walls, key=lambda b: abs(b.x - self.x) + abs(b.y - self.y))

        return None

    # =========================
    # PATH
    # =========================
    def find_path(self, grid, target):
        start = (self.x, self.y)

        # 🎯 tìm các ô xung quanh target
        goals = [
            (target.x + 1, target.y),
            (target.x - 1, target.y),
            (target.x, target.y + 1),
            (target.x, target.y - 1),
        ]

        valid_goals = []

        for gx, gy in goals:
            if grid.is_inside(gx, gy) and grid.is_empty(gx, gy):
                valid_goals.append((gx, gy))

        # nếu không có ô trống xung quanh -> vẫn phải xử lý
        if not valid_goals:
            self.path = []
            return

        # chọn goal gần nhất
        best_path = []
        shortest = float("inf")

        for g in valid_goals:
            path = bfs(grid, start, g)

            if path and len(path) < shortest:
                best_path = path
                shortest = len(path)

        self.path = best_path
        self.path_index = 0
    # =========================
    # ATTACK
    # =========================
    def attack(self, building):
        now = time.time()

        if now - self.last_attack >= self.attack_delay:
            building.take_damage(self.damage)
            self.last_attack = now

    # =========================
    # UPDATE
    # =========================
    def update(self, grid, buildings):
        if not buildings:
            return

        now = time.time()

        # chọn target
        target = self.choose_target(buildings)
        if not target:
            return

        # ===== REPATH =====
        if now - self.last_repath >= self.repath_delay:
            self.find_path(grid, target)
            self.last_repath = now

        # ===== ATTACK nếu đứng cạnh =====
        distance = abs(target.x - self.x) + abs(target.y - self.y)

        if distance == 1:
            self.attack(target)
            return

        # ===== MOVE =====

       
        if not self.path:
            # không có đường -> phá vật cản gần nhất
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                nx, ny = self.x + dx, self.y + dy

                if grid.is_inside(nx, ny) and not grid.is_empty(nx, ny):
                    block = grid.get(nx, ny)
                    self.attack(block)
                    return

            return
        if self.path_index >= len(self.path):
            return

        next_pos = self.path[self.path_index]

        # skip vị trí hiện tại
        if next_pos == (self.x, self.y):
            self.path_index += 1
            return

        if not grid.is_inside(next_pos[0], next_pos[1]):
            return

        # ===== BLOCK LOGIC =====
        if not grid.is_empty(next_pos[0], next_pos[1]):

            block = grid.get(next_pos[0], next_pos[1])

            # nếu target là HQ -> phá tường
            if target.__class__.__name__ == "HQ":
                self.attack(block)
            else:
                self.find_path(grid, target)

            return

        # ===== MOVE =====
        if now - self.last_move >= self.move_delay:
            self.x, self.y = next_pos
            self.path_index += 1
            self.last_move = now

    # =========================
    # DAMAGE
    # =========================
    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False

    # =========================
    # DRAW
    # =========================
    def draw(self, screen, cell_size):
        rect = pygame.Rect(
            self.x * cell_size,
            self.y * cell_size,
            cell_size,
            cell_size
        )
        pygame.draw.rect(screen, (200, 0, 0), rect)

        # HP bar
        hp_ratio = self.hp / 5
        hp_width = int(cell_size * hp_ratio)

        hp_rect = pygame.Rect(
            self.x * cell_size,
            self.y * cell_size,
            hp_width,
            4
        )
        pygame.draw.rect(screen, (0, 255, 0), hp_rect)