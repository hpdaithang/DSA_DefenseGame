import pygame
import time
from collections import deque

from core.grid import Grid
from entities.building import Building
from entities.farm import Farm
from core.economy import Economy
from entities.enemy import Enemy
from entities.hq import HQ
from entities.barracks import Barracks


# ===== CONFIG =====
GRID_SIZE = 20
CELL_SIZE = 32
SCREEN_SIZE = GRID_SIZE * CELL_SIZE

WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
GREEN = (0, 200, 0)
RED = (200, 0, 0)


# ===== INIT GAME =====
pygame.init()
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
pygame.display.set_caption("Stage 6 - Army System")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)


# ===== GAME STATE =====
grid = Grid(GRID_SIZE)
economy = Economy()

buildings = []
farms = []
hqs = []
barracks_list = []

current_build = "wall"

enemies = []
last_spawn = time.time()
spawn_delay = 5


# ===== PATH CHECK =====
def can_reach_single_hq(grid, hq, start):
    visited = set()
    queue = deque([start])
    target = (hq.x, hq.y)

    while queue:
        x, y = queue.popleft()

        if (x, y) == target:
            return True

        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
            nx, ny = x + dx, y + dy

            if not grid.is_inside(nx, ny):
                continue

            if (nx, ny) in visited:
                continue

            if grid.is_empty(nx, ny) or (nx, ny) == target:
                visited.add((nx, ny))
                queue.append((nx, ny))

    return False


# ===== BUILD RULE đảm bảo mọi HQ đều reachable =====
def is_valid_placement(grid, hqs, x, y):
    temp = grid.cells[y][x]
    grid.cells[y][x] = "TEMP"

    starts = [
        (0, 0),
        (0, GRID_SIZE - 1),
        (GRID_SIZE - 1, 0),
        (GRID_SIZE - 1, GRID_SIZE - 1),
    ]

    for hq in hqs:
        reachable = False

        for start in starts:
            if can_reach_single_hq(grid, hq, start):
                reachable = True
                break

        if not reachable:
            grid.cells[y][x] = temp
            return False

    grid.cells[y][x] = temp
    return True


# ===== MAIN LOOP =====
running = True
while running:
    clock.tick(60)

    # ===== HANDLE INPUT =====
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # chọn loại công trình
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                current_build = "wall"
            elif event.key == pygame.K_2:
                current_build = "farm"
            elif event.key == pygame.K_3:
                current_build = "hq"
            elif event.key == pygame.K_4:
                current_build = "barracks"

        # đặt công trình
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            gx = mx // CELL_SIZE
            gy = my // CELL_SIZE

            if not grid.is_inside(gx, gy):
                continue

            cost = 0
            if current_build == "wall":
                cost = 2
            elif current_build == "farm":
                cost = 3
            elif current_build == "hq":
                cost = 9
            elif current_build == "barracks":
                cost = 5

            if economy.can_afford(cost) and grid.is_empty(gx, gy):

                # check rule path
                if not is_valid_placement(grid, hqs, gx, gy):
                    continue

                # tạo object
                if current_build == "wall":
                    b = Building(gx, gy, (100, 100, 100), hp=15)
                elif current_build == "farm":
                    b = Farm(gx, gy)
                elif current_build == "hq":
                    b = HQ(gx, gy)
                elif current_build == "barracks":
                    b = Barracks(gx, gy)

                # đặt vào game
                if grid.place(gx, gy, b):
                    economy.spend(cost)
                    buildings.append(b)

                    if isinstance(b, Farm):
                        farms.append(b)
                    if isinstance(b, HQ):
                        hqs.append(b)
                    if isinstance(b, Barracks):
                        barracks_list.append(b)

    # ===== UPDATE LOGIC =====

    # spawn enemy
    if time.time() - last_spawn >= spawn_delay:
        enemies.append(Enemy(GRID_SIZE))
        last_spawn = time.time()

    # economy update
    economy.update(farms)

    # enemy update
    for e in enemies:
        e.update(grid, buildings)

    # HQ attack
    for hq in hqs:
        hq.attack(enemies)

    # barracks + soldier update
    for b in barracks_list:
        b.update(grid, enemies)

    # remove enemy chết
    enemies = [e for e in enemies if e.alive]

    # remove building chết
    for b in buildings[:]:
        if not b.alive:
            grid.cells[b.y][b.x] = None
            buildings.remove(b)

            if isinstance(b, Farm):
                farms.remove(b)
            if isinstance(b, HQ):
                hqs.remove(b)
            if isinstance(b, Barracks):
                barracks_list.remove(b)

    # ===== RENDER =====
    screen.fill(WHITE)

    # grid
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            rect = pygame.Rect(
                x * CELL_SIZE,
                y * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(screen, GRAY, rect, 1)

    # preview đặt
    mx, my = pygame.mouse.get_pos()
    gx = mx // CELL_SIZE
    gy = my // CELL_SIZE

    if grid.is_inside(gx, gy):
        rect = pygame.Rect(
            gx * CELL_SIZE,
            gy * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )

        if grid.is_empty(gx, gy):
            pygame.draw.rect(screen, GREEN, rect, 2)
        else:
            pygame.draw.rect(screen, RED, rect, 2)

    # draw building
    for b in buildings:
        b.draw(screen, CELL_SIZE)

    # draw enemy
    for e in enemies:
        e.draw(screen, CELL_SIZE)

    # draw soldier
    for b in barracks_list:
        for s in b.soldiers:
            s.draw(screen, CELL_SIZE)

    # UI
    text = font.render(
        f"Gold: {economy.gold}  Food: {economy.food}",
        True,
        (0, 0, 0)
    )
    screen.blit(text, (10, 10))

    text2 = font.render(
        f"Build: {current_build} (1=wall, 2=farm, 3=hq, 4=barracks)",
        True,
        (0, 0, 0)
    )
    screen.blit(text2, (10, 40))

    pygame.display.flip()

pygame.quit()