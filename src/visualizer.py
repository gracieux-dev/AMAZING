"""
Visualiseur MLX — A-Maze-ing
2.5D Animal Crossing style : tuiles de sol texturées + murs en pierre.
"""

from typing import Tuple, TYPE_CHECKING
if TYPE_CHECKING:
    from mazegen.generator import MazeGenerator

from mazegen.generator import NORTH, EAST, SOUTH, WEST

# ── tile geometry ──────────────────────────────────────────────────────────────
_CELL  = 24   # floor tile size (pixels)
_WALL  = 4    # wall thickness
_WFACE = 8    # wall front-face height (depth illusion)

# ── colour palettes ────────────────────────────────────────────────────────────
MLX_THEMES: dict = {
    'spring': {
        'floor':      0xC8DF90, 'floor_alt':  0xB0C870,
        'wall_top':   0x4A9A32, 'wall_face':  0x1E5A14,
        'path':       0xFF6B35, 'entry':      0x50B8FF,
        'exit':       0xFF5050, 'special':    0xCC80FF,
        'bg':         0xE8F5D0, 'panel':      0x2A4A2A,
        'text':       0xDDFFDD, 'accent':     0x88FF44,
    },
    'summer': {
        'floor':      0xF0E898, 'floor_alt':  0xD8D070,
        'wall_top':   0x00A8A8, 'wall_face':  0x005A5A,
        'path':       0x9055CC, 'entry':      0x3CA0FF,
        'exit':       0xFF4646, 'special':    0xC070FF,
        'bg':         0xD8F4F8, 'panel':      0x00363C,
        'text':       0xCCF8FF, 'accent':     0x00DDFF,
    },
    'autumn': {
        'floor':      0xE8C870, 'floor_alt':  0xC8A850,
        'wall_top':   0xD05810, 'wall_face':  0x882808,
        'path':       0x2BC7C9, 'entry':      0x3CA0FF,
        'exit':       0xFF4646, 'special':    0xB464DC,
        'bg':         0xFFF0D0, 'panel':      0x4A1800,
        'text':       0xFFE0C0, 'accent':     0xFF9900,
    },
    'winter': {
        'floor':      0xD8ECFF, 'floor_alt':  0xBCCEF0,
        'wall_top':   0xE8F4FF, 'wall_face':  0x7080A0,
        'path':       0xFFCC00, 'entry':      0x3CA0FF,
        'exit':       0xFF4646, 'special':    0xE080FF,
        'bg':         0xDCECFF, 'panel':      0x18243C,
        'text':       0xCCDDFF, 'accent':     0x88CCFF,
    },
}

_PANEL_W        = 240   # right panel width in pixels
_STEPS_PER_FRAME = 6    # DFS steps advanced per MLX loop tick
_KEYS = [
    ('[R]',       'Regenerer'),
    ('[S]',       'Solution on/off'),
    ('[T]',       'Changer theme'),
    ('[Entree]',  'Sauver + quitter'),
    ('[Esc]',     'Quitter'),
]


def run_interactive(
    generator,
    entry: Tuple[int, int],
    exit_pos: Tuple[int, int],
    theme: str = 'spring',
) -> None:
    MlxMazeVisualizer(generator, entry, exit_pos, theme).run()


