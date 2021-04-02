
import src.game.colors as colors
import src.engine.sprites as sprites


class AsciiScreen:

    def __init__(self, w, h, bg=" ", bg_color=colors.WHITE, anim_period=30):
        self._char_map = {}  # (x, y) -> list of (char, color)
        self._bg_char = bg
        self._bg_color = bg_color
        self._anim_period = anim_period
        self._w = w
        self._h = h

    def clear(self):
        self._char_map.clear()

    def w(self):
        return self._w

    def h(self):
        return self._h

    def size(self):
        return self.w(), self.h()

    def get_rect(self):
        return [0, 0, self.w(), self.h()]

    def is_valid(self, xy):
        return 0 <= xy[0] < self.w() and 0 <= xy[1] < self.h()

    def add(self, xy, char, color=None):
        if color is None:
            color = self._bg_color
        if not self.is_valid(xy):
            print("WARN: {} is OOB".format(xy))
            return
        if xy not in self._char_map:
            self._char_map[xy] = [(char, color)]
        else:
            self._char_map[xy].append((char, color))

    def item_at(self, xy, tick=0, include_bg=True):
        """returns: (char, color) or None"""
        if xy in self._char_map:
            items = self._char_map[xy]
            if len(items) > 0:
                idx = int(tick * len(items) / self._anim_period) % len(items)
                return items[idx]
        if include_bg:
            return self._bg_char, self._bg_color
        else:
            return None

    def get_all(self, tick=0, rect=None):
        """returns: TextBuilder"""
        if rect is None:
            rect = self.get_rect()
        builder = sprites.TextBuilder()
        for y in range(rect[1], rect[1] + rect[3]):
            if y > 0:
                builder.add("\n")
            for x in range(rect[0], rect[0] + rect[2]):
                item = self.item_at((x, y), tick=tick)
                c, color = item
                builder.add(c, color=color)

        return builder

    def get_row(self, y, tick=0):
        builder = sprites.TextBuilder()
        for x in range(0, self.w()):
            item = self.item_at((x, y), tick=tick)
            builder.add(item[0], color=item[1])
        return builder

    def pretty_print(self, tick=0, rect=None):
        my_str = self.get_all(tick=tick, rect=rect)
        print(my_str.text)


if __name__ == "__main__":
    asc = AsciiScreen(30, 20, bg="~")
    asc.add((10, 0), "☺")
    asc.pretty_print(tick=30)

