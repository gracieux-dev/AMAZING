"""
MLX Visualizer — A-Maze-ing
2.5D Animal Crossing style: textured floor tiles + stone walls.
"""

import os
import sys
import random as _rnd
from typing import Any, Optional, Tuple

from mazegen.generator import NORTH, WEST

# ── tile geometry ──────────────────────────────────────────────────────────────
_CELL = 24   # floor tile size (pixels)
_WALL = 4    # wall thickness
_WFACE = 8   # wall front-face height (depth illusion)

# ── colour palettes ────────────────────────────────────────────────────────────
MLX_THEMES: dict = {
    'spring': {
        'floor': 0xC8DF90, 'floor_alt': 0xB0C870,
        'wall_top': 0x4A9A32, 'wall_face': 0x1E5A14,
        'path': 0xFF1500, 'entry': 0x50B8FF,
        'exit': 0xFF5050, 'special': 0xCC80FF,
        'bg': 0xE8F5D0, 'panel': 0x2A4A2A,
        'text': 0xDDFFDD, 'accent': 0x88FF44,
    },
    'summer': {
        'floor': 0xF0E898, 'floor_alt': 0xD8D070,
        'wall_top': 0x00A8A8, 'wall_face': 0x005A5A,
        'path': 0xFF00CC, 'entry': 0x3CA0FF,
        'exit': 0xFF4646, 'special': 0xC070FF,
        'bg': 0xD8F4F8, 'panel': 0x00363C,
        'text': 0xCCF8FF, 'accent': 0x00DDFF,
    },
    'autumn': {
        'floor': 0xE8C870, 'floor_alt': 0xC8A850,
        'wall_top': 0xD05810, 'wall_face': 0x882808,
        'path': 0x0066FF, 'entry': 0x3CA0FF,
        'exit': 0xFF4646, 'special': 0xB464DC,
        'bg': 0xFFF0D0, 'panel': 0x4A1800,
        'text': 0xFFE0C0, 'accent': 0xFF9900,
    },
    'winter': {
        'floor': 0xD8ECFF, 'floor_alt': 0xBCCEF0,
        'wall_top': 0xE8F4FF, 'wall_face': 0x7080A0,
        'path': 0xFF8800, 'entry': 0x3CA0FF,
        'exit': 0xFF4646, 'special': 0xE080FF,
        'bg': 0xDCECFF, 'panel': 0x18243C,
        'text': 0xCCDDFF, 'accent': 0x88CCFF,
    },
}

_PANEL_W = 250   # right panel width in pixels
_STEPS_PER_FRAME = 16    # DFS steps advanced per MLX loop tick
# Minecraft-style button palette (fixed, independent of theme)
_MC_BORD = 0x111111
_MC_BTN = 0x4A4A4A
_MC_BTN_HI = 0x717171
_MC_BTN_SH = 0x1A1A1A
_MC_GO = 0x5BA832
_MC_GO_HI = 0x78D044
_MC_GO_SH = 0x2E6019
_MC_QUIT = 0x7A2222
_MC_QUIT_HI = 0xA03030
_MC_QUIT_SH = 0x3A0A0A
_MC_TXT_DIM = 0x888888

_SPLASH_TEXTS = [
    "Deadends ahead!",
    "Find the exit!",
    "No loops... or are there?",
    "Turn left. No, right.",
    "The minotaur is watching.",
    "Can you solve it?",
    "Randomized perfection!",
    "Walls everywhere!",
    "42 cells locked!",
    "Are you lost yet?",
]


try:
    from mlx import Mlx as _MlxLib
    _HAS_MLX = True
except ModuleNotFoundError:
    _HAS_MLX = False


