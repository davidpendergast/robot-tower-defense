import math
import src.game.colors as colors
import src.utils.util as util
import configs
import random
import src.engine.sprites as sprites
import src.game.ascii_screen as ascii_screen


class World:

    def __init__(self, w, h):
        self.cells = []
        self._w = w
        self._h = h

        # lots of data duplication here but we need the speed
        self.positions = {}  # entity -> xy
        self.cells = {}      # xy -> list of entities
        self._caches = {"hearts": (lambda x: x.is_heart(), {}),  # dicts are just for uniqueness and ordering
                        "enemies": (lambda x: x.is_enemy(), {}),
                        "robots": (lambda x: x.is_robot(), {}),
                        "towers": (lambda x: x.is_tower(), {}),
                        "spawners": (lambda x: x.is_spawner(), {}),
                        "rocks": (lambda x: x.is_rock(), {}),
                        "stone_items": (lambda x: x.is_stone_item(), {}),
                        "gold_ingots": (lambda x: x.is_gold_ingot(), {}),
                        "build_markers": (lambda x: x.is_build_marker(), {})}

    def w(self):
        return self._w

    def h(self):
        return self._h

    def rand_cell(self):
        return (int(random.random() * self.w()),
                int(random.random() * self.h()))

    def __contains__(self, entity):
        return entity in self.positions

    def is_valid(self, xy):
        return 0 <= xy[0] < self.w() and 0 <= xy[1] < self.h()

    def can_move_to(self, ent, xy):
        if ent.is_robot():
            return self.get_solidity(xy) in (0, 2)
        else:
            return self.get_solidity(xy) == 0

    def get_solidity(self, xy):
        if not self.is_valid(xy):
            return 1
        else:
            res = 0
            for ent in self.all_entities_in_cell(xy):
                if ent.get_solidity() == 1:
                    res = 1
                elif res != 1 and ent.get_solidity() == 2:
                    res = 2
            return res

    def get_pos(self, entity):
        if entity in self.positions:
            return self.positions[entity]

    def _remove_from_cell(self, entity, xy):
        if xy in self.cells:
            ents = self.cells[xy]
            ents.remove(entity)

    def _add_to_cell(self, entity, xy):
        if not self.is_valid(xy):
            raise ValueError("tried to add entity out of range: {} at {}".format(entity, xy))
        if xy not in self.cells:
            self.cells[xy] = []
        self.cells[xy].append(entity)

    def set_pos(self, entity, xy):
        if entity in self.positions:
            old_pos = self.positions[entity]
            self._remove_from_cell(entity, old_pos)
        self.positions[entity] = xy
        self._add_to_cell(entity, xy)

        for cache_key in self._caches:
            if self._caches[cache_key][0](entity):
                self._caches[cache_key][1][entity] = None

    def remove(self, entity):
        if entity in self.positions:
            old_pos = self.positions[entity]
            del self.positions[entity]
            self._remove_from_cell(entity, old_pos)

        for cache_key in self._caches:
            if entity in self._caches[cache_key][1]:
                del self._caches[cache_key][1][entity]

    def request_build_at(self, entity, xy):
        if self.get_solidity(xy) == 0:
            import src.game.units as units
            print("INFO: requested to build {} at {}".format(entity, xy))
            self.set_pos(units.BuildNewMarker(entity), xy)
            return True
        return False

    def all_hearts(self):
        for e in self._caches["hearts"][1]:
            yield e

    def all_spawners(self):
        for e in self._caches["spawners"][1]:
            yield e

    def all_enemies(self):
        for e in self._caches["enemies"][1]:
            yield e

    def all_robots(self):
        for e in self._caches["robots"][1]:
            yield e

    def all_towers(self):
        for e in self._caches["towers"][1]:
            yield e

    def all_rocks(self):
        for e in self._caches["rocks"][1]:
            yield e

    def all_stone_items(self):
        for e in self._caches["stone_items"][1]:
            yield e

    def all_gold_ingots(self):
        for e in self._caches["gold_ingots"][1]:
            yield e

    def all_active_rocks(self):
        for e in self._caches["rocks"][1]:
            if e.is_active():
                yield e

    def all_build_markers(self):
        for e in self._caches["build_markers"][1]:
            yield e

    def empty_cells_adjacent_to(self, xys, empty_for=None):
        xys = set(util.Utils.listify(xys))
        res = set()
        for xy in xys:
            for n in util.Utils.rand_neighbors(xy):
                if self.is_valid(n) and n not in xys and n not in res:
                    if ((empty_for is None and self.get_solidity(n) == 0)
                            or (empty_for is not None and self.can_move_to(empty_for, n))):
                        res.add(n)
        return res

    def all_entities_adjacent_to(self, xy, cond=None):
        for n in util.Utils.rand_neighbors(xy):
            for e in self.all_entities_in_cell(n, cond=cond):
                yield e

    def update_all(self, scene):
        to_update = [e for e in self.positions]
        for ent in to_update:
            # make sure it hasn't died during the action of another entity
            if ent in self.positions:
                ent.update(self, scene)

        if not scene.is_paused():
            to_remove = [ent for ent in self.positions if ent.is_dead()]
            for ent in to_remove:
                ent.on_death(self, scene)
                self.remove(ent)

    def all_entities_in_cell(self, xy, cond=None):
        if xy not in self.cells:
            return []
        else:
            for e in self.cells[xy]:
                if cond is None or cond(e):
                    yield e

    def all_cells_in_range(self, xy, radius):
        for y in range(int(math.floor(xy[1] - radius)), int(math.ceil(xy[1] + radius)) + 1):
            for x in range(int(math.floor(xy[0] - radius)), int(math.ceil(xy[0] + radius)) + 1):
                if self.is_valid((x, y)):
                    dx = xy[0] - x
                    dy = xy[1] - y
                    if math.sqrt(dx*dx + dy*dy) <= radius:
                        yield (x, y)

    def all_entities_in_range(self, xy, radius, cond=None):
        for c in self.all_cells_in_range(xy, radius):
            for e in self.all_entities_in_cell(c, cond=cond):
                yield e

    def draw(self, screen, pos, state):
        for x in range(0, self.w()):
            for y in range(0, self.h()):
                decs = []
                drew_any = False
                for ent in self.all_entities_in_cell((x, y)):
                    if ent.is_decoration():
                        decs.append(ent)
                    else:
                        drew_any = True
                        ent.draw((pos[0] + x, pos[0] + y), screen, mode=state.get_view_mode())
                if not drew_any:
                    for d in decs:
                        d.draw((pos[0] + x, pos[0] + y), screen, mode=state.get_view_mode())


