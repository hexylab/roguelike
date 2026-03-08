#!/usr/bin/env python3
"""DawnLikeタイルセットとPuny Charactersからゲーム用スプライトシートを生成する"""
from PIL import Image
import os

TILE = 16       # DawnLike素材の基本サイズ
TILE32 = 32     # Puny Characters / ゲーム内タイルサイズ
DAWN = "assets/DawnLike"
PUNY_DUNGEON = "assets/puny/Puny-Dungeon/PUNY_DUNGEON_v1"
OUT = "assets"

DB16 = [
    (20, 12, 28), (68, 36, 52), (48, 52, 109), (78, 74, 78),
    (133, 76, 48), (52, 101, 36), (208, 70, 72), (117, 113, 97),
    (89, 125, 206), (210, 125, 44), (133, 149, 161), (109, 170, 44),
    (210, 170, 153), (109, 194, 202), (218, 212, 94), (222, 238, 214),
]


def nearest_db16(r, g, b, a=255, allow_zero=True):
    if a < 128:
        return 0
    best, best_dist = 0, float('inf')
    for i, (pr, pg, pb) in enumerate(DB16):
        if not allow_zero and i == 0:
            continue
        dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if dist < best_dist:
            best_dist = dist
            best = i
    # スプライト: color 0(透明)とcolor 1(暗赤)は背景に溶け込むため
    # 暗いピクセルをcolor 3(暗灰色)に昇格して視認性向上
    if not allow_zero and best in (0, 1):
        best = 3
    return best


def remap_to_db16(img, allow_zero=True):
    """画像の全ピクセルをDB16パレットにマップ
    allow_zero=False: 不透明ピクセルを色0(透明色)にマップしない"""
    result = Image.new("RGB", img.size)
    src = img.convert("RGBA")
    for y in range(img.height):
        for x in range(img.width):
            p = src.getpixel((x, y))
            idx = nearest_db16(p[0], p[1], p[2], p[3], allow_zero=allow_zero)
            result.putpixel((x, y), DB16[idx])
    return result


def extract_tile(img, tx, ty):
    return img.crop((tx, ty, tx + TILE, ty + TILE))


def place_tile_16(dest, src_path, sx, sy, dx, dy, base_dir=DAWN, allow_zero=True):
    """16x16タイルを抽出してdestに配置"""
    src = Image.open(os.path.join(base_dir, src_path)).convert("RGBA")
    tile = extract_tile(src, sx, sy)
    tile = remap_to_db16(tile, allow_zero=allow_zero)
    dest.paste(tile, (dx, dy))


def place_tile_32(dest, src_path, sx, sy, dx, dy, base_dir=DAWN):
    """16x16タイルを32x32に拡大してdestに配置"""
    src = Image.open(os.path.join(base_dir, src_path)).convert("RGBA")
    tile = extract_tile(src, sx, sy)
    tile = tile.resize((TILE32, TILE32), Image.NEAREST)
    tile = remap_to_db16(tile)
    dest.paste(tile, (dx, dy))


def place_native_32(dest, src_path, sx, sy, dx, dy, base_dir=DAWN):
    """32x32領域をそのまま抽出してDB16変換（拡大なし）"""
    src = Image.open(os.path.join(base_dir, src_path)).convert("RGBA")
    tile = src.crop((sx, sy, sx + TILE32, sy + TILE32))
    tile = remap_to_db16(tile)
    dest.paste(tile, (dx, dy))


def place_tiled_32(dest, src_path, sx, sy, dx, dy, base_dir=DAWN):
    """16x16タイルを2×2並べて32x32タイルを構成"""
    src = Image.open(os.path.join(base_dir, src_path)).convert("RGBA")
    tile16 = extract_tile(src, sx, sy)
    tile32 = Image.new("RGBA", (TILE32, TILE32))
    for oy in (0, TILE):
        for ox in (0, TILE):
            tile32.paste(tile16, (ox, oy))
    tile32 = remap_to_db16(tile32)
    dest.paste(tile32, (dx, dy))


