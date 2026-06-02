"""
Creates all product templates by copying adulttshirt.psd and resizing canvas.
This avoids the PS2026 COM 'Make not available' error.
"""
import sys, time, os, shutil
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from product_canvas import PRODUCT_CANVAS
import win32com.client

TEMPLATE_DIR = r"C:\Varsany\template"
SOURCE       = r"C:\Varsany\template\adulttshirt.psd"

print("Connecting to Photoshop...")
ps = win32com.client.Dispatch("Photoshop.Application")
ps.DisplayDialogs = 3

done = 0
failed = 0

for product, zones in PRODUCT_CANVAS.items():
    if product == "adulttshirt":
        print(f"  SKIP adulttshirt.psd (already exists)")
        continue

    max_w  = max(w for w, h in zones.values())
    height = 15000
    fname  = os.path.join(TEMPLATE_DIR, product + ".psd")

    try:
        orig_units = ps.Preferences.RulerUnits
        ps.Preferences.RulerUnits = 1  # pixels

        # Open the source template
        doc = ps.Open(SOURCE)
        time.sleep(0.5)

        # Resize canvas to new product dimensions
        doc.ResizeCanvas(max_w, height, 9)  # 9 = psMiddleCenter

        ps.Preferences.RulerUnits = orig_units

        # Save as new product PSD
        psd_opts = win32com.client.Dispatch("Photoshop.PhotoshopSaveOptions")
        psd_opts.EmbedColorProfile = True
        psd_opts.Layers = True
        doc.SaveAs(fname, psd_opts, False)
        doc.Close(2)

        done += 1
        print(f"  OK  {product}.psd  ({max_w}x{height}px)")
    except Exception as e:
        failed += 1
        print(f"  FAIL {product}.psd — {e}")
        try: ps.ActiveDocument.Close(2)
        except: pass
    time.sleep(0.3)

print(f"\nDone: {done} created, {failed} failed.")
print(f"Templates in: {TEMPLATE_DIR}")
