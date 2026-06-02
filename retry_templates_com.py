"""
Retry failed templates — uses Duplicate + Flatten + Resize approach for narrow canvases.
"""
import sys, time, os
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from product_canvas import PRODUCT_CANVAS
import win32com.client

TEMPLATE_DIR = r"C:\Varsany\template"
SOURCE       = r"C:\Varsany\template\adulttshirt.psd"

# Only retry the failed ones
RETRY = ["kidstshirt","totebag","stringbag","knittingbag","buckethat","beanie","socks","adulthoodie"]

print("Connecting to Photoshop...")
ps = win32com.client.Dispatch("Photoshop.Application")
ps.DisplayDialogs = 3

done = 0
for product in RETRY:
    zones  = PRODUCT_CANVAS[product]
    max_w  = max(w for w, h in zones.values())
    height = 15000
    fname  = os.path.join(TEMPLATE_DIR, product + ".psd")

    try:
        orig_units = ps.Preferences.RulerUnits
        ps.Preferences.RulerUnits = 1  # pixels

        doc = ps.Open(SOURCE)
        time.sleep(0.5)

        # Resize to exact target size (anchor top-left)
        doc.ResizeCanvas(max_w, height, 1)  # 1 = psUpperLeft

        ps.Preferences.RulerUnits = orig_units

        psd_opts = win32com.client.Dispatch("Photoshop.PhotoshopSaveOptions")
        psd_opts.EmbedColorProfile = True
        psd_opts.Layers = True
        doc.SaveAs(fname, psd_opts, False)
        doc.Close(2)
        done += 1
        print(f"  OK  {product}.psd  ({max_w}x{height}px)")
    except Exception as e:
        print(f"  FAIL {product} — {e}")
        try: ps.ActiveDocument.Close(2)
        except: pass
    time.sleep(0.3)

print(f"\nDone: {done}/{len(RETRY)}")
