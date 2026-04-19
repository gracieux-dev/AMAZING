# Choix algorithmique

## Algorithme principal: Recursive Backtracking

**Pourquoi cet algorithme ?**
- Génère des labyrinthes parfaits (un seul chemin entre toutes les cellules si PERFECT=True)
- Simple à implémenter et comprendre
- Respecte automatiquement les contraintes de cohérence des murs
- Peut être adapté pour éviter les zones ouvertes

**Avantages:**
- Garantit un labyrinthe parfait si demandé
- Contrôle facile des contraintes
- Performance acceptable pour tailles raisonnables (jusqu'à 100x100)
- Implémentation récursive élégante

**Inconvénients:**
- Peut créer des chemins longs et tortueux
- Moins "naturel" que d'autres algorithmes
- Limite de récursion pour très grands labyrinthes

## Implémentation technique

### Structure des cellules
Chaque cellule utilise 4 bits pour représenter les murs :
- Bit 8 (128): Mur Nord
- Bit 4 (64): Mur Est
- Bit 2 (32): Mur Sud
- Bit 1 (16): Mur Ouest

### Algorithme de backtracking
1. Initialiser grille avec tous murs fermés (walls = 15)
2. Choisir cellule de départ aléatoire
3. Explorer récursivement les voisins non visités
4. Supprimer murs entre cellules adjacentes
5. Rétrograder quand plus de voisins

### Gestion des contraintes
- **Cohérence**: murs toujours supprimés par paires
- **Zones 3x3**: vérification post-génération et correction
- **Pattern "42"**: cellules fermées formant un motif visible
- **Chemin solution**: calculé avec A* pour optimisation

## Alternatives envisagées:
- **Kruskal**: Plus rapide, mais moins contrôle sur les contraintes
- **Prim**: Similaire au backtracking, mais plus complexe
- **Division récursive**: Bonne pour éviter zones ouvertes, mais moins flexible

## Optimisations futures
- Version itérative du backtracking pour éviter limites de récursion
- Algorithme adaptatif selon la taille du labyrinthe
- Génération progressive pour très grands labyrinthes