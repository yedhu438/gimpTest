"""
Standalone font audit — no Pillow/rembg required.
Connects to the DB to read font names from orders (if available),
then checks which TTF/OTF files are present on this machine.
Falls back to checking all fonts listed in FONT_ALIASES if DB is unreachable.
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')

# ── DB connection ─────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

import pyodbc
from db import get_connection as _db_get_connection

# ── Font folders ──────────────────────────────────────────────────────────────
_base = os.environ.get("VARSANY_BASE", r"C:\Varsany")
FONT_FOLDERS = [
    os.path.join(_base, "Fonts"),
    r"W:\fonts",
    r"C:\Windows\Fonts",
]

# ── Font aliases (mirrors batch_processor.py) ─────────────────────────────────
FONT_ALIASES = {
    "abel":             "abelregular",
    "arial":            "arial",
    "arialbold":        "arialbd",
    "bebasneuefree":    "bebasneueregular",
    "bebasneuepro":     "bebasneueregular",
    "bebasneue":        "bebasneueregular",
    "chewy":            "chewyregular",
    "fondamento":       "fondamentoregular",
    "helvetica":        "arial",
    "lato":             "latoregular",
    "latobold":         "latobold",
    "permanentmarker":  "permanentmarkerregular",
    "roboto":           "robotoregular",
    "robotoregular":    "robotoregular",
    "russoone":         "russooneregular",
    "ultra":            "ultraregular",
    "verdana":          "verdana",
    # Premium texture fonts
    "texturefont":      "smartkids",
    "texture font":     "smartkids",
    "texture":          "smartkids",
    "blockfont":        "colorfulblocks",
    "block font":       "colorfulblocks",
    "colorfulblock":    "colorfulblocks",
    "paintfont":        "paintsplashesrainbow",
    "paint font":       "paintsplashesrainbow",
    "paintsplashes":    "paintsplashesrainbow",
    "mermaidfont":      "wavemermaid",
    "mermaid font":     "wavemermaid",
    "mermaid":          "wavemermaid",
    "reflectionfont":   "refractionray",
    "reflection font":  "refractionray",
    "reflection":       "refractionray",
    "refractionray":    "refractionray",
    "camofont":         "camoblock",
    "camo font":        "camoblock",
    "camo":             "camoblock",
    "spideyfont":       "spiderweb",
    "spidey font":      "spiderweb",
    "spidey":           "spiderweb",
    "cozyfont":         "cozywinter",
    "cozy font":        "cozywinter",
    "cozy":             "cozywinter",
    "footballfont":     "soccerarmy",
    "football font":    "soccerarmy",
    "football":         "soccerarmy",
    "flowerfont":       "tropicalflower",
    "flower font":      "tropicalflower",
    "flower":           "tropicalflower",
    "tropicalflower":   "tropicalflower",
    "vinyl":            "vinylfont",
    "vinylfont":        "vinylfont",
    "vinyl font":       "vinylfont",
    # Non-print methods -> None (no TTF by design)
    "rhinestone":               None,
    "rhinestonefont":           None,
    "embroidery":               None,
    "embroideryfont":           None,
    "emroideryfont":            None,
    "crystalfont":              None,
    "varsanycrystal":           None,
    "varsanycrystalfont":       None,
    "varsanyrhinestonefont":    None,
    "25mmcapsrhinestonefont":   None,
    # Custom fonts not yet installed
    "bsl":          None,
    "dtftext":      None,
    "glovesfont":   None,
    "shortsfont":   None,
    "supervibes":   None,
    "varsany":      None,
    "welliesfont":  None,
    "wellisfont":   None,
}

def _norm(s):
    return s.lower().replace(' ', '').replace('-', '').replace('_', '')

# ── Build font index from available folders ───────────────────────────────────
font_index = {}
for folder in FONT_FOLDERS:
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.lower().endswith(('.ttf', '.otf')):
                key = _norm(os.path.splitext(f)[0])
                if key not in font_index:
                    font_index[key] = os.path.join(folder, f)

# ── Try DB for actual order font names ────────────────────────────────────────
db_fonts = []
db_error = None
db_source = None

try:
    conn = _db_get_connection(timeout=8)
    cur  = conn.cursor()
    cur.execute("""
        SELECT DISTINCT v FROM (
            SELECT FrontFonts  AS v FROM tblCustomOrderDetails WHERE FrontFonts  IS NOT NULL AND FrontFonts  <> ''
            UNION
            SELECT BackFonts   AS v FROM tblCustomOrderDetails WHERE BackFonts   IS NOT NULL AND BackFonts   <> ''
            UNION
            SELECT PocketFonts AS v FROM tblCustomOrderDetails WHERE PocketFonts IS NOT NULL AND PocketFonts <> ''
            UNION
            SELECT SleeveFonts AS v FROM tblCustomOrderDetails WHERE SleeveFonts IS NOT NULL AND SleeveFonts <> ''
        ) t ORDER BY v
    """)
    db_fonts = [r[0] for r in cur.fetchall()]
    conn.close()
    db_source = f"{_server} / {_db}"
except Exception as e:
    db_error = str(e)

# ── Parse JSON font values ────────────────────────────────────────────────────
def extract_font_names(raw):
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith('{'):
        try:
            data = json.loads(raw)
            return [v for v in (data.get("PremiumFont"), data.get("NormalFont")) if v]
        except Exception:
            return [raw]
    return [raw]

# ── Determine font list to check ──────────────────────────────────────────────
# If DB available: use actual order fonts.
# If not: check every font name the system expects to handle (FONT_ALIASES keys).
if db_fonts:
    font_list = []
    for raw in db_fonts:
        font_list.extend(extract_font_names(raw))
    check_source = f"Live DB ({len(db_fonts)} distinct values)"
else:
    # Fall back: all alias names (deduplicated by display name)
    font_list = sorted(set(FONT_ALIASES.keys()))
    check_source = "FONT_ALIASES (fallback — DB not reachable)"

# ── Check each font ───────────────────────────────────────────────────────────
found   = []   # (display_name, file_path)
missing = []   # (display_name, reason)
skipped = []   # display_name

seen = set()
for font_name in font_list:
    if font_name in seen:
        continue
    seen.add(font_name)

    n = _norm(font_name)

    if n in FONT_ALIASES:
        alias = FONT_ALIASES[n]
        if alias is None:
            skipped.append(font_name)
            continue
        if alias in font_index:
            found.append((font_name, font_index[alias]))
        else:
            missing.append((font_name, f"alias -> '{alias}'  (no .ttf/.otf file found)"))
    elif n in font_index:
        found.append((font_name, font_index[n]))
    else:
        missing.append((font_name, "not in aliases, not found in any font folder"))

# ── Display ───────────────────────────────────────────────────────────────────
W = 72

def hr(c='-'): print(c * W)

hr('=')
print("  VARSANY FONT AUDIT")
hr('=')

if db_error:
    print(f"\n  [DB not reachable]  {db_error[:120]}")
    print(f"  Falling back to checking all fonts in FONT_ALIASES.\n")
else:
    print(f"\n  Connected to: {db_source}")
    print(f"  {len(db_fonts)} distinct font values in orders.\n")

print(f"  Checking: {check_source}")
hr()

print(f"\n  PRESENT ({len(found)}) -- file found on this machine:")
hr()
if found:
    for name, path in sorted(found):
        short = path
        for prefix, label in [
            (r"C:\Windows\Fonts\\",   "[WinFonts]"),
            (r"C:\gimpTest\Fonts\\",   "[VarsanyFonts]"),
            (r"W:\fonts\\",           "[W:\\fonts]"),
        ]:
            if path.startswith(prefix):
                short = label + "\\" + path[len(prefix):]
                break
        print(f"  [OK]  {name:<33} {short}")
else:
    print("  (none)")

print(f"\n  MISSING ({len(missing)}) -- file NOT found:")
hr()
if missing:
    for name, reason in sorted(missing):
        print(f"  [!!]  {name:<33} {reason}")
else:
    print("  (none -- all fonts accounted for!)")

print(f"\n  SKIPPED ({len(skipped)}) -- no TTF by design (rhinestone / embroidery / custom):")
hr()
if skipped:
    for name in sorted(skipped):
        print(f"  [--]  {name}")
else:
    print("  (none)")

print(f"\n  Font folders searched:")
hr()
for folder in FONT_FOLDERS:
    status = "EXISTS  " if os.path.exists(folder) else "MISSING "
    print(f"  [{status}]  {folder}")

print(f"\n  Total font files indexed: {len(font_index)}")
hr('=')
print()
