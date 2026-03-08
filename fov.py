"""視界計算（再帰シャドウキャスティング）"""
from constants import TILE_WALL

_MULT = [
    (1, 0, 0, 1), (0, 1, 1, 0), (0, -1, 1, 0), (-1, 0, 0, 1),
    (-1, 0, 0, -1), (0, -1, -1, 0), (0, 1, -1, 0), (1, 0, 0, -1),
]


def _cast(tiles, visible, cx, cy, radius, row, start, end, xx, xy, yx, yy, w, h):
    if start < end:
        return
    new_start = start
    for j in range(row, radius + 1):
        blocked = False
        dx = -j - 1
        dy = -j
        while dx <= 0:
            dx += 1
            ax = cx + dx * xx + dy * xy
            ay = cy + dx * yx + dy * yy
            if ax < 0 or ax >= w or ay < 0 or ay >= h:
                continue
            l_slope = (dx - 0.5) / (dy + 0.5)
            r_slope = (dx + 0.5) / (dy - 0.5)
            if start < r_slope:
                continue
            elif end > l_slope:
                break
            if dx * dx + dy * dy <= radius * radius:
                visible.add((ax, ay))
            if blocked:
                if tiles[ay][ax] == TILE_WALL:
                    new_start = r_slope
                    continue
                else:
                    blocked = False
                    start = new_start
            elif tiles[ay][ax] == TILE_WALL and j < radius:
                blocked = True
                _cast(tiles, visible, cx, cy, radius,
                      j + 1, start, l_slope, xx, xy, yx, yy, w, h)
                new_start = r_slope
        if blocked:
            break


def compute_fov(tiles, px, py, radius):
    """(px, py)から半径radiusの視界を計算。見えるタイル座標のsetを返す"""
    h = len(tiles)
    w = len(tiles[0]) if h > 0 else 0
    visible = {(px, py)}
    for xx, xy, yx, yy in _MULT:
        _cast(tiles, visible, px, py, radius, 1, 1.0, 0.0, xx, xy, yx, yy, w, h)
    return visible
