#!/usr/bin/env python3
"""news-image-20261122 v2 -- "THE WORLD IN ONE DAY".

A newspaper front page summing up Sunday 22 November 2026, drawn from
scratch with the Python standard library only (no Pillow, no network).
Writes a deterministic 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(or /output/entry.png).

Stories (all reported on 22 Nov 2026, cross-checked across wire/AP
round-ups): COP31 climate talks collapse in Antalya; ICJ rules Myanmar
committed genocide against the Rohingya; Ukraine confirms sea drones
sank a Russian warship off Libya; two tankers hit near the Strait of
Hormuz; factory fire in Banten, Indonesia; India 720/9 v New Zealand.
Ticker: Mexico captures 'El Chapo Isidro'; Peru quake 6.8; Delta
outage delays 1,600 flights; Shuri Castle restored in Okinawa.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)   # newsprint cream
INK = (24, 24, 22)
NAVY = (20, 38, 76)
NAVY_LT = (38, 62, 110)
RED = (176, 42, 30)
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
GREY = (110, 108, 100)
BLUE = (36, 102, 168)
GREEN = (46, 125, 62)
SKY = (176, 216, 240)
ORANGE = (224, 122, 26)
DARK = (30, 30, 34)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows of 5 pixels, '#' = on. Uppercase + digits + punctuation.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def wrap(text, scale, max_w):
    """Greedy word wrap; returns list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(-r, r + 1):
            dx = int((r * r - yy * yy) ** 0.5)
            if fill:
                self.fill_rect(cx - dx, cy + yy, 2 * dx + 1, 1, c)
            else:
                self.set(cx - dx, cy + yy, c)
                self.set(cx + dx, cy + yy, c)
        if not fill:
            for xx in range(-r, r + 1):
                dy = int((r * r - xx * xx) ** 0.5)
                self.set(cx + xx, cy - dy, c)
                self.set(cx + xx, cy + dy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(-ry, ry + 1):
            dx = int(rx * (1 - (yy / ry) ** 2) ** 0.5)
            self.fill_rect(cx - dx, cy + yy, 2 * dx + 1, 1, c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon."""
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, c)

    def text(self, x, y, s, scale, c, align="left"):
        s = s.upper()  # font is uppercase-only; fold case here
        if align == "center":
            x -= text_w(s, scale) // 2
        elif align == "right":
            x -= text_w(s, scale)
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[' '])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, c)
            cx += 6 * scale
        return cx

    def text_block(self, x, y, lines, scale, c, leading=None):
        if leading is None:
            leading = 7 * scale + 4
        for ln in lines:
            self.text(x, y, ln, scale, c)
            y += leading
        return y


# -------------------------------------------------------------------- icons
def draw_globe(cv, cx, cy, r):
    cv.circle(cx, cy, r, SKY)
    cv.circle(cx, cy, r, BLUE, fill=False)
    # meridians / parallels
    for k in (-2, -1, 0, 1, 2):
        cv.ellipse(cx, cy, max(2, abs(k) * r // 3), r, (120, 180, 220))
    cv.fill_rect(cx - r, cy - 2, 2 * r, 3, (120, 180, 220))
    # land blobs (small, scattered)
    cv.poly([(cx - r + 22, cy - r + 34), (cx - 34, cy - r + 18),
             (cx - 12, cy - r + 34), (cx - 22, cy - r + 52)], GREEN)
    cv.poly([(cx + 18, cy - 18), (cx + r - 24, cy - 26), (cx + r - 18, cy + 2),
             (cx + 34, cy + 10), (cx + 16, cy + 2)], GREEN)
    cv.poly([(cx - 46, cy + 26), (cx - 16, cy + 20), (cx - 8, cy + 44),
             (cx - 30, cy + 52)], GREEN)
    cv.poly([(cx + 8, cy + 48), (cx + 34, cy + 44), (cx + 30, cy + 66),
             (cx + 10, cy + 62)], GREEN)


def draw_scales(cv, cx, cy, s):
    # s = overall half-width
    cv.vline(cx, cy - 34, 68, INK, 4)
    cv.hline(cx - s, cy - 30, 2 * s, INK, 4)
    cv.fill_rect(cx - 16, cy + 34, 32, 6, INK)
    for sx in (-1, 1):
        px = cx + sx * s
        cv.line(px, cy - 30, px - 16, cy + 2, INK, 3)
        cv.line(px, cy - 30, px + 16, cy + 2, INK, 3)
        cv.hline(px - 18, cy + 2, 36, INK, 3)
        cv.poly([(px - 18, cy + 4), (px + 18, cy + 4), (px, cy + 22)], NAVY)
    cv.circle(cx, cy - 38, 6, GOLD)


def draw_ship(cv, x, y, w, h):
    # hull + superstructure + mast + waves + drone
    cv.poly([(x, y + h - 26), (x + w, y + h - 26), (x + w - 18, y + h),
             (x + 18, y + h)], NAVY)
    cv.fill_rect(x + w // 4, y + 18, w // 2, h - 46, NAVY_LT)
    cv.fill_rect(x + w // 3, y + 2, w // 6, 18, INK)
    cv.line(x + w // 2, y + 2, x + w // 2, y - 16, INK, 3)
    cv.circle(x + w // 2, y - 18, 4, RED)
    for wy in (y + h - 8, y + h - 2):
        for k in range(4):
            xx = x + 6 + k * (w // 4)
            cv.line(xx, wy, xx + 14, wy, BLUE, 3)
    # drone with dashed path
    dx, dy = x + w - 30, y - 34
    cv.circle(dx, dy, 5, DARK)
    cv.line(dx - 12, dy - 6, dx + 12, dy + 6, DARK, 2)
    cv.line(dx - 12, dy + 6, dx + 12, dy - 6, DARK, 2)
    for k in range(4):
        cv.line(x + w // 3 + k * 16, y + 8 + k * 6,
                x + w // 3 + k * 16 + 8, y + 8 + k * 6, GREY, 2)


def draw_tanker(cv, x, y, w, h):
    cv.fill_rect(x, y + h - 30, w, 22, RED)
    cv.fill_rect(x + 8, y + h - 52, w - 16, 22, DARK)
    cv.fill_rect(x + w - 34, y + h - 74, 18, 24, DARK)
    cv.fill_rect(x + w - 36, y + h - 78, 22, 6, GOLD)
    # flame + smoke over the deck
    fx = x + w // 3
    cv.poly([(fx - 14, y + h - 52), (fx, y + h - 84), (fx + 14, y + h - 52)],
            ORANGE)
    cv.poly([(fx - 7, y + h - 52), (fx, y + h - 70), (fx + 7, y + h - 52)],
            GOLD)
    for k, (sx, sy, sr) in enumerate(((x + 18, y + 6, 10), (x + 40, y - 2, 13),
                                      (x + 64, y + 8, 9))):
        cv.circle(sx, sy, sr, (150, 148, 140))
    for wy in (y + h - 4,):
        for k in range(4):
            xx = x + 6 + k * (w // 4)
            cv.line(xx, wy, xx + 14, wy, BLUE, 3)


def draw_factory(cv, x, y, w, h):
    cv.fill_rect(x, y + h - 46, w, 46, DARK)
    for k in range(3):
        fx = x + 10 + k * 26
        cv.poly([(fx, y + h - 46), (fx + 13, y + h - 66),
                 (fx + 26, y + h - 46)], DARK)
    cv.fill_rect(x + w - 30, y + 6, 12, h - 52, DARK)
    # flame
    fx = x + w // 2
    cv.poly([(fx - 16, y + h - 44), (fx - 4, y + h - 78),
             (fx + 4, y + h - 58), (fx + 16, y + h - 44)], ORANGE)
    cv.poly([(fx - 8, y + h - 44), (fx, y + h - 62), (fx + 8, y + h - 44)],
            GOLD)
    cv.circle(x + 16, y + 10, 9, (150, 148, 140))
    cv.circle(x + 34, y + 2, 12, (150, 148, 140))


def draw_cricket(cv, x, y, w, h):
    # stumps
    for k in range(3):
        cv.vline(x + w // 2 - 14 + k * 12, y + h - 46, 40, GOLD, 5)
    cv.hline(x + w // 2 - 16, y + h - 50, 36, GOLD, 4)
    # bat, leaning
    cv.line(x + 18, y + h - 10, x + 44, y + 22, (196, 164, 110), 8)
    cv.line(x + 44, y + 22, x + 54, y + 6, (120, 84, 50), 6)
    # red ball
    cv.circle(x + w - 34, y + 26, 13, RED)
    cv.circle(x + w - 34, y + 26, 13, WHITE, fill=False)
    # pitch lines
    cv.hline(x + 8, y + h - 8, w - 16, GREEN, 3)


# ------------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)

    # ---- masthead
    cv.fill_rect(16, 16, 992, 66, NAVY)
    cv.text(512, 34, "THE WORLD IN ONE DAY", 4, WHITE, align="center")
    cv.text(512, 96, "SUNDAY 22 NOVEMBER 2026", 4, RED, align="center")
    cv.hline(16, 88, 992, INK, 2)
    cv.hline(16, 128, 992, INK, 2)

    # ---- lead story: COP31 collapse
    cv.fill_rect(16, 138, 992, 278, WHITE)
    cv.rect(16, 138, 992, 278, NAVY, 3)
    cv.text(40, 158, "ANTALYA, TURKEY - CLIMATE", 2, RED)
    cv.text(40, 188, "CLIMATE TALKS", 6, INK)
    cv.text(40, 238, "COLLAPSE", 6, INK)
    deck = wrap("COP31 ends with no deal as nearly 200 nations split "
                "over fossil fuels and climate finance.", 2, 560)
    cv.text_block(40, 296, deck, 2, INK)
    deck2 = wrap("EU and allies reject the final draft.", 2, 560)
    cv.text_block(40, 296 + len(deck) * 18 + 6, deck2, 2, GREY)
    draw_globe(cv, 800, 276, 104)
    # NO DEAL ribbon across the globe
    cv.fill_rect(668, 300, 264, 34, RED)
    cv.text(800, 307, "NO DEAL", 3, WHITE, align="center")

    # ---- row 2: two half-width panels
    # ICJ verdict
    cv.fill_rect(16, 428, 488, 260, WHITE)
    cv.rect(16, 428, 488, 260, NAVY, 3)
    draw_scales(cv, 260, 500, 52)
    cv.text(260, 552, "MYANMAR GUILTY", 4, INK, align="center")
    cv.text(260, 584, "OF GENOCIDE", 4, INK, align="center")
    cv.text(260, 620, "THE HAGUE - JUSTICE", 2, RED, align="center")
    d = wrap("World court rules Myanmar committed genocide "
             "against the Rohingya.", 2, 440)
    cv.text_block(40, 644, d, 2, INK, leading=16)

    # Ukraine warship
    cv.fill_rect(520, 428, 488, 260, WHITE)
    cv.rect(520, 428, 488, 260, NAVY, 3)
    draw_ship(cv, 640, 476, 250, 84)
    cv.text(764, 566, "UKRAINE SINKS", 4, INK, align="center")
    cv.text(764, 598, "RUSSIAN WARSHIP", 4, INK, align="center")
    cv.text(764, 634, "OFF LIBYA - WAR AT SEA", 2, RED, align="center")
    d = wrap("Zelenskyy confirms sea drones struck the vessel "
             "at Benghazi.", 2, 440)
    cv.text_block(544, 654, d, 2, INK, leading=16)

    # ---- row 3: three panels
    # Hormuz tankers
    cv.fill_rect(16, 700, 320, 220, WHITE)
    cv.rect(16, 700, 320, 220, NAVY, 3)
    draw_tanker(cv, 66, 710, 220, 84)
    cv.text(176, 806, "TANKERS HIT", 3, INK, align="center")
    cv.text(176, 832, "NEAR HORMUZ", 3, INK, align="center")
    cv.text(176, 862, "GULF OF OMAN", 2, RED, align="center")
    d = wrap("Iran says two tankers hit mines.", 2, 276)
    cv.text_block(38, 884, d, 2, INK, leading=15)

    # Indonesia factory fire
    cv.fill_rect(352, 700, 320, 220, WHITE)
    cv.rect(352, 700, 320, 220, NAVY, 3)
    draw_factory(cv, 402, 710, 220, 84)
    cv.text(512, 806, "FACTORY FIRE", 3, INK, align="center")
    cv.text(512, 832, "36 STILL MISSING", 3, INK, align="center")
    cv.text(512, 862, "BANTEN, INDONESIA", 2, RED, align="center")
    d = wrap("Candy factory blaze kills 3.", 2, 276)
    cv.text_block(374, 884, d, 2, INK, leading=15)

    # India cricket
    cv.fill_rect(688, 700, 320, 220, WHITE)
    cv.rect(688, 700, 320, 220, NAVY, 3)
    draw_cricket(cv, 738, 710, 220, 84)
    cv.text(848, 806, "INDIA 720/9", 3, INK, align="center")
    cv.text(848, 832, "LEAD BY 352", 3, INK, align="center")
    cv.text(848, 862, "WELLINGTON - SPORT", 2, RED, align="center")
    d = wrap("India declare 720/9 in Wellington.", 2, 276)
    cv.text_block(710, 884, d, 2, INK, leading=15)

    # ---- ticker
    cv.fill_rect(16, 932, 992, 60, NAVY)
    tick = wrap("ALSO TODAY: MEXICO CAPTURES CARTEL BOSS 'EL CHAPO "
                "ISIDRO' - PERU QUAKE 6.8 - DELTA OUTAGE DELAYS 1,600 "
                "FLIGHTS - SHURI CASTLE RESTORED IN OKINAWA", 2, 960)
    cv.text_block(32, 940, tick, 2, WHITE)

    return cv


# ---------------------------------------------------------------------- PNG
def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png(path, cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    write_png(os.path.join(outdir, "entry.png"), cv)


if __name__ == "__main__":
    main()
