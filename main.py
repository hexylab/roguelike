"""不思議のダンジョン風ローグライクゲーム"""
import pyxel
import random
from constants import (
    SCREEN_W, SCREEN_H, TILE_SIZE, DISPLAY_SCALE, DB16,
    DUNGEON_W, DUNGEON_H, MAX_FLOOR, FOV_RADIUS,
    TILE_FLOOR, TILE_WALL, TILE_STAIRS,
    STATE_TITLE, STATE_PLAY, STATE_INVENTORY, STATE_GAMEOVER, STATE_VICTORY,
    COL_BLACK, COL_WHITE, COL_RED, COL_GREEN, COL_YELLOW, COL_CYAN,
    COL_ORANGE, COL_BEIGE, COL_GRAY,
    POTION_EFFECTS, SCROLL_EFFECTS,
    SHAKE_FRAMES, SHAKE_INTENSITY, POPUP_FRAMES,
)
from dungeon import generate_dungeon
from fov import compute_fov
from entities import (
    Player, Monster, Item, IdentificationTable,
    spawn_monsters, spawn_items,
)
from renderer import (
    init_font, camera_offset, draw_map, draw_entity, draw_attack_effect,
    draw_damage_popups, draw_items_on_map, draw_panel, draw_inventory,
    draw_title, draw_gameover, draw_victory,
)

