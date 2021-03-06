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
        res[worlds.StatTypes.BUY_PRICE] = 25
        res[worlds.StatTypes.SELL_PRICE] = 15
        res[worlds.StatTypes.STONE_PRICE] = 5
        return res

    def get_stone_cost(self, world):
        base_cost = super().get_stone_cost(world)
        if base_cost > 0:
            cnt = sum([1 for twr in world.all_towers() if twr.get_name() == self.get_name()])
            cnt += sum([1 for bm in world.all_build_markers() if (bm.is_new_build_marker() and bm.target.get_name() == self.get_name())])
            return min(99, base_cost + cnt)
        else:
            return base_cost

    def get_shop_icon(self):
        return self.character

    def is_tower(self):
        return True

    def get_upgrades(self):
        return []


class HeartTower(Tower):

    def __init__(self):
        super().__init__("♦", colors.CYAN, "Energy Crystal",
                         "Protect this tower at all costs!\n" +
                         "Gold and stones are delivered here.")

    def get_base_color(self):
        pcnt_hp = util.Utils.bound(self.get_hp() / self.get_max_hp(), 0, 1)
        dark = colors.BLACK
        return util.Utils.linear_interp(self.base_color, dark, (1 - pcnt_hp))

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.REPAIRABLE] = 0
        res[worlds.StatTypes.HP] = 100
        res[worlds.StatTypes.SOLIDITY] = 1
        res[worlds.StatTypes.SELL_PRICE] = -1
        return res

    def is_heart(self):
        return True


class RobotSpawner(Tower):

    def __init__(self, character, color, name, description, robot_producer):
        super().__init__(character, color, name, description)
        self.robot_producer = robot_producer
        self._my_robot = None
        self.build_countup = 0
        self.robots_produced = 0

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 2
        return res

    def get_shop_icon(self):
        return super().get_shop_icon() + "/☻"

    def can_charge(self, entity):
        return entity.get_name() == self.robot_producer().get_name()

    def is_spawner(self):
        return True

    def act(self, world, state):
        my_xy = world.get_pos(self)

        if self._my_robot is None or self._my_robot.is_dead() or world.get_pos(self._my_robot) is None:
            self.build_countup += 1
            ticks_per_build = self.ticks_per_action()
            if self.build_countup >= ticks_per_build or self.robots_produced == 0:
                self._my_robot = self.robot_producer()
                world.set_pos(self._my_robot, my_xy)
                self.build_countup = 0
                self.robots_produced += 1
                # TODO play sound for building robot
        else:
            robot_xy = world.get_pos(self._my_robot)
            if robot_xy == my_xy:
                # charge the robot
                self._my_robot.add_charge(self.get_stat_value(worlds.StatTypes.CHARGE_RATE))
                # TODO play sound for charging robot


class BuildBotSpawner(RobotSpawner):

    def __init__(self):
        super().__init__("B", colors.GREEN, "Build-Bot Factory",
                         "A tower that creates Build-Bots.", lambda: BuildBot())

    def get_shop_icon(self):
        return "Blder/☻"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.BUY_PRICE] = 120
        res[worlds.StatTypes.SELL_PRICE] = 10
        return res


class MineBotSpawner(RobotSpawner):

    def __init__(self):
        super().__init__("M", colors.MID_GRAY, "Mine-Bot Factory",
                         "A tower that creates Mine-Bots.", lambda: MineBot())

    def get_shop_icon(self):
        return "Miner/☻"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.BUY_PRICE] = 150
        res[worlds.StatTypes.SELL_PRICE] = 20
        return res


class ScavengerBotSpawner(RobotSpawner):

    def __init__(self):
        super().__init__("S", colors.YELLOW, "Scavenger-Bot Factory",
                         "A tower that creates Scavenger-Bots.", lambda: ScavengerBot())

    def get_shop_icon(self):
        return "Scvgr/☻"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.BUY_PRICE] = 200
        res[worlds.StatTypes.SELL_PRICE] = 50
        return res


class Agent(worlds.Entity):

    def __init__(self, character, color, name, description):
        super().__init__(character, color, name, description)

        self.carrying_item = None

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 0
        return res

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

    def draw(self, xy, screen, mode=None):
        super().draw(xy, screen, mode=mode)

        if self.carrying_item is not None:
            screen.add(xy, self.carrying_item.get_char(), color=self.carrying_item.get_color())


