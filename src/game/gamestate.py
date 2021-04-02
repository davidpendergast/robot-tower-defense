import src.game.ascii_screen as ascii_screen
import src.engine.sprites as sprites
import src.game.const as const
import src.engine.renderengine as renderengine
import src.game.colors as colors


class GameState:

    def __init__(self):
        self.screen = ascii_screen.AsciiScreen(const.W, const.H, bg=" ", bg_color=colors.DARK_GRAY)
        self.text_sprite = None

        self.tick = 0

    def update(self):
        self.tick += 1
        self._update_screen()
        self._update_sprites()

    def _update_screen(self):
        self.screen.clear()

        # TODO pump data into screen

    def _update_sprites(self):
        raw_text = self.screen.to_string()
        if self.text_sprite is None:
            self.text_sprite = sprites.TextSprite(const.TEXT_LAYER, 0, 0, raw_text.text,
                                                  scale=1, x_kerning=0, y_kerning=0)

        screen_size = renderengine.get_instance().get_game_size()
        self.text_sprite.update(new_x=screen_size[0] // 2 - self.text_sprite.get_size()[0] // 2,
                                new_y=screen_size[1] // 2 - self.text_sprite.get_size()[1] // 2,
                                new_text=raw_text.text,
                                new_color_lookup=raw_text.colors)

    def all_sprites(self):
        yield self.text_sprite
