"""
Unit tests for the maze generator
"""

import unittest
from src.mazegen.generator import MazeGenerator, Cell
from src.mazegen.config import Config


class TestMazeGenerator(unittest.TestCase):
    """Tests for MazeGenerator"""

    def setUp(self) -> None:
        """Test setup"""
        self.config = Config(width=10, height=10, entry=(0, 0), exit=(9, 9),
                             output_file="test.txt", perfect=True, seed=42)

    def test_initialization(self) -> None:
        """Initialization test"""
        generator = MazeGenerator(self.config)
        self.assertEqual(generator.config.width, 10)

    def test_cell_walls(self) -> None:
        """Test cell wall properties"""
        cell = Cell(0, 0, 10)  # 1010 in binary
        self.assertTrue(cell.north_wall)
        self.assertFalse(cell.east_wall)
        self.assertTrue(cell.south_wall)
        self.assertFalse(cell.west_wall)


if __name__ == '__main__':
    unittest.main()
