"""描画処理（日本語フォント対応）"""
import math
import pyxel
from constants import (
    TILE_SIZE, SPRITE_SIZE_SM, MAP_VIEW_W, MAP_VIEW_H, PANEL_X, PANEL_W,
    SCREEN_W, SCREEN_H, IMG_MAP, IMG_CHARS, IMG_ITEMS,
    TILE_FLOOR, TILE_WALL, TILE_STAIRS, TILE_NONE,
    SPR_FLOOR, SPR_WALL, SPR_STAIRS,
    SPR_WALL_TL, SPR_WALL_T, SPR_WALL_TR,
    SPR_WALL_L, SPR_WALL_C, SPR_WALL_R,
    SPR_WALL_BL, SPR_WALL_B, SPR_WALL_BR,
    SPR_PLAYER, DIR_TO_IDX, PLAYER_ANIMS,
    COL_BLACK, COL_DARK_RED, COL_DARK_BLUE, COL_DARK_GRAY, COL_WHITE,
    COL_RED, COL_GREEN, COL_YELLOW, COL_CYAN, COL_BEIGE,
    COL_GRAY, COL_ORANGE, COL_LIGHT_GRAY, COL_BROWN,
    ANIM_FRAME1, ANIM_ATTACK_FRAMES, ANIM_WALK_FRAMES, FONT_PATH,
    HIT_FLASH_FRAMES, KNOCKBACK_PX, ATTACK_LUNGE_PX, POPUP_FRAMES,
)

_font = None

TILE_SPR = {
    TILE_FLOOR: SPR_FLOOR,
    TILE_STAIRS: SPR_STAIRS,
}


def _get_wall_spr(tiles, mx, my):
    """壁タイルのオートタイル選択: 隣接する床の方向に基づいてスプライトを返す"""
    h = len(tiles)
    w = len(tiles[0]) if h > 0 else 0

    def is_open(x, y):
        if 0 <= y < h and 0 <= x < w:
            return tiles[y][x] in (TILE_FLOOR, TILE_STAIRS)
        return False

    n = is_open(mx, my - 1)
    s = is_open(mx, my + 1)
    e = is_open(mx + 1, my)
    west = is_open(mx - 1, my)

    # 隣接2方向（角）
    if s and e:
        return SPR_WALL_TL
    if s and west:
        return SPR_WALL_TR
    if n and e:
        return SPR_WALL_BL
    if n and west:
        return SPR_WALL_BR

    # 隣接1方向（辺）
    if s:
        return SPR_WALL_T
    if n:
        return SPR_WALL_B
    if e:
        return SPR_WALL_L
    if west:
        return SPR_WALL_R

    # 斜め方向のみ（外角）
    if is_open(mx + 1, my + 1):
        return SPR_WALL_TL
    if is_open(mx - 1, my + 1):
        return SPR_WALL_TR
    if is_open(mx + 1, my - 1):
        return SPR_WALL_BL
    if is_open(mx - 1, my - 1):
        return SPR_WALL_BR

    # 完全に囲まれた壁
    return SPR_WALL_C

LINE_H = 10  # 行の高さ（8pxフォント + 2px間隔）


def init_font():
    global _font
    _font = pyxel.Font(FONT_PATH)


def _text(x, y, s, col):
    pyxel.text(x, y, s, col, _font)


def _char_width(c):
    return 8 if ord(c) > 0x7F else 4


def _text_width(s):
    return sum(_char_width(c) for c in s)


def _text_centered(y, s, col):
    x = (SCREEN_W - _text_width(s)) // 2
    _text(x, y, s, col)


def _wrap_text(text, max_width):
    """テキストをピクセル幅に基づいて折り返す"""
    lines = []
    line = ""
    w = 0
    for c in text:
        cw = _char_width(c)
        if w + cw > max_width:
            lines.append(line)
            line = c
            w = cw
        else:
            line += c
            w += cw
    if line:
        lines.append(line)
    return lines


