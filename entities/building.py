import pygame

class Building:
    def __init__(self, x, y, color, hp=10):
        self.x = x
        self.y = y
        self.color = color

        self.max_hp = hp
        self.hp = hp

        self.alive = True

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False

    def draw(self, screen, cell_size):
        rect = pygame.Rect(
            self.x * cell_size,
            self.y * cell_size,
            cell_size,
            cell_size
        )
        pygame.draw.rect(screen, self.color, rect)

        # vẽ HP bar
        hp_ratio = self.hp / self.max_hp
        hp_width = int(cell_size * hp_ratio)

        hp_rect = pygame.Rect(
            self.x * cell_size,
            self.y * cell_size,
            hp_width,
            4
        )
        pygame.draw.rect(screen, (0, 255, 0), hp_rect)