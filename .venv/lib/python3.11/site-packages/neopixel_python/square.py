import collections
import colorsys
import itertools
import math
import neopixel_python.shape as npxp
import random
import time

import neopixel_python.square_misc

try:
    import numpy as np
    NUMPY = True
except ImportError:
    print("`numpy` module not installed!\n`rainbow_blinky` pattern disabled.")
    NUMPY = False
try:
    import pyfiglet
    PYFIGLET = True
except ImportError:
    print("`pyfiglet` module not installed!\n`figlet` pattern disabled.")
    PYFIGLET = False

# TODO: implement LED patterns: equalizer, Siri

SQUARE_LED_PIN        = 13      # Google AIY voice hat -- Servo 2 -- GPIO 13.
SQUARE_LED_CHANNEL    = 1       # set to '1' for GPIOs 13, 19, 41, 45 or 53
SQUARE_LED_COUNT      = 64      # Number of LED pixels.

SQUARE_LED_MAP = [
    [ 0,  1,  2,  3,  4,  5,  6,  7],
    [ 8,  9, 10, 11, 12, 13, 14, 15],
    [16, 17, 18, 19, 20, 21, 22, 23],
    [24, 25, 26, 27, 28, 29, 30, 31],
    [32, 33, 34, 35, 36, 37, 38, 39],
    [40, 41, 42, 43, 44, 45, 46, 47],
    [48, 49, 50, 51, 52, 53, 54, 55],
    [56, 57, 58, 59, 60, 61, 62, 63]
]

SQUARE_COLOURS = {
    'red':npxp.get_colour(255,0,0),
    'lime':npxp.get_colour(0,255,0),
    'blue':npxp.get_colour(0,0,255),
    'yellow':npxp.get_colour(255,255,0),
    'magenta':npxp.get_colour(255,0,255),
    'cyan':npxp.get_colour(0,255,255),
    'black':npxp.get_colour(0,0,0),
    'white':npxp.get_colour(255,255,255),
    'gray':npxp.get_colour(127,127,127),
    'grey':npxp.get_colour(127,127,127),
    'silver':npxp.get_colour(192,192,192),
    'maroon':npxp.get_colour(128,0,0),
    'olive':npxp.get_colour(128,128,0),
    'green':npxp.get_colour(0,128,0),
    'purple':npxp.get_colour(128,0,128),
    'teal':npxp.get_colour(0,128,128),
    'navy':npxp.get_colour(0,0,128),
    'orange':npxp.get_colour(255,165,0),
    'gold':npxp.get_colour(255,215,0),
    'purple':npxp.get_colour(128,0,128),
    'indigo':npxp.get_colour(75,0,130)
}

def get_randomness(width, height):
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    colour = npxp.get_colour(r, g, b)

    x = random.randint(0, (width-1))
    y = random.randint(0, (height-1))
    position = (x, y)

    return position, colour

def gaussian(fwhm):
    x = np.arange(0, 8, 1, float)
    y = x[:, np.newaxis]
    x0, y0 = 3.5, 3.5
    return np.exp(-4 * np.log(2) * ((x - x0) ** 2 + (y - y0) ** 2) / fwhm ** 2)

