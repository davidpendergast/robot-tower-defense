import src.game.worlds as worlds
import src.game.colors as colors
import src.utils.util as util
import configs
import random
import math
import heapq


class Tower(worlds.Entity):

    def __init__(self, character, color, name, description):
        super().__init__(character, color, name, description)

    def get_base_stats(self):
        res = super().get_base_stats()
        return res

    def is_tower(self):
        return True

    def get_upgrades(self):
        return []


class HeartTower(Tower):

    def __init__(self):
        super().__init__("♦", colors.CYAN, "Energy Crystal",
                         "Protect this tower at all costs!\n" +
                         "Gold must be delivered here.")

    def get_base_color(self):
        pcnt_hp = util.Utils.bound(self.get_hp() / self.get_max_hp(), 0, 1)
        dark = colors.BLACK
        return util.Utils.linear_interp(self.base_color, dark, (1 - pcnt_hp))

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.REPAIRABLE] = 0
        res[worlds.StatTypes.HP] = 100
        res[worlds.StatTypes.SOLIDITY] = 1
        return res

    def is_heart(self):
        return True


class RobotSpawner(Tower):

    def __init__(self, character, color, name, description, robot_producer):
        super().__init__(character, color, name, description)
        self.robot_producer = robot_producer
        self._my_robot = robot_producer()
        self.build_countup = 0

    def get_base_stats(self):
        res = super().get_base_stats()
        return res

    def act(self, world, state):
        my_xy = world.get_pos(self)

        if self._my_robot is None or self._my_robot.is_dead():
            self.build_countup += 1
            actions_per_build = configs.target_fps / self.get_stat_value(worlds.StatTypes.BUILD_SPEED)
            ticks_per_build = self.ticks_per_action()
            if self.build_countup >= ticks_per_build:
                self._my_robot = self.robot_producer()
                world.set_pos(self._my_robot, my_xy)
                self.build_countup = 0
                # TODO play sound for building robot
        elif self._my_robot not in world:
            world.set_pos(self._my_robot, my_xy)
            # TODO play sound for building robot
        else:
            robot_xy = world.get_pos(self._my_robot)
            if robot_xy == my_xy:
                # charge the robot
                self._my_robot.add_charge(self.get_stat_value(worlds.StatTypes.CHARGE_RATE))
                # TODO play sound for charging robot


class BuildBotSpawner(RobotSpawner):

    def __init__(self):
        super().__init__("B", colors.YELLOW, "Build-Bot Factory",
                         "A tower that creates Build-Bots.", lambda: BuildBot())

    def get_base_stats(self):
        res = super().get_base_stats()
        return res


class MineBotSpawner(RobotSpawner):

    def __init__(self):
        super().__init__("M", colors.MID_GRAY, "Mine-Bot Factory",
                         "A tower that creates Mine-Bots.", lambda: MineBot())

    def get_base_stats(self):
        res = super().get_base_stats()
        return res


class ScavengerBotSpawner(RobotSpawner):

    def __init__(self):
        super().__init__("S", colors.GREEN, "Scavenger-Bot Factory",
                         "A tower that creates Scavenger-Bots.", lambda: ScavengerBot())

    def get_base_stats(self):
        res = super().get_base_stats()
        return res


class Agent(worlds.Entity):

    def __init__(self, character, color, name, description):
        super().__init__(character, color, name, description)

    def wander(self, world, state):
        xy = world.get_pos(self)
        ns = [n for n in util.Utils.neighbors(xy[0], xy[1])]
        random.shuffle(ns)
        for n in ns:
            if world.can_move_to(self, n):
                world.set_pos(self, n)
                return True
        return False

    def act(self, world, state):
        self.wander(world, state)


class Robot(Agent):

    def __init__(self, character, color, name, description):
        super().__init__(character, color, name, description)

    def is_robot(self):
        return True


class BuildBot(Robot):

    def __init__(self):
        super().__init__("☻", colors.YELLOW, "Build-Bot", "A robot that builds (and sells) towers.")

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.APS] = 2

        return res


class MineBot(Robot):

    def __init__(self):
        super().__init__("☻", colors.MID_GRAY, "Mine-Bot", "A robot that can mine resources.")


class ScavengerBot(Robot):

    def __init__(self):
        super().__init__("☻", colors.GREEN, "Scavenger-Bot", "A robot that collects and delivers gold.")


class Enemy(Agent):

    def __init__(self, character, color, base_stats, name, description):
        self._base_stats = base_stats
        super().__init__(character, color, name, description)

    def act(self, world, state):
        heart_pts = [world.get_pos(h) for h in world.all_hearts()]
        if len(heart_pts) > 0:
            best_path = find_best_path_to(self, world, heart_pts,
                                          or_adjacent_to=False,
                                          action_provider=lambda xy: AttackAndMoveAction(xy))
            if best_path is not None and len(best_path) > 0:
                best_path[0].perform(self, world)
                return
        self.wander(world, state)

    def get_base_stats(self):
        res = {}
        for s in self._base_stats:
            res[s] = self._base_stats[s]
        for s in worlds.ALL_STAT_TYPES:
            if s not in res:
                res[s] = s.default_val
        return res

    def is_enemy(self):
        return True


