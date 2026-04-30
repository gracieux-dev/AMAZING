"""
Configuration parser - Reads and validates config.txt
"""

from typing import Any
from pathlib import Path


def parse_config(filepath: str) -> dict[str, Any]:
    """
    Parse the configuration file

    Args:
        filepath: Path to the config.txt file

    Returns:
        Dictionary with validated parameters

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the configuration is invalid
    """
    config: dict[str, Any] = {}
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")

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
                    # Type conversion
                    if key in ['WIDTH', 'HEIGHT', 'SEED']:
                        config[key] = int(value)
                    elif key in ['ENTRY', 'EXIT']:
                        parts = value.split(',')
                        if len(parts) != 2:
                            raise ValueError(f"Invalid position at line {line_num}")
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
                                f"Invalid DISPLAYMODE at line {line_num}: {value}"
                            )
                        config['DISPLAYMODE'] = mode
                    else:
                        config[key] = value
                except ValueError as e:
                    raise ValueError(f"Error at line {line_num}: {e}")

    required_keys = [
        'WIDTH', 'HEIGHT', 'ENTRY', 'EXIT', 'OUTPUT_FILE',
        'PERFECT', 'THEME', 'ALGORITHM',
    ]
    missing = [key for key in required_keys if key not in config]
    if missing:
        raise ValueError(
            f"Missing configuration key(s): {', '.join(missing)}"
        )

    # Validation
    _validate_config(config)

    return config


def _validate_config(config: dict[str, Any]) -> None:
    """
    Validates the configuration

    Args:
        config: Configuration to validate

    Raises:
        ValueError: If the configuration is invalid
    """
    width = config['WIDTH']
    height = config['HEIGHT']
    entry = config['ENTRY']
    exit_pos = config['EXIT']

    if width <= 0 or height <= 0:
        raise ValueError("WIDTH and HEIGHT must be > 0")

    if not _is_valid_position(entry, width, height):
        raise ValueError(f"ENTRY {entry} invalid for dimensions {width}x{height}")

    if not _is_valid_position(exit_pos, width, height):
        raise ValueError(f"EXIT {exit_pos} invalid for dimensions {width}x{height}")

    if entry == exit_pos:
        raise ValueError("ENTRY and EXIT must be different")

    if 'SEED' in config:
        seed = config['SEED']
        if not isinstance(seed, int) or seed < 0:
            raise ValueError("SEED must be a non-negative integer")

    if 'DISPLAYMODE' in config:
        display_mode = config['DISPLAYMODE']
        if display_mode not in ('auto', 'mlx', 'terminal', 'none'):
            raise ValueError(
                "DISPLAYMODE must be one of: auto, mlx, terminal, none"
            )


def _is_valid_position(pos: tuple[int, int], width: int, height: int) -> bool:
    """Checks if a position is valid within the grid"""
    x, y = pos
    return 0 <= x < width and 0 <= y < height
