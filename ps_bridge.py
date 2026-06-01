"""
ps_bridge.py  —  Varsany Photoshop Bridge
==========================================
Python side of the Photoshop integration.
1. submit_job()  — writes a JSON job file for Photoshop to pick up
2. trigger_and_wait() — tells the open Photoshop to run ps_worker.jsx via COM, waits for result

No pywin32 needed — uses a lightweight VBScript one-liner via cscript.exe.
Photoshop must be open before calling trigger_and_wait().
"""

import json, os, shutil, subprocess, time
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

# ── Paths ──────────────────────────────────────────────────────────────────────
_DATA_PATH_FILE = Path(r"C:\Varsany\uxp-plugin\data_path.txt")

def _resolve_bridge_root() -> Path:
    # Prefer explicit env override
    if os.environ.get("PS_BRIDGE_DIR"):
        return Path(os.environ["PS_BRIDGE_DIR"])
    # Read path written by the UXP plugin on startup
    if _DATA_PATH_FILE.exists():
        p = _DATA_PATH_FILE.read_text(encoding="utf-8").strip()
        if p:
            return Path(p)
    # Fallback
    return Path(r"C:\Varsany\photoshop_bridge")

_BRIDGE_ROOT = _resolve_bridge_root()
JOBS_DIR     = _BRIDGE_ROOT / "jobs"
ASSETS_DIR   = _BRIDGE_ROOT / "images"
DONE_DIR     = _BRIDGE_ROOT / "done"
ERROR_DIR    = _BRIDGE_ROOT / "error"

for _d in (JOBS_DIR, ASSETS_DIR, DONE_DIR, ERROR_DIR):
    _d.mkdir(parents=True, exist_ok=True)

JSX_PATH = str(Path(__file__).parent / "ps_worker.jsx")

# ── Submit job ─────────────────────────────────────────────────────────────────
def submit_job(order_id, template_path, zones, output_path, canvas_w_px=3780, canvas_h_px=3780):
    """
    Write a job JSON for Photoshop.
    zones = {
        "front": {
            "customer_image": "C:/path/to/image.jpg",   # path on disk, or None
            "text_lines":     ["Line 1", "Line 2"],      # list of strings, or []
            "font_name":      "Arial Bold",
            "colour_hex":     "#ffffff",
        },
        ...
    }
    """
    # Copy customer images to shared assets folder
    clean_zones = {}
    for zone_name, zone in zones.items():
        img_src = (zone.get("customer_image") or "").strip()
        if img_src and os.path.isfile(img_src):
            # Copy to plugin data images folder using just the original filename
            img_filename = Path(img_src).name
            dest = ASSETS_DIR / img_filename
            shutil.copy2(img_src, dest)
            img_path = img_filename  # just filename — plugin looks it up by name
        else:
            img_path = img_src if img_src else None

        clean_zones[zone_name] = {
            "customer_image": img_path,
            "text_lines":     zone.get("text_lines") or [],
            "font_name":      zone.get("font_name") or "Arial Bold",
            "colour_hex":     zone.get("colour_hex") or "#ffffff",
        }

    job = {
        "order_id":     order_id,
        "template":     str(template_path),
        "zones":        clean_zones,
        "output_path":  str(output_path),
        "canvas_w_px":  canvas_w_px,
        "canvas_h_px":  canvas_h_px,
        "dpi":          320,
        "submitted_at": datetime.now().isoformat(),
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    job_file = JOBS_DIR / f"{order_id}.json"
    job_file.write_text(json.dumps(job, indent=2), encoding="utf-8")
    print(f"[PS Bridge] Job submitted: {order_id}")
    return Path(output_path)


# ── Trigger Photoshop via VBScript COM ─────────────────────────────────────────
def _trigger_photoshop():
    """
    Tell the open Photoshop to run ps_worker.jsx using a VBScript one-liner.
    No pywin32 needed — cscript.exe is built into Windows.
    """
    vbs_file = _BRIDGE_ROOT / "trigger_ps.vbs"
    vbs_content = (
        'Dim ps : Set ps = CreateObject("Photoshop.Application") : '
        'ps.DoJavaScriptFile "' + JSX_PATH.replace("\\", "\\\\") + '"'
    )
    vbs_file.write_text(vbs_content, encoding="utf-8")
    try:
        subprocess.Popen(
            [r"C:\Windows\System32\cscript.exe", "//Nologo", str(vbs_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception as e:
        print(f"[PS Bridge] VBScript trigger failed: {e}")
        return False


# ── Wait for result ────────────────────────────────────────────────────────────
def wait_for_completion(order_id, timeout_sec=180):
    """
    Trigger Photoshop, then poll until job is done or errors.
    Returns True on success, False on error or timeout.
    """
    done_file  = DONE_DIR  / f"{order_id}.json"
    error_file = ERROR_DIR / f"{order_id}.json"

    _trigger_photoshop()

    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if done_file.exists():
            print(f"[PS Bridge] Done: {order_id}")
            return True
        if error_file.exists():
            try:
                data = json.loads(error_file.read_text(encoding="utf-8"))
                print(f"[PS Bridge] Error: {data.get('error','unknown')}")
            except Exception:
                pass
            return False
        time.sleep(2)

    print(f"[PS Bridge] Timeout: {order_id}")
    return False


def ps_worker_running():
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Photoshop.exe", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        return "Photoshop.exe" in result.stdout
    except Exception:
        return False
