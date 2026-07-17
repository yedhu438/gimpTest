"""
Creates combined_template.psd by opening adulttshirt.psd and resizing canvas to 3780x15000
"""
import sys, time
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
import win32com.client, os

OUTPUT  = r"C:\gimpTest\template\combined_template.psd"
SOURCE  = r"C:\gimpTest\template\adulttshirt.psd"

print("Connecting to Photoshop...")
ps = win32com.client.Dispatch("Photoshop.Application")
time.sleep(1)
ps.DisplayDialogs = 3

print("Opening template...")
doc = ps.Open(SOURCE)
time.sleep(1)

# Delete all layers except background
print("Clearing layers...")
for i in range(doc.ArtLayers.Count - 1, -1, -1):
    try: doc.ArtLayers[i].Delete()
    except: pass

# Resize canvas to 3780 x 15000 px
print("Resizing canvas...")
orig_units = ps.Preferences.RulerUnits
ps.Preferences.RulerUnits = 1  # pixels
doc.ResizeCanvas(3780, 15000, 9)  # 9 = psMiddleCenter anchor
ps.Preferences.RulerUnits = orig_units

print("Saving to:", OUTPUT)
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
psd_opts = win32com.client.Dispatch("Photoshop.PhotoshopSaveOptions")
psd_opts.EmbedColorProfile = True
psd_opts.Layers = True
doc.SaveAs(OUTPUT, psd_opts, False)
doc.Close(2)
print("DONE:", OUTPUT)
