"""BSP法によるダンジョン生成"""
import random
from constants import TILE_FLOOR, TILE_WALL, TILE_STAIRS


class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)


class BSPNode:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.left = None
        self.right = None
        self.room = None

    def split(self, min_size=8):
        if self.left or self.right:
            return False
        if self.w / self.h >= 1.25:
            horizontal = False
        elif self.h / self.w >= 1.25:
            horizontal = True
        else:
            horizontal = random.random() > 0.5
        max_size = (self.h if horizontal else self.w) - min_size
        if max_size < min_size:
            return False
        split = random.randint(min_size, max_size)
        if horizontal:
            self.left = BSPNode(self.x, self.y, self.w, split)
            self.right = BSPNode(self.x, self.y + split, self.w, self.h - split)
        else:
            self.left = BSPNode(self.x, self.y, split, self.h)
            self.right = BSPNode(self.x + split, self.y, self.w - split, self.h)
        return True


def _get_leaves(node):
    if not node.left and not node.right:
        return [node]
    leaves = []
    if node.left:
        leaves.extend(_get_leaves(node.left))
    if node.right:
        leaves.extend(_get_leaves(node.right))
    return leaves


def _get_room(node):
    if node.room:
        return node.room
    left = _get_room(node.left) if node.left else None
    right = _get_room(node.right) if node.right else None
    if left and right:
        return random.choice([left, right])
    return left or right


def _carve_h(tiles, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
            if tiles[y][x] == TILE_WALL:
                tiles[y][x] = TILE_FLOOR


def _carve_v(tiles, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
            if tiles[y][x] == TILE_WALL:
                tiles[y][x] = TILE_FLOOR


def _connect(node, tiles):
    if not node.left or not node.right:
        return
    _connect(node.left, tiles)
    _connect(node.right, tiles)
    left_room = _get_room(node.left)
    right_room = _get_room(node.right)
    if left_room and right_room:
        cx1, cy1 = left_room.center
        cx2, cy2 = right_room.center
        if random.random() > 0.5:
            _carve_h(tiles, cx1, cx2, cy1)
            _carve_v(tiles, cy1, cy2, cx2)
        else:
            _carve_v(tiles, cy1, cy2, cx1)
            _carve_h(tiles, cx1, cx2, cy2)


def generate_dungeon(width, height, floor_num):
    """ダンジョンを生成して(tiles, rooms)を返す"""
    tiles = [[TILE_WALL] * width for _ in range(height)]
    root = BSPNode(1, 1, width - 2, height - 2)

    # 再帰的に分割
    nodes = [root]
    for _ in range(5):
        new_nodes = []
        for node in nodes:
            if node.split():
                new_nodes.extend([node.left, node.right])
            else:
                new_nodes.append(node)
        nodes = new_nodes

    # 部屋を作成
    leaves = _get_leaves(root)
    rooms = []
    for leaf in leaves:
        max_w = min(10, leaf.w - 2)
        max_h = min(10, leaf.h - 2)
        if max_w < 4 or max_h < 4:
            continue
        rw = random.randint(4, max_w)
        rh = random.randint(4, max_h)
        rx = leaf.x + random.randint(1, leaf.w - rw - 1)
        ry = leaf.y + random.randint(1, leaf.h - rh - 1)
        room = Room(rx, ry, rw, rh)
        leaf.room = room
        rooms.append(room)

    # 部屋をタイルに刻む
    for room in rooms:
        for y in range(room.y, room.y + room.h):
            for x in range(room.x, room.x + room.w):
                tiles[y][x] = TILE_FLOOR

    # 通路で接続
    _connect(root, tiles)

    # 階段を最後の部屋の中央に配置
    if rooms:
        sx, sy = rooms[-1].center
        tiles[sy][sx] = TILE_STAIRS

    return tiles, rooms
