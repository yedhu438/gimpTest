"""Resize all existing templates to 60000px height."""
import time, os, win32com.client

TEMPLATE_DIR = r"C:\gimpTest\template"
ps = win32com.client.Dispatch("Photoshop.Application")
ps.DisplayDialogs = 3

done = 0
for fname in os.listdir(TEMPLATE_DIR):
    if not fname.endswith(".psd"): continue
    if "combined" in fname: continue
    path = os.path.join(TEMPLATE_DIR, fname)
    try:
        orig = ps.Preferences.RulerUnits
        ps.Preferences.RulerUnits = 1
        doc = ps.Open(path)
        time.sleep(0.3)
        current_h = round(doc.Height * 320 / 72)
        if current_h < 59000:  # only resize if not already 60000px
            doc.ResizeCanvas(doc.Width, int(60000 * 72 / 320), 1)
        opts = win32com.client.Dispatch("Photoshop.PhotoshopSaveOptions")
        opts.EmbedColorProfile = True
        opts.Layers = True
        doc.SaveAs(path, opts, False)
        doc.Close(2)
        ps.Preferences.RulerUnits = orig
        done += 1
        print(f"  OK  {fname}")
    except Exception as e:
        print(f"  FAIL {fname} -- {e}")
        try: ps.ActiveDocument.Close(2)
        except: pass
    time.sleep(0.2)

print(f"\nDone: {done} templates resized to 60000px")
