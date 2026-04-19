"""Maze generation using recursive backtracker (DFS)."""

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


class MazeGenerator:
    """
    Generates a maze using the recursive backtracker (DFS) algorithm.

    Each cell is stored as a bitmask (int) where each bit represents
    a closed wall: bit0=North, bit1=East, bit2=South, bit3=West.
    A bit set to 1 means the wall is closed (present).

    Args:
        width: Number of columns.
        height: Number of rows.
        seed: Random seed for reproducibility.
        perfect: If True, generates a perfect maze (unique path).

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
    ) -> None:
        """Initialize the maze generator."""
        if width < 3 or height < 3:
            raise ValueError("Maze must be at least 3x3.")
        self.width = width
        self.height = height
        self.seed = seed
        self.perfect = perfect
        self.grid: list[list[int]] = []
        self.locked: set[tuple[int, int]] = set()
        self._rng = random.Random(seed)

    def generate(self) -> None:
        """Generate the maze in-place. Call this before accessing grid."""
        self._init_grid()
        p42 = Pattern42(self.width, self.height)
        self.locked = p42.get_cells()
        self._lock_pattern()
        self._dfs(0, 0)
        if not self.perfect:
            self._add_loops()

    def _init_grid(self) -> None:
        """Initialize every cell with all 4 walls closed."""
        self.grid = [
            [NORTH | EAST | SOUTH | WEST for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def _lock_pattern(self) -> None:
        """Mark pattern42 cells as visited so DFS skips them."""
        self._visited: list[list[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        for (x, y) in self.locked:
            self._visited[y][x] = True

    def _dfs(self, x: int, y: int) -> None:
        """Recursive backtracker DFS maze generation."""
        self._visited[y][x] = True
        dirs = [NORTH, EAST, SOUTH, WEST]
        self._rng.shuffle(dirs)
        for direction in dirs:
            dx, dy = DELTA[direction]
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < self.width
                and 0 <= ny < self.height
                and not self._visited[ny][nx]
                and (nx, ny) not in self.locked
            ):
                self.grid[y][x] &= ~direction
                self.grid[ny][nx] &= ~OPPOSITE[direction]
                self._dfs(nx, ny)

    def _add_loops(self) -> None:
        """Remove extra walls to create a non-perfect maze with loops."""
        removals = (self.width * self.height) // 8
        for _ in range(removals):
            x = self._rng.randint(0, self.width - 2)
            y = self._rng.randint(0, self.height - 2)
            if (x, y) not in self.locked and (x + 1, y) not in self.locked:
                self.grid[y][x] &= ~EAST
                self.grid[y][x + 1] &= ~WEST

    def to_hex_grid(self) -> list[str]:
        """
        Return the maze as a list of strings, one per row.
        Each character is a hex digit encoding closed walls.

        Returns:
            List of strings, each being one row of hex digits.
        """
        rows = []
        for row in self.grid:
            rows.append("".join(format(cell, "X") for cell in row))
        return rows