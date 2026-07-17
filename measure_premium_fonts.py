"""
measure_premium_fonts.py — Measure per-character-category scale ratios for premium SVG fonts.

Renders A-Z, a-z, 0-9, and common special characters for each installed premium font
using the same Chrome collage method as batch_processor.py. Outputs a FONT_CHAR_METRICS
dict entry for each font — paste the result into batch_processor.py.

Usage:
    py measure_premium_fonts.py
    py measure_premium_fonts.py --font smartkids   # measure one font only
    py measure_premium_fonts.py --out metrics.json # save raw measurements to JSON
"""
import os, sys, re, subprocess, json, argparse, base64 as _b64
sys.stdout.reconfigure(encoding="utf-8")

FONTS_DIR  = r"C:\gimpTest\Fonts"
TEMP_DIR   = r"C:\gimpTest\Temp"
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PREMIUM_FONTS = {
    "smartkids":           "Smart Kids.otf",
    "colorfulblocks":      "Colorful Blocks.otf",
    "paintsplashesrainbow":"Paint Splashes Rainbow.otf",
    "wavemermaid":         "Wavemermaid.otf",
    "refractionray":       "Refraction Ray.otf",
    "camoblock":           "Camoblock.otf",
    "spiderweb":           "Spider Web.otf",
    "cozywinter":          "Cozy Winter.otf",
    "soccerarmy":          "Soccer Army.otf",
    "tropicalflower":      "Tropical Flower.otf",
}

UPPER   = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER   = "abcdefghijklmnopqrstuvwxyz"
DIGITS  = "0123456789"
SPECIAL = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""

os.makedirs(TEMP_DIR, exist_ok=True)


def _load_font(path):
    try:
        from fontTools.ttLib import TTFont
        ft   = TTFont(path)
        svg  = ft.get("SVG ")
        cmap = ft.getBestCmap()
        upem = ft["head"].unitsPerEm
        hmtx = ft["hmtx"].metrics
        go   = ft.getGlyphOrder()
        return ft, svg, cmap, upem, hmtx, go
    except Exception as e:
        print(f"  ERROR loading {path}: {e}")
        return None


def _build_svg_map(svg_table, glyph_order):
    m = {}
    if not svg_table:
        return m
    for doc in svg_table.docList:
        for gid in range(doc.startGlyphID, doc.endGlyphID + 1):
            m[gid] = (doc.data, doc.startGlyphID != doc.endGlyphID)
    return m


