"""Download the specific fonts needed by batch_processor.py from NAS"""
import os, requests, urllib3
urllib3.disable_warnings()
import sys
sys.stdout.reconfigure(encoding='utf-8')

NAS_BASE  = "https://192.168.0.113:5001/webapi"
LOCAL_DIR = r"C:\gimpTest\Fonts"
NAS_FONTS = "/Vector Designs/Resources/Fonts"

# Exact NAS filenames → what to save locally as
FONTS_TO_DOWNLOAD = {
    "Smart Kids.otf":                "Smart Kids.otf",           # texturefont
    "Colorful Blocks.otf":           "Colorful Blocks.otf",      # blockfont
    "Paint Splashes Rainbow.otf":    "Paint Splashes Rainbow.otf",  # paintfont
    "Wavemermaid.otf":               "Wavemermaid.otf",          # mermaidfont
    "Refraction Ray.otf":            "Refraction Ray.otf",       # reflectionfont
    "Camoblock.otf":                 "Camoblock.otf",            # camofont (may already exist)
    "Spider Web.otf":                "Spider Web.otf",           # spideyfont
    "Cozy Winter.otf":               "Cozy Winter.otf",          # cozyfont
    "Soccer Army.otf":               "Soccer Army.otf",          # footballfont
    "Tropical Flower.otf":           "Tropical Flower.otf",      # flowerfont
    "VINYLFONT.TTF":                 "VINYLFONT.TTF",            # vinyl
    # Standard fonts
    "abel-v18-latin-regular (2).ttf":         "Abel Regular.ttf",
    "chewy-v18-latin-regular.ttf":            "Chewy Regular.ttf",
    "Fondamento-Regular.ttf":                 "Fondamento Regular.ttf",
    "lato-v24-latin-regular.ttf":             "Lato Regular.ttf",
    "permanent-marker-v16-latin-regular.ttf": "Permanent Marker Regular.ttf",
    "Roboto-Regular.ttf":                     "Roboto Regular.ttf",
    "RussoOne-Regular.ttf":                   "Russo One Regular.ttf",
    "ultra-v25-latin-regular.ttf":            "Ultra Regular.ttf",
}

os.makedirs(LOCAL_DIR, exist_ok=True)

r = requests.get(f"{NAS_BASE}/auth.cgi", params={
    "api":"SYNO.API.Auth","version":"3","method":"login",
    "account":"varsany_api","passwd":"Varsany2026",
    "session":"FileStation","format":"sid"
}, timeout=10, verify=False)
sid = r.json()["data"]["sid"]
print("Logged in OK\n")

ok = 0
skip = 0
fail = 0

for nas_name, local_name in FONTS_TO_DOWNLOAD.items():
    local_path = os.path.join(LOCAL_DIR, local_name)
    if os.path.exists(local_path):
        print(f"  skip (exists): {local_name}")
        skip += 1
        continue
    nas_path = f"{NAS_FONTS}/{nas_name}"
    print(f"  downloading: {local_name} ...", end=" ", flush=True)
    try:
        r2 = requests.get(f"{NAS_BASE}/entry.cgi", params={
            "api":"SYNO.FileStation.Download","version":"2","method":"download",
            "path":nas_path,"mode":"download","_sid":sid
        }, timeout=60, verify=False, stream=True)
        with open(local_path, "wb") as f:
            for chunk in r2.iter_content(65536):
                f.write(chunk)
        size_kb = os.path.getsize(local_path) // 1024
        print(f"OK ({size_kb} KB)")
        ok += 1
    except Exception as e:
        print(f"FAILED: {e}")
        fail += 1

requests.get(f"{NAS_BASE}/auth.cgi", params={
    "api":"SYNO.API.Auth","version":"3","method":"logout",
    "session":"FileStation","_sid":sid
}, timeout=5, verify=False)

print(f"\nDownloaded: {ok}  Skipped: {skip}  Failed: {fail}")
