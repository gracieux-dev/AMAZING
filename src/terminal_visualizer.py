"""Terminal (curses) visualizer — used automatically when MLX is unavailable."""

import curses
import random as _rnd
from typing import Optional

from mazegen.solver import MazeSolver
from mazegen.generator import NORTH, EAST, SOUTH, WEST
from .visualizer import _SPLASH_TEXTS

# Color-pair indices
_C_TITLE    = 1
_C_GO       = 2
_C_NRM      = 3
_C_QUIT     = 4
_C_DIM      = 5
_C_ENTRY    = 6
_C_EXIT     = 7
_C_PATH     = 8
_C_WALL     = 9
_C_P42      = 10
_C_ANIM_CUR = 11

_STEPS_PER_FRAME = 8

# Terminal color approximations per theme
_TERM_THEMES = {
    'spring': dict(title=curses.COLOR_GREEN,  wall=curses.COLOR_GREEN,
                   entry=curses.COLOR_CYAN,   exit=curses.COLOR_RED,
                   path=curses.COLOR_YELLOW,  go_bg=curses.COLOR_GREEN,
                   accent=curses.COLOR_GREEN),
    'summer': dict(title=curses.COLOR_CYAN,   wall=curses.COLOR_CYAN,
                   entry=curses.COLOR_BLUE,   exit=curses.COLOR_RED,
                   path=curses.COLOR_MAGENTA, go_bg=curses.COLOR_CYAN,
                   accent=curses.COLOR_CYAN),
    'autumn': dict(title=curses.COLOR_YELLOW, wall=curses.COLOR_YELLOW,
                   entry=curses.COLOR_BLUE,   exit=curses.COLOR_RED,
                   path=curses.COLOR_CYAN,    go_bg=curses.COLOR_YELLOW,
                   accent=curses.COLOR_YELLOW),
    'winter': dict(title=curses.COLOR_WHITE,  wall=curses.COLOR_WHITE,
                   entry=curses.COLOR_CYAN,   exit=curses.COLOR_RED,
                   path=curses.COLOR_YELLOW,  go_bg=curses.COLOR_WHITE,
                   accent=curses.COLOR_WHITE),
}

# Box-drawing corner lookup: (north, south, west, east) → char
_BOX = {
    (False, False, False, False): ' ',
    (True,  False, False, False): '╵',
    (False, True,  False, False): '╷',
    (False, False, True,  False): '╴',
    (False, False, False, True ): '╶',
    (True,  True,  False, False): '│',
    (False, False, True,  True ): '─',
    (True,  False, True,  False): '┘',
    (True,  False, False, True ): '└',
    (False, True,  True,  False): '┐',
    (False, True,  False, True ): '┌',
    (True,  True,  True,  False): '┤',
    (True,  True,  False, True ): '├',
    (True,  False, True,  True ): '┴',
    (False, True,  True,  True ): '┬',
    (True,  True,  True,  True ): '┼',
}

_WALL_CHARS = set(_BOX.values()) | {'─', '│'}


def _init_colors(theme: str) -> None:
    """(Re)initialize color pairs for the given theme."""
    t    = _TERM_THEMES.get(theme, _TERM_THEMES['spring'])
    dark = 238 if curses.COLORS >= 256 else curses.COLOR_BLACK
    curses.init_pair(_C_TITLE,    t['title'],          -1)
    curses.init_pair(_C_GO,       curses.COLOR_BLACK,  t['go_bg'])
    curses.init_pair(_C_NRM,      curses.COLOR_WHITE,  dark)
    curses.init_pair(_C_QUIT,     curses.COLOR_WHITE,  curses.COLOR_RED)
    curses.init_pair(_C_DIM,      curses.COLOR_WHITE,  -1)
    curses.init_pair(_C_ENTRY,    t['entry'],          -1)
    curses.init_pair(_C_EXIT,     t['exit'],           -1)
    curses.init_pair(_C_PATH,     t['path'],           -1)
    curses.init_pair(_C_WALL,     t['wall'],           -1)
    curses.init_pair(_C_P42,      curses.COLOR_MAGENTA, -1)
    curses.init_pair(_C_ANIM_CUR, t['accent'],         -1)


def run_interactive(
    generator,
    entry: tuple,
    exit_pos: tuple,
    theme: str = 'spring',
) -> None:
    """Launch the curses-based interactive visualizer."""
    curses.wrapper(_main, generator, entry, exit_pos, theme)


# ── main menu ─────────────────────────────────────────────────────────────────

