#!/usr/bin/env python3
"""
A-Maze-ing — main entry point.

Usage:
    python3 a_maze_ing.py config.txt
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
sys.path.insert(0, os.path.dirname(__file__))

from src.config_parser import parse_config
from src.output_writer import write_output
from src.visualizer import run_interactive
from mazegen import MazeGenerator


def main() -> None:
    """Parse config, generate maze, write output, launch visualizer."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        config = parse_config(config_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"[Erreur config] {e}", file=sys.stderr)
        sys.exit(1)

    try:
        gen = MazeGenerator(
            width=config["WIDTH"],
            height=config["HEIGHT"],
            seed=config["SEED"],
            perfect=config["PERFECT"],
        )
        gen.generate()
    except ValueError as e:
        print(f"[Erreur génération] {e}", file=sys.stderr)
        sys.exit(1)

    try:
        write_output(gen, config["ENTRY"], config["EXIT"], config["OUTPUT_FILE"])
        print(f"Labyrinthe sauvegardé dans '{config['OUTPUT_FILE']}'.")
    except OSError as e:
        print(f"[Erreur écriture] {e}", file=sys.stderr)
        sys.exit(1)

    run_interactive(
        gen,
        config["ENTRY"],
        config["EXIT"],
        theme=config.get("THEME", "spring"),
    )


if __name__ == "__main__":
    main()