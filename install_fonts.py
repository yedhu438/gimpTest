"""
install_fonts.py — Install every project font as a real Windows/Photoshop font.

Why this exists: batch_processor.py's FONT_INDEX only needs a font FILE to
exist somewhere in FONT_FOLDERS to resolve a name -> path. That is NOT the
same thing as Photoshop being able to render that font. The UXP plugin sets
fontPostScriptName directly in a batchPlay textStyle descriptor, and
Photoshop resolves that name against whatever fonts are actually installed
in Windows — if a .ttf/.otf is just sitting in a project folder and was
never installed, Photoshop silently substitutes Myriad Pro. This script
does the actual OS-level install (copy into C:\\Windows\\Fonts + register in
the registry) for every font file found, so nothing needs a manual/partial
FONT_MAP anymore.

Usage:
    python install_fonts.py                     # installs from the default source folder(s) below
    python install_fonts.py --source "C:\\path"   # installs from a specific folder (recursive)
"""
import argparse, ctypes, os, shutil, sys, winreg

HERE = os.path.dirname(os.path.abspath(__file__))

# Default source folders — same idea as FONT_FOLDERS in batch_processor.py.
# Point --source at the consolidated migration staging folder when setting up a new server.
DEFAULT_SOURCES = [
    os.path.join(HERE, "Fonts"),
    os.path.join(HERE, "Fonts", "Premium Fonts"),
    os.path.join(HERE, "Fonts", "Fonts"),
]

WINDOWS_FONTS = r"C:\Windows\Fonts"
FONTS_REG_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"

# Windows font-name suffix the registry expects, per file type
REG_SUFFIX = {".ttf": "(TrueType)", ".otf": "(OpenType)"}


def broadcast_font_change():
    """Tell running apps (Explorer, and often Photoshop) that the font list changed,
    without requiring a reboot. Restarting Photoshop is still the safest fallback."""
    HWND_BROADCAST = 0xFFFF
    WM_FONTCHANGE   = 0x001D
    ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)


def install_font(src_path):
    """Copy one font file into C:\\Windows\\Fonts and register it. Returns
    'installed', 'already_present', or ('failed', reason)."""
    fname = os.path.basename(src_path)
    ext   = os.path.splitext(fname)[1].lower()
    if ext not in (".ttf", ".otf"):
        return "skipped_not_a_font"

    dest = os.path.join(WINDOWS_FONTS, fname)
    if os.path.exists(dest):
        return "already_present"

    try:
        shutil.copy2(src_path, dest)
    except Exception as e:
        return ("failed", f"copy: {e}")

    try:
        display_name = f"{os.path.splitext(fname)[0]} {REG_SUFFIX.get(ext, '')}".strip()
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, FONTS_REG_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, display_name, 0, winreg.REG_SZ, fname)
        winreg.CloseKey(key)
    except Exception as e:
        return ("failed", f"copied but registry write failed (needs admin): {e}")

    return "installed"


def main():
    parser = argparse.ArgumentParser(description="Install every font file as a real Windows/Photoshop font")
    parser.add_argument("--source", action="append", help="Folder to scan (recursive). Can repeat. Defaults to the project's own Fonts folders.")
    args = parser.parse_args()

    sources = args.source or DEFAULT_SOURCES
    sources = [s for s in sources if os.path.isdir(s)]
    if not sources:
        print("No valid source folders found. Pass --source \"<folder>\" pointing at your font collection.")
        sys.exit(1)

    print(f"Scanning {len(sources)} source folder(s):")
    for s in sources:
        print(f"  - {s}")
    print()

    installed, already, failed, skipped = 0, 0, 0, 0
    failures = []

    for source in sources:
        for root, _dirs, files in os.walk(source):
            for fname in files:
                result = install_font(os.path.join(root, fname))
                if result == "installed":
                    installed += 1
                    print(f"  Installed: {fname}")
                elif result == "already_present":
                    already += 1
                elif result == "skipped_not_a_font":
                    skipped += 1
                else:
                    _, reason = result
                    failed += 1
                    failures.append((fname, reason))
                    print(f"  FAILED: {fname} — {reason}")

    print()
    print(f"Installed: {installed}  |  Already present: {already}  |  Failed: {failed}  |  Skipped (non-font files): {skipped}")

    if installed > 0:
        broadcast_font_change()
        print("Broadcast WM_FONTCHANGE. If Photoshop is already open, restart it to guarantee it picks up the new fonts.")

    if failed > 0:
        print("\nFailures usually mean this script needs to run as Administrator (registry write to HKEY_LOCAL_MACHINE requires it).")
        sys.exit(1)


if __name__ == "__main__":
    main()
