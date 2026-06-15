# Varsany Print Automation — New Device Setup Guide

> Complete step-by-step guide from zero to fully running system.
> Follow every section in order. Do NOT skip steps.

---

## QUICK REFERENCE — KEY POINTS

| Item | Value |
|---|---|
| Project folder | `C:\gimpTest` (git repo) |
| Varsany data folder | `C:\Varsany` (fonts, output, temp) |
| NAS drive letter | `Z:` (mapped to Synology) |
| Image source | `W:\images\Feb-Image` and `W:\images\Jan-Image` |
| Live DB server | `81.0.219.26` — SQL Server |
| DB name | `dbAmazonCustomOrders` |
| DB user | `CustOrderUser` (ask Yedhu for password) |
| Image server URL | `http://www.crssoft.co.uk/CustomOrderImages/` |
| Output folder | `C:\Varsany\Output\YYYY-MM-DD\` |
| Photoshop bridge folder | `C:\gimpTest\jobs` (or `C:\Varsany\photoshop_bridge`) |
| UXP plugin folder | `C:\gimpTest\uxp-plugin\` |
| DPI | 320 DPI (= 125.98 px/cm) |
| Colour mode | CMYK, U.S. Web Coated (SWOP) v2 |

---

## PART 1 — WINDOWS SETUP

### 1.1 Install Python

1. Download **Python 3.11** from https://python.org
2. During install: tick **"Add Python to PATH"** ✓
3. Verify: open PowerShell → `python --version`

### 1.2 Install ODBC Driver for SQL Server

1. Download **ODBC Driver 17 for SQL Server** from Microsoft:
   - Search: "ODBC Driver 17 SQL Server download"
   - File: `msodbcsql17_x64.msi`
2. Run installer, accept defaults
3. Verify in PowerShell:
   ```powershell
   python -c "import pyodbc; print(pyodbc.drivers())"
   ```
   Should show: `ODBC Driver 17 for SQL Server`

### 1.3 Install Google Chrome (for premium colour fonts)

Chrome renders SVG/colour fonts (Smart Kids, Camo, Reflection etc.) that PIL cannot render.

```powershell
winget install Google.Chrome
```

Or download from google.com/chrome

### 1.4 Install Git

```powershell
winget install Git.Git
```

---

## PART 2 — GET THE CODE

### 2.1 Clone the repository

```powershell
cd C:\
git clone <your-git-repo-url> gimpTest
cd C:\gimpTest
```

If you already have the folder (copied from old machine):
```powershell
cd C:\gimpTest
git status   # check everything is clean
```

### 2.2 Install Python packages

```powershell
cd C:\gimpTest
pip install -r requirements.txt
```

This installs: `pyodbc`, `Pillow`, `python-dotenv`, `requests`, `numpy`, `fonttools`, `flask`, `pandas`, `openpyxl`, `pywin32`, `psd-tools`, `rembg`

**If fontTools is needed for premium fonts:**
```powershell
pip install fonttools
```

---

## PART 3 — CREATE FOLDER STRUCTURE

Run this once to create all required folders:

```powershell
New-Item -ItemType Directory -Force "C:\Varsany\Fonts"
New-Item -ItemType Directory -Force "C:\Varsany\Output"
New-Item -ItemType Directory -Force "C:\Varsany\Temp"
New-Item -ItemType Directory -Force "C:\Varsany\Uploads"
New-Item -ItemType Directory -Force "C:\Varsany\template"
New-Item -ItemType Directory -Force "C:\gimpTest\jobs"
New-Item -ItemType Directory -Force "C:\gimpTest\done"
New-Item -ItemType Directory -Force "C:\gimpTest\error"
New-Item -ItemType Directory -Force "C:\gimpTest\Temp\OrderImages"
```

---

## PART 4 — CONFIGURE ENVIRONMENT (.env)

### 4.1 Create .env file

Copy the template and fill in values:

```powershell
copy C:\gimpTest\.env.example C:\gimpTest\.env
```

Edit `C:\gimpTest\.env`:

```env
# ── Database (Live VPS) ──────────────────────────────────────────────────────
DB_SERVER=81.0.219.26
DB_NAME=dbAmazonCustomOrders
DB_UID=CustOrderUser
DB_PWD=<ASK_YEDHU_FOR_PASSWORD>

