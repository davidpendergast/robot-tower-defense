import math
import src.game.colors as colors
import src.utils.util as util
import configs
import random

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
                        "towers": (lambda x: x.is_tower(), {})}

    def w(self):
        return self._w

    def h(self):
        return self._h

    def is_valid(self, xy):
        return 0 <= xy[0] < self.w() and 0 <= xy[1] < self.h()

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
            self._remove_from_cell(old_pos)

        for cache_key in self._caches:
            if entity in self._caches[cache_key][1]:
                del self._caches[cache_key][1][entity]

    def all_hearts(self):
        for e in self._caches["hearts"][1]:
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

    def update_all(self, scene):
        for ent in self.positions:
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


_ENTITY_ID_COUNTER = 0


class ViewModes:
    NORMAL = "normal"
    SHOW_HP = "show_hp"


def _next_id():
    global _ENTITY_ID_COUNTER
    _ENTITY_ID_COUNTER += 1
    return _ENTITY_ID_COUNTER - 1


class Entity:

    def __init__(self, character, color, max_hp, name, description, actions_per_sec):
        self.character = character
        self.base_color = color

        self.actions_per_sec = actions_per_sec
        self._ticks_until_next_action = -1

        self.name = name
        self.description = description

        self.perturbed_color = None
        self.perturbed_countdown = 0
        self.perturbed_duration = 20

        self.max_hp = max_hp
        self.hp = self.max_hp
        self._id = _next_id()

    def get_char(self):
        return self.character

    def can_show_hp(self):
        return not self.is_enemy() and not self.is_decoration()

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
                return self.base_color
            else:
                a = util.Utils.bound(1 - self.perturbed_countdown / self.perturbed_duration, 0, 1)
                return util.Utils.linear_interp(self.base_color, self.perturbed_color, a)

    def perturb_color(self, new_color, duration):
        self.perturbed_color = new_color
        self.perturbed_countdown = duration
        self.perturbed_duration = duration

    def on_death(self, world, scene):
        pass

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_sell_cost(self):
        return -1

    def get_hp(self):
        return max(self.hp, 0)

    def get_max_hp(self):
        return self.max_hp

    def set_hp(self, new_hp):
        self.hp = util.Utils.bound(new_hp, 0, self.get_max_hp())

    def is_dead(self):
        return self.get_hp() <= 0

    def is_decoration(self):
        return False

    def is_heart(self):
        return False

    def is_enemy(self):
        return False

    def is_robot(self):
        return False

    def is_tower(self):
        return False

    def update(self, world, state):
        if self.perturbed_countdown > 0:
            self.perturbed_countdown -= 1

        if not state.is_paused():
            if self._ticks_until_next_action <= 0:
                self.act(world, state)
                self._ticks_until_next_action = self._calc_ticks_until_next_action()

    def _calc_ticks_until_next_action(self):
        aps = self.actions_per_sec
        if aps <= 0:
            return 999
        else:
            fps = configs.target_fps
            variance = 0.1
            return round(fps / aps * (1 + (random.random() - 0.5) * variance))

    def act(self, world, state):
        pass

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        if isinstance(other, Entity):
            return other._id == self._id
        else:
            return False

def generate_world(w, h):
    # TODO some sweet world generation code
    return World(w, h)

