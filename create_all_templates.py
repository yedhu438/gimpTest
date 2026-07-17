"""
Writes a BUILD_TEMPLATES.json job for the UXP plugin.
Creates one tall blank PSD per product, width = widest zone, height = 15000px.
"""
import sys, json
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from product_canvas import PRODUCT_CANVAS
from pathlib import Path

JOBS_DIR = Path(r"C:\gimpTest\jobs")
JOBS_DIR.mkdir(parents=True, exist_ok=True)

job = {
    "job_type":   "build_templates",
    "products":   {}
}

for product, zones in PRODUCT_CANVAS.items():
    # Use the widest zone width as canvas width
    max_w = max(w for w, h in zones.values())
    job["products"][product] = {
        "width_px":  max_w,
        "height_px": 15000,   # tall enough for any combination of zones
    }

job_file = JOBS_DIR / "BUILD_TEMPLATES.json"
job_file.write_text(json.dumps(job, indent=2), encoding="utf-8")

print(f"Written: {job_file}")
print(f"Products: {len(job['products'])}")
for p, d in job['products'].items():
    print(f"  {p:<20} {d['width_px']}x{d['height_px']}px  → {p}.psd")