_ENTITY_ID_COUNTER = 0


class ViewModes:
    NORMAL = "normal"
    SHOW_HP = "show_hp"


def _next_id():
    global _ENTITY_ID_COUNTER
    _ENTITY_ID_COUNTER += 1
    return _ENTITY_ID_COUNTER - 1


ALL_STAT_TYPES = []


class StatType:

    def __init__(self, name, desc_maker, color, default_val):
        self.name = name
        self.desc_maker = desc_maker
        self.color = color
        self.default_val = default_val
        ALL_STAT_TYPES.append(self)

    def __eq__(self, other):
        if isinstance(other, StatType):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)

    def to_string(self, value) -> sprites.TextBuilder:
        tb = sprites.TextBuilder()
        tb.add(self.desc_maker(value), color=self.color)
        return tb


class StatTypes:

    HP = StatType("Max Health", lambda v: "Max Health: {}".format(v), colors.RED, 50)
    MAX_CHARGE = StatType("Max Charge", lambda v: "Max Charge: {}".format(v), colors.YELLOW, 0)
    CHARGE_RATE = StatType("Charge Rate", lambda v: "Charge Rate: {}".format(v), colors.LIGHT_GRAY, 10)

    APS = StatType("Speed", lambda v: "Speed: {}/sec".format(v), colors.LIGHT_GRAY, 2)
    DAMAGE = StatType("Damage", lambda v: "Damage: {}".format(v), colors.LIGHT_GRAY, 10)

    BONUS_DAMAGE = StatType("Bonus Damage", lambda v: "Bonus Damage: {}".format(v), colors.LIGHT_GRAY, 0)
    RAMPAGE = StatType("Rampage", lambda v: "Damage on Hit: {}".format(v), colors.RED, 0)

    RANGE = StatType("Range", lambda v: "Range: {}".format(v), colors.BLUE, 1.5)
    ARMOR = StatType("Armor", lambda v: "Armor: {}".format(v), colors.MID_GRAY, 0)

    BUY_PRICE = StatType("Gold Cost", lambda v: "Cost: ${}".format(v), colors.YELLOW, -1)
    SELL_PRICE = StatType("Sell Price", lambda v: "Sell for: ${}".format(v), colors.GREEN, -1)
    STONE_PRICE = StatType("Stone Cost", lambda v: "Stone Cost: {}".format(v), colors.LIGHT_GRAY, 0)
    BUILD_TIME = StatType("Build Time", lambda v: "Build Time: {}".format(v), colors.LIGHT_GRAY, 10)
    VAMPRISM = StatType("Vampirism", lambda v: "Vampirism: {}%".format(v), colors.PURPLE, 0)
    SOLIDITY = StatType("Solidity", lambda v: "", colors.WHITE, 1)  # 0 = air, 1 = wall, 2 = door

    REPAIRABLE = StatType("Repairable", lambda v: "Cannot be repaired" if v <= 0 else "", colors.LIGHT_GRAY, 0)
    BUILD_SPEED = StatType("Build Speed", lambda v: "Build Speed: {}/sec".format(v), colors.LIGHT_GRAY, 0)
    AGGRESSION = StatType("Aggression", lambda v: "Aggression: {}".format(v), colors.RED, 0)
    DEATH_REWARD = StatType("Death Reward", lambda v: "Bounty: {}".format(v), colors.YELLOW, 0)


