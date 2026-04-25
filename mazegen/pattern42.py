"""Pattern '42' embedded in the maze as fully-closed cells."""

DIGIT_4 = [
    [1, 0, 1],
    [1, 0, 1],
    [1, 1, 1],
    [0, 0, 1],
    [0, 0, 1],
]

DIGIT_2 = [
    [1, 1, 1],
    [0, 0, 1],
    [1, 1, 1],
    [1, 0, 0],
    [1, 1, 1],
]

DIGIT_H = len(DIGIT_4)
DIGIT_W = len(DIGIT_4[0])
GAP = 2
PATTERN_MIN_W = DIGIT_W * 2 + GAP + 4
PATTERN_MIN_H = DIGIT_H + 4


class Pattern42:
    """
    Computes the set of cells forming the '42' pattern.

    The pattern is centered in the maze. If the maze is too small,
    get_cells() returns an empty set and prints a warning.

    Args:
        width: Maze width in cells.
        height: Maze height in cells.
    """

    def __init__(self, width: int, height: int) -> None:
        """Initialize with maze dimensions."""
        self.width = width
        self.height = height
        self._cells: set[tuple[int, int]] = set()
        self._compute()

    def _compute(self) -> None:
        """Compute cell positions for the '42' pattern."""
        if self.width < PATTERN_MIN_W or self.height < PATTERN_MIN_H:
            print(
                f"[Warning] Maze too small ({self.width}x{self.height}) "
                f"to embed '42' pattern (needs {PATTERN_MIN_W}x{PATTERN_MIN_H})."
            )
            return

        total_w = DIGIT_W + GAP + DIGIT_W
        start_x = (self.width - total_w) // 2
        start_y = (self.height - DIGIT_H) // 2

        start_x = max(1, min(start_x, self.width - total_w - 1))
        start_y = max(1, min(start_y, self.height - DIGIT_H - 1))

        for r in range(DIGIT_H):
            for c in range(DIGIT_W):
                if DIGIT_4[r][c]:
                    self._cells.add((start_x + c, start_y + r))
                if DIGIT_2[r][c]:
                    self._cells.add((start_x + DIGIT_W + GAP + c, start_y + r))

    def get_cells(self) -> set[tuple[int, int]]:
        """Return the set of (x, y) cells forming the '42' pattern."""
        return self._cells