# ── Paths ────────────────────────────────────────────────────────────────────
VARSANY_BASE=C:\Varsany
VARSANY_IMAGES=W:\images\Feb-Image,W:\images\Jan-Image
VARSANY_FONTS_EXTRA=W:\fonts
VARSANY_OUTPUT=C:\Varsany\Output
VARSANY_LOG=C:\Varsany\batch_log.txt
VARSANY_TEMP=C:\Varsany\Temp
VARSANY_TEMPLATES=C:\Varsany\template

# ── Image server (customer uploaded images) ──────────────────────────────────
IMAGE_SERVER_URL=http://www.crssoft.co.uk/CustomOrderImages/

# ── NAS Upload (Synology) ────────────────────────────────────────────────────
NAS_HOST=<SYNOLOGY_IP_OR_HOSTNAME>
NAS_PORT=5001
NAS_USER=<NAS_USERNAME>
NAS_PASS=<NAS_PASSWORD>
NAS_PATH=/Drive DTF Orders/1. Amazon DTF/Automation Output/

# ── Photoshop Bridge ─────────────────────────────────────────────────────────
USE_PHOTOSHOP_BRIDGE=1
PS_BRIDGE_DIR=C:\gimpTest
PS_TEMPLATES_DIR=C:\Varsany\template
```

> **IMPORTANT:** Never commit `.env` to git. It contains passwords. It is already in `.gitignore`.

### 4.2 Test database connection

```powershell
cd C:\gimpTest
python db.py
```

Expected output:
```
Connecting to 81.0.219.26 / dbAmazonCustomOrders …
Connected successfully.
SQL Server version: Microsoft SQL Server ...
```

If it fails, check:
- VPS is reachable: `ping 81.0.219.26`
- Port 1433 is open on VPS firewall (ask Dhruv)
- DB_UID / DB_PWD are correct in `.env`

---

## PART 5 — FONTS SETUP

### 5.1 Standard fonts

Copy all `.ttf` and `.otf` files from the old machine's `C:\Varsany\Fonts\` to `C:\Varsany\Fonts\` on the new machine.

Or copy from NAS: `W:\fonts\` → `C:\Varsany\Fonts\`

### 5.2 Premium colour fonts (critical)

These must be installed as **system fonts** so Photoshop/Chrome can find them:

| Database name | Font filename |
|---|---|
| TextureFont / SmartKids | `SmartKids.otf` |
| BlockFont / ColorfulBlocks | `ColorfulBlocks.otf` |
| PaintFont / PaintSplashesRainbow | `PaintSplashesRainbow.otf` |
| MermaidFont / WaveMermaid | `WaveMermaid.otf` |
| ReflectionFont / RefractionRay | `RefractionRay.otf` |
| CamoFont / CamoBlock | `CamoBlock.otf` |
| SpideyFont / SpiderWeb | `SpiderWeb.otf` |
| CozyFont / CozyWinter | `CozyWinter.otf` |
| FootballFont / SoccerArmy | `SoccerArmy.otf` |
| FlowerFont / TropicalFlower | `TropicalFlower.otf` |

**To install a font system-wide:**
1. Right-click the `.otf` file → "Install for all users"
2. Or: copy to `C:\Windows\Fonts\`

### 5.3 Verify fonts are indexed

```powershell
cd C:\gimpTest
python -c "from batch_processor import FONT_INDEX; print(sorted(FONT_INDEX.keys())[:20])"
```

---

## PART 6 — PHOTOSHOP + UXP PLUGIN SETUP

### 6.1 Install Adobe Photoshop

- Photoshop 2024 (v25) or later is required
- Minimum version for UXP: v24.0
- Install via Adobe Creative Cloud

### 6.2 Install the UXP Plugin

The plugin is at `C:\gimpTest\uxp-plugin\`

**Method: Load unpacked plugin (developer mode)**

1. Open Photoshop
2. Menu: **Plugins → Development → Load Unpacked Plugin**
3. Select folder: `C:\gimpTest\uxp-plugin`
4. Panel appears: "Varsany Order Processor"

**First-time setup in the panel:**
1. Click **"📁 Set Root Folder (C:\gimpTest)"**
2. Navigate to `C:\gimpTest` and click "Select Folder"
3. Panel status turns green: "Ready: C:\gimpTest"
4. A file `uxp_token.txt` is created in `C:\gimpTest\` — this persists the folder for next launch

### 6.3 Create product templates (one-time)

With the UXP plugin panel open:

1. Click **"📦 Create All Product Templates"**
   - Creates 23 blank CMYK PSD templates in `C:\Varsany\template\`
   - e.g. `adulttshirt_combined.psd`, `adulthoodie_combined.psd` etc.
   - Each is correct DPI (320), correct width per product, 15000px tall (cropped at runtime)

2. Verify templates exist:
   ```powershell
   ls C:\Varsany\template\*.psd
   ```

> These templates are blank CMYK canvases. The UXP plugin places customer images and text on them at runtime. You only need to create them once — or re-run this if templates are lost.

---

## PART 7 — SYNOLOGY NAS SETUP

### 7.1 Map the NAS drive

The NAS drive must be mapped as **Z:** with the name "Vector Designs".

```powershell
# Replace \\SYNOLOGY_IP\share with actual path from Dhruv
net use Z: \\<NAS_IP>\<SHARE_NAME> /user:<username> <password> /persistent:yes
```

Or: Windows Explorer → Map Network Drive → Z: → `\\<NAS_IP>\<SHARE>`

**Key paths on NAS:**
- Images: `W:\images\Feb-Image\` and `W:\images\Jan-Image\`
- Fonts: `W:\fonts\`
- Output: `Z:\Drive DTF Orders\1. Amazon DTF\Automation Output\`

### 7.2 Test NAS access

```powershell
ls W:\images\Feb-Image\ | Select -First 5
ls Z:\"Drive DTF Orders"\"1. Amazon DTF"\ | Select -First 5
```

### 7.3 Test Synology upload via Python

```powershell
cd C:\gimpTest
python nas_test.py
```

---

## PART 8 — DATABASE SCHEMA CHECK

### 8.1 Verify required columns exist

The database needs these extra columns (added in a previous session):

```sql
-- Run in SQL Server Management Studio connected to live DB
USE dbAmazonCustomOrders;
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'tblCustomOrderDetails'
  AND COLUMN_NAME IN ('IsFrontBgRemove','IsBackBgRemove','QCStatus',
                      'IsComplexOrder','OutputFilePath','IsTopazImageProcess',
                      'FrontTopazImage','BackTopazImage');
