from entities.building import Building
import time

class HQ(Building):
    def __init__(self, x, y):
        super().__init__(x, y, (0, 100, 255), hp=10)

        self.damage = 2
        self.range = 3

        self.attack_delay = 1.0
        self.last_attack = time.time()

    def in_range(self, enemy):
        return abs(enemy.x - self.x) <= self.range and abs(enemy.y - self.y) <= self.range

    def attack(self, enemies):
        now = time.time()

        if now - self.last_attack < self.attack_delay:
            return

        for e in enemies:
            if self.in_range(e):
                e.take_damage(self.damage)
                self.last_attack = now
                break