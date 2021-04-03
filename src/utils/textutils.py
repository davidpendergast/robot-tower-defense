import src.engine.sprites as sprites

_ref = \
     "☺☻♥♦♣♠•◘○◙♂♀♪♫☼►◄↕‼¶§▬↨↑↓→←∟↔▲▼" + \
     " !\"#$%&'()*+,-./0123456789:;<=>?" + \
     "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_" + \
     "`abcdefghijklmnopqrstuvwxyz{|}~⌂" + \
     "ÇüéâäàåçêëèïîìÄÅÉæÆôöòûùÿÖÜ¢£¥₧ƒ" + \
     "áíóúñÑªº¿⌐¬½¼¡«»░▒▓│┤╡╢╖╕╣║╗╝╜╛┐" + \
     "└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌█▄▌▐▀" + \
     "αßΓπΣσµτΦΘΩδ∞φε∩≡±≥≤⌠⌡÷≈°∙·√ⁿ²■ "

SINGLE = ["┌", "─", "┐",  # 0  1  2
          "│", " ", "│",  # 3  4  5
          "└", "─", "┘"]  # 6  7  8
DOUBLE = ["╔", "═", "╗",
          "║", " ", "║",
          "╚", "═", "╝"]
THICK =  ["█", "█", "█",
          "█", " ", "█",
          "█", "█", "█"]


def ascii_rect(size, color=None, fill=" ", style=DOUBLE):
    builder = sprites.TextBuilder(color=color)
    for y in range(0, size[1]):
        for x in range(0, size[0]):
            if x == 0:
                if y == 0:
                    builder.add(style[0])
                elif y == size[1] - 1:
                    builder.add(style[6])
                else:
                    builder.add(style[3])
            elif x == size[0] - 1:
                if y == 0:
                    builder.add(style[2])
                elif y == size[1] - 1:
                    builder.add(style[8])
                else:
                    builder.add(style[5])
            elif y == 0:
                builder.add(style[1])
            elif y == size[1] - 1:
                builder.add(style[7])
            else:
                builder.add(fill)
        if y < size[1] - 1:
            builder.addLine("")
    return builder