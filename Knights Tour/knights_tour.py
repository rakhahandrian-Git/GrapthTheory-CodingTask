import sys

# 8 possible knight moves (dx, dy)
MOVES = [(1, 2), (2, 1), (2, -1), (1, -2),
         (-1, -2), (-2, -1), (-2, 1), (-1, 2)]


def knights_tour(cols, rows, sx, sy):
    """Return list of (x, y) visiting every square once, or None."""
    if cols <= 0 or rows <= 0 or not (0 <= sx < cols and 0 <= sy < rows):
        return None

    total = cols * rows

    # Parity pruning: odd x odd board must start on the majority color
    if cols % 2 == 1 and rows % 2 == 1 and (sx + sy) % 2 == 1:
        return None

    visited = [[False] * cols for _ in range(rows)]
    path = []

    def neighbors(x, y):
        for dx, dy in MOVES:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows and not visited[ny][nx]:
                yield nx, ny

    def degree(x, y):
        return sum(1 for _ in neighbors(x, y))

    def solve(x, y):
        visited[y][x] = True
        path.append((x, y))
        if len(path) == total:
            return True
        for nx, ny in sorted(neighbors(x, y), key=lambda p: degree(*p)):
            if solve(nx, ny):
                return True
        visited[y][x] = False
        path.pop()
        return False

    return path if solve(sx, sy) else None


def main():
    sys.setrecursionlimit(100000)
    cols, rows = map(int, input().split())
    sx, sy = map(int, input().split())

    path = knights_tour(cols, rows, sx, sy)
    if path is None:
        print("path not found")
        return

    for x, y in path:
        print(f"{x},{y}")

    grid = [[0] * cols for _ in range(rows)]
    for i, (x, y) in enumerate(path, 1):
        grid[y][x] = i
    width = len(str(cols * rows))
    print()
    for row in grid:
        print(" ".join(str(v).rjust(width) for v in row))


if __name__ == "__main__":
    main()