def run_interactive(
    generator: Any,
    entry: Tuple[int, int],
    exit_pos: Tuple[int, int],
    theme: str = 'spring',
    display_mode: str = 'auto',
) -> None:
    """Launch the interactive visualizer in the appropriate display mode."""
    display_mode = display_mode.strip().lower()
    if display_mode == 'none':
        return

    if display_mode == 'terminal':
        from .terminal_visualizer import run_interactive as _term
        _term(generator, entry, exit_pos, theme)
        return

    if display_mode == 'mlx':
        if not _HAS_MLX:
            raise RuntimeError(
                "DISPLAYMODE=mlx requested, but the mlx module is not available"
            )
        MlxMazeVisualizer(generator, entry, exit_pos, theme).run()
        return

    # auto fallback behavior
    if not _HAS_MLX or not os.getenv('DISPLAY'):
        from .terminal_visualizer import run_interactive as _term
        _term(generator, entry, exit_pos, theme)
        return

    try:
        MlxMazeVisualizer(generator, entry, exit_pos, theme).run()
    except Exception as e:
        print(
            f"[Display info] MLX failed ({e}); falling back to terminal.",
            file=sys.stderr,
        )
        from .terminal_visualizer import run_interactive as _term
        _term(generator, entry, exit_pos, theme)


