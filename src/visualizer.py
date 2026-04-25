"""
Visualiseur mlx - Sol 2D flat + murs avec face frontale uniquement
Style Animal Crossing : vue légèrement plongeante, stable et lisible
"""

from typing import Tuple, TYPE_CHECKING
if TYPE_CHECKING:
    from mazegen.generator import MazeGenerator

from mazegen.generator import NORTH, EAST, SOUTH, WEST

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_CELL  = 24   # floor tile size in pixels
_WALL  = 4    # wall thickness (pixels)
_WFACE = 8    # wall front face height (the "3D" depth illusion)

MLX_THEMES = {
    'spring': {
        'floor':       0xC8DF90,  'floor_alt':  0xB0C870,
        'wall_top':    0x4A9A32,  'wall_face':  0x1E5A14,
        'path':        0xFFCC00,  'entry':      0x50B8FF,
        'exit':        0xFF5050,  'special':    0xCC80FF,
        'bg':          0xE8F5D0,
        'panel':       0xC8E6B9,  'text':       0x1E3C1E,
    },
    'summer': {
        'floor':       0xF0E898,  'floor_alt':  0xD8D070,
        'wall_top':    0x00A8A8,  'wall_face':  0x005A5A,
        'path':        0xFFE000,  'entry':      0x3CA0FF,
        'exit':        0xFF4646,  'special':    0xC070FF,
        'bg':          0xD8F4F8,
        'panel':       0xAADCE6,  'text':       0x004650,
    },
    'autumn': {
        'floor':       0xE8C870,  'floor_alt':  0xC8A850,
        'wall_top':    0xD05810,  'wall_face':  0x882808,
        'path':        0xFFC800,  'entry':      0x3CA0FF,
        'exit':        0xFF4646,  'special':    0xB464DC,
        'bg':          0xFFF0D0,
        'panel':       0xEBBE91,  'text':       0x642308,
    },
    'winter': {
        'floor':       0xD8ECFF,  'floor_alt':  0xBCCEF0,
        'wall_top':    0xE8F4FF,  'wall_face':  0x7080A0,
        'path':        0x00D7FF,  'entry':      0x3CA0FF,
        'exit':        0xFF4646,  'special':    0xE080FF,
        'bg':          0xDCECFF,
        'panel':       0xB9CDF0,  'text':       0x233763,
    },
}


def run_interactive(generator, entry: Tuple[int, int], exit_pos: Tuple[int, int], theme: str = "spring") -> None:
    MlxMazeVisualizer(generator, entry, exit_pos, theme).run()


