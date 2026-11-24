# Waking Horizon Studio — website

Static single-page site for **Waking Horizon Studio**, served by GitHub Pages at <https://www.wakinghorizon.eu>.
No build step: plain HTML, CSS and a little JavaScript.

```
index.html          the page
css/style.css       styling
js/main.js          embers, scroll reveal, press-kit grid
assets/logo/        logo variants (png/, svg/), source/ holds the original
assets/press/       downloadable logo pack (.zip)
assets/games/       drop echoes-of-myth-capsule.jpg here to show it on the game card
tools/build_logos.py  regenerates every logo variant, icon and the OG image from the source logo
CNAME               custom domain for GitHub Pages
```

## Logo variants

`{layout}-{colorway}.{png|svg}`

| Layout | What it is |
| --- | --- |
| `logo-full` | mark + WAKING HORIZON + STUDIO |
| `logo-horizontal` | mark + WAKING HORIZON (no Studio) |
| `logo-stacked` / `logo-stacked-nostudio` | centered, with / without Studio |
| `logo-square` / `logo-square-nostudio` | stacked lockup on a square canvas; `*-color-on-night.png` is a ready 1024px avatar |
| `mark` | sunrise + cross-spike only |
| `wordmark` / `wordmark-studio` | text only, without / with Studio |

Colorways: `color` (original, for dark backgrounds), `cream`, `black`, `white` (flat one-color).
The SVGs are traced from the original raster, so they are scalable but not hand-drawn vectors.

To regenerate after changing the source: `pip install pillow numpy scipy potracer` then `python tools/build_logos.py`
(also rebuild `assets/press/waking-horizon-logo-pack.zip` afterwards).

## Local preview

```
python -m http.server 8000
```
