"""
synology_upload.py — Varsany NAS Integration
Saves PSD files to the Synology NAS via three methods (tried in order):

  Method 1 — Direct path copy  (NAS_LOCAL_PATH set — use when NAS is mapped as Z:)
  Method 2 — FileStation API   (requires router port forwarding port 5001 → NAS)
  Method 3 — SFTP              (requires router port forwarding port 22 → NAS)
               Enable SSH: DSM → Control Panel → Terminal & SNMP → Enable SSH
"""
import os, shutil, posixpath, requests, urllib3

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

urllib3.disable_warnings()

# Method 1 — direct path
NAS_LOCAL_PATH = os.environ.get("NAS_LOCAL_PATH", "").strip()

# Method 2 — FileStation API
NAS_HOST   = os.environ.get("NAS_HOST",   "")
NAS_PORT   = int(os.environ.get("NAS_PORT", "5001"))
NAS_USER   = os.environ.get("NAS_USER",   "NadiadAdmin")
NAS_PASS   = os.environ.get("NAS_PASS",   "")
NAS_FOLDER = os.environ.get("NAS_FOLDER", "/Automated")

_scheme     = "https" if NAS_PORT == 443 else "http"
_port_sfx   = f":{NAS_PORT}" if NAS_PORT not in (443, 80) else ""
_BASE_URL   = f"{_scheme}://{NAS_HOST}{_port_sfx}/webapi" if NAS_HOST else ""

# Method 3 — SFTP
NAS_SFTP_HOST   = os.environ.get("NAS_SFTP_HOST",   NAS_HOST)
NAS_SFTP_PORT   = int(os.environ.get("NAS_SFTP_PORT", "22"))
NAS_SFTP_USER   = os.environ.get("NAS_SFTP_USER",   NAS_USER)
NAS_SFTP_PASS   = os.environ.get("NAS_SFTP_PASS",   NAS_PASS)
NAS_SFTP_PATH   = os.environ.get("NAS_SFTP_PATH",
                    "/volume1/Drive DTF Orders/1. Amazon DTF/Automation Output")