def _menu_screen(stdscr, themes: list, t_idx: int) -> tuple:
    """Minecraft-style main menu. Returns (should_play, t_idx)."""
    splash = _rnd.choice(_SPLASH_TEXTS)

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.erase()
        cx = w // 2

        def put_c(row: int, text: str, attr: int = curses.A_NORMAL) -> None:
            if row < 0 or row >= h - 1:
                return
            col = max(0, cx - len(text) // 2)
            try:
                stdscr.addstr(row, col, text[:w - col - 1], attr)
            except curses.error:
                pass

        def put_btn(row: int, label: str, pair: int, bold: bool = False) -> None:
            bw   = min(32, w - 4)
            text = label.center(bw)
            col  = max(0, cx - bw // 2)
            attr = curses.color_pair(pair) | (curses.A_BOLD if bold else 0)
            try:
                stdscr.addstr(row, col, text[:w - col - 1], attr)
            except curses.error:
                pass

        row = max(1, h // 2 - 7)
        put_c(row, 'A - M A Z E - I N G',
              curses.color_pair(_C_TITLE) | curses.A_BOLD)
        row += 1
        put_c(row, splash, curses.color_pair(_C_DIM) | curses.A_DIM)
        row += 3

        put_btn(row, '[Enter]  Play', _C_GO, bold=True);           row += 2
        put_btn(row, f'[T]  Theme: {themes[t_idx].capitalize()}',
                _C_NRM);                                            row += 2
        put_btn(row, '[Q / Esc]  Quit', _C_QUIT)

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

def _main(stdscr, generator, entry, exit_pos, theme: str) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()

    themes = ['spring', 'summer', 'autumn', 'winter']
    t_idx  = themes.index(theme) if theme in themes else 0
    _init_colors(themes[t_idx])

    play, t_idx = _menu_screen(stdscr, themes, t_idx)
    if not play:
        return

    show_sol     = False
    sol_coords: Optional[list] = None
    solver       = MazeSolver(generator)
    animating    = False
    anim_iter    = None
    anim_visited: Optional[set] = None
    anim_pos: Optional[tuple]   = None
    view_r       = 0   # scroll offset in maze char rows
    view_c       = 0   # scroll offset in maze char cols

    while True:
        # ── advance animation ────────────────────────────────────────────
        if animating:
            try:
                for _ in range(_STEPS_PER_FRAME):
                    pos      = next(anim_iter)
                    anim_pos = pos
                    anim_visited.add(pos)
            except StopIteration:
                animating    = False
                anim_iter    = None
                anim_pos     = None
                anim_visited = None
                sol_coords   = None
                show_sol     = False

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

        panel_x = min(mw_chars + 2, w - 32)
        panel_w = w - panel_x - 1

        # clamp scroll to valid range
        view_r = max(0, min(view_r, mh_chars - (h - 1)))
        view_c = max(0, min(view_c, mw_chars - (panel_x - 1)))

        scrollable = mh_chars > h - 1 or mw_chars > panel_x - 1

        _draw_maze(stdscr, maze_ch, h, panel_x, view_r, view_c)
        if panel_w >= 20:
            _draw_panel(stdscr, panel_x, panel_w, h,
                        generator, show_sol, sol_coords,
                        themes[t_idx], animating, scrollable)

        stdscr.refresh()

        # ── input (non-blocking while animating) ─────────────────────────
        stdscr.timeout(30 if animating else -1)
        key = stdscr.getch()
        if key == -1:
            continue

        if key in (ord('q'), ord('Q'), 27):
            break
        elif key in (ord('r'), ord('R')):
            if not animating:
                animating    = True
                anim_visited = set()
                anim_pos     = None
                anim_iter    = generator.generate_steps()
                sol_coords   = None
                show_sol     = False
                view_r       = 0
                view_c       = 0
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
            view_r = max(0, view_r - 2)
        elif key == curses.KEY_DOWN:
            view_r += 2
        elif key == curses.KEY_LEFT:
            view_c = max(0, view_c - 2)
        elif key == curses.KEY_RIGHT:
            view_c += 2


# ── maze rendering ─────────────────────────────────────────────────────────────

def _make_maze_chars(generator, entry, exit_pos, sol_path,
                     anim_visited: Optional[set] = None,
                     anim_pos: Optional[tuple] = None) -> list:
    """Build a (2H+1) × (2W+1) character grid for the maze."""
    grid    = generator.grid
    height  = len(grid)
    width   = len(grid[0]) if height else 0
    sol_set = set(map(tuple, sol_path)) if sol_path else set()
    locked  = getattr(generator, 'locked', set()) or set()

    dh = 2 * height + 1
    dw = 2 * width + 1
    ch = [[' '] * dw for _ in range(dh)]

    for r in range(0, dh, 2):
        for c in range(0, dw, 2):
            ch[r][c] = '+'

    for y in range(height):
        for x in range(width):
            cell   = grid[y][x]
            dr, dc = y * 2 + 1, x * 2 + 1
            if cell & NORTH: ch[dr - 1][dc] = '-'
            if cell & SOUTH: ch[dr + 1][dc] = '-'
            if cell & WEST:  ch[dr][dc - 1] = '|'
            if cell & EAST:  ch[dr][dc + 1] = '|'

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
            north = r > 0     and ch[r - 1][c] == '|'
            south = r < dh-1  and ch[r + 1][c] == '|'
            west  = c > 0     and ch[r][c - 1] == '-'
            east  = c < dw-1  and ch[r][c + 1] == '-'
            ch[r][c] = _BOX[(north, south, west, east)]
        for c in range(1, dw, 2):
            if ch[r][c] == '-':
                ch[r][c] = '─'
    for r in range(1, dh, 2):
        for c in range(0, dw, 2):
            if ch[r][c] == '|':
                ch[r][c] = '│'

    return ch


def _draw_maze(stdscr, maze_ch: list, term_h: int, max_x: int,
               off_r: int = 0, off_c: int = 0) -> None:
    mh = len(maze_ch)
    mw = len(maze_ch[0]) if maze_ch else 0
    for screen_r in range(min(term_h - 1, mh - off_r)):
        maze_r = screen_r + off_r
        row    = maze_ch[maze_r]
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

def _draw_panel(stdscr, px: int, pw: int, ph: int,
                generator, show_sol: bool, sol_coords: Optional[list],
                theme: str, animating: bool, scrollable: bool = False) -> None:
    height  = len(generator.grid)
    width   = len(generator.grid[0]) if height else 0
    perfect = getattr(generator, 'perfect', True)

    def put(row: int, text: str, attr: int = curses.A_NORMAL,
            center: bool = False) -> None:
        if row < 0 or row >= ph - 1:
            return
        col = max(0, (pw - len(text)) // 2) if center else 1
        try:
            stdscr.addstr(row, px + col, text[:pw - col - 1], attr)
        except curses.error:
            pass

    def mc_btn(row: int, label: str, pair: int, bold: bool = False) -> None:
        bw   = min(pw - 2, 28)
        text = label.center(bw)
        attr = curses.color_pair(pair) | (curses.A_BOLD if bold else 0)
        put(row, text[:bw], attr)

    y = 1

    put(y, 'A - M A Z E - I N G',
        curses.color_pair(_C_TITLE) | curses.A_BOLD, center=True)
    y += 2

    info1 = f'{width} x {height}  |  {"Perfect" if perfect else "Imperfect"}'
    put(y, info1, curses.color_pair(_C_DIM) | curses.A_DIM, center=True)
    y += 1
    put(y, f'Theme: {theme.capitalize()}',
        curses.color_pair(_C_TITLE) | curses.A_DIM, center=True)
    y += 2

    if animating:
        mc_btn(y, '[R]  Generating...', _C_GO, bold=True)
    else:
        mc_btn(y, '[R]  Regenerate', _C_GO, bold=True)
    y += 2

    if animating:
        mc_btn(y, '[S]  Solution: --', _C_NRM)
    elif show_sol and sol_coords:
        mc_btn(y, f'[S]  Solution: ON ({len(sol_coords)})', _C_GO)
    else:
        mc_btn(y, '[S]  Solution: OFF', _C_NRM)
    y += 2

    mc_btn(y, f'[T]  Theme: {theme.capitalize()}', _C_NRM)
    y += 2
    mc_btn(y, '[Enter]  Save & Quit', _C_NRM)
    y += 2
    mc_btn(y, '[Q / Esc]  Quit', _C_QUIT)
    y += 3

    put(y, 'E  Entry',    curses.color_pair(_C_ENTRY));  y += 1
    put(y, 'X  Exit',     curses.color_pair(_C_EXIT));   y += 1
    put(y, '▓  Pattern42', curses.color_pair(_C_P42));   y += 1
    if show_sol and not animating:
        put(y, '•  Solution', curses.color_pair(_C_PATH)); y += 1

    if scrollable:
        y += 1
        put(y, '↑↓←→  Scroll', curses.color_pair(_C_DIM) | curses.A_DIM)

    put(ph - 2, 'v1.0.0', curses.color_pair(_C_DIM) | curses.A_DIM)
