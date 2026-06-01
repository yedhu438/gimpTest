# font_map.py — Central font name mapping for Varsany Automation
# Maps database font names to PostScript font names installed in Windows
# Used by all export scripts and the UXP plugin job writer
#
# To add a new font:
# 1. Install the font file in A:\font\Fonts or A:\font\Premium Fonts
# 2. Run: python check_all_fonts.py to get the PostScript name
# 3. Add the mapping here
# 4. Run install_fonts.py on any new machine to install the fonts

FONT_NAME_MAP = {
    # ── Normal fonts ──────────────────────────────────────────────────────────
    "Arial":             "ArialMT",
    "Arial Bold":        "Arial-BoldMT",
    "No":                "ArialMT",
    "Helvetica":         "Helvetica-Bold",
    "Helvetica Neue":    "Helvetica-Bold",
    "Bebas Neue":        "BebasNeue-Regular",
    "Chewy":             "Chewy-Regular",
    "Lato":              "Lato-Regular",
    "Russo One":         "RussoOne-Regular",
    "Permanent Marker":  "PermanentMarker-Regular",
    "Roboto":            "Roboto-Regular",
    "Ultra":             "Ultra-Regular",
    "Fondamento":        "Fondamento-Regular",
    "Abel":              "Abel-Regular",

    # ── Premium fonts ─────────────────────────────────────────────────────────
    # DB Name            PostScript Name         Font File
    "Spidey Font":       "SpiderWebRegular",     # Spider Web.otf
    "Spider Web":        "SpiderWebRegular",
    "Paint Font":        "PaintSplashesRainbow", # Paint Splashes Rainbow.otf
    "Block Font":        "ColorfulBlocksRegular",# Colorful Blocks.otf
    "Colorful Blocks":   "ColorfulBlocksRegular",
    "Texture Font":      "SmartKidsRegular",     # Smart Kids.otf
    "Smart Kids":        "SmartKidsRegular",
    "Camo Font":         "CamoBlockRegular",     # Camoblock.otf
    "Camoblock":         "CamoBlockRegular",
    "Reflection Font":   "RefractionRayRegular", # Refraction Ray.otf
    "Refraction Ray":    "RefractionRayRegular",
    "Flower Font":       "BouqetDisplay",        # Bouqet-Display.otf
    "Bouquet Display":   "BouqetDisplay",
    "Bouqet Display":    "BouqetDisplay",
    "Football Font":     "SoccerArmyVer2",       # Soccer Army.otf
    "Soccer Army":       "SoccerArmyVer2",
    "Cozy Font":         "CozyWinterRegular",    # Cozy Winter.otf
    "Cozy Winter":       "CozyWinterRegular",
    "Mermaid Font":      "WavemermaidRegular",   # Wavemermaid.otf
    "Wavemermaid":       "WavemermaidRegular",

    # ── Not yet available (missing font files) ────────────────────────────────
    # "Rhinestone Font": ???  — file not in A:\font
    # "DTF Text":        ???  — file not in A:\font
    # "Varsany Crystal": ???  — file not in A:\font
    # "Vinyl Font":      ???  — file not in A:\font
    # "Wellies Font":    ???  — file not in A:\font
    # "Embroidery Font": ???  — file not in A:\font
}


def get_ps_font_name(raw_font_json):
    """Parse font JSON from DB and return PostScript name."""
    import json
    if not raw_font_json:
        return "ArialMT"
    try:
        raw = raw_font_json.strip()
        if raw.startswith("{"):
            d = json.loads(raw)
            font = d.get("PremiumFont", "").strip()
            if not font or font.lower() in ("no", ""):
                font = d.get("NormalFont", "Arial").strip()
        else:
            font = raw
        return FONT_NAME_MAP.get(font, "ArialMT")
    except Exception:
        return "ArialMT"
