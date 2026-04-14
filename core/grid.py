# grid.py

class Grid:
    def __init__(self, size):
        self.size = size
        self.cells = [[None for _ in range(size)] for _ in range(size)]

    def is_inside(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def is_empty(self, x, y):
        return self.cells[y][x] is None

    def place(self, x, y, obj):
        if self.is_inside(x, y) and self.is_empty(x, y):
            self.cells[y][x] = obj
            return True
        return False

    def get(self, x, y):
        return self.cells[y][x]