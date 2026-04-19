# Documentation API
# Ce fichier contient la documentation détaillée des classes et fonctions

## Classes principales

### MazeGenerator
Classe principale pour générer des labyrinthes.

**Méthodes:**
- `generate()`: Génère le labyrinthe complet avec contraintes
- `save_to_file()`: Sauvegarde au format hexadécimal + chemin solution
- `get_hex_representation()`: Retourne la chaîne hex du labyrinthe

**Attributs:**
- `config`: Configuration du labyrinthe
- `maze`: Grille 2D de cellules
- `solution_path`: Liste des positions du chemin solution

### Config
Gestionnaire de configuration.

**Méthodes:**
- `from_file(filepath)`: Charge depuis un fichier config.txt

**Attributs:**
- `width`, `height`: Dimensions
- `entry`, `exit`: Positions tuple (x, y)
- `output_file`: Chemin du fichier de sortie
- `perfect`: Booléen pour labyrinthe parfait
- `seed`: Graine pour reproductibilité

### Cell
Représente une cellule du labyrinthe.

**Propriétés:**
- `north_wall`, `east_wall`, `south_wall`, `west_wall`: Booléens
- `walls`: Entier 4 bits (0-15)

### Display
Gestionnaire d'affichage ASCII.

**Méthodes:**
- `show()`: Affiche le labyrinthe en ASCII
- `toggle_solution()`: Bascule affichage du chemin solution
- `regenerate()`: Régénère un nouveau labyrinthe

## Modules utilitaires

### MazeAlgorithms
Collection d'algorithmes de génération.

**Méthodes statiques:**
- `recursive_backtracking(width, height, seed)`: Backtracking récursif
- `kruskal(width, height, seed)`: Algorithme de Kruskal

### MazeUtils
Utilitaires pour validation et calculs.

**Méthodes statiques:**
- `validate_constraints(maze)`: Vérifie toutes les contraintes
- `find_solution_path(maze, start, end)`: Calcule le chemin avec A*
- `add_42_pattern(maze)`: Ajoute le motif "42"
- `prevent_large_open_areas(maze)`: Corrige les zones 3x3 ouvertes

## Format de sortie

### Fichier hexadécimal
Chaque cellule = 1 caractère hexadécimal (0-F)
- 0 = tous murs ouverts
- F (15) = tous murs fermés
- Bits: 8=Nord, 4=Est, 2=Sud, 1=Ouest

### Chemin solution
Chaîne de lettres N/E/S/W indiquant les directions
Exemple: "EESNWW" pour Est→Est→Sud→Nord→Ouest→Ouest

## Exemple d'utilisation

```python
from mazegen import MazeGenerator, Config

config = Config.from_file("config.txt")
generator = MazeGenerator(config)
maze = generator.generate()
generator.save_to_file()

from mazegen.display import Display
display = Display(generator)
display.show()
```