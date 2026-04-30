"""
Tests pour la configuration
"""

import unittest
import tempfile
import os
from src.mazegen.config import Config


class TestConfig(unittest.TestCase):
    """Tests pour Config"""

    def test_from_file(self) -> None:
        """Test de chargement depuis fichier"""
        config_content = """WIDTH=15
HEIGHT=10
ENTRY=0,0
EXIT=14,9
OUTPUT_FILE=test.txt
PERFECT=True
SEED=123
"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(config_content)
            f.flush()

            try:
                config = Config.from_file(f.name)
                self.assertEqual(config.width, 15)
                self.assertEqual(config.height, 10)
                self.assertEqual(config.entry, (0, 0))
                self.assertEqual(config.exit, (14, 9))
                self.assertEqual(config.output_file, "test.txt")
                self.assertTrue(config.perfect)
                self.assertEqual(config.seed, 123)
            finally:
                os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
