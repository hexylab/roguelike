"""ゲームエンティティ: プレイヤー、モンスター、アイテム"""
import random
from constants import (
    MONSTER_DEFS, WEAPON_DEFS, SHIELD_DEFS,
    POTION_EFFECTS, SCROLL_EFFECTS,
    POTION_APPEARANCES, SCROLL_APPEARANCES,
    INVENTORY_MAX, IMG_ITEMS,
)


class Entity:
    def __init__(self, x, y, name, spr, img_bank):
        self.x = x
        self.y = y
        self.name = name
        self.spr = spr  # (sprite_x, sprite_y) in image bank
        self.img_bank = img_bank
        # 方向とアニメーション状態
        self.facing_dx = 0        # 向いている方向x
        self.facing_dy = 1        # 向いている方向y (デフォルト: 南)
        self.anim_timer = 0       # アニメーションタイマー（0=停止）
        self.anim_type = ""       # "walk" or "attack"
        self.attack_dx = 0        # 攻撃方向x
        self.attack_dy = 0        # 攻撃方向y
        self.hit_timer = 0        # 被弾フラッシュ残りフレーム
        self.hit_dx = 0           # 被弾ノックバック方向x
        self.hit_dy = 0           # 被弾ノックバック方向y

    @property
    def facing_left(self):
        return self.facing_dx < 0

    def start_walk_anim(self):
        from constants import ANIM_WALK_FRAMES
        self.anim_timer = ANIM_WALK_FRAMES
        self.anim_type = "walk"

    def start_attack_anim(self, dx, dy, critical=False, anim_type="attack"):
        from constants import ANIM_ATTACK_FRAMES
        self.anim_timer = ANIM_ATTACK_FRAMES
        self.anim_type = anim_type
        self.attack_dx = dx
        self.attack_dy = dy
        self.anim_critical = critical

    def start_hit(self, dx, dy):
        from constants import HIT_FLASH_FRAMES
        self.hit_timer = HIT_FLASH_FRAMES
        self.hit_dx = dx
        self.hit_dy = dy

    def tick_anim(self):
        if self.anim_timer > 0:
            self.anim_timer -= 1
        if self.hit_timer > 0:
            self.hit_timer -= 1


class Player(Entity):
    def __init__(self, x, y):
        from constants import SPR_PLAYER, IMG_CHARS
        super().__init__(x, y, "Player", SPR_PLAYER, IMG_CHARS)
        self.max_hp = 30
        self.hp = 30
        self.base_atk = 5
        self.base_def = 2
        self.level = 1
        self.exp = 0
        self.weapon = None
        self.shield = None
        self.inventory = []

    @property
    def atk(self):
        bonus = 0
        if self.weapon:
            bonus = self.weapon.power + self.weapon.plus
        return self.base_atk + bonus

    @property
    def defense(self):
        bonus = 0
        if self.shield:
            bonus = self.shield.power + self.shield.plus
        return self.base_def + bonus

    def exp_to_next(self):
        return self.level * 15

    def gain_exp(self, amount):
        """経験値を獲得。レベルアップしたらTrueを返す"""
        self.exp += amount
        leveled = False
        while self.exp >= self.exp_to_next():
            self.exp -= self.exp_to_next()
            self.level += 1
            self.max_hp += 5
            self.hp = min(self.hp + 10, self.max_hp)
            self.base_atk += 2
            self.base_def += 1
            leveled = True
        return leveled

    def can_pickup(self):
        return len(self.inventory) < INVENTORY_MAX


class Monster(Entity):
    def __init__(self, x, y, name, spr, hp, atk, defense, exp_val):
        from constants import IMG_MAP
        super().__init__(x, y, name, spr, IMG_MAP)
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.defense = defense
        self.exp_val = exp_val
        self.confused = 0  # 混乱ターン数

    @property
    def alive(self):
        return self.hp > 0


class Item(Entity):
    # item_type: "weapon", "shield", "potion", "scroll"
    def __init__(self, x, y, name, spr, item_type, power=0, plus=0,
                 effect=None, identified=True, appearance=""):
        super().__init__(x, y, name, spr, IMG_ITEMS)
        self.item_type = item_type
        self.power = power
        self.plus = plus
        self.effect = effect
        self.identified = identified
        self.appearance = appearance

    def display_name(self):
        if not self.identified and self.item_type in ("potion", "scroll"):
            if self.item_type == "potion":
                return f"{self.appearance}薬"
            return f"{self.appearance}巻物"
        name = self.name
        if self.item_type in ("weapon", "shield") and self.plus != 0:
            sign = "+" if self.plus > 0 else ""
            name = f"{name}{sign}{self.plus}"
        return name


