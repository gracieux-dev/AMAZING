#!/usr/bin/env python3
"""
Test script complet pour valider toutes les modifications
"""

def test_imports():
    """Test que tous les modules peuvent être importés"""
    try:
        from mazegen import MazeGenerator, MazeSolver, Pattern42
        from src.config_parser import parse_config
        from src.output_writer import write_output, OutputWriter
        from src.visualizer import MazeVisualizer, run_interactive
        print("✓ Tous les imports réussis")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def test_maze_generation():
    """Test de génération de labyrinthe"""
    try:
        from mazegen import MazeGenerator

        gen = MazeGenerator(width=10, height=8, seed=42, perfect=True)
        gen.generate()

        assert hasattr(gen, 'grid'), "Generator doit avoir un attribut grid"
        assert len(gen.grid) == 8, "Hauteur incorrecte"
        assert len(gen.grid[0]) == 10, "Largeur incorrecte"
        assert all(isinstance(cell, int) for row in gen.grid for cell in row), "Les cellules doivent être des entiers"

        print("✓ Génération de labyrinthe réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur génération: {e}")
        return False

def test_solver():
    """Test du solveur"""
    try:
        from mazegen import MazeGenerator, MazeSolver

        gen = MazeGenerator(width=5, height=5, seed=42, perfect=True)
        gen.generate()

        solver = MazeSolver(gen)
        path = solver.solve((0, 0), (4, 4))

        assert isinstance(path, list), "Le chemin doit être une liste"
        assert all(isinstance(step, str) for step in path), "Chaque étape doit être une string"
        assert all(step in 'NSEW' for step in path), "Directions invalides"

        print(f"✓ Solveur réussi, chemin trouvé: {len(path)} étapes")
        return True
    except Exception as e:
        print(f"❌ Erreur solveur: {e}")
        return False

def test_pattern42():
    """Test du pattern 42"""
    try:
        from mazegen import Pattern42

        p42 = Pattern42(20, 15)
        cells = p42.get_cells()

        assert isinstance(cells, set), "get_cells doit retourner un set"
        assert all(isinstance(pos, tuple) and len(pos) == 2 for pos in cells), "Positions invalides"

        print(f"✓ Pattern42 réussi, {len(cells)} cellules dans le pattern")
        return True
    except Exception as e:
        print(f"❌ Erreur Pattern42: {e}")
        return False

def test_output_writer():
    """Test de l'output writer"""
    try:
        from mazegen import MazeGenerator, MazeSolver
        from src.output_writer import OutputWriter

        gen = MazeGenerator(width=5, height=5, seed=42, perfect=True)
        gen.generate()

        solver = MazeSolver(gen)
        path = solver.solve((0, 0), (4, 4))

        writer = OutputWriter(gen.grid, path)
        content = writer.get_hex_content()

        assert isinstance(content, str), "Le contenu doit être une string"
        lines = content.split('\n')
        assert len(lines) == 6, "Doit avoir 5 lignes de grille + 1 ligne de chemin"
        assert len(lines[0]) == 5, "Chaque ligne doit avoir 5 caractères hex"

        print("✓ Output writer réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur output writer: {e}")
        return False

def test_config_parser():
    """Test du parseur de config"""
    try:
        import tempfile
        import os
        from src.config_parser import parse_config

        # Créer un fichier de config temporaire
        config_content = """WIDTH=15
HEIGHT=10
SEED=123
ENTRY=0,0
EXIT=14,9
PERFECT=true
OUTPUT_FILE=test.txt
THEME=summer"""

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
            assert config['PERFECT'] == True
            assert config['OUTPUT_FILE'] == 'test.txt'
            assert config['THEME'] == 'summer'

            print("✓ Config parser réussi")
            return True
        finally:
            os.unlink(config_path)

    except Exception as e:
        print(f"❌ Erreur config parser: {e}")
        return False

def run_all_tests():
    """Lance tous les tests"""
    print("🚀 Lancement des tests complets...\n")

    tests = [
        ("Imports", test_imports),
        ("Génération", test_maze_generation),
        ("Solveur", test_solver),
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

    print(f"📊 Résultats: {passed}/{total} tests réussis")

    if passed == total:
        print("🎉 Tous les tests sont passés! Le code est fonctionnel.")
        return True
    else:
        print("❌ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return False

if __name__ == "__main__":
    run_all_tests()