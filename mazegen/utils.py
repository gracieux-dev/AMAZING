"""
Utilitaires pour les labyrinthes
Validation des contraintes, calcul de chemins, etc.
"""

from typing import List, Tuple, Set, Dict
import heapq
from .generator import Cell

class MazeUtils:
    """Utilitaires pour les labyrinthes"""

    @staticmethod
    def validate_constraints(maze: List[List[Cell]]) -> bool:
        """
        Valide les contraintes du labyrinthe

        Args:
            maze: Grille du labyrinthe

        Returns:
            True si valide
        """
        height = len(maze)
        width = len(maze[0]) if height > 0 else 0

        # Vérifier la cohérence des murs
        for y in range(height):
            for x in range(width):
                cell = maze[y][x]

                # Vérifier cohérence avec le voisin Nord
                if y > 0:
                    north_cell = maze[y-1][x]
                    if cell.north_wall != north_cell.south_wall:
                        return False

                # Vérifier cohérence avec le voisin Ouest
                if x > 0:
                    west_cell = maze[y][x-1]
                    if cell.west_wall != west_cell.east_wall:
                        return False

        # Vérifier qu'il n'y a pas de zones 3x3 ouvertes
        if not MazeUtils._check_no_large_open_areas(maze):
            return False

        # Vérifier la présence du pattern "42"
        if not MazeUtils._check_42_pattern(maze):
            return False

        return True

    @staticmethod
    def find_solution_path(maze: List[List[Cell]],
                         start: Tuple[int, int],
                         end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Trouve le chemin solution (A*)

        Args:
            maze: Grille du labyrinthe
            start: Position de départ
            end: Position d'arrivée

        Returns:
            Chemin solution
        """
        height = len(maze)
        width = len(maze[0]) if height > 0 else 0

        def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
            x, y = pos
            neighbors = []
            cell = maze[y][x]

            # Nord
            if not cell.north_wall and y > 0:
                neighbors.append((x, y - 1))

            # Est
            if not cell.east_wall and x < width - 1:
                neighbors.append((x + 1, y))

            # Sud
            if not cell.south_wall and y < height - 1:
                neighbors.append((x, y + 1))

            # Ouest
            if not cell.west_wall and x > 0:
                neighbors.append((x - 1, y))

            return neighbors

        # A* algorithm
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        cost_so_far: Dict[Tuple[int, int], float] = {}
        came_from[start] = None
        cost_so_far[start] = 0

        while frontier:
            current = heapq.heappop(frontier)[1]

            if current == end:
                break

            for neighbor in get_neighbors(current):
                new_cost = cost_so_far[current] + 1
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + heuristic(end, neighbor)
                    heapq.heappush(frontier, (priority, neighbor))
                    came_from[neighbor] = current

        # Reconstruire le chemin
        if end not in came_from:
            return []  # Pas de chemin trouvé

        path = []
        current = end
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()

        return path

    @staticmethod
    def add_42_pattern(maze: List[List[Cell]]) -> None:
        """
        Ajoute le chiffre "42" dans le labyrinthe

        Args:
            maze: Grille du labyrinthe
        """
        height = len(maze)
        width = len(maze[0]) if height > 0 else 0

        # Pattern "42" simplifié - on va créer un motif visible
        # On choisit un coin pour placer le pattern
        pattern_x = width - 4  # Près du bord droit
        pattern_y = height - 4  # Près du bord bas

        # Créer des cellules fermées formant "42"
        # Ligne 1: XXXX (4)
        for x in range(4):
            if pattern_x + x < width and pattern_y < height:
                maze[pattern_y][pattern_x + x].walls = 15

        # Ligne 2: X  X (4)
        if pattern_y + 1 < height:
            maze[pattern_y + 1][pattern_x].walls = 15
            maze[pattern_y + 1][pattern_x + 3].walls = 15

        # Ligne 3: XXXX (4)
        if pattern_y + 2 < height:
            for x in range(4):
                if pattern_x + x < width:
                    maze[pattern_y + 2][pattern_x + x].walls = 15

        # Ligne 4:    X (2)
        if pattern_y + 3 < height:
            maze[pattern_y + 3][pattern_x + 3].walls = 15

    @staticmethod
    def prevent_large_open_areas(maze: List[List[Cell]]) -> None:
        """
        Empêche les zones ouvertes de plus de 2 cellules de large

        Args:
            maze: Grille du labyrinthe
        """
        height = len(maze)
        width = len(maze[0]) if height > 0 else 0

        # Vérifier chaque bloc 3x3
        for y in range(height - 2):
            for x in range(width - 2):
                if MazeUtils._is_open_3x3_block(maze, x, y):
                    # Fermer un mur au hasard dans ce bloc
                    MazeUtils._close_random_wall_in_block(maze, x, y)

    @staticmethod
    def _check_no_large_open_areas(maze: List[List[Cell]]) -> bool:
        """Vérifie qu'il n'y a pas de zones 3x3 ouvertes"""
        height = len(maze)
        width = len(maze[0]) if height > 0 else 0

        for y in range(height - 2):
            for x in range(width - 2):
                if MazeUtils._is_open_3x3_block(maze, x, y):
                    return False
        return True

    @staticmethod
    def _is_open_3x3_block(maze: List[List[Cell]], start_x: int, start_y: int) -> bool:
        """Vérifie si un bloc 3x3 est entièrement ouvert"""
        # Compter les cellules ouvertes (sans murs) dans le bloc 3x3
        open_cells = 0
        total_cells = 9

        for dy in range(3):
            for dx in range(3):
                cell = maze[start_y + dy][start_x + dx]
                # Une cellule est considérée ouverte si elle a au moins 2 murs ouverts
                open_walls = 4 - bin(cell.walls).count('1')
                if open_walls >= 2:  # Au moins 2 directions ouvertes
                    open_cells += 1

        return open_cells >= 7  # Plus de 7 cellules "ouvertes" = zone ouverte

    @staticmethod
    def _close_random_wall_in_block(maze: List[List[Cell]], start_x: int, start_y: int) -> None:
        """Ferme un mur au hasard dans un bloc 3x3"""
        import random

        # Collecter tous les murs ouverts dans le bloc
        open_walls = []

        for dy in range(3):
            for dx in range(3):
                cell = maze[start_y + dy][start_x + dx]
                x, y = start_x + dx, start_y + dy

                # Vérifier chaque direction
                if not cell.north_wall and y > 0:
                    open_walls.append((x, y, 'N'))
                if not cell.east_wall and x < len(maze[0]) - 1:
                    open_walls.append((x, y, 'E'))
                if not cell.south_wall and y < len(maze) - 1:
                    open_walls.append((x, y, 'S'))
                if not cell.west_wall and x > 0:
                    open_walls.append((x, y, 'W'))

        if open_walls:
            # Fermer un mur au hasard
            x, y, direction = random.choice(open_walls)
            cell = maze[y][x]

            if direction == 'N':
                cell.walls |= 8  # Fermer mur Nord
                if y > 0:
                    maze[y-1][x].walls |= 2  # Fermer mur Sud du voisin
            elif direction == 'E':
                cell.walls |= 4  # Fermer mur Est
                if x < len(maze[0]) - 1:
                    maze[y][x+1].walls |= 1  # Fermer mur Ouest du voisin
            elif direction == 'S':
                cell.walls |= 2  # Fermer mur Sud
                if y < len(maze) - 1:
                    maze[y+1][x].walls |= 8  # Fermer mur Nord du voisin
            elif direction == 'W':
                cell.walls |= 1  # Fermer mur Ouest
                if x > 0:
                    maze[y][x-1].walls |= 4  # Fermer mur Est du voisin

    @staticmethod
    def _check_42_pattern(maze: List[List[Cell]]) -> bool:
        """Vérifie la présence du pattern '42'"""
        height = len(maze)
        width = len(maze[0]) if height > 0 else 0

        # Chercher un pattern ressemblant à "42"
        # Pour simplifier, on cherche au moins 4 cellules fermées alignées
        for y in range(height):
            for x in range(width - 3):
                if all(maze[y][x + i].walls == 15 for i in range(4)):
                    return True

        for x in range(width):
            for y in range(height - 3):
                if all(maze[y + i][x].walls == 15 for i in range(4)):
                    return True

        return False