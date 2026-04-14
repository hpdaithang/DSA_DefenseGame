from entities.building import Building
from entities.soldier import Soldier
import time


class Barracks(Building):
    def __init__(self, x, y):
        super().__init__(x, y, (0, 100, 0), hp=10) # đặt màu

        self.soldiers = []
        self.max_soldiers = 5

        self.spawn_delay = 3
        self.last_spawn = time.time()

    def spawn(self):
        if len(self.soldiers) >= self.max_soldiers:
            return

        now = time.time()
        if now - self.last_spawn >= self.spawn_delay:
            s = Soldier(self.x, self.y)
            self.soldiers.append(s)
            self.last_spawn = now

    def update(self, grid, enemies):
        self.spawn()

        for s in self.soldiers:
            s.update(grid, enemies)

        self.soldiers = [s for s in self.soldiers if s.alive]

    def draw(self, screen, cell_size):
        super().draw(screen, cell_size)