class SynologyUploader:

    def __init__(self):
        self.sid   = None
        self._sftp = None
        self._ssh  = None
        self._mode = "none"

        if NAS_LOCAL_PATH:
            self._init_local()
        elif NAS_SFTP_HOST and NAS_SFTP_PASS:
            self._init_sftp()
        elif NAS_HOST and NAS_PASS:
            self._init_api()
        else:
            print("[Synology] No NAS credentials configured — uploads disabled")

    # ── Method 1: local copy ──────────────────────────────────────────────────

    def _init_local(self):
        if os.path.exists(NAS_LOCAL_PATH):
            self._mode = "local"
            print(f"[Synology] Direct-copy mode → {NAS_LOCAL_PATH}")
        else:
            print(f"[Synology] NAS_LOCAL_PATH not accessible: {NAS_LOCAL_PATH}")

    # ── Method 3: SFTP ───────────────────────────────────────────────────────

    def _init_sftp(self):
        try:
            import paramiko
            self._ssh = paramiko.SSHClient()
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._ssh.connect(
                hostname = NAS_SFTP_HOST,
                port     = NAS_SFTP_PORT,
                username = NAS_SFTP_USER,
                password = NAS_SFTP_PASS,
                timeout  = 30,
            )
            self._sftp = self._ssh.open_sftp()
            self._mode = "sftp"
            print(f"[Synology] SFTP connected → {NAS_SFTP_HOST}:{NAS_SFTP_PORT}")
        except Exception as e:
            print(f"[Synology] SFTP connection error: {e}")
            self._ssh = None

    # ── Method 2: FileStation API ─────────────────────────────────────────────

    def _init_api(self):
        try:
            r = requests.get(f"{_BASE_URL}/auth.cgi", params={
                "api": "SYNO.API.Auth", "version": "3", "method": "login",
                "account": NAS_USER, "passwd": NAS_PASS,
                "session": "FileStation", "format": "sid",
            }, timeout=30, verify=False)
            d = r.json()
            if d.get("success"):
                self.sid   = d["data"]["sid"]
                self._mode = "api"
                print(f"[Synology] API connected → {NAS_HOST}")
            else:
                print(f"[Synology] API login failed: {d}")
        except Exception as e:
            print(f"[Synology] API connection error: {e}")

    # ── Public interface ──────────────────────────────────────────────────────

    @property
    def connected(self):
        return self._mode in ("local", "sftp", "api")

    def upload(self, local_path, sub_folder=""):
        if not self.connected:
            print("[Synology] Not connected — skipping upload")
            return False
        if not os.path.exists(local_path):
            print(f"[Synology] File not found: {local_path}")
            return False

        if self._mode == "local":
            return self._copy_local(local_path, sub_folder)
        elif self._mode == "sftp":
            return self._upload_sftp(local_path, sub_folder)
        else:
            return self._upload_api(local_path, sub_folder)

    # ── Upload implementations ────────────────────────────────────────────────

    def _copy_local(self, local_path, sub_folder=""):
        dest_dir = os.path.join(NAS_LOCAL_PATH, sub_folder) if sub_folder else NAS_LOCAL_PATH
        try:
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, os.path.basename(local_path))
            shutil.copy2(local_path, dest)
            size_mb = os.path.getsize(local_path) / (1024 * 1024)
            print(f"[Synology] Copied: {dest}  ({size_mb:.1f} MB)")
            return True
        except Exception as e:
            print(f"[Synology] Copy error: {e}")
            return False

    def _upload_sftp(self, local_path, sub_folder=""):
        remote_dir = posixpath.join(NAS_SFTP_PATH, sub_folder) if sub_folder else NAS_SFTP_PATH
        filename   = os.path.basename(local_path)
        remote     = posixpath.join(remote_dir, filename)
        size_mb    = os.path.getsize(local_path) / (1024 * 1024)
        try:
            # Create remote directory if needed
            self._sftp_makedirs(remote_dir)
            self._sftp.put(local_path, remote)
            print(f"[Synology] SFTP uploaded: {remote}  ({size_mb:.1f} MB)")
            return True
        except Exception as e:
            print(f"[Synology] SFTP upload error: {e}")
            return False

    def _sftp_makedirs(self, remote_path):
        parts = remote_path.split("/")
        path  = ""
        for part in parts:
            if not part:
                continue
            path = path + "/" + part
            try:
                self._sftp.stat(path)
            except FileNotFoundError:
                self._sftp.mkdir(path)

    def _upload_api(self, local_path, sub_folder=""):
        nas_path = f"{NAS_FOLDER}/{sub_folder}".rstrip("/") if sub_folder else NAS_FOLDER
        filename = os.path.basename(local_path)
        size_mb  = os.path.getsize(local_path) / (1024 * 1024)
        timeout  = max(120, 60 + int(size_mb * 2))
        try:
            with open(local_path, "rb") as f:
                r = requests.post(
                    f"{_BASE_URL}/entry.cgi",
                    params={"api": "SYNO.FileStation.Upload", "version": "2",
                            "method": "upload", "_sid": self.sid,
                            "path": nas_path, "create_parents": "true", "overwrite": "true"},
                    files={"file": (filename, f, "application/octet-stream")},
                    timeout=timeout, verify=False,
                )
            d = r.json()
            if d.get("success"):
                print(f"[Synology] API uploaded: {nas_path}/{filename}  ({size_mb:.1f} MB)")
                return True
            else:
                print(f"[Synology] API upload failed: {d}")
                return False
        except Exception as e:
            print(f"[Synology] API upload error: {e}")
            return False

    def logout(self):
        if self._sftp:
            try:
                self._sftp.close()
                self._ssh.close()
            except Exception:
                pass
        if self._mode == "api" and self.sid:
            try:
                requests.get(f"{_BASE_URL}/auth.cgi", params={
                    "api": "SYNO.API.Auth", "version": "3", "method": "logout",
                    "session": "FileStation", "_sid": self.sid,
                }, timeout=10, verify=False)
            except Exception:
                pass
        self._mode = "none"
        print("[Synology] Disconnected")


# ── Connection test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"NAS_LOCAL_PATH : {NAS_LOCAL_PATH or '(not set)'}")
    print(f"NAS_SFTP_HOST  : {NAS_SFTP_HOST or '(not set)'}  port={NAS_SFTP_PORT}")
    print(f"NAS_API_HOST   : {NAS_HOST or '(not set)'}  port={NAS_PORT}")
    print()
    u = SynologyUploader()
    if u.connected:
        print(f"SUCCESS — mode={u._mode}")
    else:
        print("FAILED — check .env settings")
    u.logout()