class Robot(Agent):

    def __init__(self, character, color, name, description):
        super().__init__(character, color, name, description)
        self.current_path = None
        self.charge = self.get_stat_value(worlds.StatTypes.MAX_CHARGE)

    def set_item_carrying(self, e):
        self.carrying_item = e

    def get_item_carrying(self):
        return self.carrying_item

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.MAX_CHARGE] = 64
        res[worlds.StatTypes.APS] = 2.5
        return res

    def get_char(self):
        if self.character == "☻":
            return "☺" if self.charge <= 0 else "☻"

    def is_robot(self):
        return True

    def get_charging_station_locations(self, world, state):
        return [world.get_pos(s) for s in world.all_spawners() if s.can_charge(self)]

    def get_goal_locations(self, world, state):
        return []

    def try_to_do_goal_action(self, world, state):
        xy = world.get_pos(self)
        if self.charge < self.get_max_charge():
            for ent in world.all_entities_in_cell(xy, cond=lambda e: e.is_spawner() and e.can_charge(self)):
                self.add_charge(ent.get_stat_value(worlds.StatTypes.CHARGE_RATE))
                if self.charge >= self.get_max_charge():
                    pass  # TODO sound for max charge
                else:
                    pass  # TODO sound for charging
                return True

    def get_path_to_charging_station(self, from_xy, world, state):
        locs = self.get_charging_station_locations(world, state)
        return find_best_path_to(self, world, locs, start=from_xy, or_adjacent_to=False)

    def get_path_to_goal(self, from_xy, world, state):
        locs = self.get_goal_locations(world, state)
        return find_best_path_to(self, world, locs, start=from_xy, or_adjacent_to=False)

    def act(self, world, state):
        did_something = False
        if self.current_path is not None and len(self.current_path) > 0:
            next_step = self.current_path[0]
            res = next_step.perform(self, world)
            if res is False:
                # we got blocked by something, abort path
                self.current_path = None
            elif res is True:
                self.current_path.pop(0)
            else:
                pass  # the movement is in progress?
            did_something = True
            self.charge -= 1
        else:
            self.current_path = None
            if self.try_to_do_goal_action(world, state):
                did_something = True
            else:
                if self.charge > 0:
                    path_to_goal = self.get_path_to_goal(world.get_pos(self), world, state)
                    if path_to_goal is not None and len(path_to_goal) < self.charge - 1:
                        # we're going to attempt a goal
                        self.current_path = path_to_goal

                if self.current_path is None:
                    path_to_charging_station = self.get_path_to_charging_station(world.get_pos(self), world, state)
                    self.current_path = path_to_charging_station

        if self.current_path is None and not did_something:
            # can't find a path to the goal or a charging station, just wander.
            self.wander(world, state)
            self.charge -= 1

        if self.charge < 0:
            self.charge = 0


class BuildBot(Robot):

    def __init__(self):
        super().__init__("☻", colors.GREEN, "Build-Bot", "A robot that builds (and sells) towers.")

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.MAX_CHARGE] = 64
        res[worlds.StatTypes.APS] = 2.5
        return res

    def get_goal_locations(self, world, state):
        markers = [world.get_pos(b) for b in world.all_build_markers()]
        return [x for x in world.empty_cells_adjacent_to(markers)]

    def try_to_do_goal_action(self, world, state):
        xy = world.get_pos(self)
        for n in util.Utils.rand_neighbors(xy):
            for bm in world.all_entities_in_cell(n, cond=lambda e: e.is_build_marker()):
                if bm.activate(world, state):
                    return True
        return super().try_to_do_goal_action(world, state)


class MineBot(Robot):

    def __init__(self):
        super().__init__("☻", colors.MID_GRAY, "Mine-Bot", "A robot that can mine resources.")

    def get_goal_locations(self, world, state):
        if self.carrying_item is not None:
            # deliver rock to hearts
            return [xy for xy in world.empty_cells_adjacent_to([world.get_pos(h) for h in world.all_hearts()])]
        else:
            # mine more rocks
            stone_locs = [world.get_pos(e) for e in world.all_stone_items()]
            rock_locs = world.empty_cells_adjacent_to([world.get_pos(e) for e in world.all_active_rocks()], empty_for=self)
            stone_locs.extend(rock_locs)
            return stone_locs

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.MAX_CHARGE] = 72
        res[worlds.StatTypes.APS] = 1.5
        return res

    def try_to_do_goal_action(self, world, state):
        xy = world.get_pos(self)
        if self.carrying_item is None:
            for e in world.all_entities_in_cell(xy, cond=lambda e: e.is_stone_item()):
                self.set_item_carrying(e)
                world.remove(e)
                # TODO sound for picking up a stone
                return True
        else:
            for _ in world.all_entities_adjacent_to(xy, cond=lambda e: e.is_heart()):
                state.score_item(self.carrying_item)
                self.carrying_item = None
                return True

        for n in util.Utils.rand_neighbors(xy):
            for ent in world.all_entities_in_cell(n, cond=lambda e: e.is_rock() and e.is_active()):
                return ent.mine(world, state)

        return super().try_to_do_goal_action(world, state)


