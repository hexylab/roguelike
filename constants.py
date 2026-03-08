"""ゲーム定数"""

SCREEN_W = 480
SCREEN_H = 320
TILE_SIZE = 32
SPRITE_SIZE_SM = 16  # DawnLike素材のスプライトサイズ
DISPLAY_SCALE = 2  # 表示倍率（960x640で描画）

MAP_VIEW_W = 10
MAP_VIEW_H = 10
PANEL_X = MAP_VIEW_W * TILE_SIZE  # 320
PANEL_W = SCREEN_W - PANEL_X  # 160

DUNGEON_W = 48
DUNGEON_H = 48
MAX_FLOOR = 10
INVENTORY_MAX = 20
FOV_RADIUS = 8

FONT_PATH = "assets/misaki_gothic.bdf"

# タイルタイプ
TILE_NONE = 0
TILE_FLOOR = 1
TILE_WALL = 2
TILE_STAIRS = 3

# ゲーム状態
STATE_TITLE = 0
STATE_PLAY = 1
STATE_INVENTORY = 2
STATE_GAMEOVER = 3
STATE_VICTORY = 4

# Image banks
IMG_MAP = 0
IMG_CHARS = 1
IMG_ITEMS = 2

# DawnBringer 16 palette
DB16 = [
    0x140c1c, 0x442434, 0x30346d, 0x4e4a4e,
    0x854c30, 0x346524, 0xd04648, 0x757161,
    0x597dce, 0xd27d2c, 0x8595a1, 0x6daa2c,
    0xd2aa99, 0x6dc2ca, 0xdad45e, 0xdeeed6,
]

# 色インデックス
COL_BLACK = 0
COL_DARK_RED = 1
COL_DARK_BLUE = 2
COL_DARK_GRAY = 3
COL_BROWN = 4
COL_DARK_GREEN = 5
COL_RED = 6
COL_GRAY = 7
COL_BLUE = 8
COL_ORANGE = 9
COL_LIGHT_GRAY = 10
COL_GREEN = 11
COL_BEIGE = 12
COL_CYAN = 13
COL_YELLOW = 14
COL_WHITE = 15

# Bank 0 (マップタイル 32x32, 2x拡大) スプライト位置
SPR_FLOOR = (0, 0)
SPR_STAIRS = (32, 0)

# 壁オートタイル: 9方向バリアント
# TL=NW角, T=上端, TR=NE角, L=左端, C=中央, R=右端, BL=SW角, B=下端, BR=SE角
SPR_WALL_TL = (64, 0)
SPR_WALL_T = (96, 0)
SPR_WALL_TR = (128, 0)
SPR_WALL_L = (160, 0)
SPR_WALL_C = (192, 0)
SPR_WALL_R = (160, 0)   # = WallL と同じスプライト（サンプルマップ準拠）
SPR_WALL_BL = (224, 0)
SPR_WALL_B = (96, 0)    # = WallT と同じスプライト（サンプルマップ準拠）
SPR_WALL_BR = (0, 176)
SPR_WALL = SPR_WALL_C   # デフォルト/後方互換

# プレイヤー識別用 (実際の描画はPLAYER_ANIMS使用)
SPR_PLAYER = (0, 0)

# Bank 0 モンスタースプライト (16x16, y=160)
SPR_SLIME = (0, 160)
SPR_BAT = (32, 160)
SPR_SKELETON = (64, 160)
SPR_ORC = (96, 160)
SPR_GOLEM = (128, 160)
SPR_DRAGON = (160, 160)

SPR_SLIME_F1 = (16, 160)
SPR_BAT_F1 = (48, 160)
SPR_SKELETON_F1 = (80, 160)
SPR_ORC_F1 = (112, 160)
SPR_GOLEM_F1 = (144, 160)
SPR_DRAGON_F1 = (176, 160)

ANIM_FRAME1 = {
    SPR_SLIME: SPR_SLIME_F1,
    SPR_BAT: SPR_BAT_F1,
    SPR_SKELETON: SPR_SKELETON_F1,
    SPR_ORC: SPR_ORC_F1,
    SPR_GOLEM: SPR_GOLEM_F1,
    SPR_DRAGON: SPR_DRAGON_F1,
}

