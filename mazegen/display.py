"""
Module d'affichage du labyrinthe
Support ASCII et MiniLibX
"""

from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from .generator import MazeGenerator

from .generator import Cell

class Display:
    """
    Gestionnaire d'affichage du labyrinthe

    Attributes:
        generator (MazeGenerator): Générateur du labyrinthe
        show_solution (bool): Afficher le chemin solution
    """

    def __init__(self, generator: 'MazeGenerator'):
        """
        Initialise l'affichage

        Args:
            generator: Générateur du labyrinthe
        """
        self.generator = generator
        self.show_solution = False

    @property
    def maze(self) -> List[List[Cell]]:
        """Accès à la grille du labyrinthe"""
        return self.generator.maze

    @property
    def solution_path(self) -> List[tuple]:
        """Accès au chemin solution"""
        return self.generator.solution_path

    def show(self) -> None:
        """Affiche le labyrinthe"""
        if not self.maze:
            print("Aucun labyrinthe à afficher")
            return

        height = len(self.maze)
        width = len(self.maze[0]) if height > 0 else 0

        print("\n" + "=" * (width * 2 + 1))

        for y in range(height):
            # Ligne supérieure des cellules
            top_line = ""
            for x in range(width):
                cell = self.maze[y][x]
                # Coin supérieur gauche
                if x == 0:
                    top_line += "█"
                # Mur Nord ou pas
                if cell.north_wall:
                    top_line += "██"
                else:
                    top_line += "█░"
            top_line += "█"
            print(top_line)

            # Ligne du milieu avec murs Est/Ouest
            middle_line = ""
            for x in range(width):
                cell = self.maze[y][x]
                # Mur Ouest
                if cell.west_wall:
                    middle_line += "█"
                else:
                    middle_line += "░"

                # Contenu de la cellule
                if self.show_solution and (x, y) in self.solution_path:
                    middle_line += "●"  # Marqueur du chemin
                else:
                    middle_line += "░"

            # Mur Est de la dernière cellule
            if width > 0:
                middle_line += "█" if self.maze[y][width-1].east_wall else "░"
            print(middle_line)

        # Dernière ligne (murs Sud)
        bottom_line = "█"
        for x in range(width):
            cell = self.maze[height-1][x]
            if cell.south_wall:
                bottom_line += "██"
            else:
                bottom_line += "█░"
        bottom_line += "█"
        print(bottom_line)

        print("=" * (width * 2 + 1))
        print(f"Labyrinthe {width}x{height}")
        if self.show_solution:
            print("Chemin solution affiché (●)")
        else:
            print("Chemin solution masqué")

    def toggle_solution(self) -> None:
        """Bascule l'affichage du chemin solution"""
        self.show_solution = not self.show_solution
        self.show()

    def regenerate(self) -> None:
        """Régénère un nouveau labyrinthe"""
        # TODO: Implémenter la régénération
        pass