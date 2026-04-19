"""
Tests unitaires pour le générateur de labyrinthes
"""

import unittest
from src.mazegen.generator import MazeGenerator, Cell
from src.mazegen.config import Config

class TestMazeGenerator(unittest.TestCase):
    """Tests pour MazeGenerator"""

    def setUp(self):
        """Configuration des tests"""
        self.config = Config(width=10, height=10, entry=(0,0), exit=(9,9),
                           output_file="test.txt", perfect=True, seed=42)

    def test_initialization(self):
        """Test d'initialisation"""
        generator = MazeGenerator(self.config)
        self.assertEqual(generator.config.width, 10)

    def test_cell_walls(self):
        """Test des propriétés des murs des cellules"""
        cell = Cell(0, 0, 10)  # 1010 en binaire
        self.assertTrue(cell.north_wall)
        self.assertFalse(cell.east_wall)
        self.assertTrue(cell.south_wall)
        self.assertFalse(cell.west_wall)

if __name__ == '__main__':
    unittest.main()