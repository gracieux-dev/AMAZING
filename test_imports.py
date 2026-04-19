#!/usr/bin/env python3
"""
Test script to validate imports and basic functionality
"""

def test_imports():
    """Test that all modules can be imported"""
    try:
        # Test mazegen package imports
        from mazegen import MazeGenerator, MazeSolver, Pattern42
        print("✓ mazegen imports successful")

        # Test src module imports
        from src.config_parser import parse_config
        from src.output_writer import write_output
        from src.visualizer import MazeVisualizer
        print("✓ src imports successful")

        # Test basic instantiation
        gen = MazeGenerator(width=5, height=5, seed=42, perfect=True)
        print("✓ MazeGenerator instantiation successful")

        solver = MazeSolver([[0]])
        print("✓ MazeSolver instantiation successful")

        pattern42 = Pattern42()
        print("✓ Pattern42 instantiation successful")

        print("\n🎉 All imports and basic instantiations successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_imports()