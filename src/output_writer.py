"""
Output writer - Generates maze.txt in hexadecimal format
"""

from typing import Optional
from pathlib import Path
from mazegen.generator import MazeGenerator
from mazegen.solver import MazeSolver


def write_output(
    generator: MazeGenerator,
    entry: tuple[int, int],
    exit_pos: tuple[int, int],
    output_file: str,
) -> None:
    """Solve the maze and write the result to a file.

    Args:
        generator: A MazeGenerator instance after generate() has been called.
        entry: (x, y) entry cell coordinates.
        exit_pos: (x, y) exit cell coordinates.
        output_file: Path to the output file.

    Raises:
        OSError: If the file cannot be written.
    """
    solver = MazeSolver(generator)
    solution_path = solver.solve(entry, exit_pos)
    writer = OutputWriter(generator.grid, entry, exit_pos, solution_path)
    writer.write_to_file(output_file)


class OutputWriter:
    """Writes maze data to a file in hexadecimal format.

    Format:
    - Each cell = 1 hexadecimal character (0-F)
    - Bits: bit0(1)=North, bit1(2)=East, bit2(4)=South, bit3(8)=West
    - Empty line then entry/exit coordinates, then solution path in N/E/S/W
    """

    def __init__(
        self,
        maze: list[list[int]],
        entry: tuple[int, int],
        exit_pos: tuple[int, int],
        solution_path: Optional[list[str]] = None,
    ) -> None:
        """Initialize with maze grid, entry/exit positions, and optional solution path.

        Args:
            maze: 2D grid of wall bitmasks.
            entry: (x, y) entry cell coordinates.
            exit_pos: (x, y) exit cell coordinates.
            solution_path: List of direction letters ('N', 'E', 'S', 'W'), or None.
        """
        self.maze = maze
        self.entry = entry
        self.exit_pos = exit_pos
        self.solution_path = solution_path or []

    def write_to_file(self, filepath: str) -> None:
        """Write the hex content to a file at the given path.

        Args:
            filepath: Destination file path.
        """
        Path(filepath).write_text(self.get_hex_content(), encoding='utf-8')

    def get_hex_content(self) -> str:
        """Build and return the full file content as a string.

        Returns:
            Hex grid rows, followed by entry/exit coords, followed by solution path.
        """
        lines = []
        for row in self.maze:
            lines.append("".join(format(cell, 'X') for cell in row))

        content = "\n".join(lines)
        content += (
            f"\n\n{self.entry[0]},{self.entry[1]}"
            f"\n{self.exit_pos[0]},{self.exit_pos[1]}\n"
        )

        if self.solution_path:
            content += "".join(self.solution_path) + "\n"

        return content
