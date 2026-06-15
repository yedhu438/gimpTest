"""
Quick connection test — run this first before syncing.
Place in C:\gimpTest\ and run:  python nas_test.py
"""
import requests

NAS_HOST = "192.168.0.113"
NAS_PORT = 5000
NAS_USER = "varsany_api"
NAS_PASS = "Varsany2026"

base = f"http://{NAS_HOST}:{NAS_PORT}/webapi"

# 1. Login
res = requests.get(base + "/auth.cgi", params={
    "api": "SYNO.API.Auth", "version": "3", "method": "login",
    "account": NAS_USER, "passwd": NAS_PASS,
    "session": "FileStation", "format": "sid"
})
data = res.json()
if not data.get("success"):
    print(f"FAILED to login: {data}")
    exit(1)

sid = data["data"]["sid"]
print(f"Login OK — session: {sid}")

# 2. List /Automation to confirm folder exists and is accessible
res2 = requests.get(base + "/entry.cgi", params={
    "api": "SYNO.FileStation.List", "version": "2",
    "method": "list", "folder_path": "/Automation", "_sid": sid
})
data2 = res2.json()
if data2.get("success"):
    print(f"'/Automation' folder accessible OK")
    files = data2.get("data", {}).get("files", [])
    print(f"Contents ({len(files)} items): {[f['name'] for f in files]}")
else:
    print(f"'/Automation' folder NOT accessible: {data2}")

# 3. Logout
requests.get(base + "/auth.cgi", params={
    "api": "SYNO.API.Auth", "version": "1",
    "method": "logout", "session": "FileStation", "_sid": sid
})
print("Logged out. Test complete.")
