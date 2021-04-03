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

        self.tick = 0

    def get_active_scene(self):
        return self.active_scene

    def set_next_scene(self, next):
        self.next_scene = next

    def update(self):
        if self.next_scene is not None:
            self.active_scene = self.next_scene
            self.next_scene = None

        self.active_scene.update()

        self._update_screen()
        self._update_sprites()
        self.tick += 1

    def _update_screen(self):
        self.screen.clear()
        self.active_scene.draw(self.screen)

    def _update_sprites(self):
        screen_size = renderengine.get_instance().get_game_size()
        root_xy = (screen_size[0] // 2 - (self.char_size[0] * const.W) // 2,
                   screen_size[1] // 2 - (self.char_size[1] * const.H) // 2)
        font_lookup = spritesheets.get_instance().get_sheet(spritesheets.DefaultFont.SHEET_ID)
        for y in range(0, const.H):
            for x in range(0, const.W):
                character, color = self.screen.item_at((x, y), tick=self.tick)
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

        screen.add_text(xy, game_name, color=colors.rand_color(self.state.tick // 30))
        screen.add_text(xy2, msg, color=colors.rand_color(5 + self.state.tick // 30))


class InstructionsScene(Scene):

    def __init__(self, state):
        super().__init__(state)
        self.instructions = sprites.TextBuilder()
        self.instructions.addLine("Instructions:")
        self.instructions.addLine("1. Use the mouse to buy units.")
        self.instructions.add("2. You cannot build things directly,\n   only Build-Bots (")
        self.instructions.add("☻", color=colors.YELLOW)
        self.instructions.addLine(") can build!")
        self.instructions.add("3. Use robots, towers, and walls to protect your ")
        self.instructions.add("♥", color=colors.RED)
        self.instructions.addLine("s!")
        self.instructions.add("4. When all ")
        self.instructions.add("♥", color=colors.RED)
        self.instructions.addLine("s are destroyed, the game is over.\n\nSee how long you can last.")

        self.text_dims = self.instructions.get_dimensions()

    def draw(self, screen):
        xy = ((const.W - self.text_dims[0]) // 2, (const.H - self.text_dims[1]) // 2)
        screen.add_text(xy, self.instructions)