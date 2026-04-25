"""
Visualiseur ANSI - Rendu du labyrinthe avec menu interactif
Style inspiré d'Animal Crossing avec caractères spéciaux
"""

from typing import List, Tuple, TYPE_CHECKING
import os
if TYPE_CHECKING:
    from mazegen.generator import MazeGenerator

from mazegen.generator import NORTH, EAST, SOUTH, WEST

# pixels per cell and wall thickness used by both graphical renderers
_CELL = 24
_WALL = 3

MLX_THEMES = {
    'spring': {'wall': 0x225522, 'path': 0xFFC800, 'entry': 0x3CA0FF, 'exit': 0xFF4646, 'special': 0xB464DC, 'bg': 0xF0F8E6, 'panel': 0xC8E6B9, 'text': 0x1E3C1E},
    'summer': {'wall': 0x007882, 'path': 0xFFDC00, 'entry': 0x3CA0FF, 'exit': 0xFF4646, 'special': 0xB464DC, 'bg': 0xE1FAFF, 'panel': 0xAADCE6, 'text': 0x004650},
    'autumn': {'wall': 0x8C370A, 'path': 0xFFC800, 'entry': 0x3CA0FF, 'exit': 0xFF4646, 'special': 0xB464DC, 'bg': 0xFFF5E1, 'panel': 0xEBBE91, 'text': 0x642308},
    'winter': {'wall': 0x4B5F8C, 'path': 0x00D7FF, 'entry': 0x3CA0FF, 'exit': 0xFF4646, 'special': 0xB464DC, 'bg': 0xE1EBFF, 'panel': 0xB9CDF0, 'text': 0x233763},
}


def run_interactive(generator, entry: Tuple[int, int], exit_pos: Tuple[int, int], theme: str = "spring") -> None:
    """
    Lance l'interface interactive du visualiseur

    Args:
        generator: Générateur du labyrinthe
        entry: Position d'entrée
        exit_pos: Position de sortie
        theme: Thème visuel (spring, summer, autumn, winter)
    """
    try:
        visualizer: "MlxMazeVisualizer | MazeVisualizer" = MlxMazeVisualizer(generator, entry, exit_pos, theme)
    except ImportError:
        visualizer = MazeVisualizer(generator, entry, exit_pos, theme)
    visualizer.run()


# ---------------------------------------------------------------------------
# MLX graphical visualizer
# ---------------------------------------------------------------------------

