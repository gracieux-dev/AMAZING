"""
Écrivain de sortie - Génère maze.txt au format hexadécimal
"""

from typing import List, Tuple
from pathlib import Path
from mazegen.solver import MazeSolver


def write_output(generator, entry: Tuple[int, int], exit_pos: Tuple[int, int], output_file: str) -> None:
    try:
        solver = MazeSolver(generator)
        solution_path = solver.solve(entry, exit_pos)
        writer = OutputWriter(generator.grid, entry, exit_pos, solution_path)
        writer.write_to_file(output_file)
    except Exception as e:
        raise OSError(f"Erreur lors de l'écriture: {e}")


class OutputWriter:
    """
    Format:
    - Chaque cellule = 1 caractère hexadécimal (0-F)
    - Bits: bit0(1)=Nord, bit1(2)=Est, bit2(4)=Sud, bit3(8)=Ouest
    - Ligne vide puis chemin solution en N/E/S/W
    """

    def __init__(self, maze: List[List[int]], entry: Tuple[int, int],
                 exit_pos: Tuple[int, int], solution_path: List[str] = None):
        self.maze = maze
        self.entry = entry
        self.exit_pos = exit_pos
        self.solution_path = solution_path or []

    def write_to_file(self, filepath: str) -> None:
        Path(filepath).write_text(self.get_hex_content(), encoding='utf-8')

    def get_hex_content(self) -> str:
        lines = []
        for row in self.maze:
            lines.append("".join(format(cell, 'X') for cell in row))

        content = "\n".join(lines)
        content += f"\n\n{self.entry[0]},{self.entry[1]}\n{self.exit_pos[0]},{self.exit_pos[1]}\n"

        if self.solution_path:
            content += "".join(self.solution_path) + "\n"

        return content
