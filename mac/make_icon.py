#!/usr/bin/env python3
"""Generate the Skicom macOS app icon (cozy, App Store squircle style).

Renders a 1024x1024 PNG at 2x supersampling, then (optionally) build_app.sh
turns it into an .icns via `iconutil`.

Usage:  python make_icon.py [output_png]   (default: skicom_icon.png next to this file)
Only dependency: Pillow.
"""
import os
import sys
from PIL import Image, ImageDraw

# ── Cozy palette ────────────────────────────────────────────────────────────
CREAM     = (250, 246, 239)
CREAM_MID = (243, 230, 212)
SAND      = (232, 201, 160)
CLAY      = (217, 119, 87)
CLAY_DEEP = (196, 98, 63)
CLAY_LITE = (240, 168, 134)
PINE_TOP  = (124, 144, 112)
PINE      = (104, 124, 92)
SNOW      = (255, 255, 255)
SNOW_BLUE = (188, 211, 222)
CHARCOAL  = (43, 38, 34)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgrad(size, top_color, bot_color, y0, y1):
    """Return an RGB image filled with a vertical gradient between y0 and y1."""
    w, h = size
    img = Image.new("RGB", size, top_color)
    d = ImageDraw.Draw(img)
    span = max(1, y1 - y0)
    for y in range(h):
        t = min(1.0, max(0.0, (y - y0) / span))
        d.line([(0, y), (w, y)], fill=lerp(top_color, bot_color, t))
    return img


def grad_polygon(base, points, top_color, bot_color, alpha=255):
    """Paste a vertically-graded polygon onto `base`."""
    ys = [p[1] for p in points]
    strip = vgrad(base.size, top_color, bot_color, min(ys), max(ys))
    mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(mask).polygon(points, fill=alpha)
    base.paste(strip, (0, 0), mask)


def radial(base, cx, cy, r, edge_color, mid_color, core_color):
    """Draw a soft radial disc (sun) via concentric circles."""
    d = ImageDraw.Draw(base, "RGBA")
    for i in range(r, 0, -1):
        t = i / r
        col = lerp(mid_color, edge_color, (t - 0.5) / 0.5) if t > 0.5 \
            else lerp(core_color, mid_color, t / 0.5)
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=col + (255,))


def build(scale=2):
    S = 1024 * scale
    sc = lambda v: int(round(v * scale))
    box = (sc(100), sc(100), sc(924), sc(924))
    radius = sc(185)

    # Artwork drawn full-bleed, then masked to the squircle.
    art = vgrad((S, S), CREAM, SAND, sc(100), sc(924))
    # blend a mid stop for warmth
    mid = vgrad((S, S), CREAM_MID, SAND, sc(520), sc(924))
    art.paste(mid, (0, 0), Image.new("L", (S, S), 90))

    # Sun, upper-right
    radial(art, sc(700), sc(338), sc(96), CLAY_DEEP, CLAY, CLAY_LITE)

    # Back ridge (pine)
    grad_polygon(art,
                 [(sc(250), sc(720)), (sc(470), sc(395)), (sc(610), sc(560)),
                  (sc(730), sc(415)), (sc(900), sc(720))],
                 PINE_TOP, PINE)

    # Front peak (clay)
    grad_polygon(art,
                 [(sc(110), sc(730)), (sc(400), sc(290)), (sc(690), sc(730))],
                 CLAY, CLAY_DEEP)

    # Snow cap on the front peak
    grad_polygon(art,
                 [(sc(400), sc(290)), (sc(320), sc(415)), (sc(356), sc(398)),
                  (sc(386), sc(436)), (sc(418), sc(396)), (sc(450), sc(428)),
                  (sc(480), sc(414))],
                 SNOW, SNOW_BLUE)

    # Cozy snow-blue ground band
    band = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(band).rectangle([0, sc(705), S, S], fill=SNOW_BLUE + (130,))
    art = Image.alpha_composite(art.convert("RGBA"), band)

    # Soft top highlight for premium depth
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(hl).rectangle([0, sc(100), S, sc(470)], fill=(255, 255, 255, 16))
    art = Image.alpha_composite(art, hl).convert("RGB")

    # Mask to squircle
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    out.paste(art, (0, 0), mask)

    # Subtle inner edge
    ImageDraw.Draw(out, "RGBA").rounded_rectangle(
        box, radius=radius, outline=CHARCOAL + (20,), width=max(1, scale))

    return out.resize((1024, 1024), Image.LANCZOS)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "skicom_icon.png")
    build(scale=2).save(out, "PNG")
    print("Saved icon ->", out)


if __name__ == "__main__":
    main()