class ScavengerBot(Robot):

    def __init__(self):
        super().__init__("☻", colors.YELLOW, "Scavenger-Bot", "A robot that collects and delivers gold.")

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.MAX_CHARGE] = 64
        res[worlds.StatTypes.APS] = 2
        return res

    def get_goal_locations(self, world, state):
        if self.carrying_item is not None:
            # deliver gold to hearts
            return [xy for xy in world.empty_cells_adjacent_to([world.get_pos(h) for h in world.all_hearts()])]
        else:
            # pick up gold
            return [world.get_pos(e) for e in world.all_gold_ingots()]

    def try_to_do_goal_action(self, world, state):
        xy = world.get_pos(self)
        if self.carrying_item is None:
            for e in world.all_entities_in_cell(xy, cond=lambda e: e.is_gold_ingot()):
                self.set_item_carrying(e)
                world.remove(e)
                # TODO sound for picking up a stone
                return True
        else:
            for _ in world.all_entities_adjacent_to(xy, cond=lambda e: e.is_heart()):
                state.score_item(self.carrying_item)
                self.carrying_item = None
                return True
        return False


class GoldIngot(worlds.Entity):

    def __init__(self, value):
        self.value = value
        super().__init__("$", colors.DARK_YELLOW, "Gold Bar (${})".format(self.value),
                         "A valuable piece of gold.\nCan be delivered to an energy crystal.")

    def is_gold_ingot(self):
        return True

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 0
        res[worlds.StatTypes.SELL_PRICE] = self.value
        return res


class StoneItem(worlds.Entity):

    def __init__(self):
        super().__init__("•", colors.LIGHT_GRAY, "Piece of Stone",
                         "A piece of stone, used for building.\nCan be delivered to an energy crystal.")

    def is_stone_item(self):
        return True

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 0
        return res


class Enemy(Agent):

    def __init__(self, character, color, base_stats, name, description):
        self._base_stats = base_stats
        super().__init__(character, color, name, description)
        self.current_path = []  # stored in reverse order

    def forget_path(self):
        self.current_path = []

    def act(self, world, state):
        if len(self.current_path) > 0:
            res = self.current_path[-1].perform(self, world)
            if res is True:
                self.current_path.pop(-1)
            elif res is None:
                pass  # we're attacking something
            else:
                self.current_path = []  # path got interrupted?
        else:
            heart_pts = [world.get_pos(h) for h in world.all_hearts()]
            if len(heart_pts) > 0:
                best_path = find_best_path_to(self, world, heart_pts,
                                              or_adjacent_to=False,
                                              action_provider=lambda xy: AttackAndMoveAction(xy))
                if best_path is None:
                    print("WARN: failed to find path to crystals: {}".format(self))
                    self.wander(world, state)
                else:
                    best_path.reverse()
                    self.current_path = best_path
            else:
                self.wander(world, state)

        status_colors = []
        if self.is_weakened():
            status_colors.append(colors.DARK_BLUE)
            self.set_stat_value(worlds.StatTypes.WEAKENED, max(0, self.get_stat_value(worlds.StatTypes.WEAKENED) - 1))
        if self.is_slowed():
            status_colors.append(colors.PURPLE)
            self.set_stat_value(worlds.StatTypes.SLOWED, max(0, self.get_stat_value(worlds.StatTypes.SLOWED) - 1))
        if self.is_poisoned():
            status_colors.append(colors.DARK_PURPLE)
            self.set_stat_value(worlds.StatTypes.POISONED, max(0, self.get_stat_value(worlds.StatTypes.POISONED) - 1))
            self.take_damage_from(2, None)

        if len(status_colors) > 0:
            self.perturb_color(random.choice(status_colors), duration=30)

    def get_base_stats(self):
        res = {}
        for s in self._base_stats:
            res[s] = self._base_stats[s]
        super_stats = super().get_base_stats()
        for s in super_stats:
            if s not in res:
                res[s] = super_stats[s]
        return res

    def animate_damage_from(self, other):
        self.perturb_color(colors.WHITE, 10)
        # TODO noise for taking damage

    def on_death(self, world, scene):
        price = self.get_sell_price()
        xy = world.get_pos(self)
        if price > 0:
            added_gold = False
            for gold in world.all_entities_in_cell(xy, cond=lambda e: e.is_gold_ingot()):
                old_price = gold.get_sell_price()
                gold.set_stat_value(worlds.StatTypes.SELL_PRICE, old_price + price)
                added_gold = True
                break
            if not added_gold:
                world.set_pos(GoldIngot(price), xy)

        direct_reward = self.get_stat_value(worlds.StatTypes.DEATH_REWARD)
        if direct_reward > 0:
            scene.score_item(GoldIngot(direct_reward))

        scene.kills += 1

    def is_enemy(self):
        return True


