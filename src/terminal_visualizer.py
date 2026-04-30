"""Terminal (curses) visualizer — used automatically when MLX is unavailable."""

import curses
import random as _rnd
from typing import Any, Optional

from mazegen.solver import MazeSolver
from mazegen.generator import NORTH, EAST, SOUTH, WEST
from .visualizer import _SPLASH_TEXTS

# Color-pair indices
_C_TITLE = 1
_C_GO = 2
_C_NRM = 3
_C_QUIT = 4
_C_DIM = 5
_C_ENTRY = 6
_C_EXIT = 7
_C_PATH = 8
_C_WALL = 9
_C_P42 = 10
_C_ANIM_CUR = 11

_STEPS_PER_FRAME = 8  # DFS cells advanced per 30 ms frame (~266 cells/s)

# Terminal color approximations per theme
_TERM_THEMES = {
    'spring': dict(title=curses.COLOR_GREEN, wall=curses.COLOR_GREEN,
                   entry=curses.COLOR_CYAN, exit=curses.COLOR_RED,
                   path=curses.COLOR_YELLOW, go_bg=curses.COLOR_GREEN,
                   accent=curses.COLOR_GREEN),
    'summer': dict(title=curses.COLOR_CYAN, wall=curses.COLOR_CYAN,
                   entry=curses.COLOR_BLUE, exit=curses.COLOR_RED,
                   path=curses.COLOR_MAGENTA, go_bg=curses.COLOR_CYAN,
                   accent=curses.COLOR_CYAN),
    'autumn': dict(title=curses.COLOR_YELLOW, wall=curses.COLOR_YELLOW,
                   entry=curses.COLOR_BLUE, exit=curses.COLOR_RED,
                   path=curses.COLOR_CYAN, go_bg=curses.COLOR_YELLOW,
                   accent=curses.COLOR_YELLOW),
    'winter': dict(title=curses.COLOR_WHITE, wall=curses.COLOR_WHITE,
                   entry=curses.COLOR_CYAN, exit=curses.COLOR_RED,
                   path=curses.COLOR_YELLOW, go_bg=curses.COLOR_WHITE,
                   accent=curses.COLOR_WHITE),
}

# Box-drawing corner lookup: (north, south, west, east) → char
_BOX = {
    (False, False, False, False): ' ',
    (True, False, False, False): '╵',
    (False, True, False, False): '╷',
    (False, False, True, False): '╴',
    (False, False, False, True): '╶',
    (True, True, False, False): '│',
    (False, False, True, True): '─',
    (True, False, True, False): '┘',
    (True, False, False, True): '└',
    (False, True, True, False): '┐',
    (False, True, False, True): '┌',
    (True, True, True, False): '┤',
    (True, True, False, True): '├',
    (True, False, True, True): '┴',
    (False, True, True, True): '┬',
    (True, True, True, True): '┼',
}

_WALL_CHARS = set(_BOX.values()) | {'─', '│'}


# ── module-level drawing helpers ───────────────────────────────────────────────

