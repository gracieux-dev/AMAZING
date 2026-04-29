*This project has been created as part of the 42 curriculum by gracieux-dev.*

# A-Maze-ing

## Description

A-Maze-ing is a maze generator written in Python 3. Given a configuration file it:

- generates a random, reproducible maze via a seed,
- optionally produces a **perfect maze** (exactly one path between entry and exit),
- always embeds a visible **"42" pattern** made of fully closed cells,
- exports the maze to a file using a hexadecimal wall encoding,
- displays the maze interactively with an MLX graphical renderer.

## Instructions

### Requirements

Python 3.10 or later. The MLX library must be available for the visualiser.

### Install dependencies

```bash
make install
```

### Run

```bash
make run
# or directly:
python3 a_maze_ing.py config.txt
```

### Debug

```bash
make debug
```

### Lint

```bash
make lint          # flake8 + mypy (standard flags)
make lint-strict   # flake8 + mypy --strict
```

### Clean

```bash
make clean
```

## Config File Format

The config file uses one `KEY=VALUE` pair per line. Lines starting with `#` are ignored.

**Mandatory keys:**

| Key | Type | Description | Example |
|---|---|---|---|
| `WIDTH` | int | Maze width in cells | `WIDTH=20` |
| `HEIGHT` | int | Maze height in cells | `HEIGHT=20` |
| `ENTRY` | x,y | Entry cell coordinates | `ENTRY=1,0` |
| `EXIT` | x,y | Exit cell coordinates | `EXIT=15,8` |
| `OUTPUT_FILE` | string | Output filename | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | bool | Generate a perfect maze | `PERFECT=True` |

**Optional keys:**

| Key | Type | Default | Description |
|---|---|---|---|
| `SEED` | int | random | Random seed for reproducibility |
| `THEME` | string | `spring` | Visual theme: `spring`, `summer`, `autumn`, `winter` |

Example `config.txt`:

```
# A-Maze-ing configuration
WIDTH=20
HEIGHT=20
ENTRY=1,0
EXIT=15,8
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
THEME=spring
```

**Constraint:** `ENTRY` and `EXIT` must not overlap with any cell of the "42" pattern — the program will reject such a configuration with a clear error message.

## Output File Format

Each cell is encoded as one uppercase hexadecimal digit. Walls are encoded as a bitmask:

| Bit | Direction |
|---|---|
| 0 (LSB) | North |
| 1 | East |
| 2 | South |
| 3 | West |

A bit set to `1` means the wall is **closed**.

The file structure:
```
<hex grid, one row per line>

<entry x,y>
<exit x,y>
<shortest path as N/E/S/W letters>
```

## Maze Generation Algorithm

The generator uses the **recursive backtracker** (iterative DFS) algorithm.

### How it works

1. Every cell starts with all 4 walls closed.
2. The "42" pattern cells are locked (marked as already visited) so DFS skips them.
3. Starting from cell (0, 0), the algorithm picks a random unvisited neighbour, carves through the shared wall, and pushes the neighbour onto a stack.
4. When no unvisited neighbours are available it backtracks.
5. The process repeats until every non-locked cell has been visited.
6. If `PERFECT=False`, a small number of random walls are removed afterward to introduce loops.

### Why this algorithm?

- It naturally produces a **spanning tree** of the cell graph, guaranteeing a perfect maze with no isolated cells.
- It is straightforward to implement iteratively and trivially adapted to yield intermediate states for **step-by-step animation**.
- It generates mazes with long, winding corridors that are visually interesting and challenging to solve.

## Reusable Module — `mazegen`

The generation logic is packaged as a standalone pip-installable library. The pre-built packages are at the root of this repository:

```
mazegen-1.0.0-py3-none-any.whl
mazegen-1.0.0.tar.gz
```

### Install

```bash
pip install mazegen-1.0.0-py3-none-any.whl
# or from source:
pip install -e .
```

### Build from source

```bash
make build-package
# produces dist/mazegen-*.whl and dist/mazegen-*.tar.gz
```

### Quick example

```python
from mazegen import MazeGenerator, MazeSolver

# Instantiate and generate
gen = MazeGenerator(width=20, height=15, seed=42, perfect=True)
gen.generate()

# Access the raw grid — list[list[int]], one bitmask int per cell
# bit0=North, bit1=East, bit2=South, bit3=West; 1 = wall closed
for row in gen.grid:
    print(row)

# Hex representation (same encoding as the output file)
for line in gen.to_hex_grid():
    print(line)

# Solve the maze — returns a list of 'N'/'E'/'S'/'W' letters
solver = MazeSolver(gen)
path = solver.solve((0, 0), (19, 14))
print("".join(path))
```

### MazeGenerator parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `width` | `int` | required | Number of columns (≥ 3) |
| `height` | `int` | required | Number of rows (≥ 3) |
| `seed` | `int \| None` | `None` | Random seed |
| `perfect` | `bool` | `True` | Produce a perfect maze |

After calling `generate()`:
- `gen.grid` — the cell bitmask grid
- `gen.locked` — set of `(x, y)` cells belonging to the "42" pattern
- `gen.to_hex_grid()` — hex string representation
- `gen.generate_steps()` — generator that yields `(x, y)` after each carved step (for animation)

## Visual Display

The interactive display uses the MLX library.

| Key | Action |
|---|---|
| `R` | Re-generate with animation |
| `S` | Show / hide solution path |
| `T` | Cycle colour theme |
| `Enter` | Save `maze.txt` and quit |
| `Esc` | Quit without saving |

## Team and Project Management

**Team:** gracieux-dev (solo project)

**Planning:**
- Phase 1 — core generation: config parser, DFS algorithm, bitmask encoding, output writer
- Phase 2 — constraints: "42" pattern locking, perfect/imperfect modes, BFS solver
- Phase 3 — visualiser: MLX renderer, themes, animated generation
- Phase 4 — packaging: `pyproject.toml`, pip package, tests, README

**What worked well:** The iterative DFS made animation straightforward via `generate_steps()`. The bitmask encoding maps directly to the hex output format with no translation layer.

**What could be improved:** The loop-adding strategy for imperfect mazes could be more sophisticated to better control open-area density.

**Tools used:** Python 3.14, flake8, mypy, pytest, MLX, Claude (AI assistant).

## Resources

- [Maze generation algorithms — Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Recursive backtracker — jamisbuck.org](https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking)
- [Python `typing` module — docs.python.org](https://docs.python.org/3/library/typing.html)
- [flake8 documentation](https://flake8.pycqa.org/)
- [mypy documentation](https://mypy.readthedocs.io/)
- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/)

**AI usage (Claude — Anthropic):**
- Helped identify the missing entry/exit vs. "42" pattern validation.
- Suggested the `generate_steps()` generator pattern for step-by-step animation.
- Reviewed flake8/mypy diagnostics and proposed fixes.
- Drafted and reviewed docstrings following PEP 257.

All AI-generated content was reviewed, tested, and understood before inclusion.