class EnemySpawnZone(worlds.Entity):

    def __init__(self):
        super().__init__("x", colors.DARK_RED, "Enemy Spawn Zone",
                         "Cannot build here.\nEnemies are invincible while standing here.")

    def is_decoration(self):
        return True

    def is_spawn_zone(self):
        return True

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 0
        return res

    def act(self, world, state):
        pass


class RockTower(Tower):

    def __init__(self):
        super().__init__("▒", colors.LIGHT_GRAY, "Rock", "A large rock. Can be mined for stone.")
        self.deactivation_countdown = 0
        self.deactivation_period = 10
        self.mine_pcnt = 0.1

    def is_rock(self):
        return True

    def get_shop_icon(self):
        return "Rock"

    def get_base_color(self):
        return colors.LIGHT_GRAY if self.is_active() else colors.DARK_GRAY

    def is_active(self):
        return self.deactivation_countdown <= 0

    def act(self, world, state):
        if self.deactivation_countdown > 0:
            self.deactivation_countdown -= 1

    def mine(self, world, state):
        if not self.is_active():
            return False
        else:
            if random.random() < self.mine_pcnt:
                xy = world.get_pos(self)
                ns = [n for n in world.empty_cells_adjacent_to(xy)]
                if len(ns) > 0:
                    n = random.choice(ns)
                    self.drop_resources_at(n, world, state)
                self.deactivation_countdown = self.deactivation_period
            else:
                pass  # TODO sound for failed mine
            return True

    def drop_resources_at(self, pos, world, state):
        world.set_pos(StoneItem(), pos)
        # TODO play sound for mining a rock

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.HP] = 200
        res[worlds.StatTypes.SOLIDITY] = 1
        res[worlds.StatTypes.APS] = 1
        res[worlds.StatTypes.STONE_PRICE] = 20
        return res

    def get_upgrades(self):
        return [GoldOreTower()]


class GoldOreTower(RockTower):

    def __init__(self):
        super().__init__()
        self.character = "▒"
        self.base_color = colors.DARK_YELLOW
        self.name = "Gold Ore"
        self.description = "A rock with veins of gold.\nCan be mined for stone and gold."

    def get_base_color(self):
        return colors.DARK_YELLOW if self.is_active() else colors.VERY_DARK_YELLOW

    def get_upgrades(self):
        return []


class WallTower(Tower):

    def __init__(self):
        super().__init__("█", colors.LIGHT_GRAY, "Wall", "An impassible wall.\nCan be upgraded to a door.")

    def get_shop_icon(self):
        return "Wall"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 1
        res[worlds.StatTypes.HP] = 250
        res[worlds.StatTypes.STONE_PRICE] = 15
        res[worlds.StatTypes.BUY_PRICE] = 10
        res[worlds.StatTypes.SELL_PRICE] = 0
        res[worlds.StatTypes.ARMOR] = 5
        return res

    def get_upgrades(self):
        return [DoorTower()]


class DoorTower(Tower):

    def __init__(self):
        super().__init__("◘", colors.LIGHT_GRAY, "Door", "A door that only bots can pass through.")

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 2
        res[worlds.StatTypes.STONE_PRICE] = 20
        res[worlds.StatTypes.BUY_PRICE] = 50
        res[worlds.StatTypes.SELL_PRICE] = 20
        return res


class BuildMarker(worlds.Entity):

    def __init__(self, target):
        super().__init__(self.get_marker_symbol(), colors.WHITE, target.get_name(), target.get_description())
        self.target = target

        self.activation_count = 0

    def activate(self, world, state):
        """Build-bots call this to build stuff"""
        if self.activation_count >= self.n_activations_required():
            self.perform_action(world, state)
        else:
            self.activation_count += 1
            # TODO sound for building
        return True

    def n_activations_required(self):
        return self.target.get_build_time()

    def perform_action(self, world, state):
        raise NotImplementedError()

    def refund(self, world, state):
        pass

    def get_marker_symbol(self):
        raise NotImplementedError()

    def get_description(self):
        res = self.target.get_description()
        return res + "\n(Waiting for Build-Bot)"

    def is_build_marker(self):
        return True

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.SOLIDITY] = 0
        return res

    def is_new_build_marker(self):
        return False