class MlxMazeVisualizer:
    _PANEL_W = 230

    def __init__(self, generator, entry, exit_pos, theme="spring"):
        self.generator            = generator
        self.entry                = entry
        self.exit                 = exit_pos
        self.theme                = theme
        self.show_solution        = False
        self._solution_cache      = set()
        self._solution_dirty      = True
        self._pattern42_cells     = self._load_pattern42()

        from mlx import Mlx
        self._mlx = Mlx()
        self._ptr = self._mlx.mlx_init()
        self._init_window()

    # ------------------------------------------------------------------ setup

    def _load_pattern42(self):
        return getattr(self.generator, 'locked', set()) or set()

    def _c(self):
        return MLX_THEMES.get(self.theme, MLX_THEMES['spring'])

    def _init_window(self):
        gh = len(self.generator.grid)
        gw = len(self.generator.grid[0]) if gh > 0 else 0

        # Auto-scale cell so maze fits in ~1050 x 870
        cell, wf = _CELL, _WFACE
        while cell > 6:
            mw = gw * cell + _WALL
            mh = gh * cell + _WALL + wf
            if mw <= 1050 - self._PANEL_W and mh <= 870:
                break
            cell -= 1
            wf = max(2, _WFACE * cell // _CELL)
        self._cell = cell
        self._wf   = wf          # front face height
        self._wall = max(2, _WALL * cell // _CELL)

        self._mw = gw * self._cell + self._wall   # maze pixel width
        self._mh = gh * self._cell + self._wall   # maze pixel height (floor only)

        self._win_w = self._mw + self._PANEL_W
        self._win_h = max(self._mh + self._wf + 4, 380)

        self._win  = self._mlx.mlx_new_window(self._ptr, self._win_w, self._win_h, "A-Maze-ing")
        self._img  = self._mlx.mlx_new_image(self._ptr, self._win_w, self._win_h)
        self._data, self._bpp, self._sl, _ = self._mlx.mlx_get_data_addr(self._img)

    # ------------------------------------------------------------ primitives

    def _hline(self, x0, x1, y, color):
        if x0 > x1: x0, x1 = x1, x0
        x0 = max(x0, 0); x1 = min(x1, self._win_w - 1)
        if x0 > x1 or not (0 <= y < self._win_h): return
        bpp = self._bpp // 8
        r = (color >> 16) & 0xFF
        g = (color >>  8) & 0xFF
        b =  color        & 0xFF
        row = bytes([b, g, r, 0xFF]) * (x1 - x0 + 1)
        off = y * self._sl + x0 * bpp
        self._data[off:off + len(row)] = row

    def _fill_rect(self, rx, ry, rw, rh, color):
        if rw <= 0 or rh <= 0: return
        bpp = self._bpp // 8
        r = (color >> 16) & 0xFF
        g = (color >>  8) & 0xFF
        b =  color        & 0xFF
        x0 = max(rx, 0); x1 = min(rx + rw, self._win_w)
        if x0 >= x1: return
        row = bytes([b, g, r, 0xFF]) * (x1 - x0)
        for dy in range(rh):
            yy = ry + dy
            if 0 <= yy < self._win_h:
                off = yy * self._sl + x0 * bpp
                self._data[off:off + len(row)] = row

    def _fill_circle(self, cx, cy, radius, color):
        r2 = radius * radius
        bpp = self._bpp // 8
        r = (color >> 16) & 0xFF
        g = (color >>  8) & 0xFF
        b =  color        & 0xFF
        px = bytes([b, g, r, 0xFF])
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= r2:
                    xx, yy = cx+dx, cy+dy
                    if 0 <= xx < self._win_w and 0 <= yy < self._win_h:
                        off = yy * self._sl + xx * bpp
                        self._data[off:off+bpp] = px

    # ------------------------------------------------------------ wall drawing
    # A wall segment occupies `_wall` pixels wide/tall on the floor grid.
    # The "front face" is a rectangle drawn BELOW the wall top, giving depth.

    def _draw_wall_h(self, px, py, length):
        """Horizontal wall top + front face at pixel (px, py), `length` wide."""
        c   = self._c()
        w   = self._wall
        wf  = self._wf
        # top face (the wall surface seen from above)
        self._fill_rect(px, py, length, w, c['wall_top'])
        # front face (the visible south side — gives the 3D look)
        self._fill_rect(px, py + w, length, wf, c['wall_face'])

    def _draw_wall_v(self, px, py, length):
        """Vertical wall top + front face at pixel (px, py), `length` tall."""
        c   = self._c()
        w   = self._wall
        wf  = self._wf
        # top face
        self._fill_rect(px, py, w, length, c['wall_top'])
        # front face (east side of a vertical wall)
        self._fill_rect(px + w, py, wf, length, c['wall_face'])

    # ------------------------------------------------------------ solution

    def _get_solution(self):
        if self._solution_dirty:
            from mazegen.solver import MazeSolver
            dirs = MazeSolver(self.generator).solve(self.entry, self.exit)
            pos  = set()
            if dirs:
                x, y = self.entry
                pos.add((x, y))
                for d in dirs:
                    if   d == 'N': y -= 1
                    elif d == 'S': y += 1
                    elif d == 'E': x += 1
                    elif d == 'W': x -= 1
                    pos.add((x, y))
            self._solution_cache = pos
            self._solution_dirty = False
        return self._solution_cache

    # ---------------------------------------------------------------- render

    def _cell_px(self, x, y):
        """Top-left pixel of floor area inside cell (x,y)."""
        w = self._wall
        c = self._cell
        return w + x * c, w + y * c

    def _render(self):
        c    = self._c()
        grid = self.generator.grid
        gh   = len(grid)
        gw   = len(grid[0]) if gh > 0 else 0
        sol  = self._get_solution() if self.show_solution else set()
        cell = self._cell
        wall = self._wall

        # 1. Background
        self._fill_rect(0, 0, self._win_w, self._win_h, c['bg'])

        # 2. Panel
        self._fill_rect(self._mw, 0, self._PANEL_W, self._win_h, c['panel'])
        self._fill_rect(self._mw, 0, 2, self._win_h, c['wall_face'])

        # 3. Floor tiles — draw all floors first
        for y in range(gh):
            for x in range(gw):
                pos = (x, y)
                px, py = self._cell_px(x, y)
                cw = cell - wall  # inner cell width

                if pos == self.entry:
                    fc = c['entry']
                elif pos == self.exit:
                    fc = c['exit']
                elif pos in self._pattern42_cells:
                    fc = c['special']
                elif (x + y) % 2 == 0:
                    fc = c['floor']
                else:
                    fc = c['floor_alt']

                self._fill_rect(px, py, cw, cw, fc)

        # 4. Solution dots — above floors, below walls
        for pos in sol:
            if pos in (self.entry, self.exit):
                continue
            x, y = pos
            px, py = self._cell_px(x, y)
            cw = cell - wall
            cx = px + cw // 2
            cy = py + cw // 2
            r  = max(2, cell // 6)
            self._fill_circle(cx, cy, r, c['path'])

        # 5. Walls — drawn on top of everything
        # Draw NORTH and WEST walls for each cell (covers all walls exactly once)
        for y in range(gh):
            for x in range(gw):
                cell_val = grid[y][x]
                px, py   = self._cell_px(x, y)

                # NORTH wall of (x, y) — horizontal segment at top of cell
                if not (cell_val & NORTH):
                    self._draw_wall_h(px - wall, py - wall, cell + wall)

                # WEST wall of (x, y) — vertical segment at left of cell
                if not (cell_val & WEST):
                    self._draw_wall_v(px - wall, py - wall, cell + wall)

        # Outer south border
        self._draw_wall_h(0, self._mh - wall, self._mw)
        # Outer east border
        self._draw_wall_v(self._mw - wall, 0, self._mh)

        # 6. Flush
        self._mlx.mlx_put_image_to_window(self._ptr, self._win, self._img, 0, 0)

        # 7. Panel text
        tc = c['text']
        ox = self._mw + 14
        self._mlx.mlx_string_put(self._ptr, self._win, ox,  18, tc, "A-Maze-ing")
        self._mlx.mlx_string_put(self._ptr, self._win, ox,  46, tc, f"Taille  : {gw} x {gh}")
        self._mlx.mlx_string_put(self._ptr, self._win, ox,  64, tc, f"Theme   : {self.theme.capitalize()}")
        perfect = getattr(self.generator, 'perfect', True)
        self._mlx.mlx_string_put(self._ptr, self._win, ox,  82, tc, f"Parfait : {'Oui' if perfect else 'Non'}")
        # if self.show_solution:
        #     self._mlx.mlx_string_put(self._ptr, self._win, ox, 100, tc, f"Chemin  : {len(sol)} cells")
        self._mlx.mlx_string_put(self._ptr, self._win, ox, 130, tc, "-- Controles --")
        for i, (key, desc) in enumerate([
            ("[R]",      "Regenerer"),
            ("[S]",      "Solution on/off"),
            ("[T]",      "Changer theme"),
            ("[Entree]", "Sauver & quitter"),
            ("[Esc]",    "Quitter"),
        ]):
            yp = 152 + i * 18
            self._mlx.mlx_string_put(self._ptr, self._win, ox,      yp, tc, key)
            self._mlx.mlx_string_put(self._ptr, self._win, ox + 72, yp, tc, desc)

    # ---------------------------------------------------------------- events

    def _on_key(self, key, _):
        if key == 65307:
            self._mlx.mlx_loop_exit(self._ptr)
        elif key == 65293:
            from .output_writer import write_output
            write_output(self.generator, self.entry, self.exit, "maze.txt")
            self._mlx.mlx_loop_exit(self._ptr)
        elif key == 114:    # r
            self.generator.generate()
            self._solution_dirty  = True
            self._pattern42_cells = self._load_pattern42()
            self._render()
        elif key == 115:    # s
            self.show_solution = not self.show_solution
            self._render()
        elif key == 116:    # t
            themes     = list(MLX_THEMES.keys())
            self.theme = themes[(themes.index(self.theme) + 1) % len(themes)]
            self._render()
        return 0

    def run(self):
        self._render()
        self._mlx.mlx_key_hook(self._win, self._on_key, None)
        self._mlx.mlx_hook(self._win, 33, 0, lambda _: self._mlx.mlx_loop_exit(self._ptr), None)
        self._mlx.mlx_loop(self._ptr)
        self._mlx.mlx_destroy_image(self._ptr, self._img)
        self._mlx.mlx_destroy_window(self._ptr, self._win)
        self._mlx.mlx_release(self._ptr)