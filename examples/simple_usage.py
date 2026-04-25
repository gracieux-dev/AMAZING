"""
Exemple d'utilisation du package mazegen
"""

from mazegen import MazeGenerator
from src.output_writer import write_output


def main():
    """Exemple simple d'utilisation"""
    entry = (0, 0)
    exit_pos = (19, 14)

    generator = MazeGenerator(width=20, height=15, seed=42, perfect=True)
    generator.generate()

    write_output(generator, entry, exit_pos, "example_maze.txt")
    print("Labyrinthe généré et sauvegardé dans example_maze.txt")


if __name__ == "__main__":
    main()