class BuildNewMarker(BuildMarker):
    def __init__(self, target, gold_paid, stone_paid):
        super().__init__(target)
        self.scene_ticks = 0
        self.gold_paid = gold_paid
        self.stone_paid = stone_paid

    def is_new_build_marker(self):
        return True

    def perform_action(self, world, state):
        xy = world.get_pos(self)

        # surely this won't cause problems~
        to_remove = [e for e in world.all_entities_in_cell(xy)]
        for e in to_remove:
            world.remove(e)

        world.set_pos(self.target, xy)

    def refund(self, world, state):
        state.cash += self.gold_paid
        state.stones += self.stone_paid
        # TODO play sound for undoing a build command

    def update(self, world, state):
        super().update(world, state)
        self.scene_ticks = state.state.scene_ticks

    def get_marker_symbol(self):
        return "!"

    def get_char(self):
        if (self.scene_ticks // (configs.target_fps // 3) % 2) == 0:
            return self.target.get_char()
        else:
            return self.get_marker_symbol()


class SellMarker(BuildMarker):

    def __init__(self, target, price):
        super().__init__(target)
        self.price = price

    def get_marker_symbol(self):
        return "$"

    def perform_action(self, world, state):
        state.cash += self.price
        world.remove(self.target)
        world.remove(self)
        # TODO sound for selling


class UpgradeMarker(BuildMarker):

    def __init__(self, old_tower, new_tower):
        super().__init__(old_tower)
        self.new_tower = new_tower

    def refund(self, world, state):
        gold_refund = self.new_tower.get_gold_cost()
        state.cash += gold_refund

    def get_marker_symbol(self):
        return "↑"

    def perform_action(self, world, state):
        xy = world.get_pos(self)
        world.remove(self.target)
        world.remove(self)
        world.set_pos(self.new_tower, xy)
        # TODO sound for upgrading


class AttackTower(Tower):

    def __init__(self, character, color, name, desc):
        super().__init__(character, color, name, desc)

    def get_enemies_in_range(self, world):
        r = self.get_stat_value(worlds.StatTypes.RANGE)
        xy = world.get_pos(self)
        return [e for e in world.all_entities_in_range(xy, r, cond=lambda _e: _e.is_enemy())]

    def get_enemies_to_hit(self, world, scene):
        enemies = self.get_enemies_in_range(world)
        if len(enemies) > 0:
            return [random.choice(enemies)]
        else:
            return []

    def is_attack_tower(self):
        return True

    def animate(self, world, scene):
        self.perturb_color(colors.WHITE, duration=10)

    def act(self, world, state):
        hit_someone = False
        for e in self.get_enemies_to_hit(world, state):
            self.give_damage_to(e)
            hit_someone = True

        if hit_someone:
            self.animate(world, state)

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 2
        res[worlds.StatTypes.BUY_PRICE] = 25
        res[worlds.StatTypes.SELL_PRICE] = 15
        res[worlds.StatTypes.STONE_PRICE] = 5
        res[worlds.StatTypes.APS] = 2
        res[worlds.StatTypes.HP] = 75
        res[worlds.StatTypes.DAMAGE] = 5
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        return res


class GunTower(AttackTower):

    def __init__(self):
        super().__init__("G", colors.BROWN, "Gun Tower", "A basic tower that shoots enemies.")

    def get_shop_icon(self):
        return "Gun Twr"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 3
        res[worlds.StatTypes.BUY_PRICE] = 25
        res[worlds.StatTypes.SELL_PRICE] = 15
        res[worlds.StatTypes.STONE_PRICE] = 2
        res[worlds.StatTypes.APS] = 2
        res[worlds.StatTypes.HP] = 50
        res[worlds.StatTypes.DAMAGE] = 15
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        return res

    def get_upgrades(self):
        return [GunTowerII()]


class GunTowerII(AttackTower):

    def __init__(self):
        super().__init__("G", colors.LIGHT_BROWN, "Gun Tower II", "A tower that shoots enemies.")

    def get_shop_icon(self):
        return "Gun Twr"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 3
        res[worlds.StatTypes.BUY_PRICE] = 225
        res[worlds.StatTypes.SELL_PRICE] = 180
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.APS] = 2.5
        res[worlds.StatTypes.HP] = 75
        res[worlds.StatTypes.DAMAGE] = 18
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        return res

    def get_upgrades(self):
        return [GunTowerIII()]


class GunTowerIII(AttackTower):

    def __init__(self):
        super().__init__("G", colors.CYAN, "Gun Tower III", "A strong tower that shoots enemies.")

    def get_shop_icon(self):
        return "Gun Twr"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 4
        res[worlds.StatTypes.BUY_PRICE] = 350
        res[worlds.StatTypes.SELL_PRICE] = 225
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.APS] = 2.7
        res[worlds.StatTypes.HP] = 125
        res[worlds.StatTypes.DAMAGE] = 23
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        return res


