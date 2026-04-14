import time

class Economy:
    def __init__(self):
        self.gold = 20
        self.food = 0

        self.last_tick = time.time()
        self.tick_interval = 5  # 5 giây

    def update(self, farms):
        current = time.time()

        if current - self.last_tick >= self.tick_interval:
            self.last_tick = current

            # vàng cơ bản
            self.gold += 1

            # farm tạo tài nguyên
            for farm in farms:
                self.gold += 1
                self.food += 1

    def can_afford(self, cost):
        return self.gold >= cost

    def spend(self, cost):
        if self.can_afford(cost):
            self.gold -= cost
            return True
        return False