def make_stats(max_hp=None, actions_per_sec=None, damage=None, sell_price=None, cost=None):
    res = {}
    for stat_type in ALL_STAT_TYPES:
        res[stat_type] = stat_type.default_val

    if max_hp is not None:
        res[StatTypes.HP]= max_hp
    if actions_per_sec is not None:
        res[StatTypes.APS] = actions_per_sec
    if damage is not None:
        res[StatTypes.DAMAGE] = damage
    if sell_price is not None:
        res[StatTypes.SELL_PRICE] = sell_price
    if cost is not None:
        res[StatTypes.BUY_PRICE] = cost
    return res


class Entity:

    def __init__(self, character, color, name, description):
        self.character = character
        self.base_color = color

        self.stats = self.get_base_stats()
        self._ticks_until_next_action = -1

        self.name = name
        self.description = description

        self.perturbed_color = None
        self.perturbed_countdown = 0
        self.perturbed_duration = 20

        self.hp = self.get_stat_value(StatTypes.HP)
        self.charge = self.get_stat_value(StatTypes.MAX_CHARGE)

        self._id = _next_id()

    def get_info_text(self, w, in_world=True):
        tb = sprites.TextBuilder()
        tb.addLine("{} ({}):".format(self.get_name(), self.get_char()), color=self.base_color)
        tb.addLine(self.get_description(), color=self.base_color)
        return tb

    def get_base_stats(self):
        res = {}
        for stat_type in ALL_STAT_TYPES:
            res[stat_type] = stat_type.default_val
        return res

    def get_stat_value(self, stat_type):
        if stat_type in self.stats:
            return self.stats[stat_type]
        else:
            return 0

    def set_stat_value(self, stat_type, val):
        self.stats[stat_type] = val

    def ticks_per_action(self):
        aps = self.get_stat_value(StatTypes.APS)
        if aps <= 0:
            return 999
        else:
            return configs.target_fps / aps

    def is_selectable(self):
        return self.is_tower()

    def get_char(self):
        return self.character

    def can_show_hp(self):
        return not self.is_enemy() and not self.is_decoration()

    def get_base_color(self):
        return self.base_color

    def get_color(self, mode=ViewModes.NORMAL):
        if mode == ViewModes.SHOW_HP and self.can_show_hp():
            upper = colors.GREEN
            mid = colors.YELLOW
            lower = colors.RED
            pcnt = util.Utils.bound(self.get_hp() / self.get_max_hp(), 0, 1)
            if pcnt >= 0.5:
                return util.Utils.linear_interp(mid, upper, (pcnt - 0.5) / 0.5)
            else:
                return util.Utils.linear_interp(lower, mid, pcnt / 0.5)
        else:
            if self.perturbed_countdown <= 0 or self.perturbed_color is None:
                return self.get_base_color()
            else:
                a = util.Utils.bound(self.perturbed_countdown / self.perturbed_duration, 0, 1)
                return util.Utils.linear_interp(self.get_base_color(), self.perturbed_color, a)

    def perturb_color(self, new_color, duration):
        self.perturbed_color = new_color
        self.perturbed_countdown = duration
        self.perturbed_duration = duration

    def calc_damage_against(self, other):
        my_dmg = self.get_stat_value(StatTypes.DAMAGE)
        my_dmg += self.get_stat_value(StatTypes.BONUS_DAMAGE)

        other_def = other.get_stat_value(StatTypes.ARMOR)

        return max(0, my_dmg - other_def)

    def give_damage_to(self, other):
        dmg = self.calc_damage_against(other)
        if dmg > 0:
            other.take_damage_from(dmg, self)

            heal_amt = int(dmg * self.get_stat_value(StatTypes.VAMPRISM) / 100)
            self.set_hp(self.get_hp() + heal_amt)
            # TODO noise for healing

        ramp = self.get_stat_value(StatTypes.RAMPAGE)
        self.stats[StatTypes.BONUS_DAMAGE] += ramp

    def take_damage_from(self, damage, other):
        self.set_hp(self.get_hp() - damage)
        if damage > 0:
            self.animate_damage_from(other)

    def animate_damage_from(self, other):
        self.perturb_color(other.get_color(), 10)
        # TODO noise for taking damage

    def get_aggression_discount(self):
        """More aggressive = less cost to attack"""
        aggro = self.get_stat_value(StatTypes.AGGRESSION)
        return util.Utils.bound(1 - (aggro / 10), 0, 2)

    def get_gold_cost(self):
        return self.get_stat_value(StatTypes.BUY_PRICE)

    def get_stone_cost(self):
        return self.get_stat_value(StatTypes.STONE_PRICE)

    def get_sell_price(self):
        return self.get_stat_value(StatTypes.SELL_PRICE)

    def get_build_time(self):
        return self.get_stat_value(StatTypes.BUILD_TIME)

    def can_sell(self):
        return self.get_sell_price() >= 0

    def on_death(self, world, scene):
        pass

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_hp(self):
        return max(self.hp, 0)

    def get_max_hp(self):
        return self.get_stat_value(StatTypes.HP)

    def get_max_charge(self):
        return self.get_stat_value(StatTypes.MAX_CHARGE)

    def add_charge(self, val):
        self.charge = min(self.get_max_charge(), self.charge + val)

    def set_hp(self, new_hp):
        self.hp = util.Utils.bound(new_hp, 0, self.get_max_hp())

    def get_solidity(self):
        return self.get_stat_value(StatTypes.SOLIDITY)

    def is_dead(self):
        return self.get_hp() <= 0

    def is_decoration(self):
        return False

    def is_heart(self):
        return False

    def is_spawner(self):
        return False

    def is_enemy(self):
        return False

    def is_robot(self):
        return False

    def is_tower(self):
        return False

    def is_rock(self):
        return False

    def is_stone_item(self):
        return False

    def is_gold_ingot(self):
        return False

    def is_build_marker(self):
        return False

    def update(self, world, state):
        if self.perturbed_countdown > 0:
            self.perturbed_countdown -= 1

        if not state.is_paused() and not state.should_skip_this_frame():
            if self._ticks_until_next_action <= 0:
                self.act(world, state)
                self._ticks_until_next_action = self._calc_ticks_until_next_action()
            else:
                self._ticks_until_next_action -= 1

    def _calc_ticks_until_next_action(self):
        aps = self.get_stat_value(StatTypes.APS)
        if aps <= 0:
            return 999
        else:
            fps = configs.target_fps
            variance = 0.1
            return round(fps / aps * (1 + (random.random() - 0.5) * variance))

    def act(self, world, state):
        pass

    def draw(self, xy, screen: ascii_screen.AsciiScreen, mode=ViewModes.NORMAL):
        character = self.get_char()
        color = self.get_color(mode)
        screen.add(xy, character, color=color)

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        if isinstance(other, Entity):
            return other._id == self._id
        else:
            return False


