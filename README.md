*This project has been created as part of the 42 curriculum by olchacou, ancourt.*

# A-Maze-ing

## Description

A-Maze-ing is a maze generator written in Python 3. Given a configuration file it:

- generates a random, reproducible maze via a seed,
- optionally produces a **perfect maze** (exactly one path between entry and exit),
- always embeds a visible **"42" pattern** made of fully closed cells,
- exports the maze to a file using a hexadecimal wall encoding,
- displays the maze interactively with an MLX graphical renderer or a terminal curses fallback.

## Instructions

### Requirements

Python 3.10 or later. The MLX library must be available for the graphical visualiser.

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
| `THEME` | string | Visual theme: `spring`, `summer`, `autumn`, `winter` | `THEME=spring` |
| `ALGORITHM` | string | Generation algorithm: `dfs`, `kruskal` | `ALGORITHM=dfs` |

**Optional keys:**

| Key | Type | Default | Description |
|---|---|---|---|
| `SEED` | int | random | Random seed for reproducibility |
| `DISPLAYMODE` | string | `auto` | Display mode: `auto`, `mlx`, `terminal`, `none` (use `terminal` if MLX is slow or unreliable) |

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
DISPLAYMODE=auto
THEME=spring
ALGORITHM=dfs
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

## Maze Generation Algorithms

The generator supports two algorithms selectable via the `ALGORITHM` key.

### DFS — Recursive Backtracker (default)

The DFS algorithm works like an explorer carving tunnels through unvisited cells.

**How it works:**

1. Every cell starts with all 4 walls closed.
2. The "42" pattern cells are locked (marked as already visited) so DFS skips them.
3. Starting from cell (0, 0), the algorithm picks a random unvisited neighbour, carves through the shared wall, and pushes the neighbour onto a stack.
4. When no unvisited neighbours are available it backtracks by popping the stack.
5. The process repeats until every non-locked cell has been visited.
6. If `PERFECT=False`, a small number of random walls are removed afterward to introduce loops.

**Result:** Long winding corridors with few branches. The maze is challenging to navigate visually but has a single long solution path.

**Why this algorithm?**

- It naturally produces a spanning tree of the cell graph, guaranteeing a perfect maze with no isolated cells.
- It is straightforward to implement iteratively and trivially adapted to yield intermediate states for step-by-step animation via `generate_steps()`.

### Kruskal — Union-Find

The Kruskal algorithm treats the maze as a graph and builds a spanning tree by processing walls in random order.

**How it works:**

1. Every cell starts in its own group (Union-Find structure with N×M groups).
2. All internal walls are collected into a list and shuffled randomly.
3. For each wall in the shuffled list:
   - If the two cells on either side belong to **different groups**: remove the wall and merge the two groups.
   - If they already belong to the **same group**: skip the wall (removing it would create a cycle).
4. The process ends when all cells belong to a single group (N×M − 1 walls removed).

**Result:** Many short passages and frequent branching. The maze feels more uniform and open, with a shorter solution path on average.

**Comparison:**

| | DFS | Kruskal |
|---|---|---|
| Data structure | Stack | Union-Find |
| Progression | Cell by cell | Wall by wall |
| Corridor style | Long and winding | Short and branching |
| Memory | O(n) for the stack | O(n) for the UF |
| Config | `ALGORITHM=dfs` | `ALGORITHM=kruskal` |

## Visual Display

### MLX (graphical)

The interactive display uses the MLX library and renders a 2.5D Animal Crossing–style view with textured tiles and stone walls.

| Key | Action |
|---|---|
| `R` | Re-generate with animation |
| `S` | Show / hide solution path |
| `T` | Cycle colour theme |
| `Enter` | Save `maze.txt` and quit |
| `Esc` | Quit without saving |

### Terminal visualiser (curses)

The terminal visualiser is the automatic fallback when MLX is unavailable, or when `DISPLAYMODE=terminal` is set in the config. It runs entirely in the terminal using the Python `curses` library and requires no additional dependencies.

**How it works:**

- The maze is rendered as a `(2H+1) × (2W+1)` character grid. Each cell occupies one character, walls sit between cells, and corners use Unicode box-drawing characters (`┼`, `┤`, `├`, `─`, `│`).
- A side panel displays maze info and keyboard controls.
- The display refreshes every 30 ms during generation animation, and blocks on input otherwise.

**Keyboard controls:**