class MlxMazeVisualizer:
    _PANEL_W = 220

    def __init__(self, generator, entry: Tuple[int, int], exit_pos: Tuple[int, int], theme: str = "spring") -> None:
        self.generator = generator
        self.entry = entry
        self.exit = exit_pos
        self.theme = theme
        self.show_solution = False
        self._solution_cache: set = set()
        self._solution_dirty = True

        from mlx import Mlx
        self._mlx = Mlx()
        self._ptr = self._mlx.mlx_init()
        self._init_window()

    def _init_window(self) -> None:
        h = len(self.generator.grid)
        w = len(self.generator.grid[0]) if h > 0 else 0
        self._maze_w = w * _CELL + _WALL
        self._maze_h = h * _CELL + _WALL
        self._win_w  = self._maze_w + self._PANEL_W
        self._win_h  = max(self._maze_h, 340)
        self._win = self._mlx.mlx_new_window(self._ptr, self._win_w, self._win_h, "A-Maze-ing")
        self._img = self._mlx.mlx_new_image(self._ptr, self._win_w, self._win_h)
        self._data, self._bpp, self._sl, _ = self._mlx.mlx_get_data_addr(self._img)

    def _c(self) -> dict:
        return MLX_THEMES.get(self.theme, MLX_THEMES['spring'])

    def _fill_rect(self, rx: int, ry: int, rw: int, rh: int, color: int) -> None:
        bpp = self._bpp // 8
        r = (color >> 16) & 0xFF
        g = (color >>  8) & 0xFF
        b =  color        & 0xFF
        row = bytes([b, g, r, 0xFF] * rw)
        for dy in range(rh):
            y = ry + dy
            if 0 <= y < self._win_h:
                start = y * self._sl + rx * bpp
                self._data[start:start + rw * bpp] = row

    def _fill_circle(self, cx: int, cy: int, radius: int, color: int) -> None:
        bpp = self._bpp // 8
        r = (color >> 16) & 0xFF
        g = (color >>  8) & 0xFF
        b =  color        & 0xFF
        pixel = bytes([b, g, r, 0xFF])
        r2 = radius * radius
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= r2:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < self._win_w and 0 <= py < self._win_h:
                        off = py * self._sl + px * bpp
                        self._data[off:off + bpp] = pixel

    def _get_solution_positions(self) -> set:
        if self._solution_dirty:
            from mazegen.solver import MazeSolver
            solver = MazeSolver(self.generator)
            directions = solver.solve(self.entry, self.exit)
            positions: set = set()
            if directions:
                x, y = self.entry
                positions.add((x, y))
                for d in directions:
                    if   d == 'N': y -= 1
                    elif d == 'S': y += 1
                    elif d == 'E': x += 1
                    elif d == 'W': x -= 1
                    positions.add((x, y))
            self._solution_cache = positions
            self._solution_dirty = False
        return self._solution_cache

    def _render(self) -> None:
        c    = self._c()
        grid = self.generator.grid
        gh   = len(grid)
        gw   = len(grid[0]) if gh > 0 else 0
        sol  = self._get_solution_positions() if self.show_solution else set()

        # background
        self._fill_rect(0, 0, self._win_w, self._win_h, c['bg'])
        # panel background
        self._fill_rect(self._maze_w, 0, self._PANEL_W, self._win_h, c['panel'])

        cw = _CELL - _WALL  # inner cell size

        for y in range(gh):
            for x in range(gw):
                cell = grid[y][x]
                px   = x * _CELL + _WALL
                py   = y * _CELL + _WALL
                pos  = (x, y)

                if pos == self.entry:
                    self._fill_rect(px, py, cw, cw, c['entry'])
                elif pos == self.exit:
                    self._fill_rect(px, py, cw, cw, c['exit'])
                elif cell == 15:
                    self._fill_rect(px, py, cw, cw, c['special'])

                if pos in sol and pos not in (self.entry, self.exit):
                    self._fill_circle(px + cw // 2, py + cw // 2, _CELL // 6, c['path'])

                if cell & NORTH:
                    self._fill_rect(px - _WALL, py - _WALL, _CELL, _WALL, c['wall'])
                if cell & WEST:
                    self._fill_rect(px - _WALL, py - _WALL, _WALL, _CELL, c['wall'])

        # outer border
        self._fill_rect(0, 0, self._maze_w, _WALL, c['wall'])
        self._fill_rect(0, 0, _WALL, self._maze_h, c['wall'])
        self._fill_rect(0, self._maze_h - _WALL, self._maze_w, _WALL, c['wall'])
        self._fill_rect(self._maze_w - _WALL, 0, _WALL, self._maze_h, c['wall'])
        # panel divider
        self._fill_rect(self._maze_w, 0, _WALL, self._win_h, c['wall'])

        self._mlx.mlx_put_image_to_window(self._ptr, self._win, self._img, 0, 0)

        # panel text via mlx_string_put
        tc = c['text']
        ox = self._maze_w + 14
        self._mlx.mlx_string_put(self._ptr, self._win, ox, 18,  tc, "A-Maze-ing")
        gh2 = len(self.generator.grid)
        gw2 = len(self.generator.grid[0]) if gh2 > 0 else 0
        self._mlx.mlx_string_put(self._ptr, self._win, ox, 46,  tc, f"Taille  : {gw2} x {gh2}")
        self._mlx.mlx_string_put(self._ptr, self._win, ox, 64,  tc, f"Theme   : {self.theme.capitalize()}")
        perfect = getattr(self.generator, 'perfect', True)
        self._mlx.mlx_string_put(self._ptr, self._win, ox, 82,  tc, f"Parfait : {'Oui' if perfect else 'Non'}")
        if self.show_solution:
            self._mlx.mlx_string_put(self._ptr, self._win, ox, 100, tc, f"Chemin  : {len(sol)} cellules")
        self._mlx.mlx_string_put(self._ptr, self._win, ox, 130, tc, "-- Controles --")
        for i, (key, desc) in enumerate([
            ("[R]",     "Regenerer"),
            ("[S]",     "Solution on/off"),
            ("[T]",     "Changer theme"),
            ("[Entree]","Sauver & quitter"),
            ("[Esc]",   "Quitter"),
        ]):
            y_pos = 152 + i * 18
            self._mlx.mlx_string_put(self._ptr, self._win, ox,      y_pos, tc, key)
            self._mlx.mlx_string_put(self._ptr, self._win, ox + 70, y_pos, tc, desc)

    def _on_key(self, key: int, _: object) -> None:
        if key == 65307:    # Escape
            self._mlx.mlx_loop_exit(self._ptr)

        elif key == 65293:  # Return
            from .output_writer import write_output
            write_output(self.generator, self.entry, self.exit, "maze.txt")
            self._mlx.mlx_loop_exit(self._ptr)

        elif key == 114:    # r
            self.generator.generate()
            self._solution_dirty = True
            self._render()

        elif key == 115:    # s
            self.show_solution = not self.show_solution
            self._render()

        elif key == 116:    # t
            themes = list(MLX_THEMES.keys())
            self.theme = themes[(themes.index(self.theme) + 1) % len(themes)]
            self._render()

    def run(self) -> None:
        self._render()
        self._mlx.mlx_key_hook(self._win, self._on_key, None)
        self._mlx.mlx_hook(self._win, 33, 0, lambda _: self._mlx.mlx_loop_exit(self._ptr), None)
        self._mlx.mlx_loop(self._ptr)
        self._mlx.mlx_destroy_image(self._ptr, self._img)
        self._mlx.mlx_destroy_window(self._ptr, self._win)
        self._mlx.mlx_release(self._ptr)

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