def camera_offset(player_x, player_y, dw, dh):
    """カメラオフセットを計算（プレイヤー中心）"""
    cam_x = player_x - MAP_VIEW_W // 2
    cam_y = player_y - MAP_VIEW_H // 2
    cam_x = max(0, min(cam_x, dw - MAP_VIEW_W))
    cam_y = max(0, min(cam_y, dh - MAP_VIEW_H))
    return cam_x, cam_y


def draw_map(tiles, visible, explored, cam_x, cam_y):
    """マップを描画"""
    for vy in range(MAP_VIEW_H):
        for vx in range(MAP_VIEW_W):
            mx = cam_x + vx
            my = cam_y + vy
            sx = vx * TILE_SIZE
            sy = vy * TILE_SIZE

            if mx < 0 or my < 0 or my >= len(tiles) or mx >= len(tiles[0]):
                pyxel.rect(sx, sy, TILE_SIZE, TILE_SIZE, COL_BLACK)
                continue

            tile = tiles[my][mx]
            is_visible = (mx, my) in visible
            is_explored = (mx, my) in explored

            if is_visible or is_explored:
                if tile == TILE_WALL:
                    spr = _get_wall_spr(tiles, mx, my)
                else:
                    spr = TILE_SPR.get(tile)
                if spr:
                    pyxel.blt(sx, sy, IMG_MAP, spr[0], spr[1],
                              TILE_SIZE, TILE_SIZE, COL_BLACK)
                    if is_explored and not is_visible:
                        for dy in range(0, TILE_SIZE, 2):
                            for dx in range(0, TILE_SIZE, 2):
                                pyxel.pset(sx + dx, sy + dy, COL_BLACK)
                else:
                    pyxel.rect(sx, sy, TILE_SIZE, TILE_SIZE, COL_BLACK)
            else:
                pyxel.rect(sx, sy, TILE_SIZE, TILE_SIZE, COL_BLACK)