# === ファクトリ関数 ===

def spawn_monsters(rooms, floor_num, player_room_idx=0):
    """フロアのモンスターを生成"""
    monsters = []
    eligible = [d for d in MONSTER_DEFS if d[6] <= floor_num <= d[7]]
    if not eligible:
        eligible = [MONSTER_DEFS[-1]]

    for i, room in enumerate(rooms):
        if i == player_room_idx:
            continue
        count = random.randint(1, 2 + floor_num // 3)
        for _ in range(count):
            mx = random.randint(room.x + 1, room.x + room.w - 2)
            my = random.randint(room.y + 1, room.y + room.h - 2)
            d = random.choice(eligible)
            # フロアが上がるほど少し強くする
            hp_bonus = (floor_num - d[6]) * 2
            atk_bonus = (floor_num - d[6])
            m = Monster(mx, my, d[0], d[1], d[2] + hp_bonus,
                        d[3] + atk_bonus, d[4], d[5])
            monsters.append(m)
    return monsters


def create_weapon(x, y, floor_num):
    """フロアに応じた武器を生成"""
    max_idx = min(len(WEAPON_DEFS) - 1, floor_num // 2)
    idx = random.randint(0, max_idx)
    d = WEAPON_DEFS[idx]
    plus = random.randint(0, 3) if random.random() < 0.3 else 0
    return Item(x, y, d[0], (d[2], d[3]), "weapon", power=d[1], plus=plus)


def create_shield(x, y, floor_num):
    """フロアに応じた盾を生成"""
    max_idx = min(len(SHIELD_DEFS) - 1, floor_num // 2)
    idx = random.randint(0, max_idx)
    d = SHIELD_DEFS[idx]
    plus = random.randint(0, 3) if random.random() < 0.3 else 0
    return Item(x, y, d[0], (d[2], d[3]), "shield", power=d[1], plus=plus)


class IdentificationTable:
    """未識別アイテムの見た目マッピング（ゲームごとにシャッフル）"""
    def __init__(self):
        self.potion_map = list(range(len(POTION_APPEARANCES)))
        random.shuffle(self.potion_map)
        self.scroll_map = list(range(len(SCROLL_APPEARANCES)))
        random.shuffle(self.scroll_map)
        self.identified_potions = set()
        self.identified_scrolls = set()

    def get_potion_appearance(self, effect_idx):
        return POTION_APPEARANCES[self.potion_map[effect_idx]]

    def get_scroll_appearance(self, effect_idx):
        return SCROLL_APPEARANCES[self.scroll_map[effect_idx]]

    def identify_potion(self, effect_idx):
        self.identified_potions.add(effect_idx)

    def identify_scroll(self, effect_idx):
        self.identified_scrolls.add(effect_idx)


def create_potion(x, y, id_table):
    """ランダムなポーションを生成"""
    idx = random.randint(0, len(POTION_EFFECTS) - 1)
    d = POTION_EFFECTS[idx]
    app = id_table.get_potion_appearance(idx)
    # スプライト: ポーション行のidxに応じた色
    color_idx = id_table.potion_map[idx]
    spr_x = (color_idx % 8) * 16
    spr_y = 128 + (color_idx // 8) * 16
    identified = idx in id_table.identified_potions
    return Item(x, y, d[0], (spr_x, spr_y), "potion",
                effect=d[1], identified=identified, appearance=app)


def create_scroll(x, y, id_table):
    """ランダムな巻物を生成"""
    idx = random.randint(0, len(SCROLL_EFFECTS) - 1)
    d = SCROLL_EFFECTS[idx]
    app = id_table.get_scroll_appearance(idx)
    color_idx = id_table.scroll_map[idx]
    spr_x = 128 + (color_idx % 8) * 16
    spr_y = 128 + (color_idx // 8) * 16
    identified = idx in id_table.identified_scrolls
    return Item(x, y, d[0], (spr_x, spr_y), "scroll",
                effect=d[1], identified=identified, appearance=app)


def spawn_items(rooms, floor_num, id_table, player_room_idx=0):
    """フロアのアイテムを生成"""
    items = []
    for i, room in enumerate(rooms):
        if i == player_room_idx:
            continue
        if random.random() < 0.6:
            ix = random.randint(room.x + 1, room.x + room.w - 2)
            iy = random.randint(room.y + 1, room.y + room.h - 2)
            r = random.random()
            if r < 0.2:
                items.append(create_weapon(ix, iy, floor_num))
            elif r < 0.35:
                items.append(create_shield(ix, iy, floor_num))
            elif r < 0.7:
                items.append(create_potion(ix, iy, id_table))
            else:
                items.append(create_scroll(ix, iy, id_table))
    return items
