# 不思議のダンジョン ～ローグライク冒険～

Pyxel製の不思議のダンジョン風ローグライクゲーム。

## 遊び方

- **矢印キー**: 8方向移動
- **Z**: 攻撃
- **X**: 持ち物
- **C**: 階段を降りる
- **Space**: 待機

全10フロアのランダムダンジョンを踏破してクリアを目指します。

## 実行方法

### ローカル実行

```bash
pip install pyxel pillow
python3 build_assets.py
python3 generate_sprite_data.py
python3 main.py
```

### Wasm (ブラウザ) ビルド

```bash
pyxel package . main.py
pyxel app2html roguelike.pyxapp
# roguelike.html をブラウザで開く
```

## 使用アセット

- [Puny Characters](https://shade-games.itch.io/puny-characters) by Shade (CC0)
- [Puny Dungeon](https://shade-games.itch.io/puny-dungeon) by Shade (CC0)
- [DawnLike](https://opengameart.org/content/dawnlike-16x16-universal-rogue-like-tileset-v181) by DragonDePlatino (CC-BY 4.0)
- [美咲ゴシック](https://littlelimit.net/misaki.htm) by 門真なむ