class MlxMazeVisualizer:

    def __init__(self, generator, entry, exit_pos, theme: str = 'spring') -> None:
        self.generator         = generator
        self.entry             = entry
        self.exit              = exit_pos
        self.theme             = theme if theme in MLX_THEMES else 'spring'
        self.show_solution     = False
        self._sol_cache: list  = []
        self._sol_dirty        = True
        self._p42              = getattr(generator, 'locked', set()) or set()
        self._tick             = 0
        # animation state
        self._animating        = False
        self._anim_visited: set | None = None
        self._anim_pos: tuple | None   = None
        self._step_iter                = None

        from mlx import Mlx
        self._mlx = Mlx()
        self._ptr = self._mlx.mlx_init()
        self._setup_window()

    # ── window & image setup ───────────────────────────────────────────────────

    def _setup_window(self) -> None:
        gh = len(self.generator.grid)
        gw = len(self.generator.grid[0]) if gh > 0 else 0

        # auto-scale to fit inside ~1050 × 870
        cell, wf = _CELL, _WFACE
        while cell > 6:
            if gw * cell + _WALL <= 1050 - _PANEL_W and gh * cell + _WALL + wf <= 870:
                break
            cell -= 1
            wf    = max(2, _WFACE * cell // _CELL)
        wall = max(2, _WALL * cell // _CELL)

        self._cell  = cell
        self._wf    = wf
        self._wall  = wall
        self._mw    = gw * cell + wall   # maze pixel width
        self._mh    = gh * cell + wall   # maze pixel height (floor only)
        self._win_w = self._mw + _PANEL_W
        self._win_h = max(self._mh + wf + 4, 420)

        self._win  = self._mlx.mlx_new_window(self._ptr, self._win_w, self._win_h, 'A-Maze-ing')
        self._img  = self._mlx.mlx_new_image(self._ptr, self._win_w, self._win_h)
        self._data, self._bpp, self._sl, _ = self._mlx.mlx_get_data_addr(self._img)

    # ── drawing primitives ─────────────────────────────────────────────────────

    def _put(self, x: int, y: int, color: int) -> None:
        if not (0 <= x < self._win_w and 0 <= y < self._win_h):
            return
        bpp = self._bpp // 8
        off = y * self._sl + x * bpp
        self._data[off:off + bpp] = bytes([
            color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF, 0xFF,
        ])

    def _hline(self, x0: int, x1: int, y: int, color: int) -> None:
        if x0 > x1:
            x0, x1 = x1, x0
        x0 = max(x0, 0)
        x1 = min(x1, self._win_w - 1)
        if x0 > x1 or not (0 <= y < self._win_h):
            return
        bpp = self._bpp // 8
        row = bytes([color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF, 0xFF]) * (x1 - x0 + 1)
        off = y * self._sl + x0 * bpp
        self._data[off:off + len(row)] = row

    def _rect(self, rx: int, ry: int, rw: int, rh: int, color: int) -> None:
        if rw <= 0 or rh <= 0:
            return
        bpp  = self._bpp // 8
        x0   = max(rx, 0)
        x1   = min(rx + rw, self._win_w)
        row  = bytes([color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF, 0xFF]) * (x1 - x0)
        for dy in range(rh):
            yy = ry + dy
            if 0 <= yy < self._win_h:
                off = yy * self._sl + x0 * bpp
                self._data[off:off + len(row)] = row

    def _circle(self, cx: int, cy: int, r: int, color: int) -> None:
        bpp = self._bpp // 8
        px  = bytes([color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF, 0xFF])
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    xx, yy = cx + dx, cy + dy
                    if 0 <= xx < self._win_w and 0 <= yy < self._win_h:
                        self._data[yy * self._sl + xx * bpp:yy * self._sl + xx * bpp + bpp] = px

    def _diamond(self, cx: int, cy: int, r: int, color: int) -> None:
        for dy in range(-r, r + 1):
            hw = r - abs(dy)
            self._hline(cx - hw, cx + hw, cy + dy, color)

    @staticmethod
    def _dim(color: int, f: float) -> int:
        """Return color scaled by factor f (0.0 = black, 1.0 = unchanged)."""
        r = int(((color >> 16) & 0xFF) * f)
        g = int(((color >>  8) & 0xFF) * f)
        b = int(( color        & 0xFF) * f)
        return (r << 16) | (g << 8) | b

    @staticmethod
    def _blend(c1: int, c2: int, t: float) -> int:
        """Blend c1 toward c2 by factor t (0.0 = c1, 1.0 = c2)."""
        s = 1.0 - t
        r = int(((c1 >> 16) & 0xFF) * s + ((c2 >> 16) & 0xFF) * t)
        g = int(((c1 >>  8) & 0xFF) * s + ((c2 >>  8) & 0xFF) * t)
        b = int(( c1        & 0xFF) * s + ( c2        & 0xFF) * t)
        return (r << 16) | (g << 8) | b

    # ── floor tile with bevel texture ─────────────────────────────────────────

    def _draw_floor_tile(self, px: int, py: int, cw: int, fc: int) -> None:
        """Beveled stone tile: darker border, lighter top-left, darker bottom-right."""
        border  = self._dim(fc, 0.70)
        lighter = self._blend(fc, 0xFFFFFF, 0.22)
        shadow  = self._dim(fc, 0.58)
        # border frame
        self._rect(px, py, cw, cw, border)
        # main fill
        self._rect(px + 1, py + 1, cw - 2, cw - 2, fc)
        if cw >= 6:
            # top-left bevel highlight (light source top-left)
            self._hline(px + 1, px + cw - 2, py + 1, lighter)
            for dy in range(2, cw - 2):
                self._put(px + 1, py + dy, lighter)
            # bottom-right shadow
            self._hline(px + 1, px + cw - 2, py + cw - 2, shadow)
            for dy in range(2, cw - 2):
                self._put(px + cw - 2, py + dy, shadow)

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
        for dy in range(length):
            self._put(px, py + dy, self._blend(c['wall_top'], 0xFFFFFF, 0.35))
        # front face with regular horizontal score lines
        self._rect(px + self._wall, py, self._wf, length, c['wall_face'])
        if self._wf >= 4:
            score = self._dim(c['wall_face'], 0.55)
            step  = max(4, self._cell // 4)
            for sy in range(0, length, step):
                self._hline(px + self._wall, px + self._wall + self._wf - 1, py + sy, score)

    # ── path trail ────────────────────────────────────────────────────────────

    def _draw_path(self, sol: list, cw: int, c: dict) -> None:
        """Draw solution as a thick connected trail with node circles at each cell."""
        if not sol:
            return
        pc     = c['path']
        halo   = self._dim(pc, 0.38)
        half   = cw // 2
        trail  = max(3, cw // 3)   # half-width of the trail segment
        node_r = max(2, cw // 5)   # radius of the node circle

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
            self._rect(sx,     sy,     sw,     sh,     pc)

        # circle node at each cell center (skip entry/exit — they have diamond markers)
        for pos in sol:
            if pos in (self.entry, self.exit):
                continue
            x, y = pos
            px, py = self._cell_px(x, y)
            cx, cy = px + half, py + half
            self._circle(cx, cy, node_r + 1, halo)
            self._circle(cx, cy, node_r,     pc)

    # ── solution cache ─────────────────────────────────────────────────────────

    def _col(self) -> dict:
        return MLX_THEMES.get(self.theme, MLX_THEMES['spring'])

    def _get_solution(self) -> list:
        """Return ordered list of (x,y) positions along the solution path."""
        if self._sol_dirty:
            from mazegen.solver import MazeSolver
            dirs = MazeSolver(self.generator).solve(self.entry, self.exit)
            path: list = []
            if dirs:
                x, y = self.entry
                path.append((x, y))
                for d in dirs:
                    if   d == 'N': y -= 1
                    elif d == 'S': y += 1
                    elif d == 'E': x += 1
                    elif d == 'W': x -= 1
                    path.append((x, y))
            self._sol_cache = path
            self._sol_dirty = False
        return self._sol_cache

    # ── render ─────────────────────────────────────────────────────────────────

    def _cell_px(self, x: int, y: int) -> Tuple[int, int]:
        w = self._wall
        c = self._cell
        return w + x * c, w + y * c

    def _render(self) -> None:
        c    = self._col()
        grid = self.generator.grid
        gh   = len(grid)
        gw   = len(grid[0]) if gh > 0 else 0
        sol  = self._get_solution() if self.show_solution else []
        cell = self._cell
        wall = self._wall
        cw   = cell - wall

        # ── background & panel ────────────────────────────────────────────
        self._rect(0, 0, self._win_w, self._win_h, c['bg'])
        self._rect(self._mw, 0, _PANEL_W, self._win_h, c['panel'])
        self._rect(self._mw, 0, 3, self._win_h, c['wall_face'])

        # ── floor tiles with bevel texture ────────────────────────────────
        for y in range(gh):
            for x in range(gw):
                pos    = (x, y)
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

        # ── entry / exit — clean diamond markers ──────────────────────────
        for pos, color in [(self.entry, c['entry']), (self.exit, c['exit'])]:
            px, py = self._cell_px(*pos)
            cx, cy = px + cw // 2, py + cw // 2
            self._diamond(cx, cy, max(3, cw // 2 - 1), self._dim(color, 0.35))
            self._diamond(cx, cy, max(2, cw // 3),     color)
            self._circle(cx, cy, max(1, cw // 8), self._blend(color, 0xFFFFFF, 0.6))

        # ── walls ─────────────────────────────────────────────────────────
        for y in range(gh):
            for x in range(gw):
                cv = grid[y][x]
                px, py = self._cell_px(x, y)
                if cv & NORTH:
                    self._wall_h(px - wall, py - wall, cell + wall)
                if cv & WEST:
                    self._wall_v(px - wall, py - wall, cell + wall)

        # outer south + east borders (always present)
        self._wall_h(0,               self._mh - wall, self._mw)
        self._wall_v(self._mw - wall, 0,               self._mh)

        # ── corner posts at every grid junction ───────────────────────────
        for gy in range(gh + 1):
            for gx in range(gw + 1):
                cpx = gx * cell
                cpy = gy * cell
                self._rect(cpx, cpy,        wall, wall,     c['wall_top'])
                self._rect(cpx, cpy + wall, wall, self._wf, c['wall_face'])

        # ── flush to window ───────────────────────────────────────────────
        self._mlx.mlx_put_image_to_window(self._ptr, self._win, self._img, 0, 0)
        self._draw_panel(gw, gh, sol, c)

    def _draw_panel(self, gw: int, gh: int, sol: list, c: dict) -> None:
        mlx = self._mlx
        ox  = self._mw + 16
        tc  = c['text']
        ac  = c['accent']
        perfect = getattr(self.generator, 'perfect', True)

        # title
        mlx.mlx_string_put(self._ptr, self._win, ox, 20, ac, 'A - M A Z E - I N G')
        self._hline(self._mw + 8, self._win_w - 8, 36, c['wall_face'])

        # maze info
        mlx.mlx_string_put(self._ptr, self._win, ox,  52, tc, f'Taille  : {gw} x {gh}')
        mlx.mlx_string_put(self._ptr, self._win, ox,  70, tc, f'Theme   : {self.theme.capitalize()}')
        mlx.mlx_string_put(self._ptr, self._win, ox,  88, tc, f'Parfait : {"Oui" if perfect else "Non"}')
        if self._animating:
            mlx.mlx_string_put(self._ptr, self._win, ox, 106, ac, 'Generation...')
        else:
            sol_str = f'{len(sol)} cellules' if self.show_solution else 'masquee'
            mlx.mlx_string_put(self._ptr, self._win, ox, 106, tc, f'Solution: {sol_str}')

        self._hline(self._mw + 8, self._win_w - 8, 122, c['wall_face'])

        # legend: entry / exit colour swatches
        self._rect(ox, 132, 10, 10, c['entry'])
        mlx.mlx_string_put(self._ptr, self._win, ox + 14, 132, tc, 'Entree')
        self._rect(ox, 150, 10, 10, c['exit'])
        mlx.mlx_string_put(self._ptr, self._win, ox + 14, 150, tc, 'Sortie')
        if self.show_solution:
            self._rect(ox, 168, 10, 10, c['path'])
            mlx.mlx_string_put(self._ptr, self._win, ox + 14, 168, tc, 'Chemin')

        self._hline(self._mw + 8, self._win_w - 8, 188, c['wall_face'])

        # keyboard shortcuts
        mlx.mlx_string_put(self._ptr, self._win, ox, 200, ac, '-- Controles --')
        for i, (key, desc) in enumerate(_KEYS):
            yp = 218 + i * 18
            mlx.mlx_string_put(self._ptr, self._win, ox,      yp, ac, key)
            mlx.mlx_string_put(self._ptr, self._win, ox + 80, yp, tc, desc)

    # ── events ─────────────────────────────────────────────────────────────────

    def _on_key(self, key: int, _) -> int:
        if key == 65307:       # Esc
            self._mlx.mlx_loop_exit(self._ptr)
        elif key == 65293:     # Enter — save + quit
            from .output_writer import write_output
            write_output(self.generator, self.entry, self.exit, 'maze.txt')
            self._mlx.mlx_loop_exit(self._ptr)
        elif key == 114:       # r — start animated regeneration
            self._start_anim()
        elif key == 115:       # s — toggle solution
            self.show_solution = not self.show_solution
            self._render()
        elif key == 116:       # t — cycle theme
            themes     = list(MLX_THEMES)
            self.theme = themes[(themes.index(self.theme) + 1) % len(themes)]
            self._render()
        return 0

    def _start_anim(self) -> None:
        self._animating    = True
        self._anim_visited = {(0, 0)}
        self._anim_pos     = (0, 0)
        self._sol_dirty    = True
        self._step_iter    = self.generator.generate_steps()

    def _anim_frame(self, _) -> int:
        self._tick = (self._tick + 1) % 3600
        if self._animating:
            try:
                for _ in range(_STEPS_PER_FRAME):
                    pos = next(self._step_iter)
                    self._anim_pos = pos
                    self._anim_visited.add(pos)
            except StopIteration:
                self._animating    = False
                self._anim_pos     = None
                self._anim_visited = None
                self._step_iter    = None
                self._sol_dirty    = True
                self._p42          = getattr(self.generator, 'locked', set()) or set()
            self._render()
        return 0

    def run(self) -> None:
        self._render()
        self._mlx.mlx_key_hook(self._win, self._on_key, None)
        self._mlx.mlx_hook(self._win, 33, 0,
                           lambda _: self._mlx.mlx_loop_exit(self._ptr), None)
        self._mlx.mlx_loop_hook(self._ptr, self._anim_frame, None)
        self._mlx.mlx_loop(self._ptr)
        self._mlx.mlx_destroy_image(self._ptr, self._img)
        self._mlx.mlx_destroy_window(self._ptr, self._win)
        self._mlx.mlx_release(self._ptr)

    # ── public helpers (kept for API compatibility) ────────────────────────────

    def toggle_solution(self) -> None:
        self.show_solution = not self.show_solution

    def toggle_colors(self) -> None:
        pass  # MLX always uses colour

    def change_theme(self) -> None:
        themes     = list(MLX_THEMES)
        self.theme = themes[(themes.index(self.theme) + 1) % len(themes)]
