import src.game.ascii_screen as ascii_screen
import src.engine.sprites as sprites
import src.game.const as const
import src.engine.renderengine as renderengine
import src.engine.spritesheets as spritesheets
import src.game.colors as colors
import random


class GameState:

    def __init__(self):
        self.screen = ascii_screen.AsciiScreen(const.W, const.H, bg=" ", bg_color=colors.DARK_GRAY)
        self.char_sprites = []
        for x in range(0, const.W):
            self.char_sprites.append([None] * const.H)

        # will be (9, 16) unless the sprite sheet is changed
        self.char_size = spritesheets.get_instance().get_sheet(spritesheets.DefaultFont.SHEET_ID).get_char("A").size()

        self.tick = 0

    def update(self):
        self.tick += 1
        self._update_screen()
        self._update_sprites()

    def _update_screen(self):
        self.screen.clear()
        tick = self.tick

        for x in range(0, const.W):
            for y in range(0, const.H):
                c = const.ALL_CHARS[(y * const.W + x + tick // 12) % len(const.ALL_CHARS)]
                color = colors.rand_color(((y * const.W + x + tick) // 20) % len(const.ALL_CHARS))
                self.screen.add((x, y), c, color=color)

        # TODO pump data into screen

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
