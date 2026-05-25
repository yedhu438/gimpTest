"""Count all font files on NAS /Vector Designs/Resources/Fonts"""
import requests, urllib3
urllib3.disable_warnings()
import sys
sys.stdout.reconfigure(encoding='utf-8')

NAS_BASE   = "https://192.168.0.113:5001/webapi"
NAS_FOLDER = "/Vector Designs/Resources/Fonts"

r = requests.get(f"{NAS_BASE}/auth.cgi", params={
    "api":"SYNO.API.Auth","version":"3","method":"login",
    "account":"varsany_api","passwd":"Varsany2026",
    "session":"FileStation","format":"sid"
}, timeout=10, verify=False)
sid = r.json()["data"]["sid"]

total_fonts = 0
folders     = 0

def scan(path, depth=0):
    global total_fonts, folders
    offset = 0
    while True:
        r2 = requests.get(f"{NAS_BASE}/entry.cgi", params={
            "api":"SYNO.FileStation.List","version":"2","method":"list",
            "folder_path":path,"limit":500,"offset":offset,"_sid":sid
        }, timeout=15, verify=False)
        d = r2.json()
        if not d.get("success"):
            break
        items = d["data"]["files"]
        if not items:
            break
        for item in items:
            name = item["name"]
            if item["isdir"]:
                folders += 1
                indent = "  " * depth
                print(f"{indent}[{name}]")
                scan(f"{path}/{name}", depth+1)
            else:
                ext = name.rsplit(".",1)[-1].lower() if "." in name else ""
                if ext in ("ttf","otf"):
                    total_fonts += 1
        if len(items) < 500:
            break
        offset += 500

scan(NAS_FOLDER)

requests.get(f"{NAS_BASE}/auth.cgi", params={
    "api":"SYNO.API.Auth","version":"3","method":"logout",
    "session":"FileStation","_sid":sid
}, timeout=5, verify=False)

print(f"\nTotal font files on NAS : {total_fonts}")
print(f"Subfolders scanned      : {folders}")
