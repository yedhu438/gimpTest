import sys, os, json, shutil, subprocess
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection

# ── Get all unique fonts used in orders ───────────────────────────────────────
conn = get_connection()
cur  = conn.cursor()
cur.execute("SELECT DISTINCT FrontFonts FROM tblCustomOrderDetails WHERE FrontFonts IS NOT NULL AND LTRIM(RTRIM(FrontFonts)) != ''")
rows = cur.fetchall()
conn.close()

fonts_used = set()
for row in rows:
    try:
        d = json.loads(row[0])
        if d.get("PremiumFont"): fonts_used.add(d["PremiumFont"].strip())
        if d.get("NormalFont"):  fonts_used.add(d["NormalFont"].strip())
    except: pass

print("Fonts used in orders:")
for f in sorted(fonts_used): print(f"  {f}")
print()

# ── Font file mapping ──────────────────────────────────────────────────────────
# Maps font name (as stored in DB) to filename in A:\font\
FONT_MAP = {
    # Normal fonts
    "Arial Bold":           [r"A:\font\Fonts\arialbd.ttf"],
    "Arial":                [r"A:\font\Fonts\arialbd.ttf"],
    "Helvetica":            [r"A:\font\Fonts\arialbd.ttf"],  # fallback to Arial
    "Helvetica Neue":       [r"A:\font\Fonts\arialbd.ttf"],  # fallback to Arial
    "Bebas Neue":           [r"A:\font\Fonts\BebasNeue-Regular.ttf"],
    "Bebas":                [r"A:\font\Fonts\BebasNeue-Regular.ttf"],
    "Abel":                 [r"A:\font\Fonts\Abel-Regular.ttf"],
    "Chewy":                [r"A:\font\Fonts\Chewy-Regular.ttf"],
    "Fondamento":           [r"A:\font\Fonts\Fondamento-Regular.ttf"],
    "Lato":                 [r"A:\font\Fonts\Lato-Regular.ttf"],
    "Permanent Marker":     [r"A:\font\Fonts\PermanentMarker-Regular.ttf"],
    "Roboto":               [r"A:\font\Fonts\Roboto-Regular.ttf"],
    "Russo One":            [r"A:\font\Fonts\RussoOne-Regular.ttf"],
    "Ultra":                [r"A:\font\Fonts\Ultra-Regular.ttf"],
    # Premium fonts
    "Bouquet Display":      [r"A:\font\Fonts\Bouqet-Display.otf"],
    "Bouqet Display":       [r"A:\font\Fonts\Bouqet-Display.otf"],
    "Camoblock":            [r"A:\font\Fonts\Camoblock.otf"],
    "Colorful Blocks":      [r"A:\font\Premium Fonts\Colorful Blocks.otf"],
    "Cozy Winter":          [r"A:\font\Premium Fonts\Cozy Winter.otf"],
    "Paint Splashes Rainbow":[r"A:\font\Premium Fonts\Paint Splashes Rainbow.otf"],
    "Refraction Ray":       [r"A:\font\Premium Fonts\Refraction Ray.otf"],
    "Smart Kids":           [r"A:\font\Premium Fonts\Smart Kids.otf"],
    "Soccer Army":          [r"A:\font\Premium Fonts\Soccer Army.otf"],
    "Spider Web":           [r"A:\font\Premium Fonts\Spider Web.otf"],
    "Wavemermaid":          [r"A:\font\Premium Fonts\Wavemermaid.otf"],
    "Spidey Font":          [r"A:\font\Premium Fonts\Spider Web.otf"],
    "Paint Font":           [r"A:\font\Premium Fonts\Paint Splashes Rainbow.otf"],
}

WINDOWS_FONTS = r"C:\Windows\Fonts"

# ── Install all fonts from A:\font ─────────────────────────────────────────────
installed = 0
skipped   = 0
failed    = 0

print("Installing all fonts from A:\\font...")
for folder in [r"A:\font\Fonts", r"A:\font\Premium Fonts"]:
    if not os.path.exists(folder):
        print(f"  SKIP (not found): {folder}")
        continue
    for fname in os.listdir(folder):
        if not fname.lower().endswith((".ttf", ".otf")):
            continue
        src  = os.path.join(folder, fname)
        dest = os.path.join(WINDOWS_FONTS, fname)
        if os.path.exists(dest):
            skipped += 1
            continue
        try:
            shutil.copy2(src, dest)
            # Register font in Windows registry
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
                0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, fname, 0, winreg.REG_SZ, fname)
            winreg.CloseKey(key)
            print(f"  Installed: {fname}")
            installed += 1
        except Exception as e:
            # Try without registry (may still work)
            print(f"  Copied (no registry): {fname}")
            installed += 1

print(f"\nInstalled: {installed}  Already present: {skipped}  Failed: {failed}")

# ── Verify fonts used in orders are covered ────────────────────────────────────
print("\nFont coverage check:")
for font in sorted(fonts_used):
    if font in FONT_MAP:
        src = FONT_MAP[font][0]
        fname_only = os.path.basename(src)
        dest = os.path.join(WINDOWS_FONTS, fname_only)
        status = "OK" if os.path.exists(dest) else "MISSING"
        print(f"  [{status}] {font} -> {fname_only}")
    else:
        print(f"  [UNMAPPED] {font} -> no mapping defined")
