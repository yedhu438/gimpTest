# bg_remover.py — Background removal for Varsany DTF print orders
# Rule: if image background colour matches garment colour → remove it (colour-key).
# Otherwise keep original.

from pathlib import Path

GARMENT_COLOURS = {
    "BPnk": (255, 182, 193),
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

DIFF_THRESH    = 40    # max colour distance to consider "matching"
EDGE_MATCH_MIN = 0.95  # 95% of edge pixels must match garment colour
INTERIOR_MAX   = 0.80  # 80%+ interior matching = flat image, skip removal
ALPHA_THRESH   = 128   # alpha below this → fully transparent


def colour_diff(c1, c2):
    return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5


def get_garment_colour(sku):
    # Search the full SKU for a colour code — longest match wins.
    # Handles both "MenTee_BlkS" (suffix) and "VestBlkS" (embedded).
    for code, rgb in sorted(GARMENT_COLOURS.items(), key=lambda x: len(x[0]), reverse=True):
        if code in sku:
            return code, rgb
    return None, None


def _edge_pixels(img_rgb):
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
    """True if >=95% of edge pixels match garment colour."""
    edge = _edge_pixels(img_rgb)
    if not edge: return False
    match = sum(1 for p in edge if colour_diff(p, garment_rgb) <= DIFF_THRESH)
    return (match / len(edge)) >= EDGE_MATCH_MIN


def _check_interior_flat(img_rgb, garment_rgb):
    """True if >=80% of interior pixels match garment colour (flat image, no design)."""
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
    """Remove only pixels that match the garment colour. All other colours kept."""
    result = img_rgba.copy()
    px = result.load()
    w, h = result.size
    for x in range(w):
        for y in range(h):
            r, g, b, a = px[x, y]
            if colour_diff((r, g, b), garment_rgb) <= DIFF_THRESH:
                px[x, y] = (r, g, b, 0)
    return result


def _cleanup(img_rgba):
    """Set alpha < 128 → fully transparent. Crop to content bounding box."""
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
    Main entry point. Removes background if it matches garment colour.

    Step 1: Get garment RGB from SKU — if not in map, skip.
    Step 2: Sample 4 edges — if >=95% match garment colour, proceed. Else keep original.
    Step 3: Sample interior — if >=80% matches (flat image, no design), skip removal.
    Step 4: Colour-key removal — remove only pixels matching garment colour.
            Works for ALL garments (black, white, navy, pink etc.) — same rule.
    Step 5: Cleanup alpha threshold + crop to content.
    """
    try:
        from PIL import Image

        # Step 1
        code, garment_rgb = get_garment_colour(sku)
        if garment_rgb is None:
            return img_path

        img = Image.open(img_path).convert("RGBA")
        img_rgb = img.convert("RGB")

        # Step 2 — edge check
        if not _check_edge(img_rgb, garment_rgb):
            return img_path  # background colour ≠ garment colour, keep original

        # Step 3 — flat image check
        if _check_interior_flat(img_rgb, garment_rgb):
            return img_path  # no design to keep, skip

        # Step 4 — colour-key removal (same for ALL garments)
        print(f"  [bg] colour-key removal ({code}): removing {garment_rgb} pixels")
        result = _colour_key(img, garment_rgb)

        # Step 5 — cleanup + crop
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
        print(f"{'SKU':<25} {'Code':<6} {'RGB'}")
        print("=" * 55)
        for sku in ["MenTee_BlkS","WmnTee_WhtXL","KidsTee_NvyM",
                    "WmnTee_PnkL","KidsTee_RBluL","MenTee_GryM"]:
            code, rgb = get_garment_colour(sku)
            print(f"{sku:<25} {str(code):<6} {str(rgb)}")
