"""Builds all Waking Horizon logo variants (PNG + traced SVG) from the single source image.

Usage:  python tools/build_logos.py
Needs:  pillow, numpy, scipy, potracer   (pip install pillow numpy scipy potracer)
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
import potrace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "logo", "source", "logo-original.png")
OUT = os.path.join(ROOT, "assets", "logo")
K = 3            # working supersample factor
PAD = 36         # clear space around each variant, in original pixels

INK = (24, 21, 42)
CREAM = (253, 233, 203)
TEAL = (138, 136, 217)   # horizon accent (indigo-violet); source image is teal, recolored here
BLACK = (14, 12, 28)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- source layers
src = Image.open(SRC).convert("RGBA")
W0, H0 = src.size
a = np.asarray(src).astype(np.float32)
alpha = a[..., 3] / 255.0
rgb = a[..., :3]
pm = rgb * alpha[..., None]                       # premultiplied
big = lambda arr: np.asarray(Image.fromarray(arr.astype(np.float32), "F").resize((W0 * K, H0 * K), Image.LANCZOS))
alpha_b = np.clip(big(alpha), 0, 1)
pm_b = np.stack([big(pm[..., i]) for i in range(3)], -1)
rgb_b = pm_b / np.maximum(alpha_b[..., None], 1e-3)
lum = rgb_b @ np.array([0.299, 0.587, 0.114])
sil = alpha_b >= 0.5
teal = sil & ((rgb_b[..., 1] - rgb_b[..., 0]) > 16) & (lum > 80)
cream = sil & ~teal & (lum > 150)

# region split (original coordinates)
yy, xx = np.mgrid[0:H0 * K, 0:W0 * K]
xo, yo = xx / K, yy / K
R_MARK = (xo < 578) | ((xo < 700) & (yo >= 355))
R_WORD = (xo >= 578) & (yo < 360)
R_STUDIO = (xo >= 700) & (yo >= 360)


def layers(region):
    return {n: Image.fromarray(((m & region) * 255).astype(np.uint8), "L")
            for n, m in (("sil", sil), ("teal", teal), ("cream", cream))}


def bbox(l):
    return l["sil"].getbbox()


def crop_to(l):
    b = bbox(l)
    return {n: im.crop(b) for n, im in l.items()}


def scaled(l, s):
    if s == 1:
        return l
    out = {}
    for n, im in l.items():
        w, h = im.size
        r = im.resize((round(w * s), round(h * s)), Image.BILINEAR).point(lambda v: 255 if v >= 128 else 0)
        out[n] = r
    return out


MARK = crop_to(layers(R_MARK))
WORD = crop_to(layers(R_WORD))
STUDIO = crop_to(layers(R_STUDIO))
# positions of the original assembly (for the full lockup)
mark_box, word_box, studio_box = bbox(layers(R_MARK)), bbox(layers(R_WORD)), bbox(layers(R_STUDIO))


def lens_rule(width, half=8, outline=1.6):
    """Tapered horizon rule, drawn as layers (units: working pixels)."""
    w, h = int(width * K), int(2 * (half + 3) * K)
    def poly(hh):
        d = Image.new("L", (w, h), 0)
        ImageDraw.Draw(d).polygon([(0, h / 2), (w / 2, h / 2 - hh * K), (w, h / 2), (w / 2, h / 2 + hh * K)], fill=255)
        return d
    return {"sil": poly(half + outline), "teal": poly(half), "cream": Image.new("L", (w, h), 0)}


def canvas(w, h):
    return {n: Image.new("L", (w, h), 0) for n in ("sil", "teal", "cream")}


def paste(c, l, x, y):
    for n in c:
        c[n].paste(l[n], (round(x), round(y)), l[n])


def crop_to_pad(c, pad=PAD):
    b = c["sil"].getbbox()
    p = pad * K
    box = (b[0] - p, b[1] - p, b[2] + p, b[3] + p)
    return {n: im.crop(box) for n, im in c.items()}


def full_lockup():
    c = canvas(W0 * K, H0 * K)
    for l, bb in ((MARK, mark_box), (WORD, word_box), (STUDIO, studio_box)):
        paste(c, l, bb[0], bb[1])
    return crop_to_pad(c)


def horizontal_nostudio():
    c = canvas(W0 * K, H0 * K)
    paste(c, MARK, mark_box[0], mark_box[1])
    dy = 30 * K
    paste(c, WORD, word_box[0], word_box[1] + dy)
    rule_y = (mark_box[1] + mark_box[3]) // 2 + 0
    # horizon rule continues the mark's horizon line under the wordmark
    rule = lens_rule((word_box[2] - word_box[0]) / K * 0.97 + 0)
    ry = studio_box[1] + (studio_box[3] - studio_box[1]) // 2 - rule["sil"].size[1] // 2 + 8 * K
    paste(c, rule, word_box[0] + 20 * K, ry - 4 * K + 0)
    return crop_to_pad(c)


def stacked(with_studio, mark_w=None, gap_px=34, pad=PAD):
    ww = WORD["sil"].size[0]
    ms = scaled(MARK, mark_w * ww / MARK["sil"].size[0]) if mark_w else scaled(MARK, 1.15)
    gap = gap_px * K
    height = ms["sil"].size[1] + gap + WORD["sil"].size[1] + (gap + STUDIO["sil"].size[1] if with_studio else 0)
    c = canvas(ww + 20, height + 20)
    y = 10
    paste(c, ms, (ww - ms["sil"].size[0]) / 2 + 10, y)
    y += ms["sil"].size[1] + gap
    paste(c, WORD, 10, y)
    if with_studio:
        y += WORD["sil"].size[1] + gap
        paste(c, STUDIO, (ww - STUDIO["sil"].size[0]) / 2 + 10, y)
    return crop_to_pad(c, pad)


def square(with_studio):
    """Tight square: mark enlarged so the lockup fills the canvas, minimal clear space."""
    st = stacked(with_studio, mark_w=0.8 if with_studio else 0.9, gap_px=26, pad=20)
    w, h = st["sil"].size
    side = max(w, h)
    c = canvas(side, side)
    paste(c, st, (side - w) / 2, (side - h) / 2)
    return c


def mark_only():
    return crop_to_pad({n: im.copy() for n, im in MARK.items()} | {})


def wordmark_only():
    return crop_to_pad(WORD)


def wordmark_studio():
    c = canvas(WORD["sil"].size[0] + 20, WORD["sil"].size[1] + STUDIO["sil"].size[1] + 80 * K)
    ww = WORD["sil"].size[0]
    paste(c, WORD, 10, 10)
    paste(c, STUDIO, (ww - STUDIO["sil"].size[0]) / 2 + 10, 10 + WORD["sil"].size[1] + 34 * K)
    return crop_to_pad(c)


VARIANTS = {
    "logo-full": full_lockup,                       # mark + WAKING HORIZON + STUDIO
    "logo-horizontal": horizontal_nostudio,         # mark + WAKING HORIZON (no Studio)
    "logo-stacked": lambda: stacked(True),          # centered, with Studio
    "logo-stacked-nostudio": lambda: stacked(False),
    "logo-square": lambda: square(True),            # square, with Studio
    "logo-square-nostudio": lambda: square(False),  # square, name only
    "mark": mark_only,                              # icon only
    "wordmark": wordmark_only,                      # text only (no Studio)
    "wordmark-studio": wordmark_studio,             # text + Studio
}

COLORWAYS = {
    "color": None,
    "cream": CREAM,
    "black": BLACK,
    "white": WHITE,
}


# ---------------------------------------------------------------- rendering
def render(l, colorway, target_w=None):
    w, h = l["sil"].size
    s = np.asarray(l["sil"]).astype(np.float32) / 255
    out = np.zeros((h, w, 4), np.float32)
    if colorway is None:
        t = np.asarray(l["teal"]).astype(np.float32) / 255
        cr = np.asarray(l["cream"]).astype(np.float32) / 255
        col = np.zeros((h, w, 3), np.float32) + np.array(INK, np.float32)
        col = col * (1 - t[..., None]) + np.array(TEAL, np.float32) * t[..., None]
        col = col * (1 - cr[..., None]) + np.array(CREAM, np.float32) * cr[..., None]
    else:
        col = np.zeros((h, w, 3), np.float32) + np.array(colorway, np.float32)
    # premultiplied resize (K -> 2x original)
    tw = target_w or round(w * 2 / K)
    th = round(h * tw / w)
    col = col / 255.0
    chans = [col[..., i] * s for i in range(3)] + [s]
    r = [np.asarray(Image.fromarray(c, "F").resize((tw, th), Image.LANCZOS)) for c in chans]
    al = np.clip(r[3], 0, 1)
    res = np.stack([r[i] / np.maximum(al, 1e-3) for i in range(3)] + [al], -1)
    res = np.clip(res, 0, 1)
    res[..., :3][al < 1e-3] = 0
    return Image.fromarray((res * 255 + 0.5).astype(np.uint8), "RGBA")


def trace_path(mask):
    bm = potrace.Bitmap(np.asarray(mask) <= 127)
    plist = bm.trace(turdsize=6, alphamax=1.0, opticurve=True, opttolerance=0.3)
    d = []
    f = lambda p: f"{p.x / K:.1f} {p.y / K:.1f}"
    for curve in plist:
        d.append(f"M{f(curve.start_point)}")
        for seg in curve.segments:
            if seg.is_corner:
                d.append(f"L{f(seg.c)}L{f(seg.end_point)}")
            else:
                d.append(f"C{f(seg.c1)} {f(seg.c2)} {f(seg.end_point)}")
        d.append("Z")
    return "".join(d)


def svg(l, colorway, title):
    w, h = l["sil"].size
    vw, vh = w / K, h / K
    hexc = lambda c: "#%02x%02x%02x" % tuple(c)
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.1f} {vh:.1f}" '
            f'width="{vw:.0f}" height="{vh:.0f}" role="img" aria-label="{title}"><title>{title}</title>')
    if colorway is None:
        body = (f'<path fill="{hexc(INK)}" fill-rule="evenodd" d="{trace_path(l["sil"])}"/>'
                f'<path fill="{hexc(TEAL)}" fill-rule="evenodd" d="{trace_path(l["teal"])}"/>'
                f'<path fill="{hexc(CREAM)}" fill-rule="evenodd" d="{trace_path(l["cream"])}"/>')
    else:
        body = f'<path fill="{hexc(colorway)}" fill-rule="evenodd" d="{trace_path(l["sil"])}"/>'
    return head + body + "</svg>"


def main():
    for sub in ("png", "svg"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    built = {}
    for name, fn in VARIANTS.items():
        l = fn()
        built[name] = l
        for cw, col in COLORWAYS.items():
            base = f"{name}-{cw}"
            render(l, col).save(os.path.join(OUT, "png", base + ".png"), optimize=True)
            with open(os.path.join(OUT, "svg", base + ".svg"), "w", encoding="utf-8") as fh:
                fh.write(svg(l, col, "Waking Horizon Studio" if "nostudio" not in name and "horizontal" not in name and "wordmark" != name and "mark" != name else "Waking Horizon"))
        print("built", name, l["sil"].size)
    # ------------------------------------------------ icons / social
    bg = (9, 8, 24)
    for nm in ("logo-square", "logo-square-nostudio"):   # ready-made 1024px avatars on the night background
        lg = render(built[nm], None, target_w=1024)
        tile = Image.new("RGBA", lg.size, bg + (255,))
        tile.alpha_composite(lg)
        tile.convert("RGB").save(os.path.join(OUT, "png", nm + "-color-on-night.png"), optimize=True)
    mark = built["mark"]
    for size, fname in ((512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png"), (48, "favicon-48.png"), (32, "favicon-32.png")):
        m = render(mark, None, target_w=round(size * 0.84))
        sq = Image.new("RGBA", (size, size), bg + (255,))
        # round corners
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * 4 - 1, size * 4 - 1), radius=int(size * 4 * 0.22), fill=255)
        mask = mask.resize((size, size), Image.LANCZOS)
        sq.paste(m, ((size - m.width) // 2, (size - m.height) // 2 + int(size * 0.02)), m)
        sq.putalpha(mask)
        sq.save(os.path.join(OUT, "..", fname) if fname.startswith(("favicon", "apple")) else os.path.join(OUT, fname))
    # favicon.ico
    ico = Image.open(os.path.join(OUT, "..", "favicon-48.png"))
    ico.save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    # favicon svg
    msvg = svg(mark, None, "Waking Horizon")
    vb = mark["sil"].size
    with open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8") as fh:
        vw, vh = vb[0] / K, vb[1] / K
        s = 64 / (vw + 20)
        inner = msvg.split("</title>")[1].rsplit("</svg>", 1)[0]
        fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#090818"/>'
                 f'<g transform="translate({(64 - vw * 0.88 * s) / 2:.2f} {(64 - vh * 0.88 * s) / 2 + 1:.2f}) scale({0.88 * s:.4f})">{inner}</g></svg>')
    # OG image 1200x630
    og = Image.new("RGBA", (1200, 630), bg + (255,))
    px = np.asarray(og).astype(np.float32)
    gy, gx = np.mgrid[0:630, 0:1200]
    glow = np.exp(-(((gx - 600) / 520) ** 2 + ((gy - 520) / 260) ** 2))[..., None]
    px[..., :3] += glow * np.array([46, 38, 105], np.float32)
    og = Image.fromarray(np.clip(px, 0, 255).astype(np.uint8), "RGBA")
    lg = render(built["logo-full"], None, target_w=1000)
    og.paste(lg, ((1200 - lg.width) // 2, (630 - lg.height) // 2 - 10), lg)
    og.convert("RGB").save(os.path.join(ROOT, "assets", "og-image.png"), optimize=True)
    print("done")


if __name__ == "__main__":
    main()
