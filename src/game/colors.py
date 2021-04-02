import random

WHITE = (1, 1, 1)
LIGHT_GRAY = (0.666, 0.666, 0.666)
MID_GRAY = (0.5, 0.5, 0.5)
DARK_GRAY = (0.333, 0.333, 0.333)
BLACK = (0, 0, 0)

ALL_COLORS = []
ALL_BRIGHT_COLORS = []

c = [0, 0.333, 0.5, 0.666, 1]
for r in c:
    for g in c:
        for b in c:
            rgb = (r, g, b)
            ALL_COLORS.append(rgb)
            if min(r, g, b) > 0.5:
                ALL_BRIGHT_COLORS.append(rgb)


def rand_color(seed=None):
    if seed is not None:
        idx = seed % len(ALL_BRIGHT_COLORS)
    else:
        idx = int(random.random() * len(ALL_BRIGHT_COLORS))
    return ALL_BRIGHT_COLORS[idx]