```

**If any columns are missing**, run this SQL on the live DB:
```sql
ALTER TABLE tblCustomOrderDetails ADD
    IsFrontBgRemove  bit NULL DEFAULT 0,
    IsBackBgRemove   bit NULL DEFAULT 0,
    IsPocketBgRemove bit NULL DEFAULT 0,
    IsSleeveBgRemove bit NULL DEFAULT 0,
    QCStatus         nvarchar(20)  NULL DEFAULT 'pending',
    QCNotes          nvarchar(500) NULL,
    IsComplexOrder   bit           NULL DEFAULT 0,
    OutputFilePath   nvarchar(500) NULL;
```

### 8.2 Check schema

```powershell
cd C:\gimpTest
python check_schema.py
```

---

## PART 9 — TOPAZ UPSCALING (OPTIONAL BUT RECOMMENDED)

### What is Topaz?

Topaz Labs AI upscaling improves low-resolution customer images before printing. The system checks the database field `IsTopazImageProcess = 1` and uses the Topaz-enhanced image URL stored in `FrontTopazImage` / `BackTopazImage` columns.

### How it works

1. Designer upscales image on Topaz website (topazlabs.com)
2. Designer saves upscaled image URL back to DB in `FrontTopazImage` column
3. `batch_processor.py` checks `IsTopazImageProcess` flag
4. If `= 1`: uses `FrontTopazImage` URL instead of `FrontImage`
5. If `= 0` or column empty: uses original `FrontImage`

### Verify Topaz integration

```powershell
cd C:\gimpTest
python check_topaz.py
```

---

## PART 10 — BACKGROUND REMOVAL

The system removes image backgrounds automatically when the background colour matches the garment colour.

### How it works (bg_remover.py)

1. **Get garment colour from SKU** — e.g. `MenTee_BlkM` → Black `(20,20,20)`
2. **Edge check** — sample all 4 edges: if ≥95% match garment colour → proceed
3. **Interior check** — if ≥80% of interior matches garment (flat/blank image) → SKIP
4. **Colour-key removal** — remove only pixels within `DIFF_THRESH=40` of garment colour
5. **Cleanup** — alpha threshold + crop to content bounding box

### SKU colour codes

| SKU suffix | Colour |
|---|---|
| `Blk` | Black (20,20,20) |
| `Wht` | White (255,255,255) |
| `Nvy` | Navy (31,40,80) |
| `Red` | Red (200,30,30) |
| `Pnk` | Pink (255,150,180) |
| `Gry` | Grey (150,150,150) |
| `Blu` | Blue (30,100,200) |
| `Ylw` | Yellow (255,220,0) |
| `RBlu` | Royal Blue (65,105,225) |
| `SBlu` | Sky Blue (135,206,235) |
| `BPnk` | Baby Pink (255,182,193) |

### Test background removal

```powershell
cd C:\gimpTest
python bg_remover.py
# Shows colour map for common SKUs