class WeaknessTower(AttackTower):

    def __init__(self):
        super().__init__("W", colors.BLUE, "Weakness Tower",
                         "A tower that weakens enemies and makes them\ntake more damage.")

    def get_shop_icon(self):
        return "Weak Twr"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 3
        res[worlds.StatTypes.BUY_PRICE] = 95
        res[worlds.StatTypes.SELL_PRICE] = 20
        res[worlds.StatTypes.STONE_PRICE] = 7
        res[worlds.StatTypes.APS] = 1.5
        res[worlds.StatTypes.HP] = 75
        res[worlds.StatTypes.DAMAGE] = 3
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        res[worlds.StatTypes.WEAKNESS_ON_HIT] = 10
        return res

    def get_upgrades(self):
        return [WeaknessTower2()]


class WeaknessTower2(AttackTower):

    def __init__(self):
        super().__init__("W", colors.LIGHT_BLUE, "Weakness Tower II",
                         "A tower that weakens enemies and makes them\ntake more damage.")

    def get_shop_icon(self):
        return "Weak Twr"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 4
        res[worlds.StatTypes.BUY_PRICE] = 250
        res[worlds.StatTypes.SELL_PRICE] = 150
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.APS] = 1.75
        res[worlds.StatTypes.HP] = 125
        res[worlds.StatTypes.DAMAGE] = 10
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        res[worlds.StatTypes.WEAKNESS_ON_HIT] = 15
        return res

    def get_upgrades(self):
        return [WeaknessTower3()]


class WeaknessTower3(AttackTower):

    def __init__(self):
        super().__init__("W", colors.CYAN, "Weakness Tower III",
                         "A tower that weakens enemies and makes them\ntake more damage.")

    def get_shop_icon(self):
        return "Weak Twr"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 4
        res[worlds.StatTypes.BUY_PRICE] = 450
        res[worlds.StatTypes.SELL_PRICE] = 250
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.APS] = 2.25
        res[worlds.StatTypes.HP] = 175
        res[worlds.StatTypes.DAMAGE] = 18
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        res[worlds.StatTypes.WEAKNESS_ON_HIT] = 25
        return res

    def get_upgrades(self):
        return []


class SlowTower(AttackTower):

    def __init__(self):
        super().__init__("S", colors.DARK_PURPLE, "Slowing Tower",
                         "A tower that slows enemies.\nCan be upgraded to poison enemies.")

    def get_shop_icon(self):
        return "Slow Twr"

    def get_upgrades(self):
        return [PoisonTower()]

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 3
        res[worlds.StatTypes.BUY_PRICE] = 60
        res[worlds.StatTypes.SELL_PRICE] = 70
        res[worlds.StatTypes.STONE_PRICE] = 9
        res[worlds.StatTypes.APS] = 1.75
        res[worlds.StatTypes.HP] = 75
        res[worlds.StatTypes.DAMAGE] = 5
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        res[worlds.StatTypes.SLOWNESS_ON_HIT] = 10
        return res


class PoisonTower(AttackTower):

    def __init__(self):
        super().__init__("P", colors.PURPLE, "Poison Tower",
                         "A tower that poisons enemies.")

    def get_shop_icon(self):
        return "Pois Twr"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 3
        res[worlds.StatTypes.BUY_PRICE] = 100
        res[worlds.StatTypes.SELL_PRICE] = 50
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.APS] = 2
        res[worlds.StatTypes.HP] = 100
        res[worlds.StatTypes.DAMAGE] = 3
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        res[worlds.StatTypes.POISON_ON_HIT] = 10
        res[worlds.StatTypes.SLOWNESS_ON_HIT] = 5
        return res

    def get_upgrades(self):
        return [BlightTower()]


class BlightTower(AttackTower):
    def __init__(self):
        super().__init__("B", colors.CYAN, "Blight Tower",
                         "A tower that poisons and slows enemies.")

    def get_shop_icon(self):
        return "Blgt Twr"

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 4
        res[worlds.StatTypes.BUY_PRICE] = 650
        res[worlds.StatTypes.SELL_PRICE] = 300
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.APS] = 2.5
        res[worlds.StatTypes.HP] = 150
        res[worlds.StatTypes.DAMAGE] = 12
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        res[worlds.StatTypes.POISON_ON_HIT] = 15
        res[worlds.StatTypes.SLOWNESS_ON_HIT] = 20
        return res


class ExplosionTower(AttackTower):

    def __init__(self):
        super().__init__("E", colors.ORANGE, "Explosion Tower",
                         "A tower that deals damage to all enemies\nwithin its radius.")

    def get_shop_icon(self):
        return "Expl Twr"

    def get_enemies_to_hit(self, world, scene):
        return self.get_enemies_in_range(world)

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 2
        res[worlds.StatTypes.BUY_PRICE] = 75
        res[worlds.StatTypes.SELL_PRICE] = 20
        res[worlds.StatTypes.STONE_PRICE] = 4
        res[worlds.StatTypes.APS] = 1.2
        res[worlds.StatTypes.HP] = 65
        res[worlds.StatTypes.DAMAGE] = 10
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        return res

    def get_upgrades(self):
        return [ExplosionTowerII()]