class EnemySpawnZone(worlds.Entity):

    def __init__(self):
        super().__init__("x", colors.DARK_RED, "Enemy Spawn Zone",
                         "Cannot build here.\nEnemies are invincible while standing here.")

    def is_decoration(self):
        return True

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 0
        res[worlds.StatTypes.APS] = 0.25
        return res

    def act(self, world, state):
        xy = world.get_pos(self)
        if len([e for e in world.all_entities_in_cell(xy, cond=lambda _e: _e.is_enemy())]) == 0:
            new_enemy = EnemyFactory.generate_random_enemies(random.randint(0, 4), random.randint(0, 25), n=1)[0]
            world.set_pos(new_enemy, xy)


class RockTower(Tower):

    def __init__(self):
        super().__init__("▒", colors.DARK_GRAY, "Rock", "A large rock. Can be mined for stone.")

    def get_upgrades(self):
        return [GoldOreTower()]


class WallTower(Tower):

    def __init__(self):
        super().__init__("█", colors.LIGHT_GRAY, "Wall", "An impassible wall.")

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 1
        return res

    def get_upgrades(self):
        return [DoorTower()]


class DoorTower(Tower):

    def __init__(self):
        super().__init__("◘", colors.LIGHT_GRAY, "Door", "A door that only bots can pass through.")

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 2
        return res


class GoldOreTower(Tower):

    def __init__(self):
        super().__init__("▒", colors.DARK_YELLOW, "Gold Ore", "A rock with veins of gold.\nCan be mined for stone and gold.")

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 1
        return res


class BuildMarker(worlds.Entity):

    def __init__(self, target):
        super().__init__(target.get_char(), colors.WHITE, target.get_name(), target.get_description())
        self.target = target

    def is_decoration(self):
        return True

    def is_build_marker(self):
        return True

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 0
        return res


class GunTower(Tower):

    def __init__(self):
        super().__init__("G", colors.WHITE, "Gun Tower", "A basic tower that shoots enemies.")


class WeaknessTower(Tower):

    def __init__(self):
        super().__init__("W", colors.BLUE, "Weakness Tower",
                         "A tower that weakens enemies and makes them\ntake more damage.")


class SlowTower(Tower):

    def __init__(self):
        super().__init__("S", colors.DARK_PURPLE, "Slowing Tower",
                         "A tower that slows enemies.")


class PoisonTower(Tower):

    def __init__(self):
        super().__init__("P", colors.PURPLE, "Poison Tower",
                         "A tower that poisons enemies.")


class ExplosionTower(Tower):

    def __init__(self):
        super().__init__("E", colors.ORANGE, "Explosion Tower",
                         "A tower that deals damage to all enemies\nwithin its radius.")


class EnemyFactory:

    EASY_ENEMIES = "abcdefghijklmnopqrstuvwxyz"
    MEDIUM_ENEMIES = "üéâäàåçêëèïîìæôöòûùÿáíóúñ"
    HARD_ENEMIES = "αßΓπΣσµτΦΘΩδ∞φε∩≡"
    LEGENDARY_ENEMIES = "£¥₧ƒÄÅÉÆÇ"

    ENEMY_LOOKUP = {}

    @staticmethod
    def generate_random_enemies(difficulty, pts, n=1):

        if difficulty == 0:
            name = random.choice(EnemyFactory.EASY_ENEMIES)
            adj = "A weak entity"
        elif difficulty == 1:
            name = random.choice(EnemyFactory.MEDIUM_ENEMIES)
            adj = "An entity"
        elif difficulty == 2:
            name = random.choice(EnemyFactory.HARD_ENEMIES)
            adj = "An otherworldly entity"
        else:
            name = random.choice(EnemyFactory.LEGENDARY_ENEMIES)
            adj = "A legendary entity"

        if name not in EnemyFactory.ENEMY_LOOKUP:
            stats = {
                worlds.StatTypes.HP: 30,
                worlds.StatTypes.APS: 1,
                worlds.StatTypes.DAMAGE: 3,
                worlds.StatTypes.ARMOR: 0,
                worlds.StatTypes.AGGRESSION: 0
            }
            # TODO generate stats
            EnemyFactory.ENEMY_LOOKUP[name] = stats
        stats = EnemyFactory.ENEMY_LOOKUP[name]

        res = []
        for _ in range(0, n):
            res.append(Enemy(name, colors.RED, stats, "Enemy", "{} known only as \"{}\".".format(adj, name)))

        return res


class Action:

    def __init__(self, xy):
        self.xy = xy

        # used to help calculate action sequences
        self.prev = None
        self.prev_cost = 0

    def get_xy(self):
        return self.xy

    def get_name(self):
        raise NotImplementedError()

    def get_cost(self, entity, world):
        """Roughly how many ticks it will take the actor to complete this action.
           Used for calculating sequences of actions."""
        return 0

    def get_total_cost(self, entity, world):
        return self.prev_cost + self.get_cost(entity, world)

    def is_possible(self, entity, world):
        return True

    def perform(self, entity, world):
        """returns: True if action was completed successfully.
                    False if action failed.
                    None if action is in progress."""
        raise NotImplementedError()


