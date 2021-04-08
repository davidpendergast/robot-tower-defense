
import os.path
import src.game.const as const

name_of_game = "Automata Defense"
version = "1.0.1"


""" Display """
minimum_window_size = (9 * const.W, 16 * const.H)   # if the window is smaller than this, it will begin cropping the picture.
default_window_size = (2 * minimum_window_size[0],  # size of window when the game starts.
                       2 * minimum_window_size[1])

allow_fullscreen = True
allow_window_resize = True

clear_color = (0, 0, 0)


""" Pixel Scaling """
optimal_window_size = minimum_window_size
optimal_pixel_scale = 1  # how many screen pixels each "game pixel" will take up at the optimal window size.

auto_resize_pixel_scale = True  # whether to automatically update the pixel scale as the window grows and shrinks.
minimum_auto_pixel_scale = 1


""" FPS """
target_fps = 30
precise_fps = False


""" Miscellaneous """
is_dev = os.path.exists(".gitignore")  # yikes
do_crash_reporting = not is_dev  # whether to produce a crash file when the program exits via an exception.

