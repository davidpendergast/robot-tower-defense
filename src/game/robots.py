
import src.game.gamestate as gamestate
import src.engine.layers as layers
import src.game.const as const
import src.engine.game as game


class RobotTowerDefense(game.Game):

    def __init__(self):
        super().__init__()
        self.gamestate = None

    def initialize(self):
        self.gamestate = gamestate.GameState()

    def create_sheets(self):
        return []  # the only sheet we need is font.png, which is a default sheet

    def create_layers(self):
        yield layers.ImageLayer(const.TEXT_LAYER, 0, sort_sprites=False, use_color=True)

    def update(self):
        self.gamestate.update()

    def all_sprites(self):
        for spr in self.gamestate.all_sprites():
            yield spr