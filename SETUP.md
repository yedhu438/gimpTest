# Varsany Automation — VPS Setup Guide

## Requirements
- Windows Server with Photoshop 2026 installed
- Python 3.14+ at `C:\Users\yedhu\AppData\Local\Programs\Python\Python314\python.exe`
- ODBC Driver 17 for SQL Server
- Git for Windows (`C:\Program Files\Git\`)

## Folder Structure
```
C:\Varsany\
├── jobs\            ← UXP plugin reads jobs from here
├── done\            ← Completed jobs moved here
├── error\           ← Failed jobs moved here
├── template\
│   └── adulttshirt.psd   ← Base PSD template
├── Temp\
│   └── OrderImages\ ← Customer images downloaded here
└── Output\
    └── ps_test\     ← Output PSDs saved here
```

## Setup Steps

### 1. Clone repo
```
git clone https://github.com/yedhu438/gimpTest.git C:\Users\yedhu\Desktop\gimpTest
```

### 2. Install Python dependencies
```
pip install pyodbc --break-system-packages
```

### 3. Create .env file
Create `C:\Users\yedhu\Desktop\gimpTest\.env`:
```
DB_SERVER=81.0.219.26
DB_NAME=dbAmazonCustomOrders
DB_UID=OrderUser
DB_PWD=<password>
```

### 4. Create folder structure
```
mkdir C:\Varsany\jobs
mkdir C:\Varsany\done
mkdir C:\Varsany\error
mkdir C:\Varsany\template
mkdir C:\Varsany\Temp\OrderImages
mkdir C:\Varsany\Output\ps_test
```

### 5. Copy PSD template
Copy `adulttshirt.psd` to `C:\Varsany\template\adulttshirt.psd`
- Template must have layers: `CustomerText_front` (top), `CustomerImage_front` (bottom)

### 6. Install fonts
Install all fonts from `A:\font\` into Windows — right-click each font → Install for all users.

### 7. Load UXP Plugin in Photoshop
1. Open Photoshop
2. Plugins → UXP Developer Tools
3. Add Plugin → browse to `C:\Users\yedhu\Desktop\gimpTest\uxp-plugin\manifest.json`
4. Click Load
5. Click **📁 Set C:\Varsany Root** in the plugin panel → select `C:\Varsany`

### 8. Suppress PS script warning (one time)
Add to `C:\Users\yedhu\AppData\Roaming\Adobe\Adobe Photoshop 2026\Adobe Photoshop 2026 Settings\PSUserConfig.txt`:
```
WarnRunningScripts 0
```

## Daily Usage

### Export orders
```
python C:\Users\yedhu\Desktop\gimpTest\submit_uxp_jobs.py
```
This fetches last 30 days of orders from DB, downloads images, writes jobs to `C:\Varsany\jobs\`.
The UXP plugin picks them up automatically every 3 seconds.

### Output
PSDs saved to `C:\Varsany\Output\ps_test\` named `{OrderID}_{zone}.psd`

## Key Files
| File | Purpose |
|------|---------|
| `submit_uxp_jobs.py` | Fetches orders from DB, writes job JSONs |
| `font_map.py` | Maps DB font names → Photoshop PostScript names |
| `uxp-plugin/index.html` | Main plugin code (v2.2) |
| `uxp-plugin/manifest.json` | Plugin manifest |
| `db.py` | DB connection helper |
| `requeue_order.py` | Requeue a single order by ID |
| `get_single_order.py` | Fetch single order details from DB |

## Critical Notes
- **Font fix (v2.2):** Font, size, colour and text MUST be set in ONE batchPlay call — splitting causes Photoshop to reset font to Myriad Pro
- **Canvas:** Expanded 2cm at top for FRONT/BACK label strip
- **Label:** Black Arial Bold 24pt, positioned 1cm from top-left
- **Image:** Fitted to canvas (contain), centred H+V
- **Text:** Auto-sized to 80% canvas width, centred H, bottom-aligned with 4% margin

## Missing Fonts (fallback to Arial Bold)
These fonts are in the DB but not yet installed:
- Great Vibes, Rhinestone Font, DTF Text, Embroidery Font
- Vinyl Font, Wellies Font, Varsany Crystal Font
- Sippy Cup Font, Gloves Font, Shorts Font, Super Vibes
- T-Shirt Font, BSL, AAAGoldenLotus, 25mm Caps
