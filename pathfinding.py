
class MinHeap:
    def __init__(self):
        """Khởi tạo mặc định cho lớp"""
        self.priority_list = []
    
    def push(self,item):
        """Thêm 1 phần tử vào heap và vung đống lên"""
        self.priority_list.append(item) 
        self._heapify_up(len(self.priority_list) - 1) 
    
    def pop(self):
        """Lấy và xóa phần tử nhỏ nhất (gốc của Heap) và vun đống xuống"""
        if len(self.priority_list) == 0:
            return None
        if len(self.priority_list) == 1: return self.priority_list.pop()

        root = self.priority_list[0] # phần tử gốc nhỏ nhất
        self.priority_list[0] = self.priority_list.pop() # đưa phần tử cuối cùng lên làm gốc
        self._heapify_down(0) # vung đống xuống
        return root ;

    def is_empty(self):
        """Check empty?"""
        return len(self.priority_list) == 0;

    def _heapify_up(self,index): 
        """So sánh node hiện tại với node cha, nếu nhỏ hơn thì đổi chỗ đưa lên trên."""
        parent_index = (index - 1) // 2
        # Nếu chưa đến gốc và phần tử hiện tại nhỏ hơn phần tử cha
        if index > 0 and self.priority_list[index][0] < self.priority_list[parent_index][0]:
            # Hoán đổi 2 phần tử
            self.priority_list[index], self.priority_list[parent_index] = self.priority_list[parent_index], self.priority_list[index]
            # Gọi đệ quy tiếp lên trên
            self._heapify_up(parent_index)

    def _heapify_down(self, index):
        """So sánh node hiện tại với 2 node con, nếu lớn hơn con thì đổi chỗ đưa xuống dưới."""
        smallest = index
        left_child = 2 * index + 1
        right_child = 2 * index + 2

        if left_child < len(self.priority_list) and self.priority_list[left_child][0] < self.priority_list[smallest][0]:
            smallest = left_child
        if right_child < len(self.priority_list) and self.priority_list[right_child][0] < self.priority_list[smallest][0]:
            smallest = right_child

        if smallest != index:
            self.priority_list[index], self.priority_list[smallest] = self.priority_list[smallest], self.priority_list[index]
            self._heapify_down(smallest)


def heuristic(a, b):
    """Tính khoảng cách Manhattan giữa 2 điểm."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star(start, goal, grid, buildings_pos, ignore_buildings = True, is_enemy = False):
    """
    Thuật toán A* 
    tìm ra đường đi tốt nhất với các trọng số được qui định mỗi loại địa hình, từ start đến goal
    """
    nxt_dxy = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    open_set = MinHeap()
    open_set.push((0,start))

    came_from = {} # lưu nhằm truy vết
    g_score = {start: 0} # chi phí cho mỗi lựa chọn

    map_height = len(grid)
    map_width = len(grid[0])

    while not open_set.is_empty():
        current = open_set.pop()[1]

        if current == goal:
            # bắt đầu truy vết
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for dx, dy in nxt_dxy:
            dx_nxt, dy_nxt = dx + current[0], dy + current[1]

            if not (0 <= dx_nxt < map_width and 0 <= dy_nxt < map_height): 
                continue # nằm ngoài bản đồ
            if not ignore_buildings and (dx_nxt,dy_nxt) in buildings_pos and (dx_nxt,dy_nxt) != goal: 
                continue

            # tính chi phí trên các địa hình đối với enemy và quân lính
            terrain = grid[dy_nxt][dx_nxt]
            move_cost = 1.0 
            
            if terrain == 1:
                if is_enemy: move_cost = 2.0 
                else: move_cost = 1.0 
            elif terrain in (2, 3):
                if not is_enemy: move_cost = 0.5 
                else: move_cost = 1.0 
            elif terrain == 4:
                move_cost = 10.0
            
            tentative_g = g_score[current] + move_cost

            if (dx_nxt,dy_nxt) not in g_score or tentative_g < g_score[(dx_nxt,dy_nxt)]:
                came_from[(dx_nxt,dy_nxt)] = current
                g_score[(dx_nxt,dy_nxt)] = tentative_g
                f_score = tentative_g + heuristic((dx_nxt,dy_nxt), goal)
                open_set.push((f_score, (dx_nxt,dy_nxt)))
    
    return []