class Game:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Dungeon of Mystery", fps=30,
                   display_scale=DISPLAY_SCALE)

        # パレットをDawnBringer 16に設定
        for i, col in enumerate(DB16):
            pyxel.colors[i] = col

        # アセット読み込み
        self._load_assets()
        # 日本語フォント読み込み
        init_font()

        self.state = STATE_TITLE
        self.error_msg = ""
        self.messages = []
        self.inv_cursor = 0
        self.id_table = None
        pyxel.run(self.update, self.draw)

    def _load_assets(self):
        """スプライトデータをimage banksに読み込む（PNG不要・Wasm対応）"""
        import sprite_data
        sprite_data.load_all()

    def _new_game(self):
        """ゲームを初期化"""
        self.floor_num = 1
        self.turn_count = 0
        self.player = Player(0, 0)
        self.id_table = IdentificationTable()
        self.shake_timer = 0
        self.damage_popups = []
        self.messages = [(COL_WHITE, "不思議のダンジョンへ")]
        self.messages.append((COL_WHITE, "ようこそ!"))
        self._generate_floor()
        self.state = STATE_PLAY

    def _generate_floor(self):
        """現在フロアのダンジョンを生成"""
        self.tiles, self.rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, self.floor_num)
        # プレイヤーを最初の部屋に配置
        start_room = self.rooms[0]
        self.player.x, self.player.y = start_room.center
        # モンスター/アイテム生成
        self.monsters = spawn_monsters(self.rooms, self.floor_num, player_room_idx=0)
        self.items = spawn_items(self.rooms, self.floor_num, self.id_table, player_room_idx=0)
        # 視界
        self.explored = set()
        self._update_fov()

    def _update_fov(self):
        """視界を再計算"""
        self.visible = compute_fov(self.tiles, self.player.x, self.player.y, FOV_RADIUS)
        self.explored |= self.visible

    def _msg(self, text, col=COL_WHITE):
        self.messages.append((col, text))
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]

    # === 更新 ===

    def update(self):
        if self.state == STATE_TITLE:
            self._update_title()
        elif self.state == STATE_PLAY:
            self._update_play()
        elif self.state == STATE_INVENTORY:
            self._update_inventory()
        elif self.state in (STATE_GAMEOVER, STATE_VICTORY):
            if pyxel.btnp(pyxel.KEY_Z):
                self.state = STATE_TITLE

    def _update_title(self):
        if pyxel.btnp(pyxel.KEY_Z):
            try:
                self._new_game()
            except Exception as e:
                import traceback
                self.error_msg = traceback.format_exc()
                self.state = STATE_PLAY  # エラー表示用

    def _update_play(self):
        player_acted = False

        # 8方向移動
        dx, dy = 0, 0
        if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.KEY_KP_8):
            dy = -1
        elif pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.KEY_KP_2):
            dy = 1
        elif pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_KP_4):
            dx = -1
        elif pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_KP_6):
            dx = 1
        elif pyxel.btnp(pyxel.KEY_KP_7):
            dx, dy = -1, -1
        elif pyxel.btnp(pyxel.KEY_KP_9):
            dx, dy = 1, -1
        elif pyxel.btnp(pyxel.KEY_KP_1):
            dx, dy = -1, 1
        elif pyxel.btnp(pyxel.KEY_KP_3):
            dx, dy = 1, 1
        elif pyxel.btnp(pyxel.KEY_Q):
            dx, dy = -1, -1
        elif pyxel.btnp(pyxel.KEY_E):
            dx, dy = 1, -1
        elif pyxel.btnp(pyxel.KEY_A):
            dx, dy = -1, 1
        elif pyxel.btnp(pyxel.KEY_D):
            dx, dy = 1, 1

        if dx != 0 or dy != 0:
            player_acted = self._player_move(dx, dy)

        # Z: 攻撃（向いている方向に）
        if pyxel.btnp(pyxel.KEY_Z):
            player_acted = self._player_attack()

        # 足踏み（待機）
        if pyxel.btnp(pyxel.KEY_SPACE):
            player_acted = True

        # 階段を降りる
        if pyxel.btnp(pyxel.KEY_C) or pyxel.btnp(pyxel.KEY_PERIOD):
            if self.tiles[self.player.y][self.player.x] == TILE_STAIRS:
                player_acted = self._descend()

        # インベントリ
        if pyxel.btnp(pyxel.KEY_X):
            self.inv_cursor = 0
            self.state = STATE_INVENTORY
            return

        # ターン処理
        if player_acted:
            self.turn_count += 1
            self._enemy_turn()
            if self.turn_count % 5 == 0 and self.player.hp < self.player.max_hp:
                self.player.hp = min(self.player.hp + 1, self.player.max_hp)
            self._update_fov()
            if self.player.hp <= 0:
                self._msg("倒れてしまった...", COL_RED)
                self.state = STATE_GAMEOVER

    def _player_move(self, dx, dy):
        """プレイヤー移動（移動のみ、攻撃しない）"""
        nx = self.player.x + dx
        ny = self.player.y + dy

        # 向きの更新
        self.player.facing_dx = dx
        self.player.facing_dy = dy

        # マップ範囲チェック
        if ny < 0 or ny >= DUNGEON_H or nx < 0 or nx >= DUNGEON_W:
            return False

        # モンスターがいたら移動不可
        for m in self.monsters:
            if m.alive and m.x == nx and m.y == ny:
                return False

        # 壁チェック
        if self.tiles[ny][nx] == TILE_WALL:
            return False

        self.player.x = nx
        self.player.y = ny
        self.player.start_walk_anim()
        # 自動拾い
        self._auto_pickup()
        return True

    def _player_attack(self):
        """向いている方向に攻撃（素振り可能）"""
        dx = self.player.facing_dx
        dy = self.player.facing_dy
        nx = self.player.x + dx
        ny = self.player.y + dy

        # モンスターがいれば攻撃
        for m in self.monsters:
            if m.alive and m.x == nx and m.y == ny:
                is_crit = random.random() < 0.1
                self.player.start_attack_anim(dx, dy, critical=is_crit)
                self._attack_monster(m, is_crit)
                return True

        # 素振り
        self.player.start_attack_anim(dx, dy)
        self._msg("素振りをした", COL_GRAY)
        return True

    def _auto_pickup(self):
        """足元のアイテムを自動で拾う"""
        for item in list(self.items):
            if item.x == self.player.x and item.y == self.player.y:
                if self.player.can_pickup():
                    self.items.remove(item)
                    self.player.inventory.append(item)
                    self._msg(f"{item.display_name()}を拾った", COL_GREEN)
                else:
                    self._msg(f"持ち物がいっぱい!", COL_RED)
                break

    def _attack_monster(self, monster, is_crit=False):
        """プレイヤーがモンスターを攻撃"""
        dmg = max(1, self.player.atk - monster.defense // 2)
        if is_crit:
            dmg = int(dmg * 1.5)
        monster.hp -= dmg
        # ヒットエフェクト
        dx = monster.x - self.player.x
        dy = monster.y - self.player.y
        monster.start_hit(dx, dy)
        if is_crit:
            self.shake_timer = SHAKE_FRAMES
            self.damage_popups.append(
                [monster.x, monster.y, f"{dmg}!", COL_ORANGE, POPUP_FRAMES]
            )
            self._msg(f"会心の一撃! {monster.name}に{dmg}ダメージ!", COL_ORANGE)
        else:
            self.damage_popups.append(
                [monster.x, monster.y, str(dmg), COL_YELLOW, POPUP_FRAMES]
            )
            self._msg(f"{monster.name}に{dmg}ダメージ!", COL_YELLOW)
        if monster.hp <= 0:
            self._msg(f"{monster.name}を倒した!", COL_GREEN)
            if self.player.gain_exp(monster.exp_val):
                self._msg(f"レベルアップ! Lv.{self.player.level}", COL_CYAN)

    def _monster_attack(self, monster):
        """モンスターがプレイヤーを攻撃"""
        # 会心判定: 5階以降、深い階ほど確率上昇
        crit_chance = max(0, (self.floor_num - 4) * 0.03)
        is_crit = random.random() < crit_chance
        dmg = max(1, monster.atk - self.player.defense // 2)
        if is_crit:
            dmg = int(dmg * 1.5)
        self.player.hp -= dmg
        dx = self.player.x - monster.x
        dy = self.player.y - monster.y
        if dx != 0:
            monster.facing_dx = dx
        if dy != 0:
            monster.facing_dy = dy
        monster.start_attack_anim(dx, dy, critical=is_crit)
        # ヒットエフェクト
        self.player.start_hit(dx, dy)
        if is_crit:
            self.shake_timer = SHAKE_FRAMES
            self.damage_popups.append(
                [self.player.x, self.player.y, f"{dmg}!", COL_ORANGE, POPUP_FRAMES]
            )
            self._msg(f"{monster.name}の会心の一撃! {dmg}ダメージ!", COL_ORANGE)
        else:
            self.damage_popups.append(
                [self.player.x, self.player.y, str(dmg), COL_RED, POPUP_FRAMES]
            )
            self._msg(f"{monster.name}の攻撃! {dmg}ダメージ", COL_RED)

    def _enemy_turn(self):
        """全モンスターの行動"""
        for m in self.monsters:
            if not m.alive:
                continue
            # 混乱中はランダム移動
            if m.confused > 0:
                m.confused -= 1
                dx = random.randint(-1, 1)
                dy = random.randint(-1, 1)
                nx, ny = m.x + dx, m.y + dy
                if (0 <= nx < DUNGEON_W and 0 <= ny < DUNGEON_H
                        and self.tiles[ny][nx] != TILE_WALL):
                    if not self._monster_at(nx, ny):
                        if dx != 0:
                            m.facing_dx = dx
                        if dy != 0:
                            m.facing_dy = dy
                        m.x, m.y = nx, ny
                        m.start_walk_anim()
                continue

            # 視界内なら追跡
            if (m.x, m.y) not in self.visible:
                continue

            # プレイヤーに隣接なら攻撃
            dist_x = abs(m.x - self.player.x)
            dist_y = abs(m.y - self.player.y)
            if dist_x <= 1 and dist_y <= 1:
                self._monster_attack(m)
                continue

            # プレイヤーに向かって移動
            dx = 0 if m.x == self.player.x else (1 if self.player.x > m.x else -1)
            dy = 0 if m.y == self.player.y else (1 if self.player.y > m.y else -1)
            if dx != 0:
                m.facing_dx = dx
            if dy != 0:
                m.facing_dy = dy
            nx, ny = m.x + dx, m.y + dy
            if (0 <= nx < DUNGEON_W and 0 <= ny < DUNGEON_H
                    and self.tiles[ny][nx] != TILE_WALL
                    and not self._monster_at(nx, ny)
                    and not (nx == self.player.x and ny == self.player.y)):
                m.x, m.y = nx, ny
                m.start_walk_anim()

    def _monster_at(self, x, y):
        for m in self.monsters:
            if m.alive and m.x == x and m.y == y:
                return m
        return None

    def _pickup_item(self):
        """足元のアイテムを拾う"""
        for item in self.items:
            if item.x == self.player.x and item.y == self.player.y:
                if not self.player.can_pickup():
                    self._msg("持ち物がいっぱい!", COL_RED)
                    return False
                self.items.remove(item)
                self.player.inventory.append(item)
                self._msg(f"{item.display_name()}を拾った", COL_GREEN)
                return True
        return False

    def _descend(self):
        """階段を降りる"""
        if self.floor_num >= MAX_FLOOR:
            self._msg("ダンジョンクリア!!", COL_YELLOW)
            self.state = STATE_VICTORY
            return True
        self.floor_num += 1
        self._msg(f"地下{self.floor_num}階に降りた", COL_CYAN)
        self._generate_floor()
        return True

    # === インベントリ操作 ===

    def _update_inventory(self):
        inv = self.player.inventory
        if not inv:
            if pyxel.btnp(pyxel.KEY_X) or pyxel.btnp(pyxel.KEY_Z):
                self.state = STATE_PLAY
            return

        if pyxel.btnp(pyxel.KEY_UP):
            self.inv_cursor = max(0, self.inv_cursor - 1)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.inv_cursor = min(len(inv) - 1, self.inv_cursor + 1)

        if pyxel.btnp(pyxel.KEY_X):
            self.state = STATE_PLAY
            return

        if pyxel.btnp(pyxel.KEY_Z):
            item = inv[self.inv_cursor]
            self._use_item(item)
            self._clamp_cursor()
            return

        if pyxel.btnp(pyxel.KEY_V):
            item = inv[self.inv_cursor]
            self._drop_item(item)
            self._clamp_cursor()
            return

        if pyxel.btnp(pyxel.KEY_C):
            item = inv[self.inv_cursor]
            self._throw_item(item)
            self._clamp_cursor()
            return

    def _clamp_cursor(self):
        if self.inv_cursor >= len(self.player.inventory):
            self.inv_cursor = max(0, len(self.player.inventory) - 1)

    def _use_item(self, item):
        """アイテムを使用/装備"""
        if item.item_type == "weapon":
            if self.player.weapon == item:
                self.player.weapon = None
                self._msg(f"{item.display_name()}を外した", COL_BEIGE)
            else:
                self.player.weapon = item
                self._msg(f"{item.display_name()}を装備した", COL_YELLOW)
            self.state = STATE_PLAY
            self._enemy_turn()
            self._update_fov()

        elif item.item_type == "shield":
            if self.player.shield == item:
                self.player.shield = None
                self._msg(f"{item.display_name()}を外した", COL_BEIGE)
            else:
                self.player.shield = item
                self._msg(f"{item.display_name()}を装備した", COL_YELLOW)
            self.state = STATE_PLAY
            self._enemy_turn()
            self._update_fov()

        elif item.item_type == "potion":
            self._use_potion(item)
            self.player.inventory.remove(item)
            self.state = STATE_PLAY
            self._enemy_turn()
            self._update_fov()

        elif item.item_type == "scroll":
            dx, dy = self.player.facing_dx, self.player.facing_dy
            self.player.start_attack_anim(dx, dy, anim_type="stave")
            self._use_scroll(item)
            self.player.inventory.remove(item)
            self.state = STATE_PLAY
            self._enemy_turn()
            self._update_fov()

    def _identify_all(self, item_type, effect):
        """同じ効果のアイテムをすべて識別済みにする"""
        for inv_item in self.player.inventory:
            if inv_item.item_type == item_type and inv_item.effect == effect:
                inv_item.identified = True
        for floor_item in self.items:
            if floor_item.item_type == item_type and floor_item.effect == effect:
                floor_item.identified = True

    def _use_potion(self, item):
        """ポーション使用"""
        effect = item.effect
        for i, (name, eff) in enumerate(POTION_EFFECTS):
            if eff == effect:
                self.id_table.identify_potion(i)
                break
        item.identified = True
        self._identify_all("potion", effect)

        if effect == "heal":
            heal = 20
            self.player.hp = min(self.player.hp + heal, self.player.max_hp)
            self._msg(f"HPが{heal}回復した!", COL_GREEN)
        elif effect == "big_heal":
            heal = 50
            self.player.hp = min(self.player.hp + heal, self.player.max_hp)
            self._msg(f"HPが{heal}回復した!", COL_GREEN)
        elif effect == "str_up":
            self.player.base_atk += 2
            self._msg("攻撃力が上がった!", COL_ORANGE)
        elif effect == "def_up":
            self.player.base_def += 2
            self._msg("防御力が上がった!", COL_CYAN)
        elif effect == "poison":
            dmg = 10
            self.player.hp -= dmg
            self._msg(f"毒! {dmg}ダメージ!", COL_RED)

    def _use_scroll(self, item):
        """巻物使用"""
        effect = item.effect
        for i, (name, eff) in enumerate(SCROLL_EFFECTS):
            if eff == effect:
                self.id_table.identify_scroll(i)
                break
        item.identified = True
        self._identify_all("scroll", effect)

        if effect == "map_reveal":
            for y in range(len(self.tiles)):
                for x in range(len(self.tiles[0])):
                    if self.tiles[y][x] != TILE_WALL:
                        self.explored.add((x, y))
            self._msg("地図が明らかになった!", COL_CYAN)
        elif effect == "power_up":
            self.player.base_atk += 3
            self._msg("力が漲る! 攻撃+3", COL_ORANGE)
        elif effect == "confuse":
            count = 0
            for m in self.monsters:
                if m.alive and (m.x, m.y) in self.visible:
                    m.confused = 10
                    count += 1
            self._msg(f"敵{count}体を混乱させた!", COL_YELLOW)
        elif effect == "sleep_enemies":
            count = 0
            for m in self.monsters:
                if m.alive and (m.x, m.y) in self.visible:
                    m.confused = 5
                    count += 1
            self._msg(f"敵{count}体を眠らせた!", COL_CYAN)
        elif effect == "blast":
            dmg = 20
            count = 0
            for m in self.monsters:
                if m.alive:
                    dist = abs(m.x - self.player.x) + abs(m.y - self.player.y)
                    if dist <= 3:
                        m.hp -= dmg
                        count += 1
                        if m.hp <= 0:
                            self._msg(f"{m.name}を倒した!", COL_GREEN)
                            self.player.gain_exp(m.exp_val)
            self._msg(f"爆発! {count}体に{dmg}ダメージ!", COL_RED)

    def _drop_item(self, item):
        """アイテムを足元に置く"""
        if item == self.player.weapon:
            self.player.weapon = None
        elif item == self.player.shield:
            self.player.shield = None
        self.player.inventory.remove(item)
        item.x = self.player.x
        item.y = self.player.y
        self.items.append(item)
        self._msg(f"{item.display_name()}を置いた", COL_BEIGE)
        self.state = STATE_PLAY

    def _throw_item(self, item):
        """アイテムを投げる（前方に直線飛行）"""
        dx, dy = self.player.facing_dx, self.player.facing_dy
        self.player.start_attack_anim(dx, dy, anim_type="throw")
        if item == self.player.weapon:
            self.player.weapon = None
        elif item == self.player.shield:
            self.player.shield = None
        self.player.inventory.remove(item)

        # 最後に移動した方向に投げる（デフォルトは右）
        # 簡易的に最も近いモンスターに向かって投げる
        target = None
        min_dist = 999
        for m in self.monsters:
            if m.alive and (m.x, m.y) in self.visible:
                dist = abs(m.x - self.player.x) + abs(m.y - self.player.y)
                if dist < min_dist:
                    min_dist = dist
                    target = m

        if target:
            dmg = 10
            if item.item_type == "weapon":
                dmg = item.power + item.plus + 5
            target.hp -= dmg
            self._msg(f"{item.display_name()}を{target.name}に投げた! {dmg}ダメージ", COL_YELLOW)
            if target.hp <= 0:
                self._msg(f"{target.name}を倒した!", COL_GREEN)
                self.player.gain_exp(target.exp_val)
        else:
            self._msg(f"{item.display_name()}を投げた", COL_BEIGE)

        self.state = STATE_PLAY
        self._enemy_turn()
        self._update_fov()

    # === 描画 ===

    def draw(self):
        pyxel.cls(COL_BLACK)

        if self.state == STATE_TITLE:
            draw_title()
            return

        # エラー表示
        if self.error_msg:
            pyxel.cls(COL_BLACK)
            lines = self.error_msg.split("\n")
            for i, line in enumerate(lines[:30]):
                pyxel.text(4, 4 + i * 7, line[:78], COL_RED)
            return

        if self.state in (STATE_PLAY, STATE_INVENTORY, STATE_GAMEOVER, STATE_VICTORY):
            # アニメーションタイマー更新
            self.player.tick_anim()
            for m in self.monsters:
                if m.alive:
                    m.tick_anim()

            # マップ描画
            cam_x, cam_y = camera_offset(
                self.player.x, self.player.y, DUNGEON_W, DUNGEON_H
            )

            # 画面シェイク
            if self.shake_timer > 0:
                self.shake_timer -= 1
                sx = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)
                sy = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)
                pyxel.camera(-sx, -sy)

            draw_map(self.tiles, self.visible, self.explored, cam_x, cam_y)
            # アイテム描画
            draw_items_on_map(self.items, cam_x, cam_y, self.visible)
            # モンスター描画
            for m in self.monsters:
                if m.alive:
                    draw_entity(m, cam_x, cam_y, self.visible)
            # プレイヤー描画
            draw_entity(self.player, cam_x, cam_y, self.visible)
            # 攻撃エフェクト
            draw_attack_effect(self.player, cam_x, cam_y)
            for m in self.monsters:
                if m.alive:
                    draw_attack_effect(m, cam_x, cam_y)
            # ダメージポップアップ
            draw_damage_popups(self.damage_popups, cam_x, cam_y)
            # ポップアップ更新
            for p in self.damage_popups:
                p[4] -= 1
            self.damage_popups = [p for p in self.damage_popups if p[4] > 0]

            # シェイクリセット（UI前に）
            pyxel.camera(0, 0)
            # パネル
            draw_panel(self.player, self.floor_num, self.messages)

        if self.state == STATE_INVENTORY:
            draw_inventory(self.player, self.inv_cursor, self.id_table)
        elif self.state == STATE_GAMEOVER:
            draw_gameover()
        elif self.state == STATE_VICTORY:
            draw_victory()


if __name__ == "__main__":
    Game()