python bg_remover.py "C:\path\to\image.jpg" "MenTee_BlkM"
# Tests removal on a specific image
```

### Manual override

Designer can set `IsFrontBgRemove = 1` in the order page to force background removal regardless of auto-detection.

---

## PART 11 — ZONE LABELLING

Every PSD output includes a small black label at the top-left of each zone strip.

### Label content

| Zone | Label example |
|---|---|
| Front | `FRONT` or `Ylw34` (SKU code for coloured garments) |
| Back | `BACK` |
| Sleeve | `SLEEVE` |
| Pocket | `POCKET` |
| Front (kids hoodie) | `KIDSHOODIE / FRONT` |

### How labels are generated

In `sku_parser.py` → `build_zone_label(zone, sku, with_product=True)`:
- For coloured garments: returns e.g. `Ylw34` (colour + size from SKU)
- For standard: returns zone name uppercase

In the UXP plugin (`index.html`): `addLabel()` function:
- Black Arial Bold 12pt text
- Placed at top-left of each zone strip
- Layer named `Label_FRONT` etc.

---

## PART 12 — ORDER PROCESSING PROCEDURE

### Complete flow from database to final PSD

```
DB Order (IsDesignComplete=0)
    ↓
export_today.py   — queries DB, builds job JSON files in C:\gimpTest\jobs\
    ↓
UXP plugin        — polls jobs\ every 3 seconds, picks up next job
    ↓
Photoshop         — opens template, places image + text, saves PSD
    ↓
done\<orderid>.json — signals completion
    ↓
Output\YYYY-MM-DD\<Category>\<colour>\<OrderID>.psd
    ↓