def _put_centered(stdscr: Any, row: int, text: str, w: int, h: int,
                  cx: int, attr: int = 0) -> None:
    """Write text centred horizontally in the terminal, guarded by row bounds.

    Parameters:
        stdscr: Curses window to draw into.
        row: Screen row to write on.
        text: String to render; clipped to avoid writing past the right edge.
        w: Terminal width in columns.
        h: Terminal height in rows; rows >= h-1 are skipped to protect the
           status line that curses reserves at the bottom.
        cx: Horizontal centre column (typically w // 2).
        attr: Curses attribute/colour pair to apply.
    """
    if row < 0 or row >= h - 1:
        return
    col = max(0, cx - len(text) // 2)
    try:
        stdscr.addstr(row, col, text[:w - col - 1], attr)
    except curses.error:
        pass


def _put_btn(stdscr: Any, row: int, label: str, pair: int, w: int,
             cx: int, bold: bool = False) -> None:
    """Write a centred, padded button label using the given colour-pair index.

    Parameters:
        stdscr: Curses window to draw into.
        row: Screen row to write on.
        label: Button text; padded with spaces to fill the button width.
        pair: Colour-pair index (not a curses.color_pair() result).
        w: Terminal width in columns.
        cx: Horizontal centre column (typically w // 2).
        bold: Whether to apply curses.A_BOLD to the attribute.
    """
    bw = min(32, w - 4)  # cap button width; leave a 2-char margin on each side
    text = label.center(bw)
    col = max(0, cx - bw // 2)
    attr = curses.color_pair(pair) | (curses.A_BOLD if bold else 0)
    try:
        stdscr.addstr(row, col, text[:w - col - 1], attr)
    except curses.error:
        pass


def _panel_put(stdscr: Any, row: int, text: str, px: int, pw: int,
               ph: int, attr: int = 0, center: bool = False) -> None:
    """Write a line of text inside the right-hand panel, optionally centred.

    Parameters:
        stdscr: Curses window to draw into.
        row: Screen row to write on.
        text: String to render; clipped to fit within the panel width.
        px: Left-edge column of the panel.
        pw: Panel width in columns.
        ph: Panel height (terminal height) in rows; the last row is reserved
            by curses and is never written.
        attr: Curses attribute/colour pair to apply.
        center: If True, centre the text horizontally within the panel;
                otherwise left-align with a 1-column indent.
    """
    if row < 0 or row >= ph - 1:
        return
    col = max(0, (pw - len(text)) // 2) if center else 1
    try:
        stdscr.addstr(row, px + col, text[:pw - col - 1], attr)
    except curses.error:
        pass


def _panel_mc_btn(stdscr: Any, row: int, label: str, pair: int,
                  px: int, pw: int, ph: int, bold: bool = False) -> None:
    """Write a Minecraft-style centred button row inside the right-hand panel.

    Parameters:
        stdscr: Curses window to draw into.
        row: Screen row to write on.
        label: Button text; padded with spaces to fill the button width.
        pair: Colour-pair index (not a curses.color_pair() result).
        px: Left-edge column of the panel.
        pw: Panel width in columns.
        ph: Panel height in rows (passed through to _panel_put).
        bold: Whether to apply curses.A_BOLD to the attribute.
    """
    bw = min(pw - 2, 28)  # cap to panel width minus 1-char border on each side
    text = label.center(bw)
    attr = curses.color_pair(pair) | (curses.A_BOLD if bold else 0)
    _panel_put(stdscr, row, text[:bw], px, pw, ph, attr)


# ── colour initialisation ──────────────────────────────────────────────────────

def _init_colors(theme: str) -> None:
    """Initialise all 11 curses colour pairs for the given theme.

    Parameters:
        theme: One of 'spring', 'summer', 'autumn', 'winter'.
               Falls back to 'spring' if the value is unrecognised.

    Side effects:
        Calls curses.init_pair for each of the _C_* colour-pair indices.
        Must be called after curses.start_color() and curses.use_default_colors().
    """
    t = _TERM_THEMES.get(theme, _TERM_THEMES['spring'])
    # index 238 ≈ dark grey in 256-colour terminals
    dark = 238 if curses.COLORS >= 256 else curses.COLOR_BLACK
    curses.init_pair(_C_TITLE, t['title'], -1)
    curses.init_pair(_C_GO, curses.COLOR_BLACK, t['go_bg'])
    curses.init_pair(_C_NRM, curses.COLOR_WHITE, dark)
    curses.init_pair(_C_QUIT, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(_C_DIM, curses.COLOR_WHITE, -1)
    curses.init_pair(_C_ENTRY, t['entry'], -1)
    curses.init_pair(_C_EXIT, t['exit'], -1)
    curses.init_pair(_C_PATH, t['path'], -1)
    curses.init_pair(_C_WALL, t['wall'], -1)
    curses.init_pair(_C_P42, curses.COLOR_MAGENTA, -1)
    curses.init_pair(_C_ANIM_CUR, t['accent'], -1)


def run_interactive(
    generator: Any,
    entry: tuple,
    exit_pos: tuple,
    theme: str = 'spring',
) -> None:
    """Launch the curses-based interactive visualizer."""
    curses.wrapper(_main, generator, entry, exit_pos, theme)


# ── main menu ─────────────────────────────────────────────────────────────────

def _menu_screen(stdscr: Any, themes: list, t_idx: int) -> tuple:
    """Minecraft-style main menu. Returns (should_play, t_idx)."""
    splash = _rnd.choice(_SPLASH_TEXTS)

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.erase()
        cx = w // 2

        # position title ~7 rows above centre to leave room for buttons below
        row = max(1, h // 2 - 7)
        _put_centered(stdscr, row, 'A - M A Z E - I N G', w, h, cx,
                      curses.color_pair(_C_TITLE) | curses.A_BOLD)
        row += 1
        _put_centered(stdscr, row, splash, w, h, cx,
                      curses.color_pair(_C_DIM) | curses.A_DIM)
        row += 3

        _put_btn(stdscr, row, '[Enter]  Play', _C_GO, w, cx, bold=True)
        row += 2
        _put_btn(stdscr, row, f'[T]  Theme: {themes[t_idx].capitalize()}',
                 _C_NRM, w, cx)
        row += 2
        _put_btn(stdscr, row, '[Q / Esc]  Quit', _C_QUIT, w, cx)

        ver = 'v1.0.0'
        try:
            stdscr.addstr(h - 2, w - len(ver) - 1, ver,
                          curses.color_pair(_C_DIM) | curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        key = stdscr.getch()

        if key in (10, 13):
            return True, t_idx
        elif key in (27, ord('q'), ord('Q')):
            return False, t_idx
        elif key in (ord('t'), ord('T')):
            t_idx = (t_idx + 1) % len(themes)
            _init_colors(themes[t_idx])


# ── main loop ─────────────────────────────────────────────────────────────────

def _main(stdscr: Any, generator: Any, entry: tuple,
          exit_pos: tuple, theme: str) -> None:
    """Curses entry point called by curses.wrapper from run_interactive.

    Parameters:
        stdscr: Curses standard screen provided by curses.wrapper.
        generator: Maze generator whose grid will be displayed and may be
                   regenerated interactively via the 'r' key.
        entry: (x, y) entry cell coordinates.
        exit_pos: (x, y) exit cell coordinates.
        theme: Initial theme name ('spring', 'summer', 'autumn', 'winter').

    Side effects:
        Drives the interactive event loop until the user quits.
        Writes maze.txt via write_output when the user presses Enter.
    """
    stdscr.keypad(True)
    curses.curs_set(0)

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()

    themes = ['spring', 'summer', 'autumn', 'winter']
    t_idx = themes.index(theme) if theme in themes else 0
    _init_colors(themes[t_idx])

    play, t_idx = _menu_screen(stdscr, themes, t_idx)
    if not play:
        return

    show_sol = False
    sol_coords: Optional[list] = None
    solver = MazeSolver(generator)
    animating = False
    anim_iter: Optional[Any] = None
    anim_visited: Optional[set] = None
    anim_pos: Optional[tuple] = None
    view_r = 0   # scroll offset in maze char rows
    view_c = 0   # scroll offset in maze char cols

    while True:
        # ── advance animation ────────────────────────────────────────────
        if animating and anim_iter is not None and anim_visited is not None:
            try:
                for _ in range(_STEPS_PER_FRAME):
                    pos = next(anim_iter)
                    anim_pos = pos
                    anim_visited.add(pos)
            except StopIteration:
                animating = False
                anim_iter = None
                anim_pos = None
                anim_visited = None
                sol_coords = None
                show_sol = False

        # ── render ───────────────────────────────────────────────────────
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        maze_ch = _make_maze_chars(
            generator, entry, exit_pos,
            sol_coords if show_sol else None,
            anim_visited, anim_pos,
        )
        mh_chars = len(maze_ch)
        mw_chars = len(maze_ch[0]) if maze_ch else 0

        # +2 gap between maze and panel; keep the panel at the right edge
        panel_x = max(mw_chars + 2, w - 32)
        panel_w = w - panel_x - 1

        # clamp scroll to valid range
        view_r = max(0, min(view_r, mh_chars - (h - 1)))
        view_c = max(0, min(view_c, mw_chars - (panel_x - 1)))

        scrollable = mh_chars > h - 1 or mw_chars > panel_x - 1

        _draw_maze(stdscr, maze_ch, h, panel_x, view_r, view_c)
        # skip panel if terminal is too narrow to render it usefully
        if panel_w >= 20:
            _draw_panel(stdscr, panel_x, panel_w, h,
                        generator, show_sol, sol_coords,
                        themes[t_idx], animating, scrollable)

        stdscr.refresh()

        # 30 ms poll keeps animation smooth; -1 blocks until keypress
        stdscr.timeout(30 if animating else -1)
        key = stdscr.getch()
        if key == -1:
            continue

        if key in (ord('q'), ord('Q'), 27):
            break
        elif key in (ord('r'), ord('R')):
            if not animating:
                animating = True
                anim_visited = set()
                anim_pos = None
                anim_iter = generator.generate_steps()
                sol_coords = None
                show_sol = False
                view_r = 0
                view_c = 0
        elif key in (ord('s'), ord('S')):
            if not animating:
                show_sol = not show_sol
                if show_sol and sol_coords is None:
                    sol_coords = solver.solve_as_coords(entry, exit_pos)
        elif key in (ord('t'), ord('T')):
            t_idx = (t_idx + 1) % len(themes)
            _init_colors(themes[t_idx])
        elif key in (10, 13):
            if not animating:
                from .output_writer import write_output
                write_output(generator, entry, exit_pos, 'maze.txt')
                break
        elif key == curses.KEY_UP:
            # step by 2: each maze row spans 2 char rows (cell + wall)
            view_r = max(0, view_r - 2)
        elif key == curses.KEY_DOWN:
            view_r += 2
        elif key == curses.KEY_LEFT:
            # step by 2: each maze column spans 2 char columns
            view_c = max(0, view_c - 2)
        elif key == curses.KEY_RIGHT:
            view_c += 2


# ── maze rendering ─────────────────────────────────────────────────────────────

def _make_maze_chars(generator: Any, entry: tuple, exit_pos: tuple,
                     sol_path: Any,
                     anim_visited: Optional[set] = None,
                     anim_pos: Optional[tuple] = None) -> list:
    """Build a (2H+1) × (2W+1) character grid representing the maze.

    Each maze cell maps to a centre character at (2y+1, 2x+1); wall slots sit
    between cells and on the outer border. ASCII wall markers (- and |) are
    replaced with Unicode box-drawing characters at the end.

    Parameters:
        generator: Maze generator providing the cell grid and a 'locked' set.
        entry: (x, y) entry cell coordinates; rendered as 'E'.
        exit_pos: (x, y) exit cell coordinates; rendered as 'X'.
        sol_path: Iterable of (x, y) solution cells to mark with '•', or None.
        anim_visited: Set of cells already visited during a generation animation,
                      or None when no animation is in progress.
        anim_pos: Current frontier cell during generation animation (rendered as
                  '◆'), or None.

    Returns:
        A list of lists of single characters (one inner list per display row).
    """
    grid = generator.grid
    height = len(grid)
    width = len(grid[0]) if height else 0
    sol_set = set(map(tuple, sol_path)) if sol_path else set()
    locked = getattr(generator, 'locked', set()) or set()

    dh = 2 * height + 1
    dw = 2 * width + 1
    ch = [[' '] * dw for _ in range(dh)]

    for r in range(0, dh, 2):
        for c in range(0, dw, 2):
            ch[r][c] = '+'

    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            dr, dc = y * 2 + 1, x * 2 + 1
            if cell & NORTH:
                ch[dr - 1][dc] = '-'
            if cell & SOUTH:
                ch[dr + 1][dc] = '-'
            if cell & WEST:
                ch[dr][dc - 1] = '|'
            if cell & EAST:
                ch[dr][dc + 1] = '|'

            pos = (x, y)
            if pos in locked:
                ch[dr][dc] = '▓'
            elif pos == tuple(entry):
                ch[dr][dc] = 'E'
            elif pos == tuple(exit_pos):
                ch[dr][dc] = 'X'
            elif anim_pos is not None and pos == tuple(anim_pos):
                ch[dr][dc] = '◆'
            elif anim_visited is not None and pos not in anim_visited:
                ch[dr][dc] = '░'
            elif pos in sol_set:
                ch[dr][dc] = '•'

    # convert ASCII walls to Unicode box-drawing
    for r in range(0, dh, 2):
        for c in range(0, dw, 2):
            north = r > 0 and ch[r - 1][c] == '|'
            south = r < dh - 1 and ch[r + 1][c] == '|'
            west = c > 0 and ch[r][c - 1] == '-'
            east = c < dw - 1 and ch[r][c + 1] == '-'
            ch[r][c] = _BOX[(north, south, west, east)]
        for c in range(1, dw, 2):
            if ch[r][c] == '-':
                ch[r][c] = '─'
    for r in range(1, dh, 2):
        for c in range(0, dw, 2):
            if ch[r][c] == '|':
                ch[r][c] = '│'

    return ch


def _draw_maze(stdscr: Any, maze_ch: list, term_h: int, max_x: int,
               off_r: int = 0, off_c: int = 0) -> None:
    """Render the maze character grid onto stdscr with curses colour attributes.

    Parameters:
        stdscr: Curses window to draw into.
        maze_ch: 2D character grid produced by _make_maze_chars.
        term_h: Terminal height in rows; limits the vertical draw range so the
                last row (reserved by curses) is never written.
        max_x: Column limit (exclusive) for the maze region; columns at or
               beyond this value are left for the side panel.
        off_r: Vertical scroll offset in maze-character rows.
        off_c: Horizontal scroll offset in maze-character columns.
    """
    mh = len(maze_ch)
    mw = len(maze_ch[0]) if maze_ch else 0
    for screen_r in range(min(term_h - 1, mh - off_r)):
        maze_r = screen_r + off_r
        row = maze_ch[maze_r]
        for screen_c in range(min(max_x - 1, mw - off_c)):
            char = row[screen_c + off_c]
            if char == 'E':
                attr = curses.color_pair(_C_ENTRY) | curses.A_BOLD
            elif char == 'X':
                attr = curses.color_pair(_C_EXIT) | curses.A_BOLD
            elif char == '•':
                attr = curses.color_pair(_C_PATH) | curses.A_BOLD
            elif char == '▓':
                attr = curses.color_pair(_C_P42) | curses.A_BOLD
            elif char == '◆':
                attr = curses.color_pair(_C_ANIM_CUR) | curses.A_BOLD
            elif char == '░':
                attr = curses.color_pair(_C_DIM) | curses.A_DIM
            elif char in _WALL_CHARS:
                attr = curses.color_pair(_C_WALL)
            else:
                attr = curses.A_NORMAL
            try:
                stdscr.addstr(screen_r, screen_c, char, attr)
            except curses.error:
                pass


# ── panel rendering ────────────────────────────────────────────────────────────

def _draw_panel(stdscr: Any, px: int, pw: int, ph: int,
                generator: Any, show_sol: bool, sol_coords: Optional[list],
                theme: str, animating: bool, scrollable: bool = False) -> None:
    """Render the right-hand info/control panel on stdscr.

    Parameters:
        stdscr: Curses window to draw into.
        px: Left-edge column of the panel.
        pw: Panel width in columns.
        ph: Panel height (terminal height) in rows.
        generator: Maze generator providing grid, perfect, and locked attributes.
        show_sol: Whether the solution overlay is currently active.
        sol_coords: List of (x, y) solution coordinates, or None.
        theme: Active theme name string.
        animating: True while a generation animation is in progress.
        scrollable: True when the maze extends beyond the visible terminal area.
    """
    height = len(generator.grid)
    width = len(generator.grid[0]) if height else 0
    perfect = getattr(generator, 'perfect', True)

    y = 1

    _panel_put(stdscr, y, 'A - M A Z E - I N G', px, pw, ph,
               curses.color_pair(_C_TITLE) | curses.A_BOLD, center=True)
    y += 2

    info1 = f'{width} x {height}  |  {"Perfect" if perfect else "Imperfect"}'
    _panel_put(stdscr, y, info1, px, pw, ph,
               curses.color_pair(_C_DIM) | curses.A_DIM, center=True)
    y += 1
    _panel_put(stdscr, y, f'Theme: {theme.capitalize()}', px, pw, ph,
               curses.color_pair(_C_TITLE) | curses.A_DIM, center=True)
    y += 2

    if animating:
        _panel_mc_btn(stdscr, y, '[R]  Generating...', _C_GO, px, pw, ph, bold=True)
    else:
        _panel_mc_btn(stdscr, y, '[R]  Regenerate', _C_GO, px, pw, ph, bold=True)
    y += 2

    if animating:
        _panel_mc_btn(stdscr, y, '[S]  Solution: --', _C_NRM, px, pw, ph)
    elif show_sol and sol_coords:
        _panel_mc_btn(
            stdscr, y, f'[S]  Solution: ON ({len(sol_coords)})', _C_GO, px, pw, ph)
    else:
        _panel_mc_btn(stdscr, y, '[S]  Solution: OFF', _C_NRM, px, pw, ph)
    y += 2

    _panel_mc_btn(stdscr, y, f'[T]  Theme: {theme.capitalize()}', _C_NRM, px, pw, ph)
    y += 2
    _panel_mc_btn(stdscr, y, '[Enter]  Save & Quit', _C_NRM, px, pw, ph)
    y += 2
    _panel_mc_btn(stdscr, y, '[Q / Esc]  Quit', _C_QUIT, px, pw, ph)
    y += 3

    _panel_put(stdscr, y, 'E  Entry', px, pw, ph, curses.color_pair(_C_ENTRY))
    y += 1
    _panel_put(stdscr, y, 'X  Exit', px, pw, ph, curses.color_pair(_C_EXIT))
    y += 1
    _panel_put(stdscr, y, '▓  Pattern42', px, pw, ph, curses.color_pair(_C_P42))
    y += 1
    if show_sol and not animating:
        _panel_put(stdscr, y, '•  Solution', px, pw, ph, curses.color_pair(_C_PATH))
        y += 1

    if scrollable:
        y += 1
        _panel_put(stdscr, y, '↑↓←→  Scroll', px, pw, ph,
                   curses.color_pair(_C_DIM) | curses.A_DIM)

    _panel_put(stdscr, ph - 2, 'v1.0.0', px, pw, ph,
               curses.color_pair(_C_DIM) | curses.A_DIM)