class MlxMazeVisualizer:
    """2.5D Animal Crossing style maze visualizer using the MLX library."""

    def __init__(self, generator: Any, entry: Any, exit_pos: Any,
                 theme: str = 'spring') -> None:
        self.generator = generator
        self.entry = entry
        self.exit = exit_pos
        self.theme = theme if theme in MLX_THEMES else 'spring'
        self.show_solution = False
        self._sol_cache: list = []
        self._sol_dirty = True
        self._p42 = getattr(generator, 'locked', set()) or set()
        self._tick = 0
        # animation state
        self._animating = False
        self._anim_visited: Optional[set] = None
        self._anim_pos: Optional[tuple] = None
        self._step_iter: Optional[Any] = None

        self._in_menu = True
        self._splash = _rnd.choice(_SPLASH_TEXTS)
        # pac-man animation
        self._pac_anim  = False
        self._pac_idx   = 0
        self._pac_tick  = 0
        self._pac_dir: tuple = (1, 0)
        self._pac_trail: set = set()

        self._px_cache: dict = {}
        self._bpp8 = 4          # bytes-per-pixel; overwritten in _setup_window
        self._mlx = _MlxLib()
        self._ptr = self._mlx.mlx_init()
        self._setup_window()

    # ── window & image setup ───────────────────────────────────────────────────

    def _setup_window(self) -> None:
        gh = len(self.generator.grid)
        gw = len(self.generator.grid[0]) if gh > 0 else 0

        # query actual screen dimensions via MLX
        try:
            _sw, _sh = self._mlx.mlx_get_screen_size(self._ptr)
            if _sw <= 0 or _sh <= 0:
                _sw, _sh = 1920, 1080
        except Exception:
            _sw, _sh = 1920, 1080
        print(f"[DEBUG] screen={_sw}x{_sh}  grid={gw}x{gh}", flush=True)
        _max_w = max(640, _sw - _PANEL_W - 40)
        _max_h = max(480, _sh - 60)

        # auto-scale to fit screen
        cell, wf = _CELL, _WFACE
        while cell > 6:
            if gw * cell + _WALL <= _max_w and gh * cell + _WALL + wf <= _max_h:
                break
            cell -= 1
            wf = max(2, _WFACE * cell // _CELL)
        wall = max(2, _WALL * cell // _CELL)
        print(f"[DEBUG] cell={cell}  win={gw * cell + wall + _PANEL_W}x{max(gh * cell + wall + wf + 4, 420)}", flush=True)

        self._cell = cell
        self._wf = wf
        self._wall = wall
        self._mw = gw * cell + wall   # maze pixel width
        self._mh = gh * cell + wall
        self._win_w = self._mw + _PANEL_W
        self._win_h = max(self._mh + wf + 4, 420)

        self._win = self._mlx.mlx_new_window(
            self._ptr, self._win_w, self._win_h, 'A-Maze-ing')
        self._img = self._mlx.mlx_new_image(self._ptr, self._win_w, self._win_h)
        self._data, self._bpp, self._sl, _ = self._mlx.mlx_get_data_addr(self._img)
        self._bpp8 = self._bpp // 8

    # ── main menu ──────────────────────────────────────────────────────────────

    def _render_menu(self) -> None:
        c = self._col()
        tile = self._cell
        cw = max(4, tile - self._wall)

        # tiled floor background across whole window
        self._rect(0, 0, self._win_w, self._win_h, c['bg'])
        for ty in range(self._win_h // tile + 2):
            for tx in range(self._win_w // tile + 2):
                fc = c['floor'] if (tx + ty) % 2 == 0 else c['floor_alt']
                self._draw_floor_tile(tx * tile, ty * tile, cw, fc)

        # center panel dimensions
        pw = min(300, self._win_w - 40)
        ph = 210
        px = (self._win_w - pw) // 2
        py = (self._win_h - ph) // 2 - 10

        # panel border + background
        self._rect(px - 4, py - 4, pw + 8, ph + 8, _MC_BORD)
        self._rect(px, py, pw, ph, c['panel'])
        self._hline(px, px + pw - 1, py,
                    self._blend(_MC_BORD, 0xFFFFFF, 0.12))

        # pre-compute button geometry
        bw = pw - 32
        bh = 30
        bx = px + 16
        gap = 8
        btns = [
            (bx, py + 68, '[Enter]  Play',
             _MC_GO, _MC_GO_HI, _MC_GO_SH),
            (bx, py + 68 + bh + gap, f'[T]  Theme: {self.theme.capitalize()}',
             _MC_BTN, _MC_BTN_HI, _MC_BTN_SH),
            (bx, py + 68 + 2 * (bh + gap), '[Esc]  Quit',
             _MC_QUIT, _MC_QUIT_HI, _MC_QUIT_SH),
        ]

        # draw all button backgrounds to the image buffer
        for bx_, by_, _, face, hi, sh in btns:
            self._rect(bx_, by_, bw, bh, _MC_BORD)
            self._rect(bx_ + 2, by_ + 2, bw - 4, bh - 4, face)
            top_h = max(2, bh // 3)
            self._rect(bx_ + 2, by_ + 2, bw - 4, top_h, hi)
            self._rect(bx_ + 2, by_ + bh - 4, bw - 4, 2, sh)

        # flush image (shows tiles, panel bg, button shapes)
        self._mlx.mlx_put_image_to_window(self._ptr, self._win, self._img, 0, 0)

        # text drawn directly to window via mlx_string_put
        title = 'A - M A Z E - I N G'
        self._mc_text((self._win_w - len(title) * 8) // 2, py + 18,
                      title, c['accent'])
        splash_x = max(px + 4, px + pw - len(self._splash) * 8 - 6)
        self._mc_text(splash_x, py + 36, self._splash, 0xFFFF44)

        for bx_, by_, label, *_ in btns:
            tx = bx_ + max(4, (bw - len(label) * 8) // 2)
            self._mc_text(tx, by_ + (bh - 8) // 2, label)

        ver = 'v1.0.0'
        self._mc_text(self._win_w - len(ver) * 8 - 8,
                      self._win_h - 14, ver, _MC_TXT_DIM)

    # ── drawing primitives ─────────────────────────────────────────────────────

    def _px(self, color: int) -> bytes:
        """Return cached 4-byte pixel for color."""
        p = self._px_cache.get(color)
        if p is None:
            p = bytes([color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF, 0xFF])
            self._px_cache[color] = p
        return p

    def _put(self, x: int, y: int, color: int) -> None:
        if not (0 <= x < self._win_w and 0 <= y < self._win_h):
            return
        off = y * self._sl + x * self._bpp8
        self._data[off:off + self._bpp8] = self._px(color)

    def _hline(self, x0: int, x1: int, y: int, color: int) -> None:
        if x0 > x1:
            x0, x1 = x1, x0
        x0 = max(x0, 0)
        x1 = min(x1, self._win_w - 1)
        if x0 > x1 or not (0 <= y < self._win_h):
            return
        row = self._px(color) * (x1 - x0 + 1)
        off = y * self._sl + x0 * self._bpp8
        self._data[off:off + len(row)] = row

    def _rect(self, rx: int, ry: int, rw: int, rh: int, color: int) -> None:
        if rw <= 0 or rh <= 0:
            return
        bpp8 = self._bpp8
        x0 = max(rx, 0)
        x1 = min(rx + rw, self._win_w)
        w = x1 - x0
        if w <= 0:
            return
        y0 = max(ry, 0)
        y1 = min(ry + rh, self._win_h)
        row = self._px(color) * w
        rlen = w * bpp8
        sl = self._sl
        data = self._data
        base = x0 * bpp8
        for yy in range(y0, y1):
            off = yy * sl + base
            data[off:off + rlen] = row

    def _circle(self, cx: int, cy: int, r: int, color: int) -> None:
        """Filled circle via scanlines — O(r) rows instead of O(r²) pixels."""
        for dy in range(-r, r + 1):
            hw = int((r * r - dy * dy) ** 0.5)
            self._hline(cx - hw, cx + hw, cy + dy, color)

    def _draw_pacman(self, cx: int, cy: int, r: int,
                     direction: tuple, mouth_open: bool) -> None:
        """Yellow circle with a triangular mouth cut out toward direction."""
        self._circle(cx, cy, r, 0xFFEE00)
        if not mouth_open or r < 4:
            return
        dx, dy = direction
        spread = max(1, r // 2)
        for step in range(1, r + 1):
            half = int(spread * step / r)
            if dx == 1:
                self._rect(cx + step - 1, cy - half, 1, 2 * half, 0x111111)
            elif dx == -1:
                self._rect(cx - step, cy - half, 1, 2 * half, 0x111111)
            elif dy == 1:
                self._rect(cx - half, cy + step - 1, 2 * half, 1, 0x111111)
            else:
                self._rect(cx - half, cy - step, 2 * half, 1, 0x111111)

    def _diamond(self, cx: int, cy: int, r: int, color: int) -> None:
        """Filled diamond shape centered at (cx, cy) with radius r."""
        for dy in range(-r, r + 1):
            hw = r - abs(dy)
            self._hline(cx - hw, cx + hw, cy + dy, color)

    @staticmethod
    def _dim(color: int, f: float) -> int:
        """Return color scaled by factor f (0.0 = black, 1.0 = unchanged)."""
        r = int(((color >> 16) & 0xFF) * f)
        g = int(((color >> 8) & 0xFF) * f)
        b = int((color & 0xFF) * f)
        return (r << 16) | (g << 8) | b

    @staticmethod
    def _blend(c1: int, c2: int, t: float) -> int:
        """Blend c1 toward c2 by factor t (0.0 = c1, 1.0 = c2)."""
        s = 1.0 - t
        r = int(((c1 >> 16) & 0xFF) * s + ((c2 >> 16) & 0xFF) * t)
        g = int(((c1 >> 8) & 0xFF) * s + ((c2 >> 8) & 0xFF) * t)
        b = int((c1 & 0xFF) * s + (c2 & 0xFF) * t)
        return (r << 16) | (g << 8) | b

    # ── floor tile with bevel texture ─────────────────────────────────────────

    def _draw_floor_tile(self, px: int, py: int, cw: int, fc: int) -> None:
        """Beveled stone tile: darker border, lighter top-left, darker bottom-right."""
        border = self._dim(fc, 0.70)
        lighter = self._blend(fc, 0xFFFFFF, 0.22)
        shadow = self._dim(fc, 0.58)
        # border frame
        self._rect(px, py, cw, cw, border)
        # main fill
        self._rect(px + 1, py + 1, cw - 2, cw - 2, fc)
        if cw >= 6:
            # top-left bevel highlight (light source top-left)
            self._hline(px + 1, px + cw - 2, py + 1, lighter)
            self._rect(px + 1, py + 2, 1, cw - 4, lighter)
            # bottom-right shadow
            self._hline(px + 1, px + cw - 2, py + cw - 2, shadow)
            self._rect(px + cw - 2, py + 2, 1, cw - 4, shadow)

    # ── wall drawing with stone texture ───────────────────────────────────────

    def _wall_h(self, px: int, py: int, length: int) -> None:
        """Horizontal wall: beveled top face + stone-scored front face."""
        c = self._col()
        # top face with highlight on top edge
        self._rect(px, py, length, self._wall, c['wall_top'])
        self._hline(px, px + length - 1, py, self._blend(c['wall_top'], 0xFFFFFF, 0.35))
        # front face with horizontal score line (stone layer seam)
        self._rect(px, py + self._wall, length, self._wf, c['wall_face'])
        if self._wf >= 4:
            score = self._dim(c['wall_face'], 0.55)
            self._hline(px, px + length - 1, py + self._wall + self._wf // 2, score)

    def _wall_v(self, px: int, py: int, length: int) -> None:
        """Vertical wall: beveled top face + stone-scored front face."""
        c = self._col()
        # top face with highlight on left edge
        self._rect(px, py, self._wall, length, c['wall_top'])
        self._rect(px, py, 1, length, self._blend(c['wall_top'], 0xFFFFFF, 0.35))
        # front face with regular horizontal score lines
        self._rect(px + self._wall, py, self._wf, length, c['wall_face'])
        if self._wf >= 4:
            score = self._dim(c['wall_face'], 0.55)
            step = max(4, self._cell // 4)
            for sy in range(0, length, step):
                self._hline(
                    px + self._wall, px + self._wall + self._wf - 1, py + sy, score)

    # ── path trail ────────────────────────────────────────────────────────────

    def _draw_path(self, sol: list, cw: int, c: dict) -> None:
        """Draw solution as a thick connected trail with node circles at each cell."""
        if not sol:
            return
        pc = c['path']
        halo = self._dim(pc, 0.38)
        half = cw // 2
        trail = max(3, cw // 3)
        node_r = max(2, cw // 5)

        # thick connecting segment between each pair of adjacent cells
        for i in range(len(sol) - 1):
            x0, y0 = sol[i]
            x1, y1 = sol[i + 1]
            px0, py0 = self._cell_px(x0, y0)
            px1, py1 = self._cell_px(x1, y1)
            cx0, cy0 = px0 + half, py0 + half
            cx1, cy1 = px1 + half, py1 + half
            sx = min(cx0, cx1) - trail // 2
            sy = min(cy0, cy1) - trail // 2
            sw = abs(cx1 - cx0) + trail
            sh = abs(cy1 - cy0) + trail
            self._rect(sx - 1, sy - 1, sw + 2, sh + 2, halo)
            self._rect(sx, sy, sw, sh, pc)

        # circle node at each cell center (skip entry/exit — they have diamond markers)
        for pos in sol:
            if pos in (self.entry, self.exit):
                continue
            x, y = pos
            px, py = self._cell_px(x, y)
            cx, cy = px + half, py + half
            self._circle(cx, cy, node_r + 1, halo)
            self._circle(cx, cy, node_r, pc)

    # ── solution cache ─────────────────────────────────────────────────────────

    def _col(self) -> Any:
        """Return the colour palette for the current theme."""
        return MLX_THEMES.get(self.theme, MLX_THEMES['spring'])

    def _get_solution(self) -> list:
        """Return cached solution coords, recomputing if dirty."""
        if self._sol_dirty:
            from mazegen.solver import MazeSolver
            self._sol_cache = MazeSolver(self.generator).solve_as_coords(
                self.entry, self.exit)
            self._sol_dirty = False
        return self._sol_cache

    # ── render ─────────────────────────────────────────────────────────────────

    def _cell_px(self, x: int, y: int) -> Tuple[int, int]:
        """Return the pixel coordinates of the top-left corner of cell (x, y)."""
        w = self._wall
        c = self._cell
        return w + x * c, w + y * c

    def _render(self) -> None:
        """Redraw the entire maze view and flush to the MLX window."""
        c = self._col()
        grid = self.generator.grid
        gh = len(grid)
        gw = len(grid[0]) if gh > 0 else 0
        sol = self._get_solution() if self.show_solution else []
        cell = self._cell
        wall = self._wall
        cw = cell - wall

        # ── background & side panel ───────────────────────────────────────
        self._rect(0, 0, self._win_w, self._win_h, c['bg'])
        self._rect(self._mw, 0, _PANEL_W, self._win_h, c['panel'])
        self._rect(self._mw, 0, 3, self._win_h, c['wall_face'])

        # ── floor tiles with bevel texture ────────────────────────────────
        for y in range(gh):
            for x in range(gw):
                pos = (x, y)
                px, py = self._cell_px(x, y)
                if pos == self.entry:
                    fc = c['entry']
                elif pos == self.exit:
                    fc = c['exit']
                elif pos in self._p42:
                    fc = c['special']
                elif self._animating and self._anim_visited is not None:
                    if pos == self._anim_pos:
                        fc = c['accent']
                    elif pos not in self._anim_visited:
                        fc = 0x101010
                    elif (x + y) % 2 == 0:
                        fc = c['floor']
                    else:
                        fc = c['floor_alt']
                elif (x + y) % 2 == 0:
                    fc = c['floor']
                else:
                    fc = c['floor_alt']
                self._draw_floor_tile(px, py, cw, fc)

        # ── solution path trail (drawn before markers so diamonds are on top) ──
        if sol:
            self._draw_path(sol, cw, c)
            if self._pac_anim and self._pac_idx < len(sol):
                pac_pos = tuple(sol[self._pac_idx])
                half = cw // 2
                px_, py_ = self._cell_px(*pac_pos)
                mouth_open = (self._pac_tick // 4) % 2 == 0
                self._draw_pacman(px_ + half, py_ + half,
                                  max(3, cw // 2 - 1), self._pac_dir, mouth_open)

        # ── entry / exit — clean diamond markers
        for pos, color in [(self.entry, c['entry']), (self.exit, c['exit'])]:
            px, py = self._cell_px(*pos)
            cx, cy = px + cw // 2, py + cw // 2
            self._diamond(cx, cy, max(3, cw // 2 - 1), self._dim(color, 0.35))
            self._diamond(cx, cy, max(2, cw // 3), color)
            self._circle(cx, cy, max(1, cw // 8), self._blend(color, 0xFFFFFF, 0.6))

        # ── walls
        for y in range(gh):
            for x in range(gw):
                cv = grid[y][x]
                px, py = self._cell_px(x, y)
                if cv & NORTH:
                    self._wall_h(px - wall, py - wall, cell + wall)
                if cv & WEST:
                    self._wall_v(px - wall, py - wall, cell + wall)

        # outer south + east borders (always present)
        self._wall_h(0, self._mh - wall, self._mw)
        self._wall_v(self._mw - wall, 0, self._mh)

        # ── corner posts at every grid junction
        for gy in range(gh + 1):
            for gx in range(gw + 1):
                cpx = gx * cell
                cpy = gy * cell
                self._rect(cpx, cpy, wall, wall, c['wall_top'])
                self._rect(cpx, cpy + wall, wall, self._wf, c['wall_face'])

        self._mlx.mlx_clear_window(self._ptr, self._win)
        # ── flush to window, then draw panel text on top
        self._mlx.mlx_put_image_to_window(self._ptr, self._win, self._img, 0, 0)
        self._draw_panel(gw, gh, sol, c)

    def _mc_text(self, x: int, y: int, text: str,
                 col: int = 0xFFFFFF) -> None:
        """Text with a 1-pixel Minecraft-style drop shadow."""
        self._mlx.mlx_string_put(
            self._ptr, self._win, x + 1, y + 1, self._dim(col, 0.28), text)
        self._mlx.mlx_string_put(self._ptr, self._win, x, y, col, text)

    def _mc_btn(self, bx: int, y: int, bw: int, bh: int, label: str,
                face: int, hi: int, sh: int) -> None:
        """Minecraft-style beveled button with centered drop-shadow label."""
        self._rect(bx, y, bw, bh, _MC_BORD)
        self._rect(bx + 2, y + 2, bw - 4, bh - 4, face)
        top_h = max(2, bh // 3)
        self._rect(bx + 2, y + 2, bw - 4, top_h, hi)
        self._rect(bx + 2, y + bh - 4, bw - 4, 2, sh)
        tx = bx + max(4, (bw - len(label) * 8) // 2)
        self._mc_text(tx, y + (bh - 8) // 2, label)

    def _draw_panel(self, gw: int, gh: int, sol: list, c: dict) -> None:
        """Render the right-hand info and control panel."""
        px = self._mw
        pw = _PANEL_W
        bx = px + 10
        bw = pw - 20
        bh = 22
        gap = 4
        ac = c['accent']
        perfect = getattr(self.generator, 'perfect', True)

        # ── title block ───────────────────────────────────────────────
        y = 8
        self._rect(px + 4, y, pw - 8, 36, _MC_BORD)
        self._rect(px + 4, y, pw - 8, 1,
                   self._blend(_MC_BORD, 0xFFFFFF, 0.12))
        self._rect(px + 4, y + 35, pw - 8, 1, 0x000000)
        title = 'A-MAZE-ING'
        self._mc_text(px + (pw - len(title) * 8) // 2, y + 13, title, ac)
        y += 46

        # ── info lines ────────────────────────────────────────────────
        line1 = f'{gw} x {gh}  |  {"Perfect" if perfect else "Imperfect"}'
        self._mc_text(
            px + (pw - len(line1) * 8) // 2, y, line1, _MC_TXT_DIM)
        y += 14
        line2 = f'Theme: {self.theme.capitalize()}'
        self._mc_text(
            px + (pw - len(line2) * 8) // 2, y, line2, _MC_TXT_DIM)
        y += 22

        # ── menu buttons ──────────────────────────────────────────────
        self._mc_btn(bx, y, bw, bh, '[R]  Regen',
                     _MC_GO, _MC_GO_HI, _MC_GO_SH)
        y += bh + gap

        if self._animating:
            lbl = 'Generating...'
            bf, bhi, bsh = _MC_GO, _MC_GO_HI, _MC_GO_SH
        elif self.show_solution:
            lbl = f'[S]  Sol: ON  ({len(sol)})'
            bf, bhi, bsh = _MC_GO, _MC_GO_HI, _MC_GO_SH
        else:
            lbl, bf, bhi, bsh = ('[S]  Sol: OFF',
                                 _MC_BTN, _MC_BTN_HI, _MC_BTN_SH)
        self._mc_btn(bx, y, bw, bh, lbl, bf, bhi, bsh)
        y += bh + gap

        self._mc_btn(bx, y, bw, bh,
                     f'[T]  Theme: {self.theme.capitalize()}',
                     _MC_BTN, _MC_BTN_HI, _MC_BTN_SH)
        y += bh + gap

        self._mc_btn(bx, y, bw, bh, '[Ret]  S & Q',
                     _MC_BTN, _MC_BTN_HI, _MC_BTN_SH)
        y += bh + gap

        self._mc_btn(bx, y, bw, bh, '[Esc]  Quit',
                     _MC_QUIT, _MC_QUIT_HI, _MC_QUIT_SH)
        y += bh + 16

        # ── legend pills (Entry / Solution / Exit) ────────────────────
        gap3 = 4
        lbw = (bw - gap3 * 2) // 3
        lbh = 26
        legend = [
            (c['entry'], 'Entry'),
            (c['path'], 'Solution'),
            (c['exit'], 'Exit'),
        ]
        for i, (col, lbl) in enumerate(legend):
            lbx = bx + i * (lbw + gap3)
            col_hi = self._blend(col, 0xFFFFFF, 0.25)
            col_sh = self._dim(col, 0.55)
            self._rect(lbx, y, lbw, lbh, _MC_BORD)
            self._rect(lbx + 2, y + 2, lbw - 4, lbh - 4, col)
            self._rect(lbx + 2, y + 2, lbw - 4, lbh // 3, col_hi)
            self._rect(lbx + 2, y + lbh - 4, lbw - 4, 2, col_sh)
            tx = lbx + max(2, (lbw - len(lbl) * 8) // 2)
            self._mc_text(tx, y + (lbh - 8) // 2, lbl)

        # ── version footer ────────────────────────────────────────────
        ver = 'v1.0.0'
        self._mc_text(
            px + pw - len(ver) * 8 - 8, self._win_h - 14, ver, _MC_TXT_DIM)

    # ── events ─────────────────────────────────────────────────────────────────

    def _on_key(self, key: int, _: Any) -> int:
        """Handle keyboard input for both menu and game states."""
        if self._in_menu:
            if key == 65307:    # Esc — quit from menu
                self._mlx.mlx_loop_exit(self._ptr)
            elif key == 65293:  # Enter — start game
                self._in_menu = False
                self._render()
            elif key == 116:    # t — cycle theme in menu
                themes = list(MLX_THEMES)
                self.theme = themes[(themes.index(self.theme) + 1) % len(themes)]
                self._render_menu()
            return 0

        if key == 65307:       # Esc
            self._mlx.mlx_loop_exit(self._ptr)
        elif key == 65293:     # Enter — save + quit
            from .output_writer import write_output
            write_output(self.generator, self.entry, self.exit, 'maze.txt')
            self._mlx.mlx_loop_exit(self._ptr)
        elif key == 114:       # r — start animated regeneration
            self._start_anim()
        elif key == 115:       # s — toggle solution / pac-man
            self.show_solution = not self.show_solution
            if self.show_solution:
                self._get_solution()
                self._pac_anim  = True
                self._pac_idx   = 0
                self._pac_tick  = 0
                self._pac_dir   = (1, 0)
                self._pac_trail = set()
            else:
                self._pac_anim = False
            self._render()
        elif key == 116:       # t — cycle theme
            themes = list(MLX_THEMES)
            self.theme = themes[(themes.index(self.theme) + 1) % len(themes)]
            self._render()
        return 0

    def _start_anim(self) -> None:
        """Initialise animation state and start a new generation iterator."""
        self._animating = True
        self._anim_visited = {(0, 0)}
        self._anim_pos = (0, 0)
        self._sol_dirty = True
        self._step_iter = self.generator.generate_steps()
        self._pac_anim = False
        self.show_solution = False

    def _anim_frame(self, _: Any) -> int:
        """Advance the generation animation by _STEPS_PER_FRAME steps."""
        if self._in_menu:
            return 0
        self._tick = (self._tick + 1) % 3600
        if (self._animating
                and self._step_iter is not None
                and self._anim_visited is not None):
            try:
                for _ in range(_STEPS_PER_FRAME):
                    pos = next(self._step_iter)
                    self._anim_pos = pos
                    self._anim_visited.add(pos)
            except StopIteration:
                self._animating = False
                self._anim_pos = None
                self._anim_visited = None
                self._step_iter = None
                self._sol_dirty = True
                self._p42 = getattr(self.generator, 'locked', set()) or set()
            self._render()
        if self._pac_anim and self._sol_cache:
            self._pac_tick += 1
            if self._pac_tick % 3 == 0:
                sol = self._sol_cache
                if self._pac_idx < len(sol) - 1:
                    self._pac_trail.add(tuple(sol[self._pac_idx]))
                    prev = sol[self._pac_idx]
                    self._pac_idx += 1
                    cur = sol[self._pac_idx]
                    self._pac_dir = (cur[0] - prev[0], cur[1] - prev[1])
                else:
                    self._pac_idx = 0
                    self._pac_trail = set()
            self._render()
        return 0

    def run(self) -> None:
        """Start the MLX event loop."""
        self._render_menu()
        self._mlx.mlx_key_hook(self._win, self._on_key, None)
        self._mlx.mlx_hook(self._win, 33, 0,
                           lambda _: self._mlx.mlx_loop_exit(self._ptr), None)
        self._mlx.mlx_loop_hook(self._ptr, self._anim_frame, None)
        self._mlx.mlx_loop(self._ptr)
        self._mlx.mlx_destroy_image(self._ptr, self._img)
        self._mlx.mlx_destroy_window(self._ptr, self._win)
        self._mlx.mlx_release(self._ptr)
