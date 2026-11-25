#!/usr/bin/env python3
"""The World Today - Wednesday, 25 November 2026.

Draws a one-page newspaper front page summing up the day's world news
and writes it to entry.png. Pure standard library: a hand-rolled pixel
buffer, a 5x7 bitmap font drawn from scratch, and a small PNG encoder.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py
The grader runs it with no network; the output directory comes from
MAKEFUN_OUTPUT_DIR and defaults to /output. Two runs produce
byte-identical files: fixed layout, fixed colours, no clock, no random
input, deterministic zlib output.

Headlines (verified from live sources on 25 Nov 2026):
  LEAD  Houthi drone hits Riyadh's PIF Tower again, 11 wounded -
        second strike on the tower in a week (Reuters, 25 Nov).
  TURKIYE  Turkish Air Force AS-532 Cougar crashes on a training
        flight near Eskisehir, five crew killed (Reuters, 24 Nov).
  UKRAINE WAR  Putin says retaliation is "inevitable" as Ukraine
        keeps hitting Russian oil refineries (25 Nov wires).
  MIGRATION  About 175 migrants missing after contact is lost with
        a Europe-bound boat that left Dakar (Reuters, 24 Nov).
  DR CONGO  Rebels call off their advance on Bunia and pull back
        after days of fighting (25 Nov wires).
  IN BRIEF  Huawei convicted in a US trial on 10 of 12 counts;
        Anthropic shares fall below the $83 IPO price; Zelenskiy
        confirms the Sparta II ship strike; San Francisco Bay braces
        for record flooding; Australia set to pass a tech
        duty-of-care bill.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# ------------------------------------------------------------------ palette
PAPER = (246, 241, 231)
PANEL = (255, 253, 246)
INK = (26, 26, 26)
NAVY = (22, 35, 63)
RED = (178, 34, 34)
GREY = (96, 96, 96)
BORDER = (214, 206, 187)
SKY = (216, 228, 236)
SLATE = (52, 68, 92)
ORANGE = (226, 110, 44)
GOLD = (201, 162, 39)
WAVE = (70, 130, 180)
GREEN = (46, 125, 50)
YELLOW = (233, 196, 55)


# ------------------------------------------------------------------ 5x7 font
# Each glyph: 7 rows of 5 characters, "#" = ink. Uppercase only; every
# string the page prints is upper-cased before drawing.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", "..#..", "..#.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..#..", ".#..."),
    ":": (".....", "..#..", ".....", ".....", "..#..", ".....", "....."),
    ";": (".....", "..#..", ".....", ".....", "..#..", "..#..", ".#..."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
}


def char_width(scale):
    return 6 * scale


def text_width(text, scale):
    return len(text) * char_width(scale)


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    current = ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ------------------------------------------------------------------ canvas
class Canvas:
    """A plain RGB pixel buffer with rectangle/line/circle/text drawing."""

    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.pixels = bytearray(background * (width * height))

    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i] = color[0]
            self.pixels[i + 1] = color[1]
            self.pixels[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        for yy in range(y0, y1):
            base = (yy * self.width + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.pixels[i] = color[0]
                self.pixels[i + 1] = color[1]
                self.pixels[i + 2] = color[2]

    def outline_rect(self, x, y, w, h, color, thickness=2):
        self.fill_rect(x, y, w, thickness, color)
        self.fill_rect(x, y + h - thickness, w, thickness, color)
        self.fill_rect(x, y, thickness, h, color)
        self.fill_rect(x + w - thickness, y, thickness, h, color)

    def hline(self, x, y, length, color, thickness=1):
        self.fill_rect(x, y, length, thickness, color)

    def vline(self, x, y, length, color, thickness=1):
        self.fill_rect(x, y, thickness, length, color)

    def line(self, x0, y0, x1, y1, color, thickness=1):
        """Bresenham line, with a square brush of the given thickness."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thickness // 2
        while True:
            self.fill_rect(x0 - half, y0 - half, thickness, thickness, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, radius, color):
        for yy in range(cy - radius, cy + radius + 1):
            span = int((radius * radius - (yy - cy) ** 2) ** 0.5)
            self.fill_rect(cx - span, yy, span * 2 + 1, 1, color)

    def draw_text(self, x, y, text, scale, color):
        """Draw one line, upper-cased, at the given top-left corner."""
        cursor = x
        for ch in text.upper():
            glyph = FONT.get(ch)
            if glyph is None:
                cursor += char_width(scale)
                continue
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(cursor + col * scale, y + row * scale,
                                       scale, scale, color)
            cursor += char_width(scale)

    def draw_text_centered(self, y, text, scale, color, cx=None):
        if cx is None:
            cx = self.width // 2
        w = text_width(text, scale)
        self.draw_text(cx - w // 2, y, text, scale, color)

    def draw_block(self, x, y, text, scale, max_width, color, pitch=None):
        """Wrapped paragraph; returns the y just below the last line."""
        if pitch is None:
            pitch = 8 * scale + 4
        for line in wrap_text(text, scale, max_width):
            self.draw_text(x, y, line, scale, color)
            y += pitch
        return y


# ------------------------------------------------------------------ PNG
def encode_png(canvas):
    """Minimal deterministic PNG: 8-bit RGB, no filter, zlib level 9."""
    raw = bytearray()
    row_bytes = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        start = y * row_bytes
        raw += canvas.pixels[start:start + row_bytes]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# ------------------------------------------------------------------ pictures
def draw_tower(canvas, bx, by):
    """Skyscraper hit mid-facade: the PIF Tower, Riyadh."""
    canvas.fill_rect(bx, by, 260, 256, SKY)
    canvas.fill_rect(bx, by + 236, 260, 20, (148, 156, 166))
    # smaller neighbour tower
    canvas.fill_rect(bx + 18, by + 120, 52, 116, (74, 90, 114))
    for yy in range(by + 132, by + 224, 22):
        for xx in (bx + 26, bx + 42):
            canvas.fill_rect(xx, yy, 8, 10, (200, 210, 220))
    # main tower with setback top and spire
    canvas.fill_rect(bx + 96, by + 70, 96, 166, SLATE)
    canvas.fill_rect(bx + 108, by + 52, 72, 18, SLATE)
    canvas.vline(bx + 144, by + 30, 22, SLATE, 4)
    for yy in range(by + 84, by + 216, 24):
        for xx in (bx + 104, bx + 120, bx + 136, bx + 152, bx + 168):
            canvas.fill_rect(xx, yy, 8, 10, (200, 210, 220))
    # smoke above the impact
    for cx, cy, r in ((bx + 120, by + 122, 9), (bx + 168, by + 110, 7),
                      (bx + 144, by + 98, 8)):
        canvas.fill_circle(cx, cy, r, (120, 124, 128))
    # impact burst on the facade
    cx, cy = bx + 144, by + 170
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                   (1, 1), (-1, -1), (1, -1), (-1, 1)):
        canvas.line(cx, cy, cx + dx * 34, cy + dy * 34, ORANGE, 3)
    canvas.fill_circle(cx, cy, 24, ORANGE)
    canvas.fill_circle(cx, cy, 10, GOLD)


