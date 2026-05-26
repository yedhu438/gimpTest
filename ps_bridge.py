"""
ps_bridge.py — Varsany Photoshop Bridge
========================================
Submits print jobs to a running Photoshop worker (ps_worker.jsx) by dropping
JSON job files into a hot folder.  Python does zero colour conversion — all
ICC / ACE colour work is delegated to the real Adobe engine inside Photoshop.

Usage (from batch_processor.py or prototype_app.py):
    from ps_bridge import submit_job, wait_for_completion, ps_worker_running

    submit_job(
        order_id="204-0722247-8187513",
        template_path="W:/VarsaniAutomation/templates/WmnTee_PnkXXL.psd",
        zones={
            "front": {
                "customer_image": "C:/Varsany/Uploads/customer.png",
                "text_lines":     ["Happy Birthday", "Emma!"],
                "font_name":      "Bebas Neue",
                "colour_hex":     "#FFFFFF",
            },
            "back": {
                "text_lines": ["Est. 2024"],
                "font_name":  "Arial Bold",
                "colour_hex": "#FFD700",
            }
        },
        output_path="C:/Varsany/Output/2026-05-26/204-0722247-8187513.psd",
    )

    success = wait_for_completion("204-0722247-8187513", timeout_sec=120)
"""

import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

# ── Folder layout ─────────────────────────────────────────────────────────────
# These paths live on the NAS (W:\) so both India and UK can share them.
# Override with env vars if needed.
_BRIDGE_ROOT = Path(os.environ.get(
    "PS_BRIDGE_DIR",
    r"C:\Varsany\photoshop_bridge"
))

JOBS_DIR   = _BRIDGE_ROOT / "jobs"          # Python writes jobs here
ASSETS_DIR = _BRIDGE_ROOT / "assets"        # copied customer images
DONE_DIR   = _BRIDGE_ROOT / "done"          # ps_worker.jsx moves completed jobs here
ERROR_DIR  = _BRIDGE_ROOT / "error"         # ps_worker.jsx moves failed jobs here

for _d in (JOBS_DIR, ASSETS_DIR, DONE_DIR, ERROR_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# ── Public API ─────────────────────────────────────────────────────────────────

def submit_job(
    order_id: str,
    template_path: str,
    zones: dict,
    output_path: str,
) -> Path:
    """
    Build and drop a job JSON for ps_worker.jsx.

    zones format:
        {
            "front": {
                "customer_image": "<path or None>",   # optional
                "text_lines":     ["line1", "line2"], # optional
                "font_name":      "Bebas Neue",        # optional
                "colour_hex":     "#FFFFFF",           # optional
            },
            "back":  { ... },   # optional
            "pocket":{ ... },   # optional
            "sleeve":{ ... },   # optional
        }

    Returns the Path to the expected output PSD.
    """
    sanitised_zones = {}

    for zone_name, zone_data in zones.items():
        z = {}

        # Copy customer image to shared assets folder so Photoshop can reach it
        img_src = (zone_data.get("customer_image") or "").strip()
        if img_src and os.path.isfile(img_src):
            dest_name = f"{order_id}_{zone_name}_{Path(img_src).name}"
            dest_path = ASSETS_DIR / dest_name
            shutil.copy2(img_src, dest_path)
            z["customer_image"] = str(dest_path)
        else:
            z["customer_image"] = None

        z["text_lines"] = zone_data.get("text_lines") or []
        z["font_name"]  = zone_data.get("font_name")  or "Arial Bold"
        z["colour_hex"] = zone_data.get("colour_hex") or "#FFFFFF"

        sanitised_zones[zone_name] = z

    job = {
        "order_id":     order_id,
        "template":     str(template_path),
        "zones":        sanitised_zones,
        "output_path":  str(output_path),
        "submitted_at": datetime.now().isoformat(),
    }

    # Ensure output directory exists (Photoshop won't create it)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    job_file = JOBS_DIR / f"{order_id}.json"
    job_file.write_text(json.dumps(job, indent=2), encoding="utf-8")
    return Path(output_path)


def wait_for_completion(order_id: str, timeout_sec: int = 120) -> bool:
    """
    Submit job then launch Photoshop to process it, wait for completion.
    Returns True on success, False on error or timeout.
    """
    done_file  = DONE_DIR  / f"{order_id}.json"
    error_file = ERROR_DIR / f"{order_id}.json"

    # Launch Photoshop with the worker script to process pending jobs
    jsx = Path(__file__).parent / "ps_worker.jsx"
    ps  = _find_photoshop()
    if ps and jsx.exists():
        import subprocess
        subprocess.Popen([ps, str(jsx)])

    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if done_file.exists():
            return True
        if error_file.exists():
            _log_error(error_file)
            return False
        time.sleep(2)

    print(f"[PS Bridge] TIMEOUT waiting for order {order_id}")
    return False


def ps_worker_running() -> bool:
    """
    Return True if at least one Photoshop process is alive.
    Useful to decide whether to fall back to the Python PSD writer.
    """
    try:
        import subprocess
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Photoshop.exe", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        return "Photoshop.exe" in result.stdout
    except Exception:
        return False


def start_ps_worker(jsx_path: str | None = None) -> None:
    """
    Launch Photoshop with the ps_worker.jsx script if it isn't already running.
    Call once at application startup (batch_processor.py or prototype_app.py).
    """
    if ps_worker_running():
        print("[PS Bridge] Photoshop worker already running.")
        return

    ps_exe = _find_photoshop()
    if not ps_exe:
        print("[PS Bridge] WARNING: Photoshop not found — cannot start worker.")
        return

    script = jsx_path or str(Path(__file__).parent / "ps_worker.jsx")
    if not os.path.isfile(script):
        print(f"[PS Bridge] WARNING: ps_worker.jsx not found at {script}")
        return

    import subprocess
    subprocess.Popen([ps_exe, script])
    print(f"[PS Bridge] Photoshop worker launched ({ps_exe})")


# ── Internal helpers ───────────────────────────────────────────────────────────

def _find_photoshop() -> str | None:
    """Find the Photoshop executable on this machine."""
    candidates = []
    adobe_root = r"C:\Program Files\Adobe"
    if os.path.isdir(adobe_root):
        for folder in sorted(os.listdir(adobe_root), reverse=True):
            if "Photoshop" in folder:
                candidates.append(
                    os.path.join(adobe_root, folder, "Photoshop.exe")
                )
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def _log_error(error_file: Path) -> None:
    try:
        data = json.loads(error_file.read_text(encoding="utf-8"))
        print(f"[PS Bridge] ERROR — order {data.get('order_id')}: "
              f"{data.get('error', 'unknown error')}")
    except Exception:
        print(f"[PS Bridge] ERROR — could not read {error_file}")