| Key | Action |
|---|---|
| `R` | Re-generate with step-by-step animation |
| `S` | Show / hide solution path |
| `T` | Cycle colour theme |
| `↑ ↓ ← →` | Scroll when the maze is larger than the terminal |
| `Enter` | Save `maze.txt` and quit |
| `Q` / `Esc` | Quit without saving |

**Legend:**

| Symbol | Meaning |
|---|---|
| `E` | Entry cell |
| `X` | Exit cell |
| `▓` | Pattern "42" cell |
| `•` | Solution path |
| `◆` | Current animation frontier |
| `░` | Not yet visited (during animation) |

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

# Same path as (x, y) coordinates
coords = solver.solve_as_coords((0, 0), (19, 14))
print(coords)  # [(0, 0), (1, 0), ...]

# Step-by-step animation (yields (x, y) after each carved cell)
for pos in gen.generate_steps():
    print(pos)
```

### MazeGenerator parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `width` | `int` | required | Number of columns (≥ 3) |
| `height` | `int` | required | Number of rows (≥ 3) |
| `seed` | `int \| None` | `None` | Random seed for reproducibility |
| `perfect` | `bool` | `True` | Produce a perfect maze |
| `algorithm` | `str` | `'dfs'` | Generation algorithm: `'dfs'` or `'kruskal'` |

After calling `generate()`:

| Attribute / Method | Returns | Description |
|---|---|---|
| `gen.grid` | `list[list[int]]` | Cell bitmask grid |
| `gen.locked` | `set[tuple[int, int]]` | Cells belonging to the "42" pattern |
| `gen.to_hex_grid()` | `list[str]` | Hex string representation |
| `gen.generate_steps()` | generator of `(x, y)` | Yields each carved cell for animation |

### MazeSolver

```python
solver = MazeSolver(gen)
```

| Method | Returns | Description |
|---|---|---|
| `solve(entry, exit_)` | `list[str]` | Shortest path as N/E/S/W letters |
| `solve_as_coords(entry, exit_)` | `list[tuple[int, int]]` | Shortest path as (x, y) coordinates |

### Pattern42

```python
from mazegen import Pattern42

p42 = Pattern42(width=20, height=15)
cells = p42.get_cells()  # set[tuple[int, int]]
```

`Pattern42(width, height).get_cells()` returns the set of `(x, y)` cells forming the "42" pattern for a given maze size. If the maze is too small to embed the pattern, the set is empty and a warning is printed.

## Team and Project Management

**Team:** olchacou, ancourt

| Member | Contributions |
|---|---|
| olchacou | DFS generation algorithm, bitmask encoding, output writer, MLX visualiser, themes, animated generation, BFS solver, Kruskal algorithm |
| ancourt | Config file parser, seed parsing and reproducibility, terminal visualiser (curses), lint error corrections (flake8 / mypy), "42" pattern, packaging |

**Planning:**
- Phase 1 — core generation: config parser, DFS algorithm, bitmask encoding, output writer
- Phase 2 — constraints: "42" pattern locking, perfect/imperfect modes, BFS solver
- Phase 3 — visualiser: MLX renderer, themes, animated generation, terminal fallback
- Phase 4 — packaging: `pyproject.toml`, pip package, tests, README

**What worked well:** The iterative DFS made animation straightforward via `generate_steps()`. The bitmask encoding maps directly to the hex output format with no translation layer. The terminal visualiser provides a reliable fallback when MLX is unavailable.

**What could be improved:** The loop-adding strategy for imperfect mazes could be more sophisticated to better control open-area density.

**Tools used:** Python 3.11, flake8, mypy, pytest, MLX, Claude (AI assistant).

## Resources

- [Maze generation algorithms — Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Recursive backtracker — jamisbuck.org](https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking)
- [Kruskal's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Kruskal%27s_algorithm)
- [Python `curses` module — docs.python.org](https://docs.python.org/3/library/curses.html)
- [Python `typing` module — docs.python.org](https://docs.python.org/3/library/typing.html)
- [flake8 documentation](https://flake8.pycqa.org/)
- [mypy documentation](https://mypy.readthedocs.io/)
- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/)

**AI usage (Claude — Anthropic):**
- Helped identify the missing entry/exit vs. "42" pattern validation.
- Reviewed flake8/mypy diagnostics and proposed fixes.
- Drafted and reviewed docstrings following PEP 257.
- Helped design and implement the Kruskal algorithm and terminal visualiser.

All AI-generated content was reviewed, tested, and understood before inclusion.