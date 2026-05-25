import requests, urllib3
urllib3.disable_warnings()

base = "https://192.168.0.113:5001/webapi"
r = requests.get(f"{base}/auth.cgi", params={
    "api":"SYNO.API.Auth","version":"3","method":"login",
    "account":"varsany_api","passwd":"Varsany2026",
    "session":"FileStation","format":"sid"
}, timeout=10, verify=False)
sid = r.json()["data"]["sid"]
print("Logged in OK")

def list_path(path):
    r2 = requests.get(f"{base}/entry.cgi", params={
        "api":"SYNO.FileStation.List","version":"2","method":"list",
        "folder_path":path, "limit":200, "_sid":sid
    }, timeout=10, verify=False)
    d = r2.json()
    if d.get("success"):
        return [f["name"] for f in d.get("data",{}).get("files",[])]
    return None

# Search Resources folder
for path in [
    "/Vector Designs/Resources",
    "/Vector Designs/1. Google Drive Amazon DTF",
    "/Vector Designs/Templates",
]:
    items = list_path(path)
    if items is not None:
        print(f"\n{path}:")
        for item in items[:40]:
            print(f"  {item}")
        # check for fonts subfolder
        for item in items:
            if "font" in item.lower():
                sub = list_path(f"{path}/{item}")
                if sub:
                    print(f"  >> {item}/:")
                    for s in sub[:20]:
                        print(f"       {s}")
    else:
        print(f"{path}: not found")