(optional) Synology NAS upload
```

### Step-by-step manual run

**1. Export today's orders to job files:**
```powershell
cd C:\gimpTest
python export_today.py
```
This queries the live DB and creates `.json` job files in `C:\gimpTest\jobs\`

**2. Ensure Photoshop is open with the UXP plugin panel visible**
- Panel status should show green "Ready: C:\gimpTest"
- Plugin polls for jobs every 3 seconds automatically

**3. Watch the panel** — it will log each order as it processes:
```
[12:01:45] Processing: 205-6487629-5805162
[12:01:52] Placed image: front
[12:01:53] Text: front (217pt) bottom:9726
[12:01:55] Saved: 205-6487629-5805162.psd
[12:01:55] Done: 205-6487629-5805162
```

**4. Check output:**
```powershell
ls "C:\Varsany\Output\$(Get-Date -Format yyyy-MM-dd)"
```

### Automated daemon (production)

Run this to process orders continuously every 60 seconds:
```powershell
cd C:\gimpTest
python run_loop.py
```

Options:
```powershell
python run_loop.py --dry-run          # preview only, no files
python run_loop.py --interval 30      # poll every 30s
python run_loop.py --hours 24         # only last 24 hours of orders
python run_loop.py --date-after 2026-06-01  # only orders after this date
python run_loop.py --no-nas           # skip Synology upload
```

### Process specific orders only

```powershell
python process_these_orders.py        # edit the order list in that file first
python export_these_orders.py         # same, for export/job creation only
```

---

## PART 13 — OUTPUT FILE STRUCTURE

Files are saved to:
```
C:\Varsany\Output\
└── 2026-06-15\
    ├── DTF Front\
    │   ├── black\
    │   │   └── 205-6487629-5805162.psd
    │   └── white\
    │       └── 205-8801234-1234567.psd
    ├── DTF Kids Hoodie\
    │   └── black\
    └── Automated\          ← multi-zone or multi-item orders
        └── 205-9876543-0001234.psd
```

### File naming convention

- Single zone: `<OrderID>.psd`
- Multi-part (>6 zones): `<OrderID>_1.psd`, `<OrderID>_2.psd`

### Synology NAS path (after upload)

```
Z:\Drive DTF Orders\1. Amazon DTF\Automation Output\
└── 2026-06-15\
    └── 205-6487629-5805162.psd
