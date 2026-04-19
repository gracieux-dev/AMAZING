"""
Package mazegen - Générateur de labyrinthes réutilisable
"""

from .generator import MazeGenerator
from .solver import MazeSolver
from .pattern42 import Pattern42

__version__ = "1.0.0"
__all__ = ["MazeGenerator", "MazeSolver", "Pattern42"]