# Varsany Automation — VPS Setup Guide
## Version: v3.2-preview

## Requirements
- Windows Server with Photoshop 2026 installed
- Python 3.14+ installed
- ODBC Driver 17 for SQL Server
- Git for Windows

## Folder Structure (create these on VPS)
```
C:\Varsany\
├── jobs\                    ← UXP plugin reads jobs from here
├── done\                    ← Completed jobs moved here
├── error\                   ← Failed jobs moved here
├── template\
│   ├── adulttshirt.psd      ← Single-zone template
│   └── combined_template.psd← Multi-zone template (create via plugin button)
├── Temp\
│   └── OrderImages\         ← Customer images downloaded here
└── Output\
    └── ps_test\             ← Output PSDs saved here
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

### 5. Copy adulttshirt.psd template
Copy `adulttshirt.psd` to `C:\Varsany\template\adulttshirt.psd`
- Must have layers: `CustomerText_front` (top), `CustomerImage_front` (bottom)

### 6. Install fonts
Install all fonts from font folder into Windows — right-click → Install for all users.

### 7. Load UXP Plugin in Photoshop
1. Open Photoshop
2. Plugins → UXP Developer Tools
3. Add Plugin → `C:\Users\yedhu\Desktop\gimpTest\uxp-plugin\manifest.json`
4. Click **📁 Set C:\Varsany Root** → select `C:\Varsany`
5. Click **🔨 Create Combined Template** — creates `C:\Varsany\template\combined_template.psd`

### 8. Suppress PS script warning (one time)
Add to `C:\Users\yedhu\AppData\Roaming\Adobe\Adobe Photoshop 2026\Adobe Photoshop 2026 Settings\PSUserConfig.txt`:
```
WarnRunningScripts 0
```

## Daily Usage

### Export orders (last 30 days)
```
python C:\Users\yedhu\Desktop\gimpTest\submit_uxp_jobs.py
```

### Export specific test orders (2 with front+back)
```
python C:\Users\yedhu\Desktop\gimpTest\queue_2_orders.py
```

### Output
PSDs saved to `C:\Varsany\Output\ps_test\{OrderID}.psd`

## Output PSD Layer Structure (per order)
```
Label_FRONT          ← "FRONT" text label (black, top strip)
Text_front_*         ← Customer text (correct font + colour)
Preview_front        ← Customer preview image (INVISIBLE — toggle to see)
63xxxxxxx-1-front    ← Customer print image (visible, for DTF)
CustomerText_front   ← Empty placeholder from template
---gap---
Label_BACK           ← "BACK" text label
Text_back_*          ← Back text
Preview_back         ← Back preview (INVISIBLE)
63xxxxxxx-1-back     ← Back print image
```

## Key Scripts
| Script | Purpose |
|--------|---------|
| `submit_uxp_jobs.py` | Fetch last 30 days orders → write combined jobs |
| `submit_20_varied.py` | Fetch 20 orders from last 60 days for testing |
| `submit_premium.py` | Fetch 5 orders with premium fonts for testing |
| `queue_2_orders.py` | Queue 2 orders with front+back for quick testing |
| `font_map.py` | DB font name → PS PostScript name mapping |
| `create_combined_template.py` | Create blank combined template via COM (fallback) |

## Key Plugin Files
| File | Purpose |
|------|---------|
| `uxp-plugin/index.html` | Main plugin (v3.2-preview) |
| `uxp-plugin/manifest.json` | Plugin manifest |

## Critical Technical Notes
1. **Font fix:** All text properties (font+size+colour+content) MUST be in ONE batchPlay call
2. **Canvas crop:** Use `doc.resizeCanvas()` DOM API — batchPlay resizeCanvas silently fails
3. **Preview hide:** Use `layer.visible = false` DOM API — batchPlay set visible:false ignored
4. **Image margin:** 38px (0.3cm) margin each side to prevent bleed
5. **Canvas expand:** Uses `pointsUnit` with `QCSBottomLeft` anchor for 2cm label strip
6. **Label strip:** 252px (2cm at 320dpi) at top of each zone

## Missing Fonts (fallback to Arial Bold)
Great Vibes, Rhinestone Font, DTF Text, Embroidery Font, Vinyl Font,
Wellies Font, Varsany Crystal Font, Sippy Cup Font, Gloves Font,
Shorts Font, Super Vibes, T-Shirt Font, BSL, AAAGoldenLotus, 25mm Caps