class ExplosionTowerII(AttackTower):

    def __init__(self):
        super().__init__("E", colors.LIGHT_ORANGE, "Explosion Tower II",
                         "A tower that deals damage to all enemies\nwithin its radius.")

    def get_shop_icon(self):
        return "Expl Twr"

    def get_enemies_to_hit(self, world, scene):
        return self.get_enemies_in_range(world)

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 3
        res[worlds.StatTypes.BUY_PRICE] = 170
        res[worlds.StatTypes.SELL_PRICE] = 120
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.APS] = 1.4
        res[worlds.StatTypes.HP] = 110
        res[worlds.StatTypes.DAMAGE] = 16
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        return res

    def get_upgrades(self):
        return [ExplosionTowerIII()]


class ExplosionTowerIII(AttackTower):

    def __init__(self):
        super().__init__("E", colors.CYAN, "Explosion Tower III",
                         "A tower that deals damage to all enemies\nwithin its radius.")

    def get_shop_icon(self):
        return "Expl Twr"

    def get_enemies_to_hit(self, world, scene):
        return self.get_enemies_in_range(world)

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.RANGE] = 4
        res[worlds.StatTypes.BUY_PRICE] = 450
        res[worlds.StatTypes.SELL_PRICE] = 200
        res[worlds.StatTypes.STONE_PRICE] = 0
        res[worlds.StatTypes.APS] = 1.6
        res[worlds.StatTypes.HP] = 170
        res[worlds.StatTypes.DAMAGE] = 20
        res[worlds.StatTypes.ARMOR] = 0
        res[worlds.StatTypes.SOLIDITY] = 1
        return res


class EnemySpawnController:

    def __init__(self):
        self.level = 1
        self._current_wave = []

    def get_wave(self):
        return self.level - 1

    def _gen_wave(self):

        pts = 3 + self.level
        if self.level <= 5:
            difficulty = 0
            n = 2 + self.level
        elif self.level % 20 == 0:
            difficulty = 3
            pts = pts * 2
            n = self.level // 2
        elif self.level % 10 == 0:
            difficulty = 2
            pts = int(pts * 1.5)
            n = 3 + self.level // 5
        elif self.level > 7 and random.random() < 0.5:
            difficulty = 1
            pts = int(pts * 1.25)
            n = 5 + self.level // 3
        else:
            difficulty = 0
            n = 8 + self.level // 2

        n_per_pulse = 1
        if self.level > 20 and random.random() < 0.25:
            n_per_pulse = 2
        elif self.level > 30 and random.random() < 0.25:
            n_per_pulse = 3
        elif self.level > 40 and random.random() < 0.25:
            n_per_pulse = 4
        elif self.level > 50 and random.random() < 0.25:
            n_per_pulse = 5

        max_pulse_delay = 4 * configs.target_fps
        min_pulse_delay = int(0.25 * configs.target_fps)
        max_level = 100
        pulse_delay = int(util.Utils.linear_interp(max_pulse_delay, min_pulse_delay, min(1.0, self.level / max_level)))
        pulse_delay += int(random.random() * configs.target_fps / 2)

        max_wave_delay = 8 * configs.target_fps
        end_of_wave_delay = int(util.Utils.linear_interp(max_wave_delay, min_pulse_delay, min(1.0, self.level / max_level)))

        pts = int(3 + self.level / 3 + self.level * self.level / 150)
        enemies = EnemyFactory.generate_random_enemies(difficulty, pts, n=n)

        print("INFO: Wave {} Enemy: {}".format(self.level, enemies[0].get_base_stats()))

        new_wave = []
        if self.level == 1:
            # 5 second delay at the start of the game
            new_wave.append(configs.target_fps * 6)

        while len(enemies) > 0:
            pulse = []
            for i in range(0, n_per_pulse):
                if len(enemies) > 0:
                    pulse.append(enemies.pop(-1))
            new_wave.append(pulse)
            if len(enemies) > 0:
                new_wave.append(pulse_delay)
        new_wave.append(end_of_wave_delay)
        new_wave.reverse()  # so that we can pop off the end
        self._current_wave = new_wave

    def update(self, world):
        if len(self._current_wave) == 0:
            self._gen_wave()
            self.level += 1
        else:
            cur_item = self._current_wave[-1]
            if isinstance(cur_item, int):
                if cur_item <= 0:
                    self._current_wave.pop(-1)
                else:
                    self._current_wave[-1] = cur_item - 1
            else:
                # it's a list of enemies
                spawn_pads = [world.get_pos(spw) for spw in world.all_spawn_zones()]
                if len(spawn_pads) >= len(cur_item):
                    spawn_locs = random.choices(spawn_pads, k=len(cur_item))
                else:
                    spawn_locs = [random.choice(spawn_pads) for _ in range(len(cur_item))]

                for i in range(len(cur_item)):
                    world.set_pos(cur_item[i], spawn_locs[i])
                self._current_wave.pop(-1)