```

---

## PART 14 — CANVAS SIZES REFERENCE

All sizes at 320 DPI. Formula: `cm × 320 / 2.54 = pixels`

| Product | Zone | Width px | Height px |
|---|---|---|---|
| adulttshirt | front/back | 3779 | 3779 |
| adulttshirt | pocket | 1134 | 1134 |
| kidstshirt | front/back | 2898 | 3779 |
| adulthoodie | front/back | 3150 | 3150 |
| adulthoodie | sleeve | 1134 | 882 |
| kidshoodie | front/back | 2898 | 2520 |
| totebag | front/back | 3528 | 3528 |
| babyvest | front | 1890 | 2142 |
| buckethat | front | 2268 | 630 |
| slipper | front | 756 | 756 |

Full table in `CLAUDE.md` section 4 or `product_canvas.py`.

---

## PART 15 — TROUBLESHOOTING

### "Cannot connect to SQL Server"

```
Check:
1. ping 81.0.219.26   — is VPS reachable?
2. Check .env DB_UID / DB_PWD are correct
3. Ask Dhruv to open port 1433 on VPS firewall for this machine's IP
4. python db.py   — to see the exact error
```

### "Image not found: filename.jpg"

```
Check:
1. Is W:\ drive mapped? → net use W: ...
2. ls W:\images\Feb-Image\   — is the image there?
3. The system also tries to download from crssoft.co.uk automatically
```

### UXP Plugin not picking up jobs

```
Check:
1. Panel shows green "Ready: C:\gimpTest"?  If not, click "Set Root Folder"
2. Jobs exist? → ls C:\gimpTest\jobs\
3. Any errors? → ls C:\gimpTest\error\
4. Photoshop must stay open (not minimised to taskbar)
```

### Premium font renders as plain grey outline

```
This happens when Chrome is not installed.
Install Chrome: winget install Google.Chrome
Then restart batch_processor.py
```

### PSD saves but looks wrong in Photoshop (washed out / wrong colours)

```
CMYK PSD convention: 0 = full ink, 255 = no ink (opposite of PIL).
The code handles this correctly. If colours look wrong:
1. Check ICC profile: C:\gimpTest\icc\USWebCoatedSWOP.icc exists?
2. In Photoshop: Edit → Color Settings → Working Spaces → CMYK: U.S. Web Coated (SWOP) v2
3. The 72ppi display warning is normal — pixel dimensions are correct
```

### "Template not found for SKU"

```
Run: python create_all_templates_com.py
Or:  Use "📦 Create All Product Templates" button in UXP panel
Templates go to: C:\Varsany\template\
```

---

## PART 16 — GIT WORKFLOW

### Saving changes

```powershell
cd C:\gimpTest
git add -A
git commit -m "Describe what changed"
git push
```

### Pulling updates on a new machine

```powershell
cd C:\gimpTest
git pull
```

### Files NOT in git (machine-specific, gitignored)

- `.env` — database passwords, NAS credentials
- `*.psd` — generated output files
- `Output\`, `Temp\`, `done\`, `error\` — runtime folders
- `uxp_token.txt` — UXP folder token (regenerated per machine)
- `batch_log.txt`, `*.log` — log files
- `__pycache__\` — Python cache

---

## PART 17 — CHECKLIST: NEW MACHINE READY?

Run through this before going live:

```
[ ] Python 3.11 installed, in PATH
[ ] pip install -r requirements.txt  completed without errors
[ ] ODBC Driver 17 for SQL Server installed
[ ] Google Chrome installed
[ ] .env file created with correct DB_SERVER, DB_UID, DB_PWD
[ ] python db.py  → "Connected successfully"
[ ] C:\Varsany\Fonts\  folder has .ttf/.otf files
[ ] Premium fonts installed system-wide (right-click → Install for all users)
[ ] W:\ drive mapped to NAS images share
[ ] Z:\ drive mapped to NAS output share
[ ] Photoshop 2024+ installed
[ ] UXP plugin loaded: Plugins → Development → Load Unpacked → C:\gimpTest\uxp-plugin
[ ] "Set Root Folder" clicked in plugin panel → green Ready status
[ ] "Create All Product Templates" run → C:\Varsany\template\ has .psd files
[ ] python export_today.py  → creates job files in C:\gimpTest\jobs\
[ ] UXP plugin picks up first job and processes it
[ ] Output PSD appears in C:\Varsany\Output\YYYY-MM-DD\
```

---

## PART 18 — KEY FILES REFERENCE

| File | Purpose |
|---|---|
| `batch_processor.py` | Core engine — builds PSD layers, font rendering, background removal |
| `run_loop.py` | Production daemon — polls DB every 60s |
| `export_today.py` | Exports today's unprocessed orders as job JSONs |
| `db.py` | Database connection (reads from .env) |
| `shared.py` | Shared helpers: paths, job writing, image download |
| `bg_remover.py` | Background removal via colour-key matching |
| `ps_bridge.py` | Python ↔ Photoshop job handoff |
| `sku_parser.py` | SKU → product key, zone labels |
| `product_canvas.py` | Canvas size table per product |
| `font_map.py` | Font name → PostScript name mapping for Photoshop |
| `synology_upload.py` | Upload finished PSDs to NAS |
| `uxp-plugin/index.html` | Photoshop UXP plugin (polls jobs/, processes in PS) |
| `uxp-plugin/manifest.json` | UXP plugin metadata |
| `uxp-plugin/metadata/*.json` | Per-product canvas metadata |
| `.env.example` | Template for .env (copy to .env and fill in) |
| `requirements.txt` | Python dependencies |
| `CLAUDE.md` | Full project knowledge base |
| `SETUP_GUIDE.md` | This file |

---

*Last updated: 2026-06-15*
