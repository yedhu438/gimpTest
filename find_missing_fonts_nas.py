"""Search NAS for specific missing fonts"""
import requests, urllib3
urllib3.disable_warnings()
import sys
sys.stdout.reconfigure(encoding='utf-8')

NAS_BASE = "https://192.168.0.113:5001/webapi"

r = requests.get(f"{NAS_BASE}/auth.cgi", params={
    "api":"SYNO.API.Auth","version":"3","method":"login",
    "account":"varsany_api","passwd":"Varsany2026",
    "session":"FileStation","format":"sid"
}, timeout=10, verify=False)
sid = r.json()["data"]["sid"]
print("Logged in OK\n")

MISSING = [
    "cozy","fondamento","lato","mermaid","paint","permanent",
    "refraction","roboto","russo","smartkid","smart kid","soccer",
    "spider","tropical","ultra","vinyl","colorful"
]

def list_folder(path):
    results = []
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
        results.extend(items)
        if len(items) < 500:
            break
        offset += 500
    return results

def scan(path, depth=0):
    if depth > 4:
        return
    try:
        items = list_folder(path)
    except Exception:
        return
    for item in items:
        name = item["name"]
        name_lower = name.lower()
        if item["isdir"]:
            scan(f"{path}/{name}", depth+1)
        else:
            ext = name_lower.rsplit(".",1)[-1] if "." in name else ""
            if ext in ("ttf","otf"):
                for term in MISSING:
                    if term in name_lower:
                        print(f"  FOUND [{term}]: {path}/{name}")
                        break

# Search the most likely locations
for share in ["/Vector Designs/Resources", "/Vector Designs/Drive DTF Orders", "/Vector Designs/Templates"]:
    print(f"Scanning {share} ...")
    scan(share)

requests.get(f"{NAS_BASE}/auth.cgi", params={
    "api":"SYNO.API.Auth","version":"3","method":"logout",
    "session":"FileStation","_sid":sid
}, timeout=5, verify=False)
print("\nDone.")
