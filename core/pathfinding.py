from collections import deque

def get_neighbors(pos, grid, goal):
    x, y = pos
    neighbors = []

    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    for dx, dy in directions:
        nx, ny = x + dx, y + dy

        if not grid.is_inside(nx, ny):
            continue

        # cho đi vào goal
        if (nx, ny) == goal or grid.is_empty(nx, ny):
            neighbors.append((nx, ny))

    return neighbors


def bfs(grid, start, goal):
    queue = deque([start]) # hàng đợi
    visited = {start} 
    parent = {} 

    while queue:
        u = queue.popleft() 
        if u == goal:
            return reconstruct_path(parent, start, goal)
        for v in get_neighbors(u, grid, goal):
            if v not in visited:
                visited.add(v)
                parent[v] = u
                queue.append(v)

    return []


def reconstruct_path(parent, start, goal):
    path = []
    current = goal

    while current != start:
        path.append(current)
        current = parent.get(current)

        if current is None:
            return []

    path.append(start)
    path.reverse()
    return path