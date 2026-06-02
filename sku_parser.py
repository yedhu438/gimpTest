# sku_parser.py — Extract colour, size and build zone label from SKU

# Longest codes first — order matters!
COLOUR_CODES = [
    ("RBlu",  "Royal Blue"),
    ("SBlu",  "Sky Blue"),
    ("BPnk",  "Baby Pink"),
    ("GryM",  "Grey Marl"),
    ("Camo",  "Camo"),
    ("Ivry",  "Ivory"),
    ("Blk",   "Black"),
    ("Wht",   "White"),
    ("Nvy",   "Navy"),
    ("Red",   "Red"),
    ("Pnk",   "Pink"),
    ("Gry",   "Grey"),
    ("Blu",   "Blue"),
    ("Grn",   "Green"),
    ("Ylw",   "Yellow"),
    ("Fus",   "Fuchsia"),
    ("Pur",   "Purple"),
    ("Org",   "Orange"),
    ("Bur",   "Burgundy"),
    ("Nat",   "Natural"),
    ("Lav",   "Lavender"),
    ("TD",    "Tie Dye"),
]

def format_size(size_str):
    """Convert numeric size to ranged format: 911->9-11, 78->7-8, 1213->12-13"""
    if not size_str:
        return ""
    if size_str.isdigit():
        n = len(size_str)
        half = n // 2
        return size_str[:half] + "-" + size_str[half:]
    return size_str

def parse_sku(sku):
    """
    Parse SKU to extract colour name and size.
    Returns (colour_name, size_str) or (None, None) if not parseable.
    e.g. MenTee_WhtXL -> ("White", "XL")
         KidsTee_Blk78 -> ("Black", "7-8")
         MenTee_RedM   -> ("Red", "M")
    """
    if "_" not in sku:
        return None, None
    suffix = sku.rsplit("_", 1)[-1]  # take last part after final underscore
    # Try each colour code (longest first)
    for code, name in COLOUR_CODES:
        if suffix.startswith(code):
            size_raw = suffix[len(code):]
            size = format_size(size_raw)
            return name, size
    return None, None

def build_zone_label(zone, sku, is_multi_size_order=False):
    """
    Build the label text for a print zone.
    - Single design (same for all sizes): just zone name e.g. "FRONT"
    - Different design per size: "FRONT - White XL"
    """
    zone_upper = zone.upper()
    if not is_multi_size_order:
        return zone_upper
    colour, size = parse_sku(sku)
    if colour or size:
        parts = [p for p in [colour, size] if p]
        return f"{zone_upper} - {' '.join(parts)}"
    return zone_upper


if __name__ == "__main__":
    # Test
    tests = [
        ("MenTee_WhtXL",    "White", "XL"),
        ("KidsTee_Blk78",   "Black", "7-8"),
        ("MenTee_NvyXXXL",  "Navy",  "XXXL"),
        ("WmnTee_PnkM",     "Pink",  "M"),
        ("KidsTee_RBluL",   "Royal Blue", "L"),
        ("MenTee_GryMS",    "Grey Marl", "S"),
        ("AnyTxt_BPnk911",  "Baby Pink", "9-11"),
        ("MenTee_TD",       "Tie Dye", ""),
        ("MenTee_BlkS",     "Black", "S"),
    ]
    print(f"{'SKU':<25} {'Colour':<15} {'Size':<10} {'Label'}")
    print("="*70)
    for sku, exp_col, exp_size in tests:
        col, size = parse_sku(sku)
        label = build_zone_label("front", sku, is_multi_size_order=True)
        ok = "OK" if col == exp_col and size == exp_size else "FAIL"
        print(f"{sku:<25} {str(col):<15} {str(size):<10} {label}  [{ok}]")