def generate_world(w, h):
    # TODO some sweet world generation code
    res = World(w, h)

    import src.game.units as units
    res.set_pos(units.BuildBotSpawner(), (5, 5))
    res.set_pos(units.HeartTower(), (6, 6))

    res.set_pos(units.EnemySpawnZone(), (0, 0))
    res.set_pos(units.EnemySpawnZone(), (0, 1))
    res.set_pos(units.EnemySpawnZone(), (1, 0))
    res.set_pos(units.EnemySpawnZone(), (1, 1))

    for i in range(0, 5):
        res.set_pos(units.RockTower(), res.rand_cell())

    for i in range(0, 3):
        res.set_pos(units.GoldOreTower(), res.rand_cell())

    for _ in range(0, 2):
        for tower_provider in units.get_towers_in_shop():
            if tower_provider is not None:
                tower = tower_provider()
                res.set_pos(tower, res.rand_cell())
                for upgrade in tower.get_upgrades():
                    res.set_pos(upgrade, res.rand_cell())

    return res


def generate_world3(w, h):
    # TODO some sweet world generation code
    res = World(w, h)

    import src.game.units as units
    res.set_pos(units.MineBotSpawner(), (5, 5))
    res.set_pos(units.RockTower(), (10, 10))
    res.set_pos(units.HeartTower(), (15, 10))

    res.set_pos(units.BuildBotSpawner(), (20, 10))

    res.set_pos(units.GoldIngot(15), (3, 5))

    return res

