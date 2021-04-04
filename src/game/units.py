import src.game.worlds as worlds
import src.game.colors as colors
import src.utils.util as util
import random


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
        super().__init__("♥", colors.RED, "Energy Crystal", "Protect this tower at all costs!")

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
            ticks_per_build = self.ticks_per_action(self.get_stat_value(worlds.StatTypes.BUILD_SPEED))
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
                         "A tower that creates and charges Build-Bots.", lambda: BuildBot())

    def get_base_stats(self):
        res = super().get_base_stats()
        return res


class MineBotSpawner(RobotSpawner):

    def __init__(self):
        super().__init__("M", colors.MID_GRAY, "Mine-Bot Factory",
                         "A tower that creates and charges Mine-Bots.", lambda: MineBot())

    def get_base_stats(self):
        res = super().get_base_stats()
        return res


class ScavengerBotSpawner(RobotSpawner):

    def __init__(self):
        super().__init__("S", colors.GREEN, "Scavenger-Bot Factory",
                         "A tower that creates and charges Scavenger-Bots.", lambda: ScavengerBot())

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
        super().__init__("☻", colors.YELLOW, "Build-Bot", "A robot that builds and destroys towers.")

    def get_base_stats(self):
        res = super().get_base_stats()
        res[worlds.StatTypes.APS] = 2

        return res


class MineBot(Robot):

    def __init__(self):
        super().__init__("☻", colors.MID_GRAY, "Mine-Bot", "A robot that can mine resources.")


class ScavengerBot(Robot):

    def __init__(self):
        super().__init__("☻", colors.GREEN, "Scavenger-Bot", "A robot that collects gold from the battlefield.")


class Enemy(Agent):

    def __init__(self, character, color, base_stats, name, description):
        self._base_stats = base_stats
        super().__init__(character, color, name, description)

    def act(self, world, state):
        self.wander(world, state)

    def get_base_stats(self):
        return self._base_stats

    def is_enemy(self):
        return True


class EnemySpawnZone(worlds.Entity):

    def __init__(self):
        super().__init__("x", colors.DARK_RED, "Enemy Spawn Zone",
                         "Cannot build here. Enemies are invincible while standing here.")

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
        super().__init__("▒", colors.DARK_GRAY, "Rock", "A large rock.")

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
        super().__init__("▒", colors.DARK_YELLOW, "Gold Ore", "A rock with veins of gold. Can be mined by Mine-Bots.")

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
                         "A tower that weakens enemies and makes them take more damage.")


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
                         "A tower that deals damage to all enemies within its radius.")


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
        elif difficulty == 1:
            name = random.choice(EnemyFactory.MEDIUM_ENEMIES)
        elif difficulty == 2:
            name = random.choice(EnemyFactory.HARD_ENEMIES)
        else:
            name = random.choice(EnemyFactory.LEGENDARY_ENEMIES)

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
            res.append(Enemy(name, colors.RED, stats, "Enemy", "An otherworldly entity known only as \"{}\".".format(name)))

        return res


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