class MoveToAction(Action):

    def __init__(self, xy):
        super().__init__(xy)

    def get_name(self):
        return "MoveToAction(xy={})".format(self.xy)

    def get_cost(self, entity, world):
        return entity.ticks_per_action()

    def is_possible(self, entity, world):
        return world.can_move_to(entity, self.xy)

    def perform(self, entity, world):
        """returns: True if action was completed successfully.
                    False if action failed.
                    None if action is in progress."""
        cur_xy = world.get_pos(entity)
        if util.Utils.dist_manhattan(cur_xy, self.xy) <= 1 and world.can_move_to(entity, self.xy):
            world.set_pos(entity, self.xy)
            return True
        else:
            return False


class AttackAndMoveAction(MoveToAction):

    def __init__(self, xy):
        super().__init__(xy)

    def get_name(self):
        return "AttackAndMoveAction(xy={})".format(self.xy)

    def get_cost(self, entity, world):
        ticks_per_action = entity.ticks_per_action()
        res = 0
        for e in world.all_entities_in_cell(self.xy, cond=lambda e: e.get_solidity() != 0):
            cur_hp = e.get_stat_value(worlds.StatTypes.HP)
            dmg = entity.calc_damage_against(e)
            ramp = entity.get_stat_value(worlds.StatTypes.RAMPAGE)

            # calculating how many attacks it'll take to kill this thing
            if ramp <= 0 and dmg == 0:
                x = cur_hp * 999  # looks like we can't break it
            elif ramp == 0:
                x = math.ceil(cur_hp / dmg)
            else:
                a = (ramp / 2)
                b = (dmg - ramp / 2)
                c = -cur_hp
                x = (-b + math.sqrt(b*b - 4*a*c)) / 2*a

            aggression_mult = e.get_aggression_discount()

            res += int(math.ceil(x) * ticks_per_action * aggression_mult)

        return res + super().get_cost(entity, world)  # cost to move afterwards

    def is_possible(self, entity, world):
        return True

    def perform(self, entity, world):
        cur_xy = world.get_pos(entity)
        if util.Utils.dist_manhattan(cur_xy, self.xy) <= 1:
            if world.can_move_to(entity, self.xy):
                return super().perform(entity, world)
            else:
                ents_blocking = [e for e in world.all_entities_in_cell(self.xy, cond=lambda e: e.get_solidity() != 0)]
                if len(ents_blocking) == 0:
                    # can't move there and there's nothing there?
                    # Must be at the edge of the world or something.
                    return False
                else:
                    to_attack = ents_blocking[int(random.random() * len(ents_blocking))]
                    entity.give_damage_to(to_attack)
                    return None
        else:
            return False


def find_best_path_to(entity, world, endpoints, or_adjacent_to=False, action_provider=lambda xy: MoveToAction(xy)):
    final_action = _find_best_path_helper(entity, world, endpoints, or_adjacent_to=or_adjacent_to,
                                          action_provider=action_provider)

    if final_action is None:
        return None
    else:
        res = [final_action]
        action = final_action.prev
        while action is not None:
            res.append(action)
            action = action.prev
        res.reverse()
        return res


def _find_best_path_helper(entity, world, endpoints, or_adjacent_to=False, action_provider=lambda xy: MoveToAction(xy)):
    if len(endpoints) == 0:
        raise ValueError("endpoints is empty")
    endpoints = set(endpoints)
    if or_adjacent_to:
        for pt in endpoints:
            for n in util.Utils.neighbors(pt[0], pt[1]):
                endpoints.add(n)
    start_xy = world.get_pos(entity)
    seen_pts = set()
    seen_pts.add(start_xy)

    q = []
    i = 0  # tiebreaker
    for n in util.Utils.rand_neighbors(start_xy):
        seen_pts.add(n)
        move_action = action_provider(n)
        if move_action.is_possible(entity, world):
            item = (move_action.get_cost(entity, world), i, move_action)
            heapq.heappush(q, item)
            i += 1

    while len(q) > 0:
        cost, _, action = heapq.heappop(q)
        if action.get_xy() in endpoints:
            return action  # we did it
        else:
            for n in util.Utils.rand_neighbors(action.get_xy()):
                if n not in seen_pts:
                    seen_pts.add(n)
                    move_action = action_provider(n)
                    move_action.prev_cost = cost
                    move_action.prev = action
                    if move_action.is_possible(entity, world):
                        new_item = (move_action.get_total_cost(entity, world), i, move_action)
                        heapq.heappush(q, new_item)
                        i += 1

    return None  # no way to do it


def get_towers_in_shop():
    return [
        BuildBotSpawner(),
        MineBotSpawner(),
        ScavengerBotSpawner(),
        GunTower(),
        ExplosionTower(),
        WeaknessTower(),
        SlowTower(),
        PoisonTower(),
        WallTower()
    ]