class EnemyFactory:

    EASY_ENEMIES = "abcdefghijklmnopqrstuvwxyz"
    MEDIUM_ENEMIES = "üéâäàåçêëèïîìæôöòûùÿáíóúñ"
    HARD_ENEMIES = "αßΓπΣσµτΦΘΩδ∞φε∩≡"
    LEGENDARY_ENEMIES = "£¥₧ƒÄÅÉÆÇ"

    @staticmethod
    def generate_random_enemies(difficulty, pts, n=1):
        if difficulty == 0:
            name = random.choice(EnemyFactory.EASY_ENEMIES)
            adj = "A weak entity"
            reward = 3
            gold_drop_chance = 0.01
        elif difficulty == 1:
            name = random.choice(EnemyFactory.MEDIUM_ENEMIES)
            adj = "An entity"
            reward = 5
            gold_drop_chance = 0.05
        elif difficulty == 2:
            name = random.choice(EnemyFactory.HARD_ENEMIES)
            adj = "An otherworldly entity"
            reward = 10
            gold_drop_chance = 0.25
        else:
            name = random.choice(EnemyFactory.LEGENDARY_ENEMIES)
            adj = "A legendary entity"
            reward = 20
            gold_drop_chance = 1.0

        stats = {
            worlds.StatTypes.HP: 50,
            worlds.StatTypes.APS: 1.5,
            worlds.StatTypes.DAMAGE: 10,
            worlds.StatTypes.ARMOR: 0,
            worlds.StatTypes.AGGRESSION: 0,
            worlds.StatTypes.DEATH_REWARD: reward,
            worlds.StatTypes.VAMPRISM: 0,
            worlds.StatTypes.RAMPAGE: 1
        }

        increase_per_pt = {
            worlds.StatTypes.HP: 15,
            worlds.StatTypes.APS: 0.25,
            worlds.StatTypes.DAMAGE: 3,
            worlds.StatTypes.ARMOR: 1,
            worlds.StatTypes.AGGRESSION: 0.25,
            worlds.StatTypes.VAMPRISM: 10,
            worlds.StatTypes.RAMPAGE: 1,
        }

        for _ in range(0, pts // 3):
            stats[worlds.StatTypes.HP] += increase_per_pt[worlds.StatTypes.HP]

        max_vals = {
            worlds.StatTypes.APS: 4,
            worlds.StatTypes.AGGRESSION: 1.0,
            worlds.StatTypes.VAMPRISM: 80,
            worlds.StatTypes.RAMPAGE: 3,
        }

        for pt in range(pts):
            choices = [s for s in stats if (s in increase_per_pt and (s not in max_vals or stats[s] < max_vals[s]))]
            if len(choices) > 0:
                stat_to_inc = random.choice(choices)
                stats[stat_to_inc] += increase_per_pt[stat_to_inc]

        res = []
        for _ in range(0, n):
            stat_copy = stats.copy()

            if random.random() < gold_drop_chance:
                dropped_gold = random.randint(1, 5) * 10
                stat_copy[worlds.StatTypes.SELL_PRICE] = dropped_gold

            res.append(Enemy(name, colors.RED, stat_copy, "Enemy", "{} known only as \"{}\".".format(adj, name)))

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

    def __repr__(self):
        return "{}{}".format(type(self).__name__, self.get_xy())

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
                x = (-b + math.sqrt(b*b - 4*a*c)) / (2*a)

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


def find_best_path_to(entity, world, endpoints, start=None, or_adjacent_to=False, action_provider=lambda xy: MoveToAction(xy)):
    final_action = _find_best_path_helper(entity, world, endpoints, start=start, or_adjacent_to=or_adjacent_to,
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


def _find_best_path_helper(entity, world, endpoints, start=None, or_adjacent_to=False, action_provider=lambda xy: MoveToAction(xy)):
    if len(endpoints) == 0:
        return None
    endpoint_set = set(endpoints)
    if or_adjacent_to:
        for pt in endpoints:
            for n in util.Utils.neighbors(pt[0], pt[1]):
                endpoint_set.add(n)
    endpoints = endpoint_set
    start_xy = start if start is not None else world.get_pos(entity)
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
        lambda: BuildBotSpawner(),
        lambda: MineBotSpawner(),
        lambda: ScavengerBotSpawner(),
        None,
        lambda: GunTower(),
        lambda: ExplosionTower(),
        lambda: WeaknessTower(),
        lambda: SlowTower(),
        None,
        lambda: WallTower(),
        lambda: RockTower()
    ]

