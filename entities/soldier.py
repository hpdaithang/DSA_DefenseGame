import pygame
import time
import random
from core.pathfinding import bfs


class Soldier:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.hp = 5
        self.damage = 1
        self.alive = True

        self.move_delay = 0.3
        self.last_move = time.time()

        self.attack_delay = 1.0
        self.last_attack = time.time()

        self.path = []
        self.path_index = 0
        self.repath_delay = 1.0
        self.last_repath = time.time()

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False

    def find_path(self, grid, target):
        start = (self.x, self.y)
        goal = (target.x, target.y)

        self.path = bfs(grid, start, goal)
        self.path_index = 0

    def attack(self, enemy):
        now = time.time()
        if now - self.last_attack >= self.attack_delay:
            enemy.take_damage(self.damage)
            self.last_attack = now

    def update(self, grid, enemies):
        if not enemies:
            return

        now = time.time()

        target = min(enemies, key=lambda e: abs(e.x - self.x) + abs(e.y - self.y))
        distance = abs(target.x - self.x) + abs(target.y - self.y)

        if distance == 1:
            self.attack(target)
            return

        if now - self.last_repath >= self.repath_delay:
            self.find_path(grid, target)
            self.last_repath = now

        # MOVE
        if self.path and self.path_index < len(self.path):
            next_pos = self.path[self.path_index]

            if next_pos == (self.x, self.y):
                self.path_index += 1
                return

            if grid.is_inside(*next_pos):

                if grid.is_empty(*next_pos):
                    if now - self.last_move >= self.move_delay:
                        self.x, self.y = next_pos
                        self.path_index += 1
                        self.last_move = now
                        return
                else:
                    self.find_path(grid, target)
                    return

        # FALLBACK: đi random (KHÔNG phá building)
        dirs = [(1,0), (-1,0), (0,1), (0,-1)]
        random.shuffle(dirs)

        for dx, dy in dirs:
            nx, ny = self.x + dx, self.y + dy

            if grid.is_inside(nx, ny) and grid.is_empty(nx, ny):
                if now - self.last_move >= self.move_delay:
                    self.x, self.y = nx, ny
                    self.last_move = now
                    return

        # FALLBACK 2: đi random (KHÔNG BAO GIỜ đứng im)
        dirs = [(1,0), (-1,0), (0,1), (0,-1)]
        random.shuffle(dirs)

        for dx, dy in dirs:
            nx, ny = self.x + dx, self.y + dy

            if grid.is_inside(nx, ny) and grid.is_empty(nx, ny):
                if now - self.last_move >= self.move_delay:
                    self.x, self.y = nx, ny
                    self.last_move = now
                    return


    def draw(self, screen, cell_size):
        rect = pygame.Rect(
            self.x * cell_size,
            self.y * cell_size,
            cell_size,
            cell_size
        )
        pygame.draw.rect(screen, (255, 165, 0), rect) # màu

        hp_ratio = self.hp / 5
        hp_width = int(cell_size * hp_ratio)

        hp_rect = pygame.Rect(
            self.x * cell_size,
            self.y * cell_size,
            hp_width,
            4
        )
        pygame.draw.rect(screen, (0, 255, 0), hp_rect)