# プレイヤー8方向インデックス
# スプライトシート行順: S(0), SE(1), E(2), NE(3), N(4), NW(5), W(6), SW(7)
DIR_TO_IDX = {
    (0, 1): 0,     # S
    (1, 1): 1,     # SE
    (1, 0): 2,     # E
    (1, -1): 3,    # NE
    (0, -1): 4,    # N
    (-1, -1): 5,   # NW
    (-1, 0): 6,    # W
    (-1, 1): 7,    # SW
}

# プレイヤーアニメーション定義: {名前: (y_base, フレーム数, x_base, img_bank)}
# x = x_base + dir_idx * 32, y = y_base + frame * 32
# Bank 1 (IMG_CHARS): idle, walk, attack (32x32フル)
# Bank 0 (IMG_MAP): hurt, death (32x32フル, y=32+)
PLAYER_ANIMS = {
    "idle":   (0, 2, 0, IMG_CHARS),
    "walk":   (64, 3, 0, IMG_CHARS),
    "attack": (160, 3, 0, IMG_CHARS),
    "hurt":   (32, 2, 0, IMG_MAP),
    "death":  (96, 2, 0, IMG_MAP),
    "stave":  (160, 3, 0, IMG_CHARS),   # attackを再利用
    "throw":  (160, 3, 0, IMG_CHARS),   # attackを再利用
    "bow":    (160, 3, 0, IMG_CHARS),   # attackを再利用
}

# アニメーション定数
ANIM_WALK_FRAMES = 8
ANIM_ATTACK_FRAMES = 6
HIT_FLASH_FRAMES = 6
SHAKE_FRAMES = 6
SHAKE_INTENSITY = 4
POPUP_FRAMES = 20
KNOCKBACK_PX = 6
ATTACK_LUNGE_PX = 8

# 8方向入力マッピング
DIRS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
    "up_left": (-1, -1),
    "up_right": (1, -1),
    "down_left": (-1, 1),
    "down_right": (1, 1),
}

# モンスター定義: (名前, SPR, HP, ATK, DEF, EXP, 出現フロア範囲)
MONSTER_DEFS = [
    ("スライム", SPR_SLIME, 8, 3, 0, 3, 1, 2),
    ("コウモリ", SPR_BAT, 12, 5, 1, 5, 2, 4),
    ("スケルトン", SPR_SKELETON, 20, 8, 3, 10, 3, 5),
    ("オーク", SPR_ORC, 30, 12, 5, 18, 5, 7),
    ("ゴーレム", SPR_GOLEM, 45, 16, 8, 30, 7, 9),
    ("ドラゴン", SPR_DRAGON, 60, 22, 12, 50, 9, 10),
]

# 武器定義: (名前, ATK, スプライトx, スプライトy in bank2)
WEAPON_DEFS = [
    ("短剣", 3, 0, 0),
    ("小剣", 5, 16, 0),
    ("剣", 8, 32, 0),
    ("広刃の剣", 12, 48, 0),
    ("長剣", 16, 64, 0),
    ("大剣", 20, 80, 0),
]

# 盾定義: (名前, DEF, スプライトx, スプライトy in bank2)
SHIELD_DEFS = [
    ("木の盾", 2, 0, 112),
    ("鉄の盾", 4, 16, 112),
    ("鋼の盾", 6, 32, 112),
    ("騎士の盾", 9, 48, 112),
    ("竜の盾", 13, 64, 112),
]

# ポーション定義: (効果名, 効果)
POTION_EFFECTS = [
    ("回復薬", "heal"),
    ("大回復薬", "big_heal"),
    ("ちからの薬", "str_up"),
    ("まもりの薬", "def_up"),
    ("毒薬", "poison"),
]

# 巻物定義
SCROLL_EFFECTS = [
    ("地図の巻物", "map_reveal"),
    ("ちからの巻物", "power_up"),
    ("混乱の巻物", "confuse"),
    ("睡眠の巻物", "sleep_enemies"),
    ("爆発の巻物", "blast"),
]

# ポーション/巻物の見た目（色名）- 未識別時の表示用
POTION_APPEARANCES = [
    "赤い", "青い", "緑の", "黄色い", "紫の",
    "白い", "橙の", "水色の",
]

SCROLL_APPEARANCES = [
    "金の", "銀の", "赤い", "青い", "緑の",
    "紫の", "白い", "茶色の",
]
