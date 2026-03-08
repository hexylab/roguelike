#!/usr/bin/env python3
"""タイルセットPNGからpyxel.images[n].set()用のPythonデータを生成する"""
from PIL import Image
import os

DB16 = [
    (20, 12, 28), (68, 36, 52), (48, 52, 109), (78, 74, 78),
    (133, 76, 48), (52, 101, 36), (208, 70, 72), (117, 113, 97),
    (89, 125, 206), (210, 125, 44), (133, 149, 161), (109, 170, 44),
    (210, 170, 153), (109, 194, 202), (218, 212, 94), (222, 238, 214),
]


def nearest_db16(r, g, b, a=255):
    if a < 128:
        return 0
    best, best_dist = 0, float('inf')
    for i, (pr, pg, pb) in enumerate(DB16):
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_dist:
            best_dist = d
            best = i
    return best


def png_to_set_data(path):
    """PNG画像をpyxel.images[n].set()用のデータに変換"""
    img = Image.open(path).convert("RGBA")
    rows = []
    for y in range(img.height):
        row = ""
        for x in range(img.width):
            p = img.getpixel((x, y))
            idx = nearest_db16(p[0], p[1], p[2], p[3])
            row += format(idx, 'x')
        rows.append(row)
    return rows


def main():
    assets = "assets"
    files = {
        "MAP": os.path.join(assets, "tileset_map.png"),
        "CHARS": os.path.join(assets, "tileset_chars.png"),
        "ITEMS": os.path.join(assets, "tileset_items.png"),
    }

    with open("sprite_data.py", "w") as f:
        f.write('"""自動生成されたスプライトデータ (generate_sprite_data.py)"""\n\n')
        f.write("# 各バンクの画像データ: list of row strings\n")
        f.write("# 各文字は16色パレットのインデックス(0-f)\n\n")

        for name, path in files.items():
            print(f"Processing {path}...")
            data = png_to_set_data(path)

            # 空行（全て色0）を末尾から削除して圧縮
            while data and all(c == '0' for c in data[-1]):
                data.pop()

            f.write(f"BANK_{name} = [\n")
            for row in data:
                # 末尾の0を省略して圧縮はしない（set()は行全体が必要）
                f.write(f'    "{row}",\n')
            f.write("]\n\n")

        # ローダー関数
        f.write("""
def load_all():
    \"\"\"全スプライトデータをpyxel image banksに読み込む\"\"\"
    import pyxel
    for bank_idx, data in enumerate([BANK_MAP, BANK_CHARS, BANK_ITEMS]):
        if data:
            pyxel.images[bank_idx].set(0, 0, data)
""")

    size = os.path.getsize("sprite_data.py")
    print(f"sprite_data.py generated ({size} bytes)")


if __name__ == "__main__":
    main()
