"""
Visualiseur ANSI - Rendu du labyrinthe avec menu interactif
Style inspiré d'Animal Crossing avec caractères spéciaux
"""

from typing import List, Tuple, TYPE_CHECKING
import os
if TYPE_CHECKING:
    from mazegen.generator import MazeGenerator

from mazegen.generator import NORTH, EAST, SOUTH, WEST

def run_interactive(generator, entry: Tuple[int, int], exit_pos: Tuple[int, int], theme: str = "spring") -> None:
    """
    Lance l'interface interactive du visualiseur

    Args:
        generator: Générateur du labyrinthe
        entry: Position d'entrée
        exit_pos: Position de sortie
        theme: Thème visuel (spring, summer, autumn, winter)
    """
    visualizer = MazeVisualizer(generator, entry, exit_pos, theme)
    visualizer.run()

class MazeVisualizer:
    """
    Visualiseur de labyrinthe en ANSI avec menu interactif

    Caractères utilisés:
    - █ : murs (block)
    - ░ : passages (light shade)
    - ● : chemin solution (black circle)
    - ▓ : cellules spéciales (dark shade)
    - 🚪 : entrée
    - 🏁 : sortie
    """

    def __init__(self, generator, entry: Tuple[int, int], exit_pos: Tuple[int, int], theme: str = "spring"):
        """
        Initialise le visualiseur

        Args:
            generator: Générateur du labyrinthe
            entry: Position d'entrée
            exit_pos: Position de sortie
            theme: Thème visuel
        """
        self.generator = generator
        self.entry = entry
        self.exit = exit_pos
        self.theme = theme
        self.show_solution = False
        self.color_mode = True
        self._solution_positions = None

    def _get_solution_positions(self) -> set:
        """Calcule les positions du chemin solution"""
        if self._solution_positions is None:
            from mazegen.solver import MazeSolver
            solver = MazeSolver(self.generator)
            directions = solver.solve(self.entry, self.exit)
            if directions:
                # Convertir les directions en positions
                positions = set()
                x, y = self.entry
                positions.add((x, y))
                
                for direction in directions:
                    if direction == 'N':
                        y -= 1
                    elif direction == 'S':
                        y += 1
                    elif direction == 'E':
                        x += 1
                    elif direction == 'W':
                        x -= 1
                    positions.add((x, y))
                
                self._solution_positions = positions
            else:
                self._solution_positions = set()
        
        return self._solution_positions

    def display_menu(self) -> None:
        """Affiche le menu principal"""
        os.system('cls' if os.name == 'nt' else 'clear')

        print("🐾 A-Maze-Ing - Générateur de Labyrinthes 🐾")
        print("=" * 50)
        print()
        self.display_maze()
        print()
        print("Menu:")
        print("1. Régénérer un nouveau labyrinthe")
        print("2. Afficher/Masquer le chemin solution")
        print("3. Changer le mode couleur")
        print("4. Changer de thème")
        print("5. Sauvegarder et quitter")
        print("6. Quitter sans sauvegarder")
        print()
        print("Choix: ", end="")

    def run(self) -> None:
        """Lance la boucle interactive"""
        try:
            while True:
                self.display_menu()

                try:
                    choice = input().strip()

                    if choice == '1':
                        # Régénérer
                        print("Régénération en cours...")
                        self.generator.generate()
                        self._solution_positions = None  # Invalider le cache
                        print("Nouveau labyrinthe généré!")

                    elif choice == '2':
                        self.toggle_solution()
                        print(f"Chemin solution {'affiché' if self.show_solution else 'masqué'}")

                    elif choice == '3':
                        self.toggle_colors()
                        print(f"Mode couleur {'activé' if self.color_mode else 'désactivé'}")

                    elif choice == '4':
                        self.change_theme()

                    elif choice == '5':
                        # Sauvegarder et quitter
                        print("Sauvegarde en cours...")
                        from .output_writer import write_output
                        write_output(self.generator, self.entry, self.exit, "maze.txt")
                        print("Labyrinthe sauvegardé dans maze.txt")
                        return

                    elif choice == '6':
                        # Quitter sans sauvegarder
                        return

                    else:
                        print("Choix invalide. Appuyez sur Entrée pour continuer...")
                        input()

                except KeyboardInterrupt:
                    print("\nInterruption détectée. Au revoir! 🐾")
                    return
                except Exception as e:
                    print(f"Erreur: {e}")
                    print("Appuyez sur Entrée pour continuer...")
                    input()

        except KeyboardInterrupt:
            print("\nAu revoir! 🐾")

    def display_maze(self) -> None:
        """Affiche le labyrinthe en ANSI"""
        if not self.generator.grid:
            print("Aucun labyrinthe à afficher")
            return

        height = len(self.generator.grid)
        width = len(self.generator.grid[0]) if height > 0 else 0

        # Bordure supérieure
        print("█" * (width * 2 + 1))

        for y in range(height):
            # Ligne supérieure des cellules
            top_line = "█"
            for x in range(width):
                cell_walls = self.generator.grid[y][x]
                if cell_walls & NORTH:  # Mur nord
                    top_line += "██"
                else:
                    top_line += "█░"
            top_line += "█"
            print(self._colorize(top_line, 'wall'))

            # Ligne du milieu avec contenu
            middle_line = "█"
            for x in range(width):
                cell_walls = self.generator.grid[y][x]

                # Mur ouest
                if cell_walls & WEST:  # Mur ouest
                    middle_line += "█"
                else:
                    middle_line += "░"

                # Contenu de la cellule
                pos = (x, y)
                if pos == self.entry:
                    middle_line += self._colorize("🚪", 'entry')
                elif pos == self.exit:
                    middle_line += self._colorize("🏁", 'exit')
                elif self.show_solution and (x, y) in self._get_solution_positions():
                    middle_line += self._colorize("●", 'path')
                elif cell_walls == 15:  # Cellule entièrement fermée (pattern 42)
                    middle_line += self._colorize("▓", 'special')
                else:
                    middle_line += "░"

            # Mur est de la dernière cellule
            if width > 0:
                last_cell_walls = self.generator.grid[y][width-1]
                middle_line += "█" if (last_cell_walls & EAST) else "░"
            print(middle_line)

        # Bordure inférieure
        bottom_line = "█"
        for x in range(width):
            cell_walls = self.generator.grid[height-1][x]
            if cell_walls & SOUTH:  # Mur sud
                bottom_line += "██"
            else:
                bottom_line += "█░"
        bottom_line += "█"
        print(self._colorize(bottom_line, 'wall'))

        # Informations
        print()
        print(f"Dimensions: {width}x{height}")
        print(f"Entrée: {self.entry}")
        print(f"Sortie: {self.exit}")
        print(f"Parfait: {'Oui' if getattr(self.generator, 'perfect', True) else 'Non'}")
        if self.show_solution and self._get_solution_positions():
            print(f"Chemin solution: {len(self._get_solution_positions())} étapes")
        print(f"Mode couleur: {'Activé' if self.color_mode else 'Désactivé'}")
        print(f"Thème: {self.theme}")

    def _colorize(self, text: str, element_type: str) -> str:
        """
        Applique la couleur ANSI selon le type d'élément

        Args:
            text: Texte à colorer
            element_type: Type d'élément ('wall', 'path', 'entry', 'exit', 'special')

        Returns:
            Texte avec codes ANSI
        """
        if not self.color_mode:
            return text

        # Thèmes de couleur selon le thème choisi
        themes = {
            'spring': {
                'wall': '\033[92m',      # Vert printanier
                'path': '\033[93m',      # Jaune
                'entry': '\033[94m',     # Bleu
                'exit': '\033[91m',      # Rouge
                'special': '\033[95m',   # Magenta
            },
            'summer': {
                'wall': '\033[96m',      # Cyan
                'path': '\033[93m',      # Jaune
                'entry': '\033[94m',     # Bleu
                'exit': '\033[91m',      # Rouge
                'special': '\033[95m',   # Magenta
            },
            'autumn': {
                'wall': '\033[33m',      # Orange
                'path': '\033[93m',      # Jaune
                'entry': '\033[94m',     # Bleu
                'exit': '\033[91m',      # Rouge
                'special': '\033[95m',   # Magenta
            },
            'winter': {
                'wall': '\033[37m',      # Blanc
                'path': '\033[96m',      # Cyan
                'entry': '\033[94m',     # Bleu
                'exit': '\033[91m',      # Rouge
                'special': '\033[95m',   # Magenta
            }
        }

        reset = '\033[0m'
        color = themes.get(self.theme, themes['spring']).get(element_type, '')
        return f"{color}{text}{reset}"

    def toggle_solution(self) -> None:
        """Bascule l'affichage du chemin solution"""
        self.show_solution = not self.show_solution

    def toggle_colors(self) -> None:
        """Bascule le mode couleur"""
        self.color_mode = not self.color_mode

    def change_theme(self) -> None:
        """Change le thème de couleur"""
        themes = ['spring', 'summer', 'autumn', 'winter']
        current_index = themes.index(self.theme)
        self.theme = themes[(current_index + 1) % len(themes)]
        print(f"Thème changé: {self.theme}")