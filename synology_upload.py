import requests
import os

NAS_HOST = "192.168.0.113"
NAS_PORT = 5000
NAS_USER = "varsany_api"
NAS_PASS = "Varsany2026"
NAS_BASE_FOLDER = "/Automation"


class SynologyUploader:
    def __init__(self):
        self.base = f"http://{NAS_HOST}:{NAS_PORT}/webapi"
        self.sid = None
        self._login()

    @property
    def connected(self):
        return self.sid is not None

    def _login(self):
        try:
            res = requests.get(self.base + "/auth.cgi", params={
                "api":     "SYNO.API.Auth",
                "version": "3",
                "method":  "login",
                "account": NAS_USER,
                "passwd":  NAS_PASS,
                "session": "FileStation",
                "format":  "sid"
            }, timeout=8)
            data = res.json()
            if data.get("success"):
                self.sid = data["data"]["sid"]
                print("[NAS] Logged in OK")
            else:
                print(f"[NAS] Login failed: {data}")
        except Exception as e:
            print(f"[NAS] Connection failed (will skip uploads): {e}")

    def _ensure_folder(self, folder_path):
        """Create folder on NAS if it doesn't exist."""
        parts = folder_path.strip("/").split("/")
        current = ""
        for part in parts:
            current += "/" + part
            requests.get(self.base + "/entry.cgi", params={
                "api":         "SYNO.FileStation.CreateFolder",
                "version":     "2",
                "method":      "create",
                "folder_path": os.path.dirname(current) or "/",
                "name":        part,
                "_sid":        self.sid
            })

    def upload(self, local_path, sub_folder=""):
        """
        Upload a file to the NAS.
        sub_folder: path relative to NAS_BASE_FOLDER
                    e.g. "2026-06-11/DTF Front/black"
        """
        dest_folder = NAS_BASE_FOLDER
        if sub_folder:
            dest_folder = f"{NAS_BASE_FOLDER}/{sub_folder.strip('/')}"

        self._ensure_folder(dest_folder)

        filename = os.path.basename(local_path)
        with open(local_path, "rb") as f:
            res = requests.post(
                self.base + "/entry.cgi",
                params={
                    "api":         "SYNO.FileStation.Upload",
                    "version":     "2",
                    "method":      "upload",
                    "path":        dest_folder,
                    "create_parents": "true",
                    "overwrite":   "true",
                    "_sid":        self.sid
                },
                files={"file": (filename, f, "application/octet-stream")}
            )
        data = res.json()
        if data.get("success"):
            print(f"[NAS] Uploaded: {filename} → {dest_folder}")
        else:
            print(f"[NAS] Upload failed: {filename} — {data}")

    def logout(self):
        requests.get(self.base + "/auth.cgi", params={
            "api":     "SYNO.API.Auth",
            "version": "1",
            "method":  "logout",
            "session": "FileStation",
            "_sid":    self.sid
        })
        print("[NAS] Logged out")


def sync_output_folder(local_root=r"C:\gimpTest\Output"):
    """
    Walk C:\\gimpTest\\Output and upload every PSD,
    preserving the subfolder structure on the NAS.
    e.g. C:\\gimpTest\\Output\\2026-06-11\\DTF Front\\black\\order.psd
      -> /Automation/2026-06-11/DTF Front/black/order.psd
    """
    nas = SynologyUploader()
    uploaded = 0
    failed = 0

    for dirpath, _, filenames in os.walk(local_root):
        for filename in filenames:
            if not filename.lower().endswith(".psd"):
                continue
            local_path = os.path.join(dirpath, filename)
            # Build relative sub_folder path
            rel = os.path.relpath(dirpath, local_root)
            sub_folder = rel.replace("\\", "/") if rel != "." else ""
            try:
                nas.upload(local_path, sub_folder=sub_folder)
                uploaded += 1
            except Exception as e:
                print(f"[NAS] ERROR {filename}: {e}")
                failed += 1

    nas.logout()
    print(f"\n[NAS] Done — {uploaded} uploaded, {failed} failed")


if __name__ == "__main__":
    sync_output_folder()
