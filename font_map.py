# font_map.py — Central font name mapping for Varsany Automation
# Maps database font names → (PostScript name, Family name for PS2026)
# Default fallback: Arial Bold

DEFAULT_PS   = "Arial-BoldMT"
DEFAULT_FAMILY = "Arial"
DEFAULT_STYLE  = "Bold"

# (db_name): (postscript_name, family_name, style_name)
FONT_MAP = {
    # ── Normal fonts — INSTALLED ──────────────────────────────────────────────
    "Arial":                    ("Arial-BoldMT",              "Arial",                "Bold"),
    "Arial Bold":               ("Arial-BoldMT",              "Arial",                "Bold"),
    "No":                       ("Arial-BoldMT",              "Arial",                "Bold"),
    "Helvetica":                ("Helvetica-Bold",             "Helvetica",            "Bold"),
    "Helvetica Neue":           ("Helvetica-Bold",             "Helvetica",            "Bold"),
    "Bebas Neue":               ("BebasNeue-Regular",          "Bebas Neue",           "Regular"),
    "Chewy":                    ("Chewy-Regular",              "Chewy",                "Regular"),
    "Lato":                     ("Lato-Regular",               "Lato",                 "Regular"),
    "Russo One":                ("RussoOne-Regular",           "Russo One",            "Regular"),
    "Permanent Marker":         ("PermanentMarker-Regular",    "Permanent Marker",     "Regular"),
    "Ultra":                    ("Ultra-Regular",              "Ultra",                "Regular"),
    "Fondamento":               ("Fondamento-Regular",         "Fondamento",           "Regular"),
    "Abel":                     ("Abel-Regular",               "Abel",                 "Regular"),
    "Roboto":                   ("Roboto-Regular",             "Roboto",               "Regular"),
    "Verdana":                  ("Verdana",                    "Verdana",              "Regular"),

    # ── Normal fonts — MISSING (fallback to Arial Bold) ───────────────────────
    "Great Vibes":              ("Arial-BoldMT",              "Arial",                "Bold"),
    "Rhinestone Font":          ("Arial-BoldMT",              "Arial",                "Bold"),
    "Rhinestone font":          ("Arial-BoldMT",              "Arial",                "Bold"),
    "Rhinestone":               ("Arial-BoldMT",              "Arial",                "Bold"),
    "DTF Text":                 ("Arial-BoldMT",              "Arial",                "Bold"),
    "Embroidery Font":          ("Arial-BoldMT",              "Arial",                "Bold"),
    "Embroidery font":          ("Arial-BoldMT",              "Arial",                "Bold"),
    "Vinyl Font":               ("VINYLFONT",                 "VINYLFONT",            "Regular"),
    "VinylFont":                ("VINYLFONT",                 "VINYLFONT",            "Regular"),
    "Wellies Font":             ("Arial-BoldMT",              "Arial",                "Bold"),
    "Wellis font":              ("Arial-BoldMT",              "Arial",                "Bold"),
    "Varsany Crystal Font":     ("Arial-BoldMT",              "Arial",                "Bold"),
    "Varsany":                  ("Arial-BoldMT",              "Arial",                "Bold"),
    "Varsany Rhinestone Font":  ("Arial-BoldMT",              "Arial",                "Bold"),
    "Sippy Cup Font":           ("Arial-BoldMT",              "Arial",                "Bold"),
    "Gloves Font":              ("Arial-BoldMT",              "Arial",                "Bold"),
    "Shorts Font":              ("Arial-BoldMT",              "Arial",                "Bold"),
    "ShortsFont":               ("Arial-BoldMT",              "Arial",                "Bold"),
    "Super Vibes":              ("Arial-BoldMT",              "Arial",                "Bold"),
    "T-Shirt Font":             ("Arial-BoldMT",              "Arial",                "Bold"),
    "BSL":                      ("Arial-BoldMT",              "Arial",                "Bold"),
    "AAAGoldenLotus Stg1_Ver1": ("Arial-BoldMT",              "Arial",                "Bold"),
    "25mm Caps rhinestone font":("Arial-BoldMT",              "Arial",                "Bold"),

    # ── Premium fonts — INSTALLED ─────────────────────────────────────────────
    "Spidey Font":              ("SpiderWebRegular",           "Spider Web",           "Regular"),
    "Spider Web":               ("SpiderWebRegular",           "Spider Web",           "Regular"),
    "Paint Font":               ("PaintSplashesRainbow",       "Paint Splashes Rainbow","Regular"),
    "Block Font":               ("ColorfulBlocksRegular",      "Colorful Blocks",      "Regular"),
    "Colorful Blocks":          ("ColorfulBlocksRegular",      "Colorful Blocks",      "Regular"),
    "Texture Font":             ("SmartKidsRegular",           "Smart Kids",           "Regular"),
    "Smart Kids":               ("SmartKidsRegular",           "Smart Kids",           "Regular"),
    "Camo Font":                ("CamoBlockRegular",           "Camo Block",           "Regular"),
    "Camoblock":                ("CamoBlockRegular",           "Camo Block",           "Regular"),
    "Reflection Font":          ("RefractionRayRegular",       "RefractionRay",        "Regular"),
    "Refraction Ray":           ("RefractionRayRegular",       "RefractionRay",        "Regular"),
    "Flower Font":              ("BouqetDisplay",              "Bouqet",               "Display"),
    "Bouquet Display":          ("BouqetDisplay",              "Bouqet",               "Display"),
    "Football Font":            ("SoccerArmyVer2",             "Soccer Army Ver 2",    "Regular"),
    "Soccer Army":              ("SoccerArmyVer2",             "Soccer Army Ver 2",    "Regular"),
    "Cozy Font":                ("CozyWinterRegular",          "Cozy Winter",          "Regular"),
    "Cozy Winter":              ("CozyWinterRegular",          "Cozy Winter",          "Regular"),
    "Mermaid Font":             ("WavemermaidRegular",         "Wavemermaid",          "Regular"),
    "Wavemermaid":              ("WavemermaidRegular",         "Wavemermaid",          "Regular"),
}


def get_font_info(raw_font_json):
    """Parse font JSON from DB. Returns (ps_name, family, style)."""
    import json as _json
    if not raw_font_json:
        return (DEFAULT_PS, DEFAULT_FAMILY, DEFAULT_STYLE)
    try:
        raw = raw_font_json.strip()
        if raw.startswith("{"):
            d = _json.loads(raw)
            # PremiumFont takes priority if not "No"
            font = (d.get("PremiumFont") or "").strip()
            if not font or font.lower() == "no":
                font = (d.get("NormalFont") or "").strip()
        else:
            font = raw
        result = FONT_MAP.get(font)
        if result:
            return result
        # Try case-insensitive match
        font_lower = font.lower()
        for k, v in FONT_MAP.items():
            if k.lower() == font_lower:
                return v
        # Not found — fallback
        print(f"  [font_map] Unknown font '{font}' — using Arial Bold fallback")
        return (DEFAULT_PS, DEFAULT_FAMILY, DEFAULT_STYLE)
    except Exception as e:
        print(f"  [font_map] Error parsing font JSON: {e} — using Arial Bold fallback")
        return (DEFAULT_PS, DEFAULT_FAMILY, DEFAULT_STYLE)


def get_ps_font_name(raw_font_json):
    """Legacy helper — returns PostScript name only."""
    return get_font_info(raw_font_json)[0]
