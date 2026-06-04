# bg_remover.py — Background removal for Varsany DTF print orders
# Full 5-step spec implementation

from pathlib import Path

# ── Step 1: Garment colour map ────────────────────────────────────────────────
GARMENT_COLOURS = {
    "BPnk": (255, 182, 193),  # longest first
    "GryM": (160, 160, 160),
    "RBlu": (65,  105, 225),
    "SBlu": (135, 206, 235),
    "Blk":  (20,  20,  20),
    "Wht":  (255, 255, 255),
    "Nvy":  (31,  40,  80),
    "Red":  (200, 30,  30),
    "Pnk":  (255, 150, 180),
    "Gry":  (150, 150, 150),
    "Blu":  (30,  100, 200),
    "Ylw":  (255, 220, 0),
}

DIFF_THRESH      = 40    # colour distance threshold
EDGE_MATCH_MIN   = 0.95  # 95% edges must match
INTERIOR_MAX     = 0.80  # 80%+ interior = flat image, skip
LIGHT_THRESH     = 160   # brightness above this = light garment
ALPHA_THRESH     = 128   # alpha below this → fully transparent
AI_VISIBLE_MIN   = 0.15  # if AI leaves <15% visible → fallback


def colour_diff(c1, c2):
    return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5


def get_garment_colour(sku):
    """Step 1 — Extract garment RGB from SKU suffix."""
    suffix = sku.rsplit("_", 1)[-1] if "_" in sku else sku
    for code, rgb in GARMENT_COLOURS.items():
        if suffix.startswith(code):
            return code, rgb
    return None, None


def is_light(rgb):
    return sum(rgb) / 3 > LIGHT_THRESH


def _edge_pixels(img_rgb):
    """Return list of RGB tuples from all four edges."""
    w, h = img_rgb.size
    px = img_rgb.load()
    edge = []
    for x in range(w):
        edge.append(px[x, 0][:3])
        edge.append(px[x, h-1][:3])
    for y in range(1, h-1):
        edge.append(px[0, y][:3])
        edge.append(px[w-1, y][:3])
    return edge


def _check_edge(img_rgb, garment_rgb):
    """Step 2 — True if ≥95% of edge pixels match garment colour."""
    edge = _edge_pixels(img_rgb)
    if not edge:
        return False
    match = sum(1 for p in edge if colour_diff(p, garment_rgb) <= DIFF_THRESH)
    return (match / len(edge)) >= EDGE_MATCH_MIN


def _check_interior_flat(img_rgb, garment_rgb):
    """Step 3 — True if ≥80% of interior pixels match (flat image, skip)."""
    w, h = img_rgb.size
    x0, y0 = int(w*0.10), int(h*0.10)
    x1, y1 = int(w*0.90), int(h*0.90)
    px = img_rgb.load()
    total = match = 0
    for x in range(x0, x1):
        for y in range(y0, y1):
            total += 1
            if colour_diff(px[x, y][:3], garment_rgb) <= DIFF_THRESH:
                match += 1
    return total > 0 and (match / total) >= INTERIOR_MAX


def _colour_key(img_rgba, garment_rgb):
    """Step 4 dark — Remove pixels matching garment colour."""
    result = img_rgba.copy()
    px = result.load()
    w, h = result.size
    for x in range(w):
        for y in range(h):
            r, g, b, a = px[x, y]
            if colour_diff((r, g, b), garment_rgb) <= DIFF_THRESH:
                px[x, y] = (r, g, b, 0)
    return result


def _ai_remove(img_rgba):
    """Step 4 light — AI removal via rembg."""
    from rembg import remove as rembg_remove
    return rembg_remove(img_rgba)


def _cleanup(img_rgba):
    """Step 5 — Threshold alpha + crop to content."""
    result = img_rgba.copy().convert("RGBA")
    px = result.load()
    w, h = result.size
    for x in range(w):
        for y in range(h):
            r, g, b, a = px[x, y]
            if a < ALPHA_THRESH:
                px[x, y] = (r, g, b, 0)
    bbox = result.getbbox()
    return result.crop(bbox) if bbox else result


def remove_background(img_path, sku, output_path=None):
    """
    Main entry point — full 5-step pipeline.
    Returns path to cleaned PNG, or original path if no removal needed.
    """
    try:
        from PIL import Image

        # Step 1
        code, garment_rgb = get_garment_colour(sku)
        if garment_rgb is None:
            return img_path  # colour not in map

        img = Image.open(img_path).convert("RGBA")
        img_rgb = img.convert("RGB")

        # Step 2
        if not _check_edge(img_rgb, garment_rgb):
            return img_path  # background doesn't match garment

        light = is_light(garment_rgb)

        # Step 3 (light garments only)
        if light and _check_interior_flat(img_rgb, garment_rgb):
            return img_path  # flat colour image, skip

        # Step 4
        result = None
        if not light:
            # Dark garment: colour-key
            print(f"  [bg] colour-key removal ({code})")
            result = _colour_key(img, garment_rgb)
        else:
            # Light garment: try rembg, fall back to colour-key
            try:
                print(f"  [bg] AI (rembg) removal ({code})")
                result = _ai_remove(img)
                # Validate rembg output
                px = result.load()
                w, h = result.size
                visible = sum(1 for x in range(w) for y in range(h) if px[x, y][3] > 10)
                if visible / (w * h) < AI_VISIBLE_MIN:
                    print(f"  [bg] rembg <15% visible — colour-key fallback")
                    result = _colour_key(img, garment_rgb)
            except ImportError:
                print(f"  [bg] rembg not installed — colour-key fallback")
                result = _colour_key(img, garment_rgb)
            except Exception as e:
                print(f"  [bg] rembg error: {e} — colour-key fallback")
                result = _colour_key(img, garment_rgb)

        # Step 5
        result = _cleanup(result)

        out = output_path or str(Path(img_path).with_suffix(".clean.png"))
        result.save(out, "PNG")
        print(f"  [bg] saved: {Path(out).name}")
        return out

    except Exception as e:
        print(f"  [bg] failed: {e} — using original")
        return img_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        out = remove_background(sys.argv[1], sys.argv[2])
        print(f"Result: {out}")
    else:
        print(f"{'SKU':<25} {'Code':<6} {'RGB':<22} {'Light'}")
        print("=" * 60)
        for sku in ["MenTee_BlkS","WmnTee_WhtXL","KidsTee_NvyM",
                    "WmnTee_PnkL","KidsTee_RBluL","KidsTee_Ylw1213",
                    "AnyTxtBabyVest_BPnkM","MenTee_GryMS"]:
            code, rgb = get_garment_colour(sku)
            l = is_light(rgb) if rgb else "-"
            print(f"{sku:<25} {str(code):<6} {str(rgb):<22} {l}")
