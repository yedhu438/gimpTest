import subprocess, sys

result = subprocess.run([
    "powershell", "-Command",
    "[System.Reflection.Assembly]::LoadWithPartialName('System.Drawing') | Out-Null; $f=New-Object System.Drawing.Text.InstalledFontCollection; $f.Families|%{$_.Name}"
], capture_output=True, text=True, encoding='utf-8')

installed = set(f.strip().lower() for f in result.stdout.strip().split('\n') if f.strip())

needed = [
    "Arial", "Bebas Neue", "Chewy", "Permanent Marker", "Lato",
    "Russo One", "Ultra", "Helvetica", "Fondamento", "Abel",
    "Roboto", "Great Vibes", "Verdana",
    "Rhinestone Font", "DTF Text", "Embroidery Font",
    "Vinyl Font", "Wellies Font", "Varsany Crystal Font",
    "Varsany Rhinestone Font", "Sippy Cup Font", "Gloves Font",
    "Shorts Font", "Super Vibes", "T-Shirt Font", "BSL",
    "AAAGoldenLotus Stg1_Ver1", "25mm Caps rhinestone font",
    "Spider Web", "Paint Splashes Rainbow", "Colorful Blocks",
    "Smart Kids", "Camo Block", "RefractionRay", "Bouqet",
    "Soccer Army Ver 2", "Cozy Winter", "Wavemermaid",
]

missing = []
found = []
for f in needed:
    ok = f.lower() in installed
    status = "INSTALLED" if ok else "MISSING"
    print(f"{status:<10} {f}")
    if ok: found.append(f)
    else: missing.append(f)

print(f"\nInstalled: {len(found)}  Missing: {len(missing)}")
print("\nMISSING:")
for f in missing: print(f"  - {f}")
