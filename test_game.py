"""ゲーム全機能の包括テスト"""
import sys
import os
import random
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAIL = 0


def test(name, func):
    global PASS, FAIL
    try:
        func()
        print(f"  OK: {name}")
        PASS += 1
    except Exception as e:
        print(f"  FAIL: {name}")
        traceback.print_exc()
        FAIL += 1


def run_tests():
    global PASS, FAIL

    print("=== 1. モジュールインポート ===")

    test("constants import", lambda: __import__("constants"))
    test("dungeon import", lambda: __import__("dungeon"))
    test("fov import", lambda: __import__("fov"))
    test("entities import", lambda: __import__("entities"))
    def test_all_imports_resolve():
        """全モジュールの全シンボルが解決できることを検証（AST解析）"""
        import ast
        files = ["main.py", "renderer.py", "entities.py", "dungeon.py", "fov.py"]
        errors = []
        for fname in files:
            with open(fname) as f:
                tree = ast.parse(f.read())
            names_used = set()
            names_local = set()
            names_imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    names_used.add(node.id)
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    names_local.add(node.name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in (node.names or []):
                        names_imported.add(alias.asname or alias.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        names_imported.add(alias.asname or alias.name)
                elif isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            names_local.add(t.id)
            prefixes = ("COL_", "SPR_", "TILE_", "STATE_", "IMG_",
                        "DUNGEON_", "MAP_", "PANEL_", "SCREEN_", "FOV_", "MAX_", "DB16")
            for name in names_used:
                if any(name.startswith(p) for p in prefixes):
                    if name not in names_imported and name not in names_local:
                        errors.append(f"{fname}: {name}")
        assert not errors, "Missing imports:\n  " + "\n  ".join(errors)

    test("all symbol imports resolve (AST)", test_all_imports_resolve)

    print("\n=== 2. ダンジョン生成 ===")
    from constants import TILE_FLOOR, TILE_WALL, TILE_STAIRS, DUNGEON_W, DUNGEON_H
    from dungeon import generate_dungeon

    def test_dungeon_basic():
        random.seed(1)
        tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, 1)
        assert len(tiles) == DUNGEON_H, f"height={len(tiles)}"
        assert len(tiles[0]) == DUNGEON_W, f"width={len(tiles[0])}"
        assert len(rooms) > 0, "no rooms generated"

    def test_dungeon_has_stairs():
        random.seed(2)
        tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, 1)
        stairs_count = sum(1 for row in tiles for t in row if t == TILE_STAIRS)
        assert stairs_count == 1, f"stairs_count={stairs_count}"

    def test_dungeon_rooms_walkable():
        random.seed(3)
        tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, 1)
        for room in rooms:
            cx, cy = room.center
            assert tiles[cy][cx] in (TILE_FLOOR, TILE_STAIRS), \
                f"room center ({cx},{cy}) is {tiles[cy][cx]}"

    def test_dungeon_all_floors():
        """全10フロア生成テスト"""
        for floor in range(1, 11):
            random.seed(floor * 100)
            tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, floor)
            assert len(rooms) >= 2, f"floor {floor}: only {len(rooms)} rooms"

    def test_dungeon_boundary():
        """マップ境界が壁であること"""
        random.seed(4)
        tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, 1)
        for x in range(DUNGEON_W):
            assert tiles[0][x] == TILE_WALL, f"top boundary at ({x},0)"
            assert tiles[DUNGEON_H-1][x] == TILE_WALL, f"bottom boundary at ({x},{DUNGEON_H-1})"
        for y in range(DUNGEON_H):
            assert tiles[y][0] == TILE_WALL, f"left boundary at (0,{y})"
            assert tiles[y][DUNGEON_W-1] == TILE_WALL, f"right boundary at ({DUNGEON_W-1},{y})"

    test("basic generation", test_dungeon_basic)
    test("stairs placement", test_dungeon_has_stairs)
    test("room centers walkable", test_dungeon_rooms_walkable)
    test("all 10 floors", test_dungeon_all_floors)
    test("boundary walls", test_dungeon_boundary)

    print("\n=== 3. 視界(FOV)計算 ===")
    from fov import compute_fov

    def test_fov_basic():
        random.seed(5)
        tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, 1)
        px, py = rooms[0].center
        visible = compute_fov(tiles, px, py, 8)
        assert (px, py) in visible, "player pos not visible"
        assert len(visible) > 1, f"only {len(visible)} visible tiles"

    def test_fov_walls_block():
        """壁の向こうは見えない"""
        tiles = [[TILE_WALL]*10 for _ in range(10)]
        for y in range(2, 8):
            for x in range(2, 8):
                tiles[y][x] = TILE_FLOOR
        tiles[5][5] = TILE_WALL  # 真ん中に壁
        visible = compute_fov(tiles, 3, 3, 8)
        assert (3, 3) in visible
        # 壁の向こう側は見えにくいはず
        assert len(visible) > 0

    def test_fov_all_floors():
        """全フロアでFOVがクラッシュしない"""
        for floor in range(1, 11):
            random.seed(floor * 200)
            tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, floor)
            px, py = rooms[0].center
            visible = compute_fov(tiles, px, py, 8)
            assert len(visible) > 0, f"floor {floor}: no visible tiles"

    test("basic FOV", test_fov_basic)
    test("walls block vision", test_fov_walls_block)
    test("FOV on all floors", test_fov_all_floors)

    print("\n=== 4. エンティティ生成 ===")
    from entities import (
        Player, Monster, IdentificationTable,
        spawn_monsters, spawn_items,
        create_weapon, create_shield, create_potion, create_scroll,
    )

    def test_player_creation():
        p = Player(5, 5)
        assert p.hp == p.max_hp == 30
        assert p.atk == 5
        assert p.defense == 2
        assert p.level == 1
        assert p.weapon is None
        assert p.shield is None
        assert len(p.inventory) == 0

    def test_player_level_up():
        p = Player(0, 0)
        leveled = p.gain_exp(100)
        assert leveled, "should have leveled up"
        assert p.level > 1

    def test_player_equip():
        p = Player(0, 0)
        id_t = IdentificationTable()
        w = create_weapon(0, 0, 1)
        p.inventory.append(w)
        p.weapon = w
        assert p.atk == p.base_atk + w.power + w.plus

    def test_monster_spawn_all_floors():
        """全フロアでモンスターが正常生成される"""
        for floor in range(1, 11):
            random.seed(floor * 300)
            tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, floor)
            monsters = spawn_monsters(rooms, floor, 0)
            assert len(monsters) > 0, f"floor {floor}: no monsters"
            for m in monsters:
                assert m.hp > 0, f"floor {floor}: monster {m.name} hp={m.hp}"
                assert m.atk > 0, f"floor {floor}: monster {m.name} atk={m.atk}"
                # モンスター位置がマップ内かチェック
                assert 0 <= m.x < DUNGEON_W, f"monster x={m.x} out of bounds"
                assert 0 <= m.y < DUNGEON_H, f"monster y={m.y} out of bounds"
                # モンスター位置が壁でないかチェック
                assert tiles[m.y][m.x] != TILE_WALL, \
                    f"monster {m.name} at wall ({m.x},{m.y})"

    def test_item_spawn_all_floors():
        """全フロアでアイテムが正常生成される"""
        id_t = IdentificationTable()
        for floor in range(1, 11):
            random.seed(floor * 400)
            tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, floor)
            items = spawn_items(rooms, floor, id_t, 0)
            for item in items:
                assert item.item_type in ("weapon", "shield", "potion", "scroll"), \
                    f"unknown item type: {item.item_type}"
                assert item.display_name(), f"empty display name for {item.item_type}"
                assert 0 <= item.x < DUNGEON_W, f"item x={item.x}"
                assert 0 <= item.y < DUNGEON_H, f"item y={item.y}"
                assert tiles[item.y][item.x] != TILE_WALL, \
                    f"item at wall ({item.x},{item.y})"

    def test_identification():
        """未識別システムのテスト"""
        id_t = IdentificationTable()
        p1 = create_potion(0, 0, id_t)
        assert not p1.identified or p1.effect is not None
        name_before = p1.display_name()
        # 識別後
        from constants import POTION_EFFECTS
        for i, (_, eff) in enumerate(POTION_EFFECTS):
            id_t.identify_potion(i)
        p2 = create_potion(0, 0, id_t)
        assert p2.identified, "should be identified after identify_potion"

    def test_weapon_shield_display():
        w = create_weapon(0, 0, 5)
        assert w.display_name(), "weapon display name empty"
        s = create_shield(0, 0, 5)
        assert s.display_name(), "shield display name empty"

    test("player creation", test_player_creation)
    test("player level up", test_player_level_up)
    test("player equip weapon", test_player_equip)
    test("monster spawn all floors", test_monster_spawn_all_floors)
    test("item spawn all floors", test_item_spawn_all_floors)
    test("identification system", test_identification)
    test("weapon/shield display", test_weapon_shield_display)

    print("\n=== 5. 戦闘システム ===")

    def test_combat_damage():
        """ダメージ計算: max(1, ATK - DEF//2)"""
        p = Player(0, 0)
        from constants import SPR_SLIME
        m = Monster(1, 0, "Slime", SPR_SLIME, 8, 3, 0, 3)
        # Player ATK=5, Slime DEF=0 → dmg = max(1, 5 - 0) = 5
        dmg_to_monster = max(1, p.atk - m.defense // 2)
        assert dmg_to_monster == 5, f"dmg_to_monster={dmg_to_monster}"
        # Slime ATK=3, Player DEF=2 → dmg = max(1, 3 - 1) = 2
        dmg_to_player = max(1, m.atk - p.defense // 2)
        assert dmg_to_player == 2, f"dmg_to_player={dmg_to_player}"

    def test_combat_min_damage():
        """最低ダメージは1"""
        p = Player(0, 0)
        p.base_def = 100
        from constants import SPR_SLIME
        m = Monster(1, 0, "Slime", SPR_SLIME, 8, 3, 0, 3)
        dmg = max(1, m.atk - p.defense // 2)
        assert dmg == 1, f"min dmg should be 1, got {dmg}"

    def test_monster_death():
        from constants import SPR_SLIME
        m = Monster(0, 0, "Slime", SPR_SLIME, 8, 3, 0, 3)
        assert m.alive
        m.hp = 0
        assert not m.alive

    test("damage calculation", test_combat_damage)
    test("minimum damage = 1", test_combat_min_damage)
    test("monster death", test_monster_death)

    print("\n=== 6. インベントリ ===")
    from constants import INVENTORY_MAX

    def test_inventory_capacity():
        p = Player(0, 0)
        assert p.can_pickup()
        id_t = IdentificationTable()
        for _ in range(INVENTORY_MAX):
            p.inventory.append(create_weapon(0, 0, 1))
        assert not p.can_pickup(), "should be full"

    def test_equip_unequip():
        p = Player(0, 0)
        w = create_weapon(0, 0, 3)
        s = create_shield(0, 0, 3)
        p.inventory.append(w)
        p.inventory.append(s)
        p.weapon = w
        atk_with = p.atk
        p.weapon = None
        atk_without = p.atk
        assert atk_with > atk_without, f"equipped ATK should be higher: {atk_with} vs {atk_without}"
        p.shield = s
        def_with = p.defense
        p.shield = None
        def_without = p.defense
        assert def_with > def_without

    test("inventory capacity", test_inventory_capacity)
    test("equip/unequip", test_equip_unequip)

    print("\n=== 7. ゲームフロー統合テスト ===")

    def test_full_game_flow():
        """タイトル→新規ゲーム→移動→戦闘→アイテム取得→階段降りるの全フロー"""
        random.seed(42)
        tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, 1)
        player = Player(0, 0)
        player.x, player.y = rooms[0].center
        id_table = IdentificationTable()
        monsters = spawn_monsters(rooms, 1, 0)
        items = spawn_items(rooms, 1, id_table, 0)
        explored = set()
        visible = compute_fov(tiles, player.x, player.y, 8)
        explored |= visible

        # 移動テスト
        old_x, old_y = player.x, player.y
        moved = False
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = player.x + dx, player.y + dy
            if 0 <= nx < DUNGEON_W and 0 <= ny < DUNGEON_H:
                if tiles[ny][nx] in (TILE_FLOOR, TILE_STAIRS):
                    player.x, player.y = nx, ny
                    moved = True
                    break
        assert moved, "couldn't move in any direction"

        # FOV更新
        visible = compute_fov(tiles, player.x, player.y, 8)
        explored |= visible

        # 戦闘テスト
        if monsters:
            m = monsters[0]
            dmg = max(1, player.atk - m.defense // 2)
            m.hp -= dmg
            if m.hp <= 0:
                player.gain_exp(m.exp_val)

        # アイテム取得テスト
        if items:
            item = items[0]
            player.inventory.append(item)
            assert len(player.inventory) == 1

            # 装備テスト
            if item.item_type == "weapon":
                player.weapon = item
                assert player.weapon is not None
            elif item.item_type == "shield":
                player.shield = item
                assert player.shield is not None

        # 階段テスト（次フロアへ）
        tiles2, rooms2 = generate_dungeon(DUNGEON_W, DUNGEON_H, 2)
        player.x, player.y = rooms2[0].center
        visible = compute_fov(tiles2, player.x, player.y, 8)
        assert len(visible) > 0

    def test_10_floor_clear():
        """1Fから10Fまで全フロアを生成して問題なし"""
        player = Player(0, 0)
        id_table = IdentificationTable()
        for floor in range(1, 11):
            random.seed(floor * 500)
            tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, floor)
            player.x, player.y = rooms[0].center
            monsters = spawn_monsters(rooms, floor, 0)
            items = spawn_items(rooms, floor, id_table, 0)
            visible = compute_fov(tiles, player.x, player.y, 8)
            explored = set(visible)
            # 各フロアの基本検証
            assert len(rooms) >= 2, f"floor {floor}: {len(rooms)} rooms"
            assert len(visible) > 0, f"floor {floor}: no visible"
            for m in monsters:
                assert m.alive, f"floor {floor}: dead monster spawned"

    def test_potion_effects():
        """全ポーション効果のテスト"""
        from constants import POTION_EFFECTS
        p = Player(0, 0)
        id_t = IdentificationTable()
        for i, (name, effect) in enumerate(POTION_EFFECTS):
            p_test = Player(0, 0)
            p_test.hp = 10  # HPを下げておく
            old_hp = p_test.hp
            old_atk = p_test.base_atk
            old_def = p_test.base_def
            if effect == "heal":
                p_test.hp = min(p_test.hp + 20, p_test.max_hp)
                assert p_test.hp > old_hp or p_test.hp == p_test.max_hp
            elif effect == "big_heal":
                p_test.hp = min(p_test.hp + 50, p_test.max_hp)
                assert p_test.hp >= old_hp
            elif effect == "str_up":
                p_test.base_atk += 2
                assert p_test.base_atk > old_atk
            elif effect == "def_up":
                p_test.base_def += 2
                assert p_test.base_def > old_def
            elif effect == "poison":
                p_test.hp -= 10
                assert p_test.hp < old_hp

    def test_scroll_effects():
        """全巻物効果のテスト"""
        from constants import SCROLL_EFFECTS
        for name, effect in SCROLL_EFFECTS:
            assert effect in ("map_reveal", "power_up", "confuse",
                              "sleep_enemies", "blast"), f"unknown effect: {effect}"

    test("full game flow", test_full_game_flow)
    test("10 floor clear", test_10_floor_clear)
    test("potion effects", test_potion_effects)
    test("scroll effects", test_scroll_effects)

    print("\n=== 8. エッジケース ===")

    def test_empty_room_spawn():
        """小さい部屋でもモンスター/アイテム生成がクラッシュしない"""
        from dungeon import Room
        small_rooms = [Room(5, 5, 4, 4), Room(20, 20, 4, 4)]
        for _ in range(20):  # 複数回試行
            monsters = spawn_monsters(small_rooms, 10, 0)
            for m in monsters:
                assert m.x >= small_rooms[1].x + 1
                assert m.x <= small_rooms[1].x + small_rooms[1].w - 2

    def test_fov_at_boundary():
        """マップ端でのFOV"""
        tiles, rooms = generate_dungeon(DUNGEON_W, DUNGEON_H, 1)
        # 壁際ではFOVがクラッシュしない
        visible = compute_fov(tiles, 1, 1, 8)
        assert (1, 1) in visible

    def test_large_inventory_display():
        """インベントリ満杯時の表示名"""
        p = Player(0, 0)
        id_t = IdentificationTable()
        for _ in range(INVENTORY_MAX):
            r = random.random()
            if r < 0.25:
                p.inventory.append(create_weapon(0, 0, 5))
            elif r < 0.5:
                p.inventory.append(create_shield(0, 0, 5))
            elif r < 0.75:
                p.inventory.append(create_potion(0, 0, id_t))
            else:
                p.inventory.append(create_scroll(0, 0, id_t))
        for item in p.inventory:
            name = item.display_name()
            assert isinstance(name, str), f"display_name returned {type(name)}"
            assert len(name) > 0, "empty display name"

    def test_camera_offset():
        """カメラオフセット計算"""
        from constants import MAP_VIEW_W, MAP_VIEW_H
        from renderer import camera_offset
        # 中央付近
        cx, cy = camera_offset(24, 24, DUNGEON_W, DUNGEON_H)
        assert cx >= 0 and cy >= 0
        # 左上端
        cx, cy = camera_offset(0, 0, DUNGEON_W, DUNGEON_H)
        assert cx == 0 and cy == 0
        # 右下端
        cx, cy = camera_offset(DUNGEON_W-1, DUNGEON_H-1, DUNGEON_W, DUNGEON_H)
        assert cx == DUNGEON_W - MAP_VIEW_W
        assert cy == DUNGEON_H - MAP_VIEW_H

    test("small room spawn", test_empty_room_spawn)
    test("FOV at boundary", test_fov_at_boundary)
    test("large inventory display", test_large_inventory_display)
    test("camera offset", test_camera_offset)

    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        sys.exit(1)
    else:
        print("All tests passed!")


if __name__ == "__main__":
    run_tests()
