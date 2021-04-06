import pygame
import src.game.ascii_screen as ascii_screen
import src.engine.sprites as sprites
import src.game.const as const
import src.engine.renderengine as renderengine
import src.engine.spritesheets as spritesheets
import src.game.colors as colors
import random
import math
import configs
import sys
import src.engine.inputs as inputs
import src.utils.textutils as textutils
import src.game.worlds as worlds
import src.utils.util as utils


class GameState:

    def __init__(self):
        self.screen = ascii_screen.AsciiScreen(const.W, const.H, bg=" ", bg_color=colors.DARK_GRAY)
        self.char_sprites = []
        for x in range(0, const.W):
            self.char_sprites.append([None] * const.H)

        # will be (9, 16) unless the sprite sheet is changed
        self.char_size = spritesheets.get_instance().get_sheet(spritesheets.DefaultFont.SHEET_ID).get_char("A").size()

        self.active_scene = TitleScene(self)
        self.next_scene = None

        self.scene_ticks = 0
        self.global_ticks = 0

        self.mouse_xy = None

    def get_active_scene(self):
        return self.active_scene

    def set_next_scene(self, next):
        self.next_scene = next

    def get_mouse_pos(self):
        """in ascii coords"""
        return self.mouse_xy

    def update(self):
        if self.next_scene is not None:
            self.active_scene = self.next_scene
            self.next_scene = None
            self.scene_ticks = 0

        self.mouse_xy = None
        if inputs.get_instance().mouse_in_window():
            mouse_pos = inputs.get_instance().mouse_pos()
            mouse_xy = self.to_ascii_coords(mouse_pos)
            if 0 <= mouse_xy[0] < const.W and 0 <= mouse_xy[1] < const.H:
                self.mouse_xy = mouse_xy

        self.active_scene.update()

        self._update_screen()
        self._update_sprites()
        self.global_ticks += 1
        self.scene_ticks += 1

    def _update_screen(self):
        self.screen.clear()
        self.active_scene.draw(self.screen)

    def to_ascii_coords(self, screen_pos):
        screen_size = renderengine.get_instance().get_game_size()
        root_xy = (screen_size[0] // 2 - (self.char_size[0] * const.W) // 2,
                   screen_size[1] // 2 - (self.char_size[1] * const.H) // 2)
        x = int((screen_pos[0] - root_xy[0]) / self.char_size[0])
        y = int((screen_pos[1] - root_xy[1]) / self.char_size[1])
        return (x, y)

    def _update_sprites(self):
        screen_size = renderengine.get_instance().get_game_size()
        root_xy = (screen_size[0] // 2 - (self.char_size[0] * const.W) // 2,
                   screen_size[1] // 2 - (self.char_size[1] * const.H) // 2)
        font_lookup = spritesheets.get_instance().get_sheet(spritesheets.DefaultFont.SHEET_ID)
        for y in range(0, const.H):
            for x in range(0, const.W):
                character, color = self.screen.item_at((x, y), tick=self.scene_ticks)
                pos = (root_xy[0] + x * self.char_size[0],
                       root_xy[1] + y * self.char_size[1])
                if self.char_sprites[x][y] is None:
                    self.char_sprites[x][y] = sprites.ImageSprite.new_sprite(const.TEXT_LAYER)

                char_model = font_lookup.get_char(character)

                self.char_sprites[x][y] = self.char_sprites[x][y].update(
                    new_x=pos[0],
                    new_y=pos[1],
                    new_color=color,
                    new_model=char_model)

    def all_sprites(self):
        for y in range(0, len(self.char_sprites[0])):
            for x in range(0, len(self.char_sprites)):
                yield self.char_sprites[x][y]


class Scene:

    def __init__(self, state):
        self.state = state

    def update(self):
        pass

    def draw(self, screen):
        pass


class TitleScene(Scene):

    def __init__(self, state):
        super().__init__(state)
        self.ascii_buffer = [None] * (const.W * const.H)

    def update(self):
        if inputs.get_instance().was_pressed(pygame.K_ESCAPE):
            print("Quitting game!")
            sys.exit()
        elif (inputs.get_instance().was_anything_pressed()
              or inputs.get_instance().mouse_was_pressed(1)
              or inputs.get_instance().mouse_was_pressed(3)):
            self.state.set_next_scene(InstructionsScene(self.state))

    def draw(self, screen: ascii_screen.AsciiScreen):
        cx, cy = (const.W // 2, const.H // 2)
        for x in range(0, const.W):
            for y in range(0, const.H):
                d = math.sqrt((cx - x) * (cx - x) + (cy - y) * (cy - y) * 2)
                if d < 20:
                    self.ascii_buffer[y * const.W + x] = None
                elif random.random() < 1 / (configs.target_fps * 2):
                    if random.random() > d / 300:
                        self.ascii_buffer[y * const.W + x] = None
                    else:
                        self.ascii_buffer[y * const.W + x] = (random.choice(const.ALL_CHARS), colors.rand_color())
                if self.ascii_buffer[y * const.W + x] is not None:
                    c, color = self.ascii_buffer[y * const.W + x]
                    screen.add_text((x, y), c, color=color)

        game_name = "ASCII Robot Tower Defense"
        xy = ((const.W - len(game_name)) // 2, const.H // 2 - 1)
        msg = "Press Any Key to Start"
        xy2 = ((const.W - len(msg)) // 2, xy[1] + 1)

        screen.add_text(xy, game_name, color=colors.rand_color(self.state.scene_ticks // 30))
        screen.add_text(xy2, msg, color=colors.rand_color(5 + self.state.scene_ticks // 30))

        rect_size = (max(len(game_name), len(msg)) + 2, 4)
        rect_text = textutils.ascii_rect(rect_size, color=colors.LIGHT_GRAY)
        screen.add_text((xy[0]-1, xy[1]-1), rect_text, ignore=" ")


class InstructionsScene(Scene):

    def __init__(self, state):
        super().__init__(state)
        import src.game.units as units
        crystal = units.HeartTower()
        buildbot = units.BuildBot()
        self.instructions = sprites.TextBuilder(color=colors.LIGHT_GRAY)
        self.instructions.addLine("Instructions:")
        self.instructions.addLine("1. Use the mouse to buy units.")
        self.instructions.add("2. You cannot build things directly;\n   only Build-Bots (")
        self.instructions.add(buildbot.get_char(), color=buildbot.get_base_color())
        self.instructions.addLine(") can build!")
        self.instructions.add("3. Use robots, towers, and walls to protect your ")
        self.instructions.add(crystal.get_char(), color=crystal.get_base_color())
        self.instructions.addLine("s!")
        self.instructions.add("4. When all ")
        self.instructions.add(crystal.get_char(), color=crystal.get_base_color())
        self.instructions.addLine("s are destroyed, the game is over.\n")
        self.instructions.add("             See how long you can last.")

        self.text_dims = self.instructions.get_dimensions()

    def update(self):
        if inputs.get_instance().was_pressed(pygame.K_ESCAPE):
            self.state.set_next_scene(TitleScene(self.state))
        elif self.state.scene_ticks > 7 and (inputs.get_instance().was_anything_pressed()
                                             or inputs.get_instance().mouse_was_pressed(1)
                                             or inputs.get_instance().mouse_was_pressed(3)):
            self.state.set_next_scene(InGameScene(self.state))

    def draw(self, screen):
        xy = ((const.W - self.text_dims[0]) // 2, (const.H - self.text_dims[1]) // 2)
        screen.add_text(xy, self.instructions)


class Button:

    def __init__(self, scene, rect):
        self.scene = scene
        self.rect = rect

    def is_active(self):
        return True

    def contains(self, xy):
        return utils.Utils.rect_contains(self.rect, xy)

    def draw(self, screen):
        pass

    def is_hovered(self):
        return self.scene.hovered_button is self

    def on_click(self):
        pass

    def get_associated_entity(self):
        return None


class ShopButton(Button):

    def __init__(self, tower_provider, scene, rect):
        super().__init__(scene, rect)
        self._tower_provider = tower_provider
        self._tower_example = tower_provider()

    def is_active(self):
        return True

    def get_gold_cost(self):
        return self._tower_example.get_stat_value(worlds.StatTypes.BUY_PRICE)

    def get_stone_cost(self):
        return self._tower_example.get_stat_value(worlds.StatTypes.STONE_PRICE)

    def can_afford(self):
        return self.scene.cash >= self.get_gold_cost() and self.scene.stones >= self.get_stone_cost()

    def is_selected(self):
        current_sel = self.scene.selected_entity
        my_sel = self.get_associated_entity()
        if current_sel is not None:
            return (current_sel[0].get_name() == my_sel[0].get_name()
                    and current_sel[1] == my_sel[1])
        else:
            return False

    def on_click(self):
        if self.is_active() and self.can_afford() and not self.is_selected():
            self.scene.set_selected(self.get_associated_entity())
        else:
            self.scene.set_selected(None)

    def draw(self, screen):
        icon = self._tower_example.get_shop_icon()
        color = self._tower_example.get_color()
        gold_cost = self._tower_example.get_stat_value(worlds.StatTypes.BUY_PRICE)
        stone_cost = self._tower_example.get_stat_value(worlds.StatTypes.STONE_PRICE)
        x = self.rect[0]
        w = self.rect[2]
        y = self.rect[1]

        icon_tb = sprites.TextBuilder()
        if self.is_selected():
            icon_tb.add(">", color=colors.BRIGHT_RED)
        icon_tb.add(icon, color=color if self.can_afford() else colors.DARK_GRAY)
        screen.add_text((x, y), icon_tb)

        price_tb = sprites.TextBuilder()
        if gold_cost > 0:
            price_tb.add("${}".format(gold_cost), color=colors.YELLOW if self.can_afford() else colors.DARK_GRAY)
        if gold_cost > 0 and stone_cost > 0:
            price_tb.add("/", color=color if self.can_afford() else colors.DARK_GRAY)
        if stone_cost > 0:
            price_tb.add("{}".format(stone_cost), color=colors.LIGHT_GRAY if self.can_afford() else colors.DARK_GRAY)
        screen.add_text((x + w - len(price_tb.text), y), price_tb)

    def get_associated_entity(self):
        return (self._tower_provider(), "shop")


class InGameScene(Scene):

    def __init__(self, state):
        super().__init__(state)
        self.shop_rect = [const.W - 16, 0, 16, const.H]
        self.info_rect = [0, const.H - 6, const.W - self.shop_rect[2], 6]

        self._paused = False
        self._playback_speed = 0  # larger = slower

        self.wave = 0
        self.wave_prog = 0

        self.cash = 200
        self.stones = 15
        self.score = 0

        self._world = worlds.generate_world(const.W - self.shop_rect[2] - 1,
                                           const.H - self.info_rect[3] - 1)
        self._world_rect = [1, 1, self._world.w(), self._world.h()]

        self.selected_entity = None  # (Entity, str=("world", "shop"))
        self.hovered_entity = None   # (Entity, str=("world", "shop"))

        self.hovered_button = None
        self.buttons = self._build_buttons()

    def should_draw_tower_range(self, tower):
        return True

    def is_game_over(self):
        return self._world.is_game_over()

    def get_center_message(self):
        if self.is_paused():
            return "*PAUSED*"
        elif self.is_game_over():
            return "GAME OVER!"
        else:
            return None

    def _build_buttons(self):
        res = []
        import src.game.units as units
        x = self.shop_rect[0] + 1
        y = self.shop_rect[1] + 4
        w = self.shop_rect[2] - 2
        for t_provider in units.get_towers_in_shop():
            if t_provider is not None:
                res.append(ShopButton(t_provider, self, [x, y, w, 1]))
            y += 1
        return res

    def get_active_buttons(self):
        return [b for b in self.buttons if b.is_active()]

    def is_paused(self):
        return self._paused

    def set_paused(self, val):
        self._paused = val

    def toggle_paused(self):
        self.set_paused(not self.is_paused())

    def should_skip_this_frame(self):
        return self.state.scene_ticks % (1 + self._playback_speed) != 0

    def increment_playback_speed(self):
        self._playback_speed = (self._playback_speed + 1) % 3

    def score_item(self, ent):
        if ent.is_stone_item():
            self.stones += 1
            self.score += 50
            # TODO play sound for scoring a stone
        elif ent.is_gold_ingot():
            self.cash += ent.get_sell_price()
            self.score += ent.get_sell_price() * 10
            # TODO play sound for scoring gold

    def update(self):
        if inputs.get_instance().was_pressed(pygame.K_SPACE):
            self.toggle_paused()
        if inputs.get_instance().was_pressed(pygame.K_TAB):
            self.increment_playback_speed()

        mouse_xy = self.state.get_mouse_pos()
        old_hover_button = self.hovered_button
        self.hovered_button = None
        if mouse_xy is not None:
            for b in self.get_active_buttons():
                if b.contains(mouse_xy):
                    self.hovered_button = b
            self.hovered_entity = self.get_entity_at_screen_pos(mouse_xy)
            if inputs.get_instance().mouse_was_pressed(1):
                self.handle_click(mouse_xy)
        if old_hover_button is not self.hovered_button:
            # TODO play sound for hovering over a button
            pass

        self._world.update_all(self)

    def get_pos_in_world(self, xy):
        if utils.Utils.rect_contains(self._world_rect, xy):
            return (xy[0] - self._world_rect[0], xy[1] - self._world_rect[1])
        else:
            return None

    def set_selected(self, entity_and_location):
        if self.selected_entity != entity_and_location:
            self.selected_entity = entity_and_location
            if entity_and_location is None:
                print("INFO: selected None")
                pass  # TODO play sound for deselecting
            else:
                print("INFO: selected {} ({})".format(self.selected_entity[0], self.selected_entity[1]))
                pass  # TODO play sound for selecting

    def handle_click(self, xy):
        if self.hovered_button is not None:
            self.hovered_button.on_click()
        else:
            if self.selected_entity is None:
                if self.hovered_entity is not None and self.hovered_entity[0].is_selectable():
                    self.set_selected(self.hovered_entity)
                else:
                    pass  # clicked nothing with nothing selected
            else:
                world_xy = self.get_pos_in_world(xy)
                if world_xy is None:
                    # clicked nothing, deselect selected entity
                    self.set_selected(None)
                else:
                    if self.selected_entity[1] == "world":
                        if self.hovered_entity is not None and self.hovered_entity[0].is_selectable():
                            # clicked something else, select that instead
                            self.set_selected(self.hovered_entity)
                        else:
                            # clicked nothing, deselect selected entity
                            self.set_selected(None)
                    elif self.selected_entity[1] == "shop":
                        # we're currently trying to buy something, and we clicked in world
                        if self._world.request_build_at(self.selected_entity[0], world_xy):
                            self.cash -= self.selected_entity[0].get_gold_cost()
                            self.stones -= self.selected_entity[0].get_stone_cost()
                            self.set_selected(None)
                        else:
                            pass  # TODO play sound for failing to place

    def get_entity_at_screen_pos(self, xy):
        world_xy = self.get_pos_in_world(xy)
        if world_xy is not None:
            ents = [e for e in self._world.all_entities_in_cell(world_xy, cond=lambda _e: _e.is_tower())]
            if len(ents) == 0:
                ents = [e for e in self._world.all_entities_in_cell(world_xy, cond=lambda _e: _e.is_robot())]
            if len(ents) == 0:
                ents = [e for e in self._world.all_entities_in_cell(world_xy, cond=lambda _e: _e.is_enemy())]
            if len(ents) == 0:
                ents = [e for e in self._world.all_entities_in_cell(world_xy)]

            if len(ents) > 0:
                return (ents[0], "world")
        else:
            for b in self.get_active_buttons():
                if b.contains(xy):
                    return b.get_associated_entity()

    def _draw_shop(self, screen):
        if self.cash < 10000:
            cash_text = "Gold: ${}".format(self.cash)
        else:
            cash_text = "Gold: $9999+"
        if self.stones < 1000:
            stones_text = "Stone: {}".format(self.stones)
        else:
            stones_text = "Stone: 999+"

        x = self.shop_rect[0] + 1
        y = self.shop_rect[1] + 1
        w = self.shop_rect[2]
        screen.add_text((x, y), cash_text, color=colors.YELLOW)
        screen.add_text((x, y + 1), stones_text, color=colors.LIGHT_GRAY)
        screen.add_text((x-1, y + 2), "╟" + "─" * (w - 2) + "╢", color=self.get_border_color(), replace=True)

    def get_wave(self):
        return self.wave

    def get_wave_prog(self):
        return self.wave_prog

    def _draw_info_text(self, screen):
        x = self.info_rect[0] + 1
        y = self.info_rect[1] + 1
        w = self.info_rect[2] - 2
        ent_to_show = self.selected_entity
        if ent_to_show is None:
            ent_to_show = self.hovered_entity

        if ent_to_show is None:
            score_text = "Score: {}".format(self.score)
            screen.add_text((x, y), score_text, color=colors.LIGHT_GRAY, replace=True)
            wave_text = "Wave {}".format(self.get_wave() + 1)
            screen.add_text((x, y + 1), wave_text, color=colors.LIGHT_GRAY, replace=True)
        else:
            text = ent_to_show[0].get_info_text(w, in_world=ent_to_show[1] == "world")
            screen.add_text((x, y), text, replace=True)

    def _draw_buttons(self, screen):
        for b in self.buttons:
            b.draw(screen)

    def _draw_overlays(self, screen):
        center_text = self.get_center_message()
        if center_text is not None and (self.state.scene_ticks // 15 % 2) == 0:
            lines = center_text.count("\n") + 1
            pos = (self._world_rect[0] + (self._world_rect[2] - len(center_text)) // 2,
                   self._world_rect[1] + (self._world_rect[3] - lines) // 2)
            screen.add_text(pos, center_text, color=colors.WHITE, replace=True, ignore="")

    def draw(self, screen):
        self._world.draw(screen, (1, 1), self)
        self._draw_borders(screen)
        self._draw_shop(screen)
        self._draw_info_text(screen)
        self._draw_buttons(screen)

        self._draw_overlays(screen)

    def get_view_mode(self):
        return worlds.ViewModes.NORMAL

    def get_border_color(self):
        return colors.DARK_GRAY

    def _draw_borders(self, screen: ascii_screen.AsciiScreen):
        color = self.get_border_color()
        screen.add((0, 0), textutils.DOUBLE[0], color=color, replace=True)
        screen.add((const.W - 1, 0), textutils.DOUBLE[2], color=color, replace=True)
        screen.add((0, const.H - 1), textutils.DOUBLE[6], color=color, replace=True)
        screen.add((const.W - 1, const.H - 1), textutils.DOUBLE[8], color=color, replace=True)
        for x in range(1, const.W - 1):
            if x == const.W - self.shop_rect[2]:
                screen.add((x, 0), "╦", color=color, replace=True)
                screen.add((x, const.H - 1), "╩", color=color, replace=True)
            else:
                screen.add((x, 0), textutils.DOUBLE[1], color=color, replace=True)
                screen.add((x, const.H - 1), textutils.DOUBLE[1], color=color, replace=True)

        for y in range(1, const.H - 1):
            if y == const.H - self.info_rect[3]:
                screen.add((0, y), "╠", color=color, replace=True)
                screen.add((const.W - self.shop_rect[2], y), "╣", color=color, replace=True)
                screen.add((const.W - 1, y), textutils.DOUBLE[3], color=color, replace=True)
            else:
                screen.add((0, y), textutils.DOUBLE[3], color=color, replace=True)
                screen.add((const.W - 1, y), textutils.DOUBLE[3], color=color, replace=True)
                screen.add((const.W - self.shop_rect[2], y), textutils.DOUBLE[3], color=color, replace=True)

        for x in range(1, const.W - self.shop_rect[2]):
            screen.add((x, const.H - self.info_rect[3]), textutils.DOUBLE[1], color=color, replace=True)
