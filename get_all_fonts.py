import sys, json
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection

conn = get_connection()
cur  = conn.cursor()
cur.execute("""
    SELECT FrontFonts, BackFonts FROM tblCustomOrderDetails
    WHERE FrontFonts IS NOT NULL AND LTRIM(RTRIM(FrontFonts)) != ''
""")
rows = cur.fetchall()
conn.close()

normal_fonts = set()
premium_fonts = set()

for r in rows:
    for col in r:
        if not col: continue
        raw = col.strip()
        if not raw.startswith("{"): continue
        try:
            d = json.loads(raw)
            nf = (d.get("NormalFont") or "").strip()
            pf = (d.get("PremiumFont") or "").strip()
            if nf: normal_fonts.add(nf)
            if pf and pf.lower() not in ("no", ""): premium_fonts.add(pf)
        except: pass

print(f"NORMAL FONTS ({len(normal_fonts)}):")
for f in sorted(normal_fonts): print(f"  {f}")
print(f"\nPREMIUM FONTS ({len(premium_fonts)}):")
for f in sorted(premium_fonts): print(f"  {f}")