def _get_player_sprite(entity):
    """プレイヤーの8方向アニメーションスプライトを取得 → (spr_x, spr_y, img_bank)"""
    dir_key = (entity.facing_dx, entity.facing_dy)
    dir_idx = DIR_TO_IDX.get(dir_key, 0)

    # 死亡
    if getattr(entity, 'hp', 1) <= 0:
        y_base, nf, x_base, bank = PLAYER_ANIMS["death"]
        return (x_base + dir_idx * TILE_SIZE, y_base + TILE_SIZE, bank)  # 最終フレーム

    # 被弾 → hurtスプライト使用
    if entity.hit_timer > 0:
        y_base, nf, x_base, bank = PLAYER_ANIMS["hurt"]
        progress = 1.0 - entity.hit_timer / HIT_FLASH_FRAMES
        frame = min(nf - 1, int(progress * nf))
        return (x_base + dir_idx * TILE_SIZE, y_base + frame * TILE_SIZE, bank)

    # アクションアニメーション
    if entity.anim_timer > 0 and entity.anim_type in PLAYER_ANIMS:
        anim_key = entity.anim_type
        y_base, nf, x_base, bank = PLAYER_ANIMS[anim_key]
        if anim_key == "walk":
            total = ANIM_WALK_FRAMES
        else:
            total = ANIM_ATTACK_FRAMES
        elapsed = total - entity.anim_timer
        frame = min(nf - 1, elapsed * nf // total)
        return (x_base + dir_idx * TILE_SIZE, y_base + frame * TILE_SIZE, bank)

    # アイドル
    y_base, nf, x_base, bank = PLAYER_ANIMS["idle"]
    frame = (pyxel.frame_count // 20) % nf
    return (x_base + dir_idx * TILE_SIZE, y_base + frame * TILE_SIZE, bank)


def draw_entity(entity, cam_x, cam_y, visible):
    """エンティティを描画（アニメーション対応）"""
    if (entity.x, entity.y) not in visible:
        return
    sx = (entity.x - cam_x) * TILE_SIZE
    sy = (entity.y - cam_y) * TILE_SIZE
    if not (0 <= sx < MAP_VIEW_W * TILE_SIZE and 0 <= sy < MAP_VIEW_H * TILE_SIZE):
        return

    is_player = (entity.spr == SPR_PLAYER)

    # スプライト選択
    if is_player:
        spr = _get_player_sprite(entity)  # (x, y, bank)
        img_bank = spr[2]
        spr_size = TILE_SIZE  # 32x32
    else:
        spr = entity.spr
        img_bank = entity.img_bank
        f1 = ANIM_FRAME1.get(entity.spr)
        if f1 and (pyxel.frame_count // 20) % 2 == 1:
            spr = f1
        spr_size = SPRITE_SIZE_SM  # 16x16

    # 攻撃アニメーション: ターゲット方向にオフセット
    if entity.anim_timer > 0 and entity.anim_type in ("attack", "bow", "stave", "throw"):
        progress = entity.anim_timer / ANIM_ATTACK_FRAMES
        offset = int(ATTACK_LUNGE_PX * progress)
        sx += entity.attack_dx * offset
        sy += entity.attack_dy * offset

    # ノックバック: 被弾時にヒット方向へずれる
    if entity.hit_timer > 0:
        kb_progress = entity.hit_timer / HIT_FLASH_FRAMES
        kb_offset = int(KNOCKBACK_PX * kb_progress)
        sx += entity.hit_dx * kb_offset
        sy += entity.hit_dy * kb_offset

    # ヒットフラッシュ: パレットを白に一瞬変更（プレイヤーはhurtスプライトも使用）
    flash = entity.hit_timer > 0 and entity.hit_timer % 2 == 0
    if flash:
        for i in range(1, 16):
            pyxel.pal(i, COL_WHITE)

    if is_player:
        # プレイヤー: 32x32をそのまま描画
        pyxel.blt(sx, sy, img_bank, spr[0], spr[1],
                  TILE_SIZE, TILE_SIZE, COL_BLACK)
    else:
        # モンスター/アイテム: 16x16を32x32セルの中央に描画
        center_offset = (TILE_SIZE - SPRITE_SIZE_SM) // 2  # 8px
        draw_x = sx + center_offset
        draw_y = sy + center_offset
        w = -SPRITE_SIZE_SM if entity.facing_left else SPRITE_SIZE_SM
        pyxel.blt(draw_x, draw_y, img_bank, spr[0], spr[1],
                  w, SPRITE_SIZE_SM, COL_BLACK)

    if flash:
        pyxel.pal()



def draw_attack_effect(entity, cam_x, cam_y):
    """斬撃エフェクト（三日月形のスラッシュ）"""
    if entity.anim_timer <= 0 or entity.anim_type != "attack":
        return
    tx = entity.x + entity.attack_dx
    ty = entity.y + entity.attack_dy
    sx = (tx - cam_x) * TILE_SIZE
    sy = (ty - cam_y) * TILE_SIZE
    if not (0 <= sx < MAP_VIEW_W * TILE_SIZE and 0 <= sy < MAP_VIEW_H * TILE_SIZE):
        return

    cx = sx + TILE_SIZE // 2
    cy = sy + TILE_SIZE // 2
    t = entity.anim_timer
    progress = (ANIM_ATTACK_FRAMES - t) / ANIM_ATTACK_FRAMES  # 0→1

    is_crit = getattr(entity, 'anim_critical', False)
    base = math.atan2(-entity.attack_dy, entity.attack_dx)

    # 弧のパラメータ（会心は大きく、32pxタイル用にスケール）
    r_max = 18 if is_crit else 14
    arc_half = math.pi * 0.42  # 各方向75度 = 合計150度の弧
    max_thick = 8 if is_crit else 6

    # スイープアニメーション: 前半で弧が伸び、後半で消える
    if progress < 0.5:
        vis_start = 0.0
        vis_end = progress * 2
    else:
        vis_start = (progress - 0.5) * 2
        vis_end = 1.0

    # 三日月形の弧を描画
    steps = 24
    for i in range(steps + 1):
        frac = i / steps
        if frac < vis_start or frac > vis_end:
            continue

        angle = base + math.pi / 2 - arc_half + arc_half * 2 * frac

        # 三日月の太さ: 中央が太く端が細い（sine curve）
        thickness = max(1, int(math.sin(frac * math.pi) * max_thick))

        # 先端に近いほど白く、遠いほど暗い
        dist_to_tip = abs(frac - vis_end)
        if dist_to_tip < 0.12:
            col_edge, col_fill = COL_WHITE, COL_WHITE
        elif dist_to_tip < 0.3:
            col_edge, col_fill = COL_WHITE, COL_YELLOW
        else:
            col_edge = COL_YELLOW
            col_fill = COL_ORANGE if is_crit else COL_YELLOW

        for dr in range(thickness):
            r = r_max - dr
            px = cx + int(r * math.cos(angle))
            py = cy + int(r * math.sin(angle))
            pyxel.pset(px, py, col_edge if dr == 0 else col_fill)

    # 先端にスパーク
    if vis_end > 0.05:
        tip_angle = base + math.pi / 2 - arc_half + arc_half * 2 * vis_end
        tip_x = cx + int((r_max + 3) * math.cos(tip_angle))
        tip_y = cy + int((r_max + 3) * math.sin(tip_angle))
        pyxel.pset(tip_x, tip_y, COL_WHITE)

    # 会心の一撃: 初期フレームでインパクトリング
    if is_crit and t >= ANIM_ATTACK_FRAMES - 2:
        pyxel.circb(cx, cy, r_max + 3, COL_WHITE)


def draw_damage_popups(popups, cam_x, cam_y):
    """ダメージ数値のポップアップを描画"""
    for popup in popups:
        tx, ty, text, col, timer = popup
        sx = (tx - cam_x) * TILE_SIZE + TILE_SIZE // 2
        sy = (ty - cam_y) * TILE_SIZE
        elapsed = POPUP_FRAMES - timer
        sy -= elapsed  # 上に浮かぶ
        if timer < 5 and timer % 2 == 0:
            continue  # 消える前に点滅
        tw = _text_width(text)
        _text(sx - tw // 2, int(sy), text, col)


def draw_items_on_map(items, cam_x, cam_y, visible):
    """地面のアイテムを描画"""
    for item in items:
        draw_entity(item, cam_x, cam_y, visible)


def draw_panel(player, floor_num, messages):
    """右側ステータスパネル"""
    x = PANEL_X + 4
    max_w = PANEL_W - 8
    # 背景
    pyxel.rect(PANEL_X, 0, PANEL_W, SCREEN_H, COL_BLACK)
    pyxel.line(PANEL_X, 0, PANEL_X, SCREEN_H, COL_DARK_GRAY)

    y = 4
    _text(x, y, f"地下{floor_num}階", COL_YELLOW)
    y += LINE_H
    _text(x, y, f"Lv.{player.level}", COL_WHITE)
    y += LINE_H + 2

    # HPバー
    _text(x, y, "HP", COL_WHITE)
    bar_x = x + 16
    bar_w = max_w - 16
    pyxel.rect(bar_x, y + 1, bar_w, 6, COL_DARK_RED)
    hp_w = int(bar_w * player.hp / max(1, player.max_hp))
    hp_col = COL_RED if player.hp > player.max_hp // 4 else COL_ORANGE
    pyxel.rect(bar_x, y + 1, hp_w, 6, hp_col)
    y += 9
    _text(x + 4, y, f"{player.hp}/{player.max_hp}", COL_WHITE)
    y += LINE_H + 2

    # EXPバー
    _text(x, y, "EXP", COL_WHITE)
    bar_x2 = x + 20
    bar_w2 = max_w - 20
    pyxel.rect(bar_x2, y + 1, bar_w2, 6, COL_DARK_BLUE)
    exp_w = int(bar_w2 * player.exp / max(1, player.exp_to_next()))
    pyxel.rect(bar_x2, y + 1, exp_w, 6, COL_CYAN)
    y += 9
    _text(x + 4, y, f"{player.exp}/{player.exp_to_next()}", COL_WHITE)
    y += LINE_H + 4

    _text(x, y, f"攻撃:{player.atk}", COL_ORANGE)
    y += LINE_H
    _text(x, y, f"防御:{player.defense}", COL_CYAN)
    y += LINE_H + 4

    # 装備
    _text(x, y, "[装備]", COL_YELLOW)
    y += LINE_H
    wep_name = player.weapon.display_name() if player.weapon else "---"
    _text(x, y, f"武:{wep_name}", COL_BEIGE)
    y += LINE_H
    shd_name = player.shield.display_name() if player.shield else "---"
    _text(x, y, f"盾:{shd_name}", COL_BEIGE)
    y += LINE_H + 4

    _text(x, y, f"所持品:{len(player.inventory)}/20", COL_LIGHT_GRAY)
    y += LINE_H + 4

    # メッセージログ
    _text(x, y, "[ログ]", COL_YELLOW)
    y += LINE_H
    for msg_col, msg in messages[-15:]:
        wrapped = _wrap_text(msg, max_w)
        for line in wrapped:
            _text(x, y, line, msg_col)
            y += 9
            if y > SCREEN_H - 10:
                return


def draw_inventory(player, cursor, id_table):
    """インベントリ画面"""
    # マップ領域にオーバーレイ
    ox, oy = 24, 8
    ow, oh = 292, 304
    pyxel.rect(ox, oy, ow, oh, COL_BLACK)
    pyxel.rectb(ox, oy, ow, oh, COL_LIGHT_GRAY)
    tx = ox + 8
    ty = oy + 6
    _text(tx, ty, "持ち物 (Z:使う/装備 X:閉じる)", COL_YELLOW)
    ty += LINE_H
    _text(tx, ty, "C:投げる  V:置く", COL_YELLOW)
    ty += LINE_H + 4

    if not player.inventory:
        _text(tx, ty, "何も持っていない", COL_GRAY)
        return

    for i, item in enumerate(player.inventory):
        y = ty + i * LINE_H
        if y > oy + oh - LINE_H:
            break
        col = COL_WHITE if i == cursor else COL_GRAY
        marker = ">" if i == cursor else " "
        equipped = ""
        if item == player.weapon:
            equipped = "[装]"
        elif item == player.shield:
            equipped = "[装]"
        _text(tx, y, f"{marker}{item.display_name()}{equipped}", col)


def draw_title():
    """タイトル画面"""
    pyxel.cls(COL_BLACK)
    _text_centered(80, "不思議のダンジョン", COL_YELLOW)
    _text_centered(100, "～ローグライク冒険～", COL_BEIGE)
    # 点滅表示
    if (pyxel.frame_count // 30) % 2 == 0:
        _text_centered(160, "Zキーでスタート", COL_WHITE)
    _text_centered(230, "矢印キー: 8方向移動", COL_GRAY)
    _text_centered(244, "Z:攻撃  X:持ち物", COL_GRAY)
    _text_centered(258, "C:階段  Space:待機", COL_GRAY)


def draw_gameover():
    """ゲームオーバー画面"""
    bx = (SCREEN_W - 240) // 2
    by = (SCREEN_H - 80) // 2
    pyxel.rect(bx, by, 240, 80, COL_BLACK)
    pyxel.rectb(bx, by, 240, 80, COL_RED)
    _text_centered(by + 20, "ゲームオーバー", COL_RED)
    _text_centered(by + 48, "Zキーでリスタート", COL_WHITE)


def draw_victory():
    """クリア画面"""
    bx = (SCREEN_W - 240) // 2
    by = (SCREEN_H - 80) // 2
    pyxel.rect(bx, by, 240, 80, COL_BLACK)
    pyxel.rectb(bx, by, 240, 80, COL_YELLOW)
    _text_centered(by + 20, "ダンジョンクリア!", COL_YELLOW)
    _text_centered(by + 48, "Zキーでリスタート", COL_WHITE)
