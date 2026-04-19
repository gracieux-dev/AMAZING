"""
Gestionnaire de configuration
Lit et valide le fichier de configuration
"""

from typing import Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    """
    Configuration du labyrinthe

    Attributes:
        width (int): Largeur du labyrinthe
        height (int): Hauteur du labyrinthe
        entry (Tuple[int, int]): Position d'entrée
        exit (Tuple[int, int]): Position de sortie
        output_file (str): Fichier de sortie
        perfect (bool): Labyrinthe parfait (un seul chemin)
        seed (int): Graine pour la génération aléatoire
    """

    width: int
    height: int
    entry: Tuple[int, int]
    exit: Tuple[int, int]
    output_file: str
    perfect: bool
    seed: int

    @classmethod
    def from_file(cls, filepath: str) -> 'Config':
        """
        Charge la configuration depuis un fichier

        Args:
            filepath: Chemin vers le fichier de config

        Returns:
            Instance de Config
        """
        config = {}
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"Fichier de config non trouvé: {filepath}")

        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Conversion des types
                    if key in ['WIDTH', 'HEIGHT', 'SEED']:
                        config[key.lower()] = int(value)
                    elif key in ['ENTRY', 'EXIT']:
                        x, y = map(int, value.split(','))
                        config[key.lower()] = (x, y)
                    elif key == 'PERFECT':
                        config[key.lower()] = value.lower() == 'true'
                    else:
                        config[key.lower()] = value

        return cls(
            width=config.get('width', 20),
            height=config.get('height', 15),
            entry=config.get('entry', (0, 0)),
            exit=config.get('exit', (19, 14)),
            output_file=config.get('output_file', 'maze.txt'),
            perfect=config.get('perfect', True),
            seed=config.get('seed', 42)
        )