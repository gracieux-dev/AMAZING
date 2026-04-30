#!/usr/bin/env python3
"""
Test script to validate imports and basic functionality
"""


def test_imports() -> bool:
    """Test that all modules can be imported"""
    try:
        # Test mazegen package imports
        from mazegen import MazeGenerator, MazeSolver, Pattern42
        print("✓ mazegen imports successful")

        # Test src module imports
        from src.config_parser import parse_config  # noqa: F401
        from src.output_writer import write_output  # noqa: F401
        from src.visualizer import run_interactive  # noqa: F401
        print("✓ src imports successful")

        # Test basic instantiation
        gen = MazeGenerator(width=5, height=5, seed=42, perfect=True)
        gen.generate()
        print("✓ MazeGenerator instantiation successful")

        solver = MazeSolver(gen)
        path = solver.solve((0, 0), (4, 4))
        print(f"✓ MazeSolver instantiation successful ({len(path)} steps)")

        pattern42 = Pattern42(20, 15)
        print(f"✓ Pattern42 instantiation successful ({len(pattern42.get_cells())} cells)")

        print("\nOK All imports and basic instantiations successful!")
        return True

    except ImportError as e:
        print(f"FAIL Import error: {e}")
        return False
    except Exception as e:
        print(f"FAIL Error: {e}")
        return False


if __name__ == "__main__":
    test_imports()
