"""
Creates all product PSD templates in C:\Varsany\template\ using Photoshop COM API.
Each zone (front/back/pocket/sleeve) gets its own PSD file.
"""
import sys, os, time
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
import win32com.client

DPI = 320
PX_PER_CM = DPI / 2.54

def px(cm): return int(round(cm * PX_PER_CM))

OUTPUT_DIR = r"C:\Varsany\template"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Product canvas sizes: {product: {zone: (w_cm, h_cm)}}
PRODUCTS = {
    "adulttshirt":   {"front":(30,30), "back":(30,30), "pocket":(9,9)},
    "kidstshirt":    {"front":(23,30), "back":(23,30), "pocket":(9,9)},
    "adulthoodie":   {"front":(25,25), "back":(25,25), "pocket":(9,9), "sleeve":(9,7)},
    "kidshoodie":    {"front":(23,20), "back":(23,20), "pocket":(9,9)},
    "totebag":       {"front":(28,28), "back":(28,28)},
    "backpack":      {"front":(18,12)},
    "makeupbag":     {"front":(23,14)},
    "shoebag":       {"front":(23,14)},
    "shoebag2":      {"front":(14,14)},
    "stringbag":     {"front":(22,24)},
    "knittingbag":   {"front":(25,21)},
    "buckethat":     {"front":(18,5)},
    "beanie":        {"front":(9.5,4.5)},
    "socks":         {"front":(6,12)},
    "seatbelt":      {"front":(18,4)},
    "babyvest":      {"front":(15,17)},
    "sleepsuit":     {"front":(13,18)},
    "hodieblanket":  {"front":(17,5)},
    "cushion":       {"front":(30,30)},
    "memorialplaque":{"front":(13,8)},
    "golftowel":     {"front":(17,17)},
    "golfcase":      {"front":(15,6)},
    "slipper":       {"front":(6,6)},
}

print("Connecting to Photoshop...")
ps = win32com.client.Dispatch("Photoshop.Application")
time.sleep(0.5)
ps.DisplayDialogs = 3  # no dialogs

created = 0
errors  = 0

for product, zones in PRODUCTS.items():
    for zone, (w_cm, h_cm) in zones.items():
        fname = f"{product}_{zone}.psd"
        fpath = os.path.join(OUTPUT_DIR, fname)

        if os.path.exists(fpath):
            print(f"  EXISTS: {fname}")
            continue

        try:
            # Create new CMYK document
            doc = ps.Documents.Add(px(w_cm), px(h_cm), DPI, fname, 1, 1, 1)
            # Set color profile
            doc.ColorProfileName = "U.S. Web Coated (SWOP) v2"

            # Save as PSD
            opts = win32com.client.Dispatch("Photoshop.PhotoshopSaveOptions")
            opts.EmbedColorProfile = True
            opts.Layers = True
            doc.SaveAs(fpath, opts, False)
            doc.Close(2)  # don't save again

            print(f"  CREATED: {fname} ({px(w_cm)}x{px(h_cm)}px = {w_cm}x{h_cm}cm)")
            created += 1

        except Exception as e:
            print(f"  ERROR: {fname} — {e}")
            errors += 1
            try: ps.ActiveDocument.Close(2)
            except: pass

print(f"\nDone. Created: {created}  Errors: {errors}")
