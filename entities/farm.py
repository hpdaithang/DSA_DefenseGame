from entities.building import Building

class Farm(Building):
    def __init__(self, x, y):
        super().__init__(x, y, (255, 200, 0), hp=7)