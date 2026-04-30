#!/usr/bin/env python3
"""
Complete test script to validate all modifications
"""


def test_all_imports() -> bool:
    """Test that all modules can be imported"""
    try:
        from mazegen import MazeGenerator, MazeSolver, Pattern42  # noqa: F401
        from src.config_parser import parse_config  # noqa: F401
        from src.output_writer import write_output, OutputWriter  # noqa: F401
        from src.visualizer import run_interactive  # noqa: F401
        print("OK All imports successful")
        return True
    except ImportError as e:
        print(f"FAIL Import error: {e}")
        return False


def test_maze_generation() -> bool:
    """Test maze generation"""
    try:
        from mazegen import MazeGenerator

        gen = MazeGenerator(width=10, height=8, seed=42, perfect=True)
        gen.generate()

        assert hasattr(gen, 'grid'), "Generator must have a grid attribute"
        assert len(gen.grid) == 8, "Incorrect height"
        assert len(gen.grid[0]) == 10, "Incorrect width"
        assert all(
            isinstance(cell, int) for row in gen.grid for cell in row
        ), "Cells must be integers"

        print("OK Maze generation successful")
        return True
    except Exception as e:
        print(f"FAIL Generation error: {e}")
        return False


def test_solver() -> bool:
    """Test the solver"""
    try:
        from mazegen import MazeGenerator, MazeSolver

        gen = MazeGenerator(width=5, height=5, seed=42, perfect=True)
        gen.generate()

        solver = MazeSolver(gen)
        path = solver.solve((0, 0), (4, 4))

        assert isinstance(path, list), "Path must be a list"
        assert all(isinstance(step, str) for step in path), "Each step must be a string"
        assert all(step in 'NSEW' for step in path), "Invalid directions"

        print(f"OK Solver successful, path found: {len(path)} steps")
        return True
    except Exception as e:
        print(f"FAIL Solver error: {e}")
        return False


def test_pattern42() -> bool:
    """Test pattern 42"""
    try:
        from mazegen import Pattern42

        p42 = Pattern42(20, 15)
        cells = p42.get_cells()

        assert isinstance(cells, set), "get_cells must return a set"
        assert all(
            isinstance(pos, tuple) and len(pos) == 2 for pos in cells
        ), "Invalid positions"

        print(f"OK Pattern42 successful, {len(cells)} cells in pattern")
        return True
    except Exception as e:
        print(f"FAIL Pattern42 error: {e}")
        return False


def test_output_writer() -> bool:
    """Test the output writer"""
    try:
        from mazegen import MazeGenerator, MazeSolver
        from src.output_writer import OutputWriter

        gen = MazeGenerator(width=5, height=5, seed=42, perfect=True)
        gen.generate()

        solver = MazeSolver(gen)
        path = solver.solve((0, 0), (4, 4))

        writer = OutputWriter(gen.grid, (0, 0), (4, 4), path)
        content = writer.get_hex_content()

        assert isinstance(content, str), "Content must be a string"
        lines = content.split('\n')
        assert len(lines) >= 5, "Must have at least 5 grid lines"
        assert len(lines[0]) == 5, "Each line must have 5 hex characters"

        print("OK Output writer successful")
        return True
    except Exception as e:
        print(f"FAIL Output writer error: {e}")
        return False


def test_config_parser() -> bool:
    """Test the config parser"""
    try:
        import tempfile
        import os
        from src.config_parser import parse_config

        config_content = """WIDTH=15
HEIGHT=10
SEED=123
ENTRY=0,0
EXIT=14,9
PERFECT=true
OUTPUT_FILE=test.txt
DISPLAYMODE=terminal
THEME=summer
ALGORITHM=dfs"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = parse_config(config_path)

            assert config['WIDTH'] == 15
            assert config['HEIGHT'] == 10
            assert config['SEED'] == 123
            assert config['ENTRY'] == (0, 0)
            assert config['EXIT'] == (14, 9)
            assert config['PERFECT'] is True
            assert config['OUTPUT_FILE'] == 'test.txt'
            assert config['DISPLAYMODE'] == 'terminal'
            assert config['THEME'] == 'summer'

            print("OK Config parser successful")
            return True
        finally:
            os.unlink(config_path)

    except Exception as e:
        print(f"FAIL Config parser error: {e}")
        return False


def run_all_tests() -> bool:
    """Run all tests"""
    print("Running complete tests...\n")

    tests = [
        ("Imports", test_all_imports),
        ("Generation", test_maze_generation),
        ("Solver", test_solver),
        ("Pattern42", test_pattern42),
        ("Output Writer", test_output_writer),
        ("Config Parser", test_config_parser),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"Test: {name}")
        if test_func():
            passed += 1
        print()

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("All tests passed! The code is functional.")
        return True
    else:
        print("FAIL Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    run_all_tests()
