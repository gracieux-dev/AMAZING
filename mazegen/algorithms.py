"""
Algorithmes de génération de labyrinthes
"""

from typing import List, Tuple, Set
import random
from .generator import Cell

class MazeAlgorithms:
    """Collection d'algorithmes de génération"""

    @staticmethod
    def recursive_backtracking(width: int, height: int, seed: int = None) -> List[List[Cell]]:
        """
        Algorithme de backtracking récursif

        Args:
            width: Largeur du labyrinthe
            height: Hauteur du labyrinthe
            seed: Graine pour la reproductibilité

        Returns:
            Grille générée
        """
        if seed is not None:
            random.seed(seed)

        # Initialiser la grille avec toutes les cellules fermées
        maze = [[Cell(x, y, 15) for x in range(width)] for y in range(height)]

        # Pile pour le backtracking
        stack = []

        # Directions: Nord, Est, Sud, Ouest
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        # Bits correspondants pour chaque direction
        wall_bits = [(2, 8), (1, 4), (8, 2), (4, 1)]  # (mur actuel, mur voisin)

        # Fonction récursive pour creuser
        def carve(x: int, y: int):
            # Marquer comme visitée (on pourrait utiliser un set visited, mais on utilise les murs)
            # Au lieu de ça, on va vérifier si une cellule a des murs ouverts

            # Obtenir les voisins non visités (cellules avec tous les murs fermés)
            neighbors = []
            for i, (dy, dx) in enumerate(directions):
                ny, nx = y + dy, x + dx
                if 0 <= nx < width and 0 <= ny < height:
                    neighbor = maze[ny][nx]
                    # Considérer comme non visitée si elle a tous les murs fermés
                    if neighbor.walls == 15:
                        neighbors.append((nx, ny, i))

            # Mélanger les voisins pour l'aléatoire
            random.shuffle(neighbors)

            # Visiter chaque voisin
            for nx, ny, dir_idx in neighbors:
                neighbor = maze[ny][nx]
                if neighbor.walls == 15:  # Encore non visitée
                    # Supprimer les murs entre la cellule courante et le voisin
                    current_bit, neighbor_bit = wall_bits[dir_idx]
                    maze[y][x].walls &= ~current_bit
                    neighbor.walls &= ~neighbor_bit

                    # Récursion
                    carve(nx, ny)

        # Commencer depuis une cellule aléatoire (ou l'entrée si spécifiée)
        start_x = random.randint(0, width - 1)
        start_y = random.randint(0, height - 1)
        carve(start_x, start_y)

        return maze

    @staticmethod
    def kruskal(width: int, height: int, seed: int = None) -> List[List[Cell]]:
        """
        Algorithme de Kruskal

        Args:
            width: Largeur du labyrinthe
            height: Hauteur du labyrinthe
            seed: Graine pour la reproductibilité

        Returns:
            Grille générée
        """
        if seed is not None:
            random.seed(seed)

        # Initialiser la grille avec toutes les cellules fermées
        maze = [[Cell(x, y, 15) for x in range(width)] for y in range(height)]

        # Structure Union-Find pour les ensembles
        parent = {}
        rank = {}

        def find(cell_id):
            if parent[cell_id] != cell_id:
                parent[cell_id] = find(parent[cell_id])
            return parent[cell_id]

        def union(cell1_id, cell2_id):
            root1 = find(cell1_id)
            root2 = find(cell2_id)
            if root1 != root2:
                if rank[root1] > rank[root2]:
                    parent[root2] = root1
                elif rank[root1] < rank[root2]:
                    parent[root1] = root2
                else:
                    parent[root2] = root1
                    rank[root1] += 1

        # Initialiser Union-Find
        for y in range(height):
            for x in range(width):
                cell_id = (x, y)
                parent[cell_id] = cell_id
                rank[cell_id] = 0

        # Créer la liste de tous les murs possibles
        walls = []

        # Murs horizontaux
        for y in range(height):
            for x in range(width - 1):
                walls.append(((x, y), (x + 1, y), 'E'))  # Mur Est

        # Murs verticaux
        for y in range(height - 1):
            for x in range(width):
                walls.append(((x, y), (x, y + 1), 'S'))  # Mur Sud

        # Mélanger les murs
        random.shuffle(walls)

        # Traiter chaque mur
        for (x1, y1), (x2, y2), direction in walls:
            cell1_id = (x1, y1)
            cell2_id = (x2, y2)

            # Si les cellules ne sont pas dans le même ensemble
            if find(cell1_id) != find(cell2_id):
                # Supprimer le mur
                if direction == 'E':
                    # Supprimer mur Est de cell1 et mur Ouest de cell2
                    maze[y1][x1].walls &= ~4  # ~0100 = 1011
                    maze[y2][x2].walls &= ~1  # ~0001 = 1110
                elif direction == 'S':
                    # Supprimer mur Sud de cell1 et mur Nord de cell2
                    maze[y1][x1].walls &= ~2  # ~0010 = 1101
                    maze[y2][x2].walls &= ~8  # ~1000 = 0111

                # Unir les ensembles
                union(cell1_id, cell2_id)

        return maze