def measure_font(key, filename):
    path = os.path.join(FONTS_DIR, filename)
    if not os.path.exists(path):
        print(f"  SKIP — file not found: {path}")
        return None

    result = _load_font(path)
    if result is None:
        return None
    ft, svg_table, cmap, upem, hmtx, glyph_order = result

    if not svg_table:
        print(f"  SKIP — no SVG table in {filename}")
        return None

    svg_map = _build_svg_map(svg_table, glyph_order)
    scale   = 1000 / upem          # render at 1000px glyph height
    glyph_h = 1000
    vb_top  = -850
    vb_h_r  = 1000

    chars_to_measure = UPPER + LOWER + DIGITS + SPECIAL

    char_svg  = {}
    for ch in chars_to_measure:
        cp        = ord(ch)
        gname     = cmap.get(cp)
        if not gname:
            continue
        try:
            gid = glyph_order.index(gname)
        except ValueError:
            continue
        entry = svg_map.get(gid)
        if not entry:
            continue
        svg_raw, shared = entry
        adv_units = hmtx.get(gname, (upem // 3, 0))[0]
        adv_px    = max(1, int(adv_units * scale))
        h_px      = glyph_h

        svg = svg_raw
        vb_attr = f'viewBox="0 {vb_top} {upem} {vb_h_r}"'
        if "viewBox" in svg:
            svg = re.sub(r'viewBox="[^"]*"', vb_attr, svg)
        else:
            svg = svg.replace("<svg", f"<svg {vb_attr}", 1)
        svg = re.sub(r'\s+preserveAspectRatio="[^"]*"', "", svg)
        svg = re.sub(r'\s+width="[^"]*"',  "", svg)
        svg = re.sub(r'\s+height="[^"]*"', "", svg)
        svg = svg.replace("<svg", f'<svg width="{h_px}px" height="{h_px}px"', 1)
        if shared:
            hide = (f"<style>g{{display:none}}"
                    f"#glyph{gid}{{display:inline}}"
                    f"#glyph\\.{gid}{{display:inline}}</style>")
            svg = re.sub(r"(<svg[^>]*>)", r"\1" + hide, svg, count=1)

        char_svg[ch] = (adv_px, h_px, svg)

    if not char_svg:
        print(f"  SKIP — no SVG chars in {filename}")
        return None

    # Build collage HTML
    collage_w = sum(v[1] for v in char_svg.values()) + 10
    collage_h = glyph_h + 10
    items_html = ""
    x_pos = {}
    cx = 0
    for ch, (adv_px, h_px, svg_str) in char_svg.items():
        svg_b64 = _b64.b64encode(svg_str.encode("utf-8")).decode("ascii")
        items_html += (
            f'<img style="position:absolute;left:{cx}px;top:0;'
            f'width:{h_px}px;height:{h_px}px;display:block" '
            f'src="data:image/svg+xml;base64,{svg_b64}">\n'
        )
        x_pos[ch] = cx
        cx += h_px

    html_src = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0}}html,body{{background:#ffffff;overflow:hidden}}
.c{{position:relative;width:{collage_w}px;height:{collage_h}px}}
</style></head><body>
<div class="c">{items_html}</div>
</body></html>"""

    html_path = os.path.join(TEMP_DIR, f"measure_{key}.html")
    png_path  = os.path.join(TEMP_DIR, f"measure_{key}.png")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_src)
    try:
        os.remove(png_path)
    except Exception:
        pass

    cmd = [
        CHROME_EXE, "--headless", "--no-sandbox",
        "--disable-gpu", "--disable-extensions",
        "--no-first-run", "--disable-sync",
        f"--screenshot={png_path}",
        f"--window-size={collage_w},{collage_h}",
        "file:///" + html_path.replace("\\", "/"),
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=60)
    except Exception as e:
        print(f"  ERROR Chrome: {e}")
        return None

    if not os.path.exists(png_path):
        print(f"  ERROR — Chrome produced no PNG for {key}")
        return None

    try:
        from PIL import Image
        import numpy as np
        collage_img = Image.open(png_path).convert("RGBA")
    except Exception as e:
        print(f"  ERROR loading PNG: {e}")
        return None

    dpr          = collage_img.width / collage_w if collage_w > 0 else 1.0
    baseline_y   = int(850 / 1000 * glyph_h)       # 850/1000 * glyph_h

    above_bl = {}
    below_bl = {}
    for ch, (adv_px, h_px, _) in char_svg.items():
        x0 = int(x_pos[ch] * dpr)
        x1 = int((x_pos[ch] + adv_px) * dpr)
        y1 = int(h_px * dpr)
        crop = collage_img.crop((x0, 0, min(x1, collage_img.width),
                                 min(y1, collage_img.height)))
        if dpr != 1.0:
            crop = crop.resize((adv_px, h_px), Image.LANCZOS)
        arr = np.array(crop)
        # make white transparent
        white = (arr[:, :, 0] > 240) & (arr[:, :, 1] > 240) & (arr[:, :, 2] > 240)
        arr[white, 3] = 0
        row_alpha = arr[:, :, 3].max(axis=1)
        vis = [i for i, a in enumerate(row_alpha) if a > 0]
        if vis:
            yt = vis[0]; yb = vis[-1] + 1
            above_bl[ch] = max(0, min(baseline_y, yb) - yt)
            below_bl[ch] = max(0, yb - baseline_y)
        else:
            above_bl[ch] = 0
            below_bl[ch] = 0

    # Compute category statistics
    def _cat_heights(chars):
        vals = [above_bl[c] for c in chars if c in above_bl and above_bl[c] > 0]
        return vals

    upper_h  = _cat_heights(UPPER)
    lower_h  = _cat_heights(LOWER)
    digit_h  = _cat_heights(DIGITS)
    special_h= _cat_heights(SPECIAL)

    if not upper_h:
        print(f"  SKIP — no uppercase glyphs rendered for {key}")
        return None

    cap_h = sum(upper_h) / len(upper_h)

    def _ratio(vals):
        if not vals:
            return None
        return round(sum(vals) / len(vals) / cap_h, 3)

    metrics = {
        "upper":   _ratio(upper_h),    # should be ~1.0 (reference)
        "lower":   _ratio(lower_h),
        "digit":   _ratio(digit_h),
        "special": _ratio(special_h),
        "cap_h_px": int(cap_h),         # absolute cap height in pixels at glyph_h=1000
    }

    # Per-character detail for logging
    char_detail = {ch: {"above": above_bl.get(ch, 0), "below": below_bl.get(ch, 0)}
                   for ch in chars_to_measure if ch in above_bl}

    return metrics, char_detail


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font",  default=None, help="Measure only this font key")
    parser.add_argument("--out",   default=None, help="Save raw JSON measurements to file")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    targets = {k: v for k, v in PREMIUM_FONTS.items()
               if args.font is None or k == args.font}

    all_metrics = {}
    all_detail  = {}

    for key, filename in targets.items():
        print(f"\n{'─'*60}")
        print(f"Font: {key}  ({filename})")
        result = measure_font(key, filename)
        if result is None:
            continue
        metrics, detail = result
        all_metrics[key] = metrics
        all_detail[key]  = detail
        print(f"  cap_h_px : {metrics['cap_h_px']} px  (at glyph_h=1000)")
        print(f"  upper    : {metrics['upper']:.3f}  (reference)")
        print(f"  lower    : {metrics['lower']}")
        print(f"  digit    : {metrics['digit']}")
        print(f"  special  : {metrics['special']}")
        if args.verbose:
            print(f"\n  Per-character above_bl:")
            for ch in sorted(detail.keys()):
                ratio = round(detail[ch]['above'] / metrics['cap_h_px'], 3) if metrics['cap_h_px'] else 0
                print(f"    {repr(ch):6s}  above={detail[ch]['above']:4d}  below={detail[ch]['below']:4d}  ratio={ratio:.3f}")

    if not all_metrics:
        print("\nNo fonts measured.")
        return

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"metrics": all_metrics, "detail": all_detail}, f, indent=2, ensure_ascii=False)
        print(f"\nRaw measurements saved to: {args.out}")

    # Print dict ready to paste into batch_processor.py
    print(f"\n{'='*60}")
    print("Paste this into batch_processor.py as FONT_CHAR_METRICS:\n")
    print("FONT_CHAR_METRICS = {")
    for key, m in all_metrics.items():
        upper  = m["upper"]
        lower  = m["lower"]
        digit  = m["digit"]
        special= m["special"]
        print(f'    "{key}": {{')
        print(f'        "upper":   {upper},')
        print(f'        "lower":   {lower},')
        print(f'        "digit":   {digit},')
        print(f'        "special": {special},')
        print(f'    }},')
    print("}")


if __name__ == "__main__":
    main()
