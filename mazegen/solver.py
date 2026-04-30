"""BFS maze solver."""

from collections import deque
from typing import Optional
from .generator import MazeGenerator, NORTH, EAST, SOUTH, WEST, DELTA

DIRECTION_LETTER = {NORTH: "N", EAST: "E", SOUTH: "S", WEST: "W"}


class MazeSolver:
    """
    Solves a maze using BFS to find the shortest path.

    Args:
        generator: A MazeGenerator instance after generate() has been called.

    Example:
        solver = MazeSolver(gen)
        path = solver.solve((0, 0), (gen.width - 1, gen.height - 1))
        print(path)  # ['E', 'S', 'E', 'E', ...]
    """

    def __init__(self, generator: MazeGenerator) -> None:
        """Initialize with a generated maze."""
        self.gen = generator

    def solve(
        self,
        entry: tuple[int, int],
        exit_: tuple[int, int],
    ) -> list[str]:
        """
        Find the shortest path from entry to exit.

        Args:
            entry: (x, y) starting cell.
            exit_: (x, y) destination cell.

        Returns:
            List of direction letters ('N', 'E', 'S', 'W').
            Empty list if no path found.
        """
        prev: dict[tuple[int, int], Optional[tuple[tuple[int, int], str]]] = {
            entry: None
        }
        queue: deque[tuple[int, int]] = deque([entry])

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == exit_:
                return self._reconstruct(prev, entry, exit_)
            cell = self.gen.grid[cy][cx]
            for direction, (dx, dy) in DELTA.items():
                nx, ny = cx + dx, cy + dy
                if (
                    not (cell & direction)
                    and 0 <= nx < self.gen.width
                    and 0 <= ny < self.gen.height
                    and (nx, ny) not in prev
                ):
                    prev[(nx, ny)] = ((cx, cy), DIRECTION_LETTER[direction])
                    queue.append((nx, ny))

        return []

    def _reconstruct(
        self,
        prev: dict[tuple[int, int], Optional[tuple[tuple[int, int], str]]],
        entry: tuple[int, int],
        exit_: tuple[int, int],
    ) -> list[str]:
        """Reconstruct the path from the BFS parent map."""
        path: list[str] = []
        current: tuple[int, int] = exit_
        while current != entry:
            node = prev[current]
            if node is None:
                break
            parent, letter = node
            path.append(letter)
            current = parent
        return list(reversed(path))

    def solve_as_coords(
        self,
        entry: tuple[int, int],
        exit_: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """
        Same as solve() but returns a list of (x, y) coordinates.

        Args:
            entry: Starting cell.
            exit_: Destination cell.

        Returns:
            List of (x, y) tuples from entry to exit inclusive.
        """
        directions = self.solve(entry, exit_)
        dir_map = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
        coords = [entry]
        cx, cy = entry
        for d in directions:
            dx, dy = dir_map[d]
            cx += dx
            cy += dy
            coords.append((cx, cy))
        return coords
