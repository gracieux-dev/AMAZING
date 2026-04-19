"""
Exemple d'utilisation du package mazegen
"""

from mazegen import MazeGenerator, Config

def main():
    """Exemple simple d'utilisation"""

    # Configuration
    config = Config(
        width=20,
        height=15,
        entry=(0, 0),
        exit=(19, 14),
        output_file="example_maze.txt",
        perfect=True,
        seed=42
    )

    # Génération
    generator = MazeGenerator(config)
    maze = generator.generate()

    # Sauvegarde
    generator.save_to_file()

    print("Labyrinthe généré et sauvegardé dans example_maze.txt")

if __name__ == "__main__":
    main()