"""Download all fonts from NAS /Vector Designs/Resources/Fonts to C:\\Varsany\\Fonts\\"""
import os, requests, urllib3
urllib3.disable_warnings()
import sys
sys.stdout.reconfigure(encoding='utf-8')

NAS_BASE   = "https://192.168.0.113:5001/webapi"
NAS_USER   = "varsany_api"
NAS_PASS   = "Varsany2026"
NAS_FOLDER = "/Vector Designs/Resources/Fonts"
LOCAL_DIR  = r"C:\Varsany\Fonts"

os.makedirs(LOCAL_DIR, exist_ok=True)

# Login
r = requests.get(f"{NAS_BASE}/auth.cgi", params={
    "api":"SYNO.API.Auth","version":"3","method":"login",
    "account":NAS_USER,"passwd":NAS_PASS,
    "session":"FileStation","format":"sid"
}, timeout=10, verify=False)
sid = r.json()["data"]["sid"]
print("Logged in OK")

def list_folder(path):
    r2 = requests.get(f"{NAS_BASE}/entry.cgi", params={
        "api":"SYNO.FileStation.List","version":"2","method":"list",
        "folder_path":path, "limit":500, "_sid":sid
    }, timeout=10, verify=False)
    d = r2.json()
    if d.get("success"):
        return d["data"]["files"]
    return []

def download_file(nas_path, local_path):
    r3 = requests.get(f"{NAS_BASE}/entry.cgi", params={
        "api":"SYNO.FileStation.Download","version":"2","method":"download",
        "path":nas_path,"mode":"download","_sid":sid
    }, timeout=60, verify=False, stream=True)
    with open(local_path, "wb") as f:
        for chunk in r3.iter_content(65536):
            f.write(chunk)

def process_folder(nas_path, indent=0):
    items = list_folder(nas_path)
    for item in items:
        name = item["name"]
        full_nas = f"{nas_path}/{name}"
        if item["isdir"]:
            print(" " * indent + f"[{name}]")
            process_folder(full_nas, indent + 2)
        else:
            ext = os.path.splitext(name)[1].lower()
            if ext in (".ttf", ".otf"):
                local_path = os.path.join(LOCAL_DIR, name)
                if os.path.exists(local_path):
                    print(" " * indent + f"  skip (exists): {name}")
                else:
                    print(" " * indent + f"  downloading: {name} ...", end=" ", flush=True)
                    try:
                        download_file(full_nas, local_path)
                        size_kb = os.path.getsize(local_path) // 1024
                        print(f"OK ({size_kb} KB)")
                    except Exception as e:
                        print(f"FAILED: {e}")

process_folder(NAS_FOLDER)

# Summary
fonts = [f for f in os.listdir(LOCAL_DIR) if f.lower().endswith((".ttf",".otf"))]
print(f"\nDone. {len(fonts)} fonts in {LOCAL_DIR}:")
for f in sorted(fonts):
    print(f"  {f}")

# Logout
requests.get(f"{NAS_BASE}/auth.cgi", params={
    "api":"SYNO.API.Auth","version":"3","method":"logout",
    "session":"FileStation","_sid":sid
}, timeout=5, verify=False)
print("\nLogged out.")
