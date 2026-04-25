"""
Écrivain de sortie - Génère maze.txt au format hexadécimal
"""

from typing import List, Tuple
from pathlib import Path
from mazegen.solver import MazeSolver

def write_output(generator, entry: Tuple[int, int], exit_pos: Tuple[int, int], output_file: str) -> None:
    """
    Écrit le labyrinthe au format hexadécimal

    Args:
        generator: Générateur du labyrinthe
        entry: Position d'entrée
        exit_pos: Position de sortie
        output_file: Chemin du fichier de sortie

    Raises:
        OSError: En cas d'erreur d'écriture
    """
    try:
        solver = MazeSolver(generator)
        solution_path = solver.solve(entry, exit_pos)
        writer = OutputWriter(generator.grid, entry, exit_pos, solution_path)
        writer.write_to_file(output_file)

    except Exception as e:
        raise OSError(f"Erreur lors de l'écriture: {e}")

class OutputWriter:
    """
    Gestionnaire d'écriture du fichier de sortie au format hexadécimal

    Format:
    - Chaque cellule = 1 caractère hexadécimal (0-F)
    - Bits: 8=Nord, 4=Est, 2=Sud, 1=Ouest
    - Ligne vide puis chemin solution en N/E/S/W
    """

    def __init__(self, maze: List[List[int]], entry: Tuple[int, int], exit_pos: Tuple[int, int], solution_path: List[str] = None):
        """
        Initialise l'écrivain

        Args:
            maze: Grille du labyrinthe (liste de listes d'entiers bitmask)
            entry: Position d'entrée
            exit_pos: Position de sortie
            solution_path: Chemin solution en directions (optionnel)
        """
        self.maze = maze
        self.entry = entry
        self.exit_pos = exit_pos
        self.solution_path = solution_path or []

    def write_to_file(self, filepath: str) -> None:
        """
        Écrit le labyrinthe dans un fichier

        Args:
            filepath: Chemin du fichier de sortie
        """
        content = self.get_hex_content()
        Path(filepath).write_text(content, encoding='utf-8')

    def get_hex_content(self) -> str:
        """
        Génère le contenu hexadécimal complet

        Returns:
            Contenu du fichier avec labyrinthe + coordonnées + chemin
        """
        lines = []
        for row in self.maze:
            hex_row = "".join(format(cell, 'X') for cell in row)
            lines.append(hex_row)

        content = "\n".join(lines)
        content += f"\n\n{self.entry[0]},{self.entry[1]}\n{self.exit_pos[0]},{self.exit_pos[1]}\n"

        if self.solution_path:
            content += "".join(self.solution_path) + "\n"

        return content

    def get_hex_grid_only(self) -> str:
        """
        Génère seulement la grille hexadécimale (sans chemin)

        Returns:
            Grille hexadécimale
        """
        lines = []
        for row in self.maze:
            hex_row = "".join(format(cell, 'X') for cell in row)
            lines.append(hex_row)
        return "\n".join(lines)

    def get_solution_directions(self) -> str:
        """
        Génère seulement les directions du chemin solution

        Args:
            maze: Grille du labyrinthe
            path: Chemin solution

        Returns:
            Chaîne de directions N/E/S/W
        """
        if not self.solution_path:
            return ""

        solver = MazeSolver(self.maze)
        return solver.path_to_directions(self.solution_path)

    @staticmethod
    def validate_hex_format(content: str) -> bool:
        """
        Valide le format hexadécimal du contenu

        Args:
            content: Contenu à valider

        Returns:
            True si le format est valide
        """
        lines = content.strip().split('\n')
        if not lines:
            return False

        # Vérifier que toutes les lignes ont la même longueur
        first_line_len = len(lines[0])
        for line in lines:
            if len(line) != first_line_len:
                return False

            # Vérifier que tous les caractères sont hexadécimaux
            for char in line:
                if char not in '0123456789ABCDEF':
                    return False

        return True