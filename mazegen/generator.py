"""Maze generation — DFS (recursive backtracker) and Kruskal's algorithm."""

import random
from typing import Optional
from .pattern42 import Pattern42


NORTH = 0b0001
EAST  = 0b0010
SOUTH = 0b0100
WEST  = 0b1000

OPPOSITE = {NORTH: SOUTH, SOUTH: NORTH, EAST: WEST, WEST: EAST}
DELTA = {
    NORTH: (0, -1),
    EAST:  (1, 0),
    SOUTH: (0, 1),
    WEST:  (-1, 0),
}

_ALGORITHMS = ('dfs', 'kruskal')


class MazeGenerator:
    """
    Generates a maze using DFS (recursive backtracker) or Kruskal's algorithm.

    Each cell is stored as a bitmask (int) where each bit represents
    a closed wall: bit0=North, bit1=East, bit2=South, bit3=West.
    A bit set to 1 means the wall is closed (present).

    Args:
        width: Number of columns.
        height: Number of rows.
        seed: Random seed for reproducibility.
        perfect: If True, generates a perfect maze (unique path).
        algorithm: 'dfs' (default) or 'kruskal'.

    Example:
        gen = MazeGenerator(width=20, height=15, seed=42, perfect=True)
        gen.generate()
        cell_walls = gen.grid[row][col]  # int bitmask
    """

    def __init__(
        self,
        width: int,
        height: int,
        seed: Optional[int] = None,
        perfect: bool = True,
        algorithm: str = 'dfs',
    ) -> None:
        if width < 3 or height < 3:
            raise ValueError("Maze must be at least 3x3.")
        if algorithm not in _ALGORITHMS:
            raise ValueError(
                f"Unknown algorithm '{algorithm}'. Choose from: {_ALGORITHMS}.")
        self.width     = width
        self.height    = height
        self.seed      = seed
        self.perfect   = perfect
        self.algorithm = algorithm
        self.grid: list[list[int]] = []
        self.locked: set[tuple[int, int]] = set()
        self._rng = random.Random(seed)

    # ── public API ────────────────────────────────────────────────────────────

    def generate(self) -> None:
        """Generate the maze in-place. Call this before accessing grid."""
        self._rng = random.Random(self.seed)
        self._init_grid()
        self.locked = Pattern42(self.width, self.height).get_cells()
        self._lock_pattern()
        if self.algorithm == 'kruskal':
            self._kruskal()
        else:
            self._dfs(0, 0)
        if not self.perfect:
            self._add_loops()

    def generate_steps(self):
        """Yield (x, y) of each newly carved cell for step-by-step animation."""
        self._rng = random.Random(self.seed)
        self._init_grid()
        self.locked = Pattern42(self.width, self.height).get_cells()
        self._lock_pattern()
        if self.algorithm == 'kruskal':
            yield from self._kruskal_steps()
        else:
            yield from self._dfs_steps()
        if not self.perfect:
            self._add_loops()

    def to_hex_grid(self) -> list[str]:
        """Return the maze as a list of hex-digit strings, one per row."""
        return [
            "".join(format(cell, "X") for cell in row)
            for row in self.grid
        ]

    # ── shared helpers ────────────────────────────────────────────────────────

    def _init_grid(self) -> None:
        self.grid = [
            [NORTH | EAST | SOUTH | WEST for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def _lock_pattern(self) -> None:
        """Mark pattern42 cells as visited so algorithms skip them."""
        self._visited: list[list[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        for (x, y) in self.locked:
            self._visited[y][x] = True

    def _add_loops(self) -> None:
        """Remove extra walls to create a non-perfect maze with loops."""
        removals = (self.width * self.height) // 8
        for _ in range(removals):
            x = self._rng.randint(0, self.width - 2)
            y = self._rng.randint(0, self.height - 2)
            if (x, y) not in self.locked and (x + 1, y) not in self.locked:
                self.grid[y][x]     &= ~EAST
                self.grid[y][x + 1] &= ~WEST

    # ── DFS ───────────────────────────────────────────────────────────────────

    def _dfs(self, x: int, y: int) -> None:
        """Iterative recursive-backtracker DFS."""
        self._visited[y][x] = True
        stack = [(x, y)]
        while stack:
            cx, cy = stack[-1]
            dirs = [NORTH, EAST, SOUTH, WEST]
            self._rng.shuffle(dirs)
            moved = False
            for direction in dirs:
                dx, dy = DELTA[direction]
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and not self._visited[ny][nx]
                    and (nx, ny) not in self.locked
                ):
                    self.grid[cy][cx] &= ~direction
                    self.grid[ny][nx] &= ~OPPOSITE[direction]
                    self._visited[ny][nx] = True
                    stack.append((nx, ny))
                    moved = True
                    break
            if not moved:
                stack.pop()

    def _dfs_steps(self):
        self._visited[0][0] = True
        stack = [(0, 0)]
        yield (0, 0)
        while stack:
            cx, cy = stack[-1]
            dirs = [NORTH, EAST, SOUTH, WEST]
            self._rng.shuffle(dirs)
            moved = False
            for direction in dirs:
                dx, dy = DELTA[direction]
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and not self._visited[ny][nx]
                    and (nx, ny) not in self.locked
                ):
                    self.grid[cy][cx] &= ~direction
                    self.grid[ny][nx] &= ~OPPOSITE[direction]
                    self._visited[ny][nx] = True
                    stack.append((nx, ny))
                    yield (nx, ny)
                    moved = True
                    break
            if not moved:
                stack.pop()

    # ── Kruskal ───────────────────────────────────────────────────────────────

    def _kruskal_setup(self):
        """Build the Union-Find structure and shuffled edge list."""
        parent = {
            (x, y): (x, y)
            for y in range(self.height)
            for x in range(self.width)
        }

        def find(c):
            while parent[c] != c:
                parent[c] = parent[parent[c]]
                c = parent[c]
            return c

        def union(a, b) -> bool:
            ra, rb = find(a), find(b)
            if ra == rb:
                return False
            parent[ra] = rb
            return True

        edges = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.locked:
                    continue
                if x + 1 < self.width and (x + 1, y) not in self.locked:
                    edges.append(((x, y), (x + 1, y), EAST))
                if y + 1 < self.height and (x, y + 1) not in self.locked:
                    edges.append(((x, y), (x, y + 1), SOUTH))
        self._rng.shuffle(edges)
        return union, edges

    def _kruskal(self) -> None:
        union, edges = self._kruskal_setup()
        for (x1, y1), (x2, y2), direction in edges:
            if union((x1, y1), (x2, y2)):
                self.grid[y1][x1] &= ~direction
                self.grid[y2][x2] &= ~OPPOSITE[direction]

    def _kruskal_steps(self):
        union, edges = self._kruskal_setup()
        for (x1, y1), (x2, y2), direction in edges:
            if union((x1, y1), (x2, y2)):
                self.grid[y1][x1] &= ~direction
                self.grid[y2][x2] &= ~OPPOSITE[direction]
                yield (x1, y1)
                yield (x2, y2)
