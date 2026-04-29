#!/usr/bin/env python3
"""
A-Maze-ing — main entry point.

Usage:
    python3 a_maze_ing.py config.txt
"""

import sys

from src.config_parser import parse_config
from src.output_writer import write_output
from src.visualizer import run_interactive
from mazegen import MazeGenerator
from mazegen.pattern42 import Pattern42


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

    locked = Pattern42(config["WIDTH"], config["HEIGHT"]).get_cells()
    for label, pos in [("ENTRY", config["ENTRY"]), ("EXIT", config["EXIT"])]:
        if pos in locked:
            print(
                f"[Erreur config] {label} {pos} est sur le pattern '42'. "
                "Choisissez une autre position.",
                file=sys.stderr,
            )
            sys.exit(1)

    try:
        gen = MazeGenerator(
            width=config["WIDTH"],
            height=config["HEIGHT"],
            seed=config.get("SEED"),
            perfect=config["PERFECT"],
            algorithm=config["ALGORITHM"],
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

    display_mode = config.get("DISPLAYMODE", "auto")
    try:
        run_interactive(
            gen,
            config["ENTRY"],
            config["EXIT"],
            theme=config["THEME"],
            display_mode=display_mode,
        )
    except RuntimeError as e:
        print(f"[Erreur affichage] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()