class SquareLED(npxp.DriveLED):
    """
    Usage example:
        rr = SquareLED(pattern="none")
        rr.start()

        rr.switch_pattern("lorem")

        rr.stop()
    """

    def _init_strip(self, led_count, led_pin, led_freq_hz, led_dma, led_invert,
            led_brightness, led_channel, led_strip, led_map):
        # Create NeoPixel object with appropriate configuration.
        if led_count is None:
            led_count = SQUARE_LED_COUNT
        if led_pin is None:
            led_pin = SQUARE_LED_PIN
        if led_freq_hz is None:
            led_freq_hz = npxp.LED_FREQ_HZ
        if led_dma is None:
            led_dma = npxp.LED_DMA
        if led_invert is None:
            led_invert = npxp.LED_INVERT
        if led_brightness is None:
            led_brightness = npxp.LED_BRIGHTNESS
        if led_channel is None:
            led_channel = SQUARE_LED_CHANNEL
        if led_strip is None:
            led_strip = npxp.LED_STRIP
        strip = npxp.get_neopixel(led_count, led_pin, led_freq_hz, led_dma,
                led_invert, led_brightness, led_channel, led_strip)

        # Create LED map
        if led_map is None:
            led_map = SQUARE_LED_MAP

        return strip, led_map

    def _get_pixel_id(self, pixel_position):
        x, y = pixel_position
        if x < 0 or x >7:
            raise print("x: {}".format(x))
        if y < 0 or y >7:
            raise print("y: {}".format(y))
        return self.led_map[x][y]

    def _rotated_pixel(self, pixel_id):
        if self.rotation == 0:
            return pixel_id
        elif self.rotation == 90:
            return (self.width-1-pixel_id[1], self.width-1-pixel_id[0])
        elif self.rotation == 180:
            return (self.height-1-pixel_id[0], self.width-1-pixel_id[1])
        elif self.rotation == 270:
            return (self.height-1-pixel_id[1], pixel_id[0])
        else:
            print("Unknown rotation value: {}.\nReverting to no rotation.".format(self.rotation))
            self.rotation = 0
            return pixel_id

    # Predefined circular patterns -- necessary inits
    def _init_custom_patterns(self):
        self.width = len(SQUARE_LED_MAP[0])
        self.height = len(SQUARE_LED_MAP)

        self.bucket_heights = [0] * (self.width - 2)
        self.bucket_contour_colour = npxp.get_colour(255, 255, 255)
        self.bucket_state = "drop"  # "clean"

        self.rainbow_wave_state_2 = 0.0
        self.rainbow_wave_state_15 = 0.0

        # TODO: pre-compute -- numpy i snot a requirement anymore
        z = list(range(1, 10)[::-1]) + list(range(1, 10))
        z_fwhm = [5.0/i for i in z]
        gauss = [gaussian(fwhm) for fwhm in z_fwhm]
        self.rainbow_blinky_gauss = itertools.cycle(gauss)
        self.rainbow_blinky_z = next(self.rainbow_blinky_gauss)

        self.cross_points = []
        self.cross_Point = collections.namedtuple("Point", "position colour direction")

        self.figlet_text = "GLASS-BOX"
        self.figlet_scroll = -3
        self.figlet_text_colour = npxp.get_colour(0, 255, 0)

        self.ascii_pic = "        \n        \n  X  X  \n        \nX      X\n XXXXXX \n        \n        \n        "
        self.ascii_colour = npxp.get_colour(0, 255, 0)
        self.ascii_scroll = 0

        custom_patterns_map = {"random_flicker": self._random_flicker,
                "bucket": self._bucket, "rainbow": self._rainbow,
                "cross": self._cross, "ascii": self._ascii}
        self.pattern_map.update(custom_patterns_map)
        if NUMPY:
            self.pattern_map.update({"rainbow_blinky": self._rainbow_blinky})
        if PYFIGLET:
            self.pattern_map.update({"figlet": self._figlet})

    def _random_flicker(self, wait_ms=5, **kwargs):
        for i in range(self.width):
            for j in range(self.height):
                _, c = get_randomness(self.width, self.height)
                self.set_pixel_colour((i, j), c)
        self.switch_fade_back()  # Fade back after switch
        self.show()

        while not self.colour_loop_break.is_set():
            p, c = get_randomness(self.width, self.height)
            self.set_pixel_colour(p, c)
            self.show()
            time.sleep(wait_ms/1000.0)

    def _bucket(self, ms_time=1000, ms_time_balldrop=20, ms_time_flush=20, contour_colour=None, bucket_contents_colour=None, exit_animation=True, **kwargs):
        def ball_colour():
            r = random.randint(100, 255)
            g = random.randint(100, 255)
            b = random.randint(100, 255)
            return npxp.get_colour(r, g, b)

        if contour_colour is None:
            contour_colour = self.bucket_contour_colour
        if bucket_contents_colour is None:
            bucket_contents_colour = ball_colour
        else:
            bucket_contents_colour = lambda: bucket_contents_colour

        # Draw contour
        for i in range(self.height):
            self.set_pixel_colour((i, 0), contour_colour)
            self.set_pixel_colour((i, self.width-1), contour_colour)
        for i in range(self.width):
            self.set_pixel_colour((self.height-1, i), contour_colour)
        # Draw bars
        for i, height in enumerate(self.bucket_heights):
            for j in range(1, height+1):
                self.set_pixel_colour((self.height-1-j, i+1), bucket_contents_colour())
        self.switch_fade_back()  # Fade back after switch
        self.show()
        while not self.colour_loop_break.is_set():
            # fill the bucket
            while not self.colour_loop_break.is_set() and min(self.bucket_heights) < self.height-1 and self.bucket_state == "drop":
                filling_colour = bucket_contents_colour()

                filling_bar = random.randint(1, self.width-2)
                while self.bucket_heights[filling_bar-1] == self.height-1:
                    filling_bar = random.randint(1, self.width-2)

                # Drop the ball
                self.set_pixel_colour((0, filling_bar), filling_colour)
                self.show()
                for i in range(0, self.height-self.bucket_heights[filling_bar-1]-2):
                    self.set_pixel_colour((i, filling_bar), SQUARE_COLOURS["black"])
                    self.set_pixel_colour((i+1, filling_bar), filling_colour)
                    self.show()
                    time.sleep(ms_time_balldrop/1000.0)

                self.bucket_heights[filling_bar-1] += 1

            if not self.colour_loop_break.is_set():
                self.bucket_state = "clean"
                time.sleep(ms_time/1000.0)

            # leak the bucket
            buck_h = max(self.bucket_heights)
            while not self.colour_loop_break.is_set() and buck_h != 0 and exit_animation and self.bucket_state == "clean":
                for i in range(1, self.width-1):
                    self.set_pixel_colour((self.height-buck_h-1, i), SQUARE_COLOURS["black"])
                self.show()

                buck_h -= 1
                self.bucket_heights = [i-1 for i in self.bucket_heights]
                time.sleep(ms_time_flush/1000.0)
            if not self.colour_loop_break.is_set() and not exit_animation and self.bucket_state == "clean":
                self.bucket_heights = [0] * (self.width - 2)
                for i in range(1, self.width-1):
                    for j in range(0, self.height-1):
                        self.set_pixel_colour((j, i), SQUARE_COLOURS["black"])
                self.show()

            if not self.colour_loop_break.is_set():
                self.bucket_state = "drop"
                time.sleep(ms_time/1000.0)

    # Rainbow
    def _rainbow(self, ms_time=10, **kwargs):
        def get_rain_bow(i2, i15, x, y, offset=30):
            r = (math.cos((x+i2)/2.0) + math.cos((y+i2)/2.0)) * 64.0 + 128.0
            g = (math.sin((x+i15)/1.5) + math.sin((y+i2)/2.0)) * 64.0 + 128.0
            b = (math.sin((x+i2)/2.0) + math.cos((y+i15)/1.5)) * 64.0 + 128.0
            r = max(0, min(255, r+offset))
            g = max(0, min(255, g+offset))
            b = max(0, min(255, b+offset))
            return npxp.get_colour(int(r), int(g), int(b))

        # Set the initial colours
        for y in range(self.height):
            for x in range(self.width):
                self.set_pixel_colour((x, y), get_rain_bow(self.rainbow_wave_state_2, self.rainbow_wave_state_15, x, y))
        self.switch_fade_back()  # Fade back after switch
        self.show()

        while not self.colour_loop_break.is_set():
            self.rainbow_wave_state_2 += 0.3
            self.rainbow_wave_state_15 += 0.3
            # prevent overflow
            self.rainbow_wave_state_2 %= 4 * math.pi
            self.rainbow_wave_state_15 %= 3 * math.pi
            #
            for y in range(self.height):
                for x in range(self.width):
                    self.set_pixel_colour((x, y), get_rain_bow(self.rainbow_wave_state_2, self.rainbow_wave_state_15, x, y))
            self.show()
            time.sleep(ms_time/1000.0)

    # Rainbow blinky
    def _rainbow_blinky(self, **kwargs):
        self._rainbow_blinky_blink(self.rainbow_blinky_z)
        self.switch_fade_back()  # Fade back after switch
        self.show()

        while not self.colour_loop_break.is_set():
            self.rainbow_blinky_z = next(self.rainbow_blinky_gauss)
            start = time.time()
            self._rainbow_blinky_blink(self.rainbow_blinky_z)
            self.show()
            end = time.time()
            t = end - start
            if t < 0.04:
                time.sleep(0.04 - t)
    def _rainbow_blinky_blink(self, z):
        for y in range(self.height):
            for x in range(self.width):
                if self.height<=self.width:
                    delta = 0
                    v = z[x,y+delta]
                else:
                    delta = 2
                    v = z[x+delta,y]
                h = 1.0/(x + y + delta + 1)
                s = 0.8
                rgb = [int(i*255.0) for i in colorsys.hsv_to_rgb(h, s, v)]
                self.set_pixel_colour((x, y), npxp.get_colour(*rgb))

    # Cross
    def _cross(self, ms_time=30, **kwargs):
        self._cross_plot_points()
        self.switch_fade_back()  # Fade back after switch
        self.show()

        while not self.colour_loop_break.is_set():
            if len(self.cross_points) < 10 and random.randint(0, 5) > 1:
                self._cross_new_point()
            # Update points
            for point in self.cross_points:
                if point.direction == 1:
                    point.position[0] += 1
                    if point.position[0] > self.height - 1:
                        self.cross_points.remove(point)
                elif point.direction == 2:
                    point.position[1] += 1
                    if point.position[1] > self.width - 1:
                        self.cross_points.remove(point)
                elif point.direction == 3:
                    point.position[0] -= 1
                    if point.position[0] < 0:
                        self.cross_points.remove(point)
                else:
                    point.position[1] -= 1
                    if point.position[1] < 0:
                        self.cross_points.remove(point)
            self._u_dark()
            self._cross_plot_points()
            self.show()
            time.sleep(ms_time/1000.0)
    def _cross_plot_points(self):
        for point in self.cross_points:
            self.set_pixel_colour(point.position, point.colour)
    def _cross_new_point(self):
        direction = random.randint(1, 4)
        if direction == 1:
            point = [0, random.randint(0, self.width - 1)]
        elif direction == 2:
            point = [random.randint(0, self.height - 1), 0]
        elif direction == 3:
            point = [self.height-1, random.randint(0, self.width - 1)]
        else:
            point = [random.randint(0, self.height - 1), self.width - 1]

        colour = []
        for i in range(0, 3):
            colour.append(random.randint(100, 255))
        colour = npxp.get_colour(*colour)

        self.cross_points.append(self.cross_Point(position=point, colour=colour, direction=direction))

    def _figlet(self, ms_time=200, text=None, text_colour=None, **kwargs):
        if text_colour is None:
            text_colour = self.figlet_text_colour
        if text is None:
            text = self.figlet_text
        else:
            self.figlet_scroll = -3

        # 8 height by default
        figlet_text = pyfiglet.figlet_format(text+" ", "banner", width=1000)
        figlet_matrix = figlet_text.split("\n")[:self.width]
        text_width = len(figlet_matrix[0])

        self._figlet_draw(figlet_matrix, text_width, text_colour)
        self.switch_fade_back()  # Fade back after switch
        # TODO: do I really need these `self.show()` in all the patterns
        self.show()

        while not self.colour_loop_break.is_set():
            self.figlet_scroll += 1
            self.figlet_scroll %= text_width
            self._figlet_draw(figlet_matrix, text_width, text_colour)
            self.show()
            time.sleep(ms_time/1000.0)
    def _figlet_draw(self, figlet_matrix, text_width, text_colour):
        for h in range(self.height):
            for w in range(self.width):
                w_pos = (self.figlet_scroll+w) % text_width
                if figlet_matrix[h][w_pos] == " ":
                    self.set_pixel_colour((h, w), SQUARE_COLOURS["black"])
                else:
                    self.set_pixel_colour((h, w), text_colour)

    # TODO: merge with `_figlet_...`
    def _ascii(self, ms_time=200, ascii_pic=None, colour=None, scroll=True, **kwargs):
        if ascii_pic is None:
            ascii_pic = self.ascii_pic
        else:
            if ascii_pic in neopixel_python.square_misc.ascii_pics:
                ascii_pic = neopixel_python.square_misc.ascii_pics[ascii_pic]
        if colour is None:
            colour = self.ascii_colour
        if not scroll:
            self.ascii_scroll = 0  # reset position

        ascii_pic = ascii_pic.split("\n")
        ascii_len = len(ascii_pic)

        # restore
        self._ascii_draw(ascii_pic, ascii_len, colour)
        self.switch_fade_back()  # Fade back after switch

        if scroll:
            while not self.colour_loop_break.is_set():
                self.ascii_scroll += 1
                self.ascii_scroll %= ascii_len
                self._ascii_draw(ascii_pic, ascii_len, colour)
                self.show()
                time.sleep(ms_time/1000.0)
        else:
            while not self.colour_loop_break.is_set():
                time.sleep(1000/1000.0)
    def _ascii_draw(self, ascii, ascii_height, ascii_colour):
        for h in range(self.height):
            for w in range(self.width):
                h_pos = (self.ascii_scroll+h) % ascii_height
                if ascii[h_pos][w] == " ":
                    self.set_pixel_colour((h, w), SQUARE_COLOURS["black"])
                else:
                    self.set_pixel_colour((h, w), ascii_colour)
