"""
Parseur de configuration - Lit et valide config.txt
"""

from typing import Any
from pathlib import Path

def parse_config(filepath: str) -> dict[str, Any]:
    """
    Parse le fichier de configuration

    Args:
        filepath: Chemin vers le fichier config.txt

    Returns:
        Dictionnaire avec les paramètres validés

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        ValueError: Si la configuration est invalide
    """
    config = {}
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Fichier de config non trouvé: {filepath}")

    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip().upper()
                value = value.strip()

                try:
                    # Conversion des types
                    if key in ['WIDTH', 'HEIGHT', 'SEED']:
                        config[key] = int(value)
                    elif key in ['ENTRY', 'EXIT']:
                        parts = value.split(',')
                        if len(parts) != 2:
                            raise ValueError(f"Position invalide à la ligne {line_num}")
                        config[key] = tuple(map(int, parts))
                    elif key == 'PERFECT':
                        config[key] = value.lower() in ('true', '1', 'yes', 'on')
                    elif key in ['DISPLAYMODE', 'DISPLAY_MODE']:
                        mode = value.strip().lower()
                        if mode in ('default', 'auto', 'detect'):
                            mode = 'auto'
                        elif mode in ('terminal', 'text', 'tty'):
                            mode = 'terminal'
                        elif mode in ('mlx', 'gui', 'graphical'):
                            mode = 'mlx'
                        elif mode in ('none', 'off', 'no'):
                            mode = 'none'
                        if mode not in ('auto', 'mlx', 'terminal', 'none'):
                            raise ValueError(
                                f"DISPLAYMODE invalide à la ligne {line_num}: {value}"
                            )
                        config['DISPLAYMODE'] = mode
                    else:
                        config[key] = value
                except ValueError as e:
                    raise ValueError(f"Erreur à la ligne {line_num}: {e}")

    required_keys = [
        'WIDTH', 'HEIGHT', 'ENTRY', 'EXIT', 'OUTPUT_FILE',
        'PERFECT', 'THEME', 'ALGORITHM',
    ]
    missing = [key for key in required_keys if key not in config]
    if missing:
        raise ValueError(
            f"Clé(s) de configuration manquante(s) : {', '.join(missing)}"
        )

    # Validation
    _validate_config(config)

    return config

def _validate_config(config: dict[str, Any]) -> None:
    """
    Valide la configuration

    Args:
        config: Configuration à valider

    Raises:
        ValueError: Si la configuration est invalide
    """
    width = config['WIDTH']
    height = config['HEIGHT']
    entry = config['ENTRY']
    exit_pos = config['EXIT']

    if width <= 0 or height <= 0:
        raise ValueError("WIDTH et HEIGHT doivent être > 0")

    if not _is_valid_position(entry, width, height):
        raise ValueError(f"ENTRY {entry} invalide pour dimensions {width}x{height}")

    if not _is_valid_position(exit_pos, width, height):
        raise ValueError(f"EXIT {exit_pos} invalide pour dimensions {width}x{height}")

    if entry == exit_pos:
        raise ValueError("ENTRY et EXIT doivent être différents")

    if 'SEED' in config:
        seed = config['SEED']
        if not isinstance(seed, int) or seed < 0:
            raise ValueError("SEED doit être un entier positif ou nul")

    if 'DISPLAYMODE' in config:
        display_mode = config['DISPLAYMODE']
        if display_mode not in ('auto', 'mlx', 'terminal', 'none'):
            raise ValueError(
                "DISPLAYMODE doit être l'un de: auto, mlx, terminal, none"
            )

def _is_valid_position(pos: tuple[int, int], width: int, height: int) -> bool:
    """Vérifie si une position est valide dans la grille"""
    x, y = pos
    return 0 <= x < width and 0 <= y < height