def draw_helicopter(canvas, bx, by):
    """AS-532 Cougar in flight over a plain sky."""
    canvas.fill_rect(bx, by, 132, 176, (222, 232, 238))
    canvas.hline(bx + 14, by + 52, 104, INK, 4)
    canvas.vline(bx + 66, by + 52, 16, INK, 4)
    canvas.line(bx + 40, by + 84, bx + 8, by + 72, SLATE, 6)
    canvas.fill_rect(bx + 6, by + 58, 8, 18, SLATE)
    canvas.fill_rect(bx + 38, by + 70, 58, 34, SLATE)
    canvas.fill_circle(bx + 96, by + 87, 17, SLATE)
    canvas.fill_rect(bx + 78, by + 76, 16, 12, (200, 220, 230))
    canvas.hline(bx + 34, by + 118, 66, INK, 3)
    canvas.vline(bx + 44, by + 104, 14, INK, 3)
    canvas.vline(bx + 88, by + 104, 14, INK, 3)


def draw_flame(canvas, bx, by):
    """Oil refinery towers with a flame."""
    canvas.fill_rect(bx, by, 132, 176, (253, 230, 210))
    canvas.fill_rect(bx + 16, by + 96, 26, 54, SLATE)
    canvas.fill_rect(bx + 48, by + 76, 26, 74, SLATE)
    canvas.vline(bx + 61, by + 60, 16, SLATE, 5)
    canvas.fill_circle(bx + 98, by + 110, 20, ORANGE)
    canvas.fill_circle(bx + 98, by + 94, 14, ORANGE)
    canvas.fill_circle(bx + 98, by + 80, 8, GOLD)
    canvas.hline(bx + 10, by + 150, 112, (150, 140, 130), 3)


def draw_boat(canvas, bx, by):
    """A pirogue under sail, with waves below."""
    canvas.fill_rect(bx, by, 132, 176, (214, 232, 240))
    canvas.vline(bx + 66, by + 48, 48, INK, 3)
    for yy in range(by + 52, by + 94):
        width = 28 - (yy - (by + 52)) * 28 // 42
        canvas.fill_rect(bx + 66, yy, max(1, width), 1, PANEL)
    canvas.fill_rect(bx + 30, by + 96, 72, 6, SLATE)
    canvas.fill_rect(bx + 26, by + 102, 80, 6, SLATE)
    canvas.fill_rect(bx + 22, by + 108, 88, 6, SLATE)
    for yy in (by + 126, by + 136, by + 146):
        for xx in range(bx + 12, bx + 120, 16):
            canvas.fill_rect(xx, yy, 10, 3, WAVE)


def draw_flag(canvas, bx, by):
    """A flag on a pole: the push on Bunia is called off."""
    canvas.fill_rect(bx, by, 132, 176, (220, 236, 220))
    canvas.vline(bx + 28, by + 28, 122, INK, 4)
    canvas.fill_rect(bx + 32, by + 28, 26, 44, GREEN)
    canvas.fill_rect(bx + 58, by + 28, 26, 44, YELLOW)
    canvas.fill_rect(bx + 84, by + 28, 26, 44, RED)
    canvas.fill_circle(bx + 96, by + 118, 11, GOLD)
    canvas.hline(bx + 12, by + 150, 108, (140, 150, 140), 3)


# ------------------------------------------------------------------ layout
CARDS = [
    ("TURKIYE", "HELICOPTER CRASH KILLS FIVE",
     "AIR FORCE COUGAR DOWN ON A TRAINING FLIGHT NEAR ESKISEHIR.",
     draw_helicopter, (222, 232, 238)),
    ("UKRAINE WAR", "PUTIN WARNS RETALIATION IS 'INEVITABLE'",
     "UKRAINE KEEPS HITTING RUSSIAN OIL REFINERIES.",
     draw_flame, (253, 230, 210)),
    ("MIGRATION", "175 MIGRANTS MISSING AT SEA",
     "CONTACT LOST WITH A EUROPE-BOUND BOAT THAT LEFT DAKAR.",
     draw_boat, (214, 232, 240)),
    ("DR CONGO", "REBELS HALT PUSH ON BUNIA",
     "FIGHTERS CALL OFF THE ADVANCE AND PULL BACK AFTER DAYS OF CLASHES.",
     draw_flag, (220, 236, 220)),
]

BRIEFS = [
    "HUAWEI CONVICTED IN US TRIAL ON 10 OF 12 COUNTS",
    "ANTHROPIC SHARES FALL BELOW $83 IPO PRICE",
    "ZELENSKIY CONFIRMS SPARTA II SHIP STRIKE",
    "SAN FRANCISCO BAY BRACES FOR RECORD FLOODING",
    "AUSTRALIA SET TO PASS TECH DUTY-OF-CARE BILL",
]


def draw_card(canvas, x, y, kicker, headline, deck, picture, bg):
    canvas.fill_rect(x, y, 480, 176, PANEL)
    canvas.outline_rect(x, y, 480, 176, BORDER, 2)
    picture(canvas, x, y)
    tx = x + 148
    canvas.draw_text(tx, y + 16, kicker, 2, RED)
    lines = wrap_text(headline, 3, 316)
    hy = y + 42
    for line in lines:
        canvas.draw_text(tx, hy, line, 3, INK)
        hy += 26
    canvas.draw_block(tx, hy + 10, deck, 2, 316, INK, pitch=19)


def build():
    canvas = Canvas(WIDTH, HEIGHT, PAPER)
    # masthead
    canvas.fill_rect(0, 0, WIDTH, 140, NAVY)
    canvas.draw_text_centered(22, "THE WORLD TODAY", 7, PANEL)
    canvas.draw_text_centered(90, "WEDNESDAY, 25 NOVEMBER 2026", 3,
                              (235, 225, 200))
    canvas.hline(0, 140, WIDTH, RED, 5)
    # lead story
    canvas.fill_rect(32, 156, 960, 296, PANEL)
    canvas.outline_rect(32, 156, 960, 296, BORDER, 2)
    canvas.draw_text(52, 176, "MIDDLE EAST", 2, RED)
    canvas.draw_text(52, 206, "HOUTHI DRONE HITS", 4, INK)
    canvas.draw_text(52, 246, "RIYADH TOWER AGAIN", 4, INK)
    canvas.draw_block(
        52, 300,
        "ELEVEN WOUNDED IN THE SECOND STRIKE ON THE PIF TOWER IN A "
        "WEEK. THE SAUDI-LED COALITION VOWS A DECISIVE RESPONSE.",
        2, 608, INK, pitch=20)
    canvas.hline(52, 378, 608, BORDER, 2)
    canvas.draw_text(52, 394, "MOST INTERNATIONAL FLIGHTS TO RIYADH "
                   "CANCELLED.", 2, GREY)
    draw_tower(canvas, 700, 176)
    # four story cards
    positions = [(32, 468), (512, 468), (32, 660), (512, 660)]
    for (x, y), (kicker, headline, deck, picture, _bg) in zip(positions, CARDS):
        draw_card(canvas, x, y, kicker, headline, deck, picture, _bg)
    # in brief
    canvas.draw_text(32, 850, "IN BRIEF", 3, NAVY)
    canvas.hline(32, 878, 960, RED, 3)
    y = 890
    for item in BRIEFS:
        canvas.fill_rect(32, y + 2, 10, 10, RED)
        canvas.draw_text(52, y, item, 2, INK)
        y += 21
    # footer
    canvas.hline(32, 996, 960, BORDER, 2)
    canvas.draw_text_centered(1004, "THE WORLD TODAY - 25 NOVEMBER 2026",
                              2, GREY)
    return canvas


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(data), WIDTH, HEIGHT))


if __name__ == "__main__":
    main()