def place_row(dest, src_path, sy, dx, dy, count=8, allow_zero=True):
    """src_pathの1行分の16x16タイルをdestに配置"""
    src = Image.open(os.path.join(DAWN, src_path)).convert("RGBA")
    for i in range(min(count, src.width // TILE)):
        tile = extract_tile(src, i * TILE, sy)
        tile = remap_to_db16(tile, allow_zero=allow_zero)
        dest.paste(tile, (dx + i * TILE, dy))


def place_puny_frame(dest, puny, col, row, dx, dy):
    """Puny Characters 32x32フレームをDB16リマップしてdestに配置
    不透明ピクセルは色0(透明色)を避ける"""
    sx, sy = col * TILE32, row * TILE32
    tile = puny.crop((sx, sy, sx + TILE32, sy + TILE32))
    tile = remap_to_db16(tile, allow_zero=False)
    dest.paste(tile, (dx, dy))


def main():
    os.makedirs(OUT, exist_ok=True)

    # =============================================================
    # Bank 0 (IMG_MAP): マップタイル(32x32) + プレイヤーextras(32x32) + モンスター(16x16)
    # =============================================================
    bank0 = Image.new("RGB", (256, 256), DB16[0])

    # --- マップタイル (16x16 → 2倍拡大 → 32x32) ---
    # Puny Dungeon: 16x16タイル、サンプルマップから座標を特定
    # 壁: cols 0-3, rows 0-3 / 床: cols 4-7, rows 0-3
    PD = "punyworld-dungeon-tileset.png"
    # Floor: (4,0)
    place_tile_32(bank0, PD, 4*TILE, 0*TILE, 0, 0, base_dir=PUNY_DUNGEON)
    # Stairs
    place_tile_32(bank0, "UniversalFantasyRL.png", 0, 16, 32, 0, base_dir=OUT)
    # Wall autotile: 16x16を2倍拡大して32x32に
    place_tile_32(bank0, PD, 1*TILE, 0*TILE,  64, 0,  base_dir=PUNY_DUNGEON)  # WallTL: (1,0)
    place_tile_32(bank0, PD, 2*TILE, 3*TILE,  96, 0,  base_dir=PUNY_DUNGEON)  # WallT:  (2,3)
    place_tile_32(bank0, PD, 3*TILE, 0*TILE, 128, 0,  base_dir=PUNY_DUNGEON)  # WallTR: (3,0)
    place_tile_32(bank0, PD, 0*TILE, 1*TILE, 160, 0,  base_dir=PUNY_DUNGEON)  # WallL:  (0,1)
    place_tile_32(bank0, PD, 0*TILE, 0*TILE, 192, 0,  base_dir=PUNY_DUNGEON)  # WallC:  (0,0)
    place_tile_32(bank0, PD, 1*TILE, 2*TILE, 224, 0,  base_dir=PUNY_DUNGEON)  # WallBL: (1,2)
    place_tile_32(bank0, PD, 3*TILE, 2*TILE,   0, 176, base_dir=PUNY_DUNGEON) # WallBR: (3,2)
    print("  Map tiles: Floor+Stairs+7 wall autotile (16x16→2x, Puny Dungeon)")

    # --- プレイヤー Hurt/Death (Puny Characters 32x32) ---
    puny_path = os.path.join(OUT, "puny/Puny-Characters/Human-Soldier-Red.png")
    if os.path.exists(puny_path):
        puny = Image.open(puny_path).convert("RGBA")

        # Hurt (cols 20-21) → Bank0 y=32,64
        # Death (cols 22-23) → Bank0 y=96,128
        EXTRAS = [
            ("hurt",  [20, 21], 32),
            ("death", [22, 23], 96),
        ]
        for anim_name, cols, y_base in EXTRAS:
            for frame_idx, col in enumerate(cols):
                for direction in range(8):
                    place_puny_frame(bank0, puny, col, direction,
                                     direction * TILE32, y_base + frame_idx * TILE32)
            print(f"  Player {anim_name}: {len(cols)}f x 8dirs → Bank0 y={y_base}")

    # --- モンスター (DawnLike 16x16) at y=160 ---
    MONSTER_TILES = [
        ("Slime",    "Characters/Slime0.png",     "Characters/Slime1.png",     0, 1,   0, 160),
        ("Bat",      "Characters/Avian0.png",     "Characters/Avian1.png",     0, 1,  32, 160),
        ("Skeleton", "Characters/Undead0.png",    "Characters/Undead1.png",    0, 2,  64, 160),
        ("Orc",      "Characters/Humanoid0.png",  "Characters/Humanoid1.png",  0, 6,  96, 160),
        ("Golem",    "Characters/Elemental0.png", "Characters/Elemental1.png", 0, 8, 128, 160),
        ("Dragon",   "Characters/Reptile0.png",   "Characters/Reptile1.png",   0,11, 160, 160),
    ]
    for name, src0, src1, sc, sr, dx, dy in MONSTER_TILES:
        sx, sy = sc * TILE, sr * TILE
        place_tile_16(bank0, src0, sx, sy, dx, dy, allow_zero=False)
        place_tile_16(bank0, src1, sx, sy, dx + TILE, dy, allow_zero=False)
        print(f"  {name}: F0=({dx},{dy}) F1=({dx+TILE},{dy})")

    bank0.save(os.path.join(OUT, "tileset_map.png"))
    print("tileset_map.png saved")

    # =============================================================
    # Bank 1 (IMG_CHARS): プレイヤー core アニメーション (32x32)
    # 8cols × 8rows = 64 tiles (256x256)
    # Row 0-1: Idle (2f), Row 2-4: Walk (3f), Row 5-7: Attack F0-F2 (3f)
    # =============================================================
    bank1 = Image.new("RGB", (256, 256), DB16[0])

    if os.path.exists(puny_path):
        # Puny Characters 列レイアウト:
        # Idle(0-1), Walk(2-4), Attack(5-8), Bow(9-12),
        # Stave(13-16), Throw(17-19), Hurt(20-21), Death(22-23)
        CORE_ANIMS = [
            ("idle",   0, 2, 0),     # cols 0-1 → y=0,32
            ("walk",   2, 3, 64),    # cols 2-4 → y=64,96,128
            ("attack", 5, 3, 160),   # cols 5-7 → y=160,192,224 (3 of 4 frames)
        ]
        for anim_name, start_col, num_frames, y_base in CORE_ANIMS:
            for frame in range(num_frames):
                for direction in range(8):
                    place_puny_frame(bank1, puny, start_col + frame, direction,
                                     direction * TILE32, y_base + frame * TILE32)
            print(f"  Player {anim_name}: {num_frames}f x 8dirs → Bank1 y={y_base}")
        print("Player core animations extracted from Puny Characters")
    else:
        print(f"WARNING: {puny_path} not found, skipping player sprites")

    bank1.save(os.path.join(OUT, "tileset_chars.png"))
    print("tileset_chars.png saved")

    # =============================================================
    # Bank 2 (IMG_ITEMS): アイテム (16x16, 変更なし)
    # =============================================================
    bank2 = Image.new("RGB", (256, 256), DB16[0])
    for row in range(5):
        place_row(bank2, "Items/ShortWep.png", row * TILE, 0, row * TILE, allow_zero=False)
    for row in range(2):
        place_row(bank2, "Items/MedWep.png", row * TILE, 0, 80 + row * TILE, allow_zero=False)
    place_row(bank2, "Items/Shield.png", 0, 0, 112, allow_zero=False)
    for row in range(5):
        place_row(bank2, "Items/Potion.png", row * TILE, 0, 128 + row * TILE, allow_zero=False)
    for row in range(5):
        place_row(bank2, "Items/Scroll.png", row * TILE, 128, 128 + row * TILE, allow_zero=False)
    place_row(bank2, "Items/Food.png", 0, 0, 224, allow_zero=False)
    bank2.save(os.path.join(OUT, "tileset_items.png"))
    print("tileset_items.png saved")

    print("Done! Check assets/ for output files.")


if __name__ == "__main__":
    main()
