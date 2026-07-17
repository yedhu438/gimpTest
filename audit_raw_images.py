"""
Audit raw (non-Topaz) images from the last export.
For each image: show DB fields + check if file exists locally in Temp/OrderImages.
"""
import sys, os
sys.path.insert(0, r"C:\gimpTest")
from db import get_connection

TEMP_DIR = r"C:\gimpTest\Temp\OrderImages"

ALL_ORDER_IDS = [
    "206-0765171-9435537","206-8320801-3516311","203-0958398-6908349","202-7535142-8209967",
    "203-8527305-8206760","202-1368265-9848315","206-5982109-9667503","203-4781098-5941959",
    "203-1494879-9981133","026-0212240-6430755","203-8990486-7580352","203-7154475-2834731",
    "205-4304095-4728322",
    "026-8320691-7700315","204-5039273-2417166","206-3733229-0444322","206-5880772-8433134",
    "026-4644118-6006732","026-1772455-0177941","205-4862104-9561915","206-9663784-7689161",
    "203-4380503-5751535",
    "202-1335807-9834726","026-6684671-7015512","202-2578485-9273155","203-4165960-9269919",
    "202-1017113-9763522","203-2617297-4925914","204-3602245-8582758","202-5524662-6600321",
    "206-2816408-1143507","203-4958037-9809947","206-5493308-5434767","204-0573699-9620349",
    "206-8511868-0021969","026-2794054-4272322","204-2840141-7993948",
    "026-4549518-0005966","204-5511522-3006702","205-2041094-9376349","202-1705310-7848337",
    "205-5675263-3073940","205-6704670-2746720","026-6215098-6374722","206-0227530-5873930",
    "204-3344772-4553937","205-2542593-4141968","203-3710077-7859526","204-7223834-2689947",
    "203-7929911-2921104","204-7988403-0493936","204-0879284-7151568",
    "204-6465372-6478715","204-7769811-0290751","205-3763394-0706717","026-9586109-7195542",
    "203-1654379-2851512","205-0588063-3845952","205-9045291-9444363","026-3536249-0361113",
]

placeholders = ",".join("?" * len(ALL_ORDER_IDS))
conn = get_connection()
cur = conn.cursor()

cur.execute(f"""
    SELECT
        o.OrderID, o.SKU, o.Quantity, o.PurchaseDate,
        d.idCustomOrderDetails,
        d.CustomizationCategory,
        d.IsTopazImageProcess,
        d.FrontImage,  d.FrontTopazImage,  d.FrontText,  d.FrontFonts,  d.FrontColours,  d.FrontPreviewImage,
        d.BackImage,   d.BackTopazImage,   d.BackText,   d.BackFonts,   d.BackColours,   d.BackPreviewImage,
        d.PocketImage, d.PocketTopazImage, d.PocketText, d.PocketFonts, d.PocketColours,
        d.SleeveImage, d.SleeveTopazImage, d.SleeveText, d.SleeveFonts, d.SleeveColours,
        d.Topaz_Processed, d.IsDesignComplete, d.DateAdd
    FROM tblCustomOrderDetails d
    JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
    WHERE o.OrderID IN ({placeholders})
    ORDER BY o.OrderID, d.DateAdd
""", ALL_ORDER_IDS)

rows = cur.fetchall()
cols = [d[0] for d in cur.description]
conn.close()

def cell(row, name):
    return row[cols.index(name)]

def check_local(filename):
    if not filename:
        return "—"
    fname = os.path.basename(filename.strip())
    path = os.path.join(TEMP_DIR, fname)
    return "LOCAL" if os.path.isfile(path) else "missing"

zones = [
    ("Front",  "FrontImage",  "FrontTopazImage",  "FrontText",  "FrontFonts",  "FrontColours",  "FrontPreviewImage"),
    ("Back",   "BackImage",   "BackTopazImage",   "BackText",   "BackFonts",   "BackColours",   "BackPreviewImage"),
    ("Pocket", "PocketImage", "PocketTopazImage", "PocketText", "PocketFonts", "PocketColours", None),
    ("Sleeve", "SleeveImage", "SleeveTopazImage", "SleeveText", "SleeveFonts", "SleeveColours", None),
]

# Group by OrderID
from collections import defaultdict
by_order = defaultdict(list)
for row in rows:
    by_order[cell(row, "OrderID")].append(row)

print(f"{'='*80}")
print(f"RAW IMAGE AUDIT — {len(ALL_ORDER_IDS)} orders total")
print(f"{'='*80}\n")

raw_image_total = 0
local_found = 0
local_missing = 0

for order_id, order_rows in sorted(by_order.items()):
    first = order_rows[0]
    is_topaz = bool(cell(first, "IsTopazImageProcess"))
    if is_topaz:
        continue  # skip Topaz orders — focus on raw only

    sku = cell(first, "SKU")
    qty = cell(first, "Quantity")
    cat = cell(first, "CustomizationCategory") or "Standard"
    date = str(cell(first, "DateAdd"))[:10]
    n_items = len(order_rows)

    print(f"ORDER: {order_id}  SKU={sku}  qty={qty}  items={n_items}  cat={cat}  date={date}")

    for row in order_rows:
        row_sku = cell(row, "SKU")
        print(f"  Item SKU: {row_sku}")

        for zone_label, img_col, topaz_col, txt_col, font_col, col_col, prev_col in zones:
            img  = cell(row, img_col)   or ""
            timg = cell(row, topaz_col) or ""
            txt  = cell(row, txt_col)   or ""
            font = cell(row, font_col)  or ""
            colour = cell(row, col_col) or ""
            prev = cell(row, prev_col)  if prev_col else ""

            if not img.strip() and not txt.strip():
                continue  # zone not used

            local_status = check_local(img) if img.strip() else "—"
            topaz_status = f"TOPAZ:{timg.strip()}" if timg.strip() else "no-topaz"

            if img.strip():
                raw_image_total += 1
                if local_status == "LOCAL":
                    local_found += 1
                else:
                    local_missing += 1

            print(f"    [{zone_label}]")
            print(f"      image  : {img.strip() or '(none)'}  -> {local_status}")
            print(f"      topaz  : {topaz_status}")
            if prev and prev.strip():
                print(f"      preview: {prev.strip()}")
            if txt.strip():
                print(f"      text   : {txt.strip()[:80]}")
            if font.strip():
                print(f"      font   : {font.strip()}  colour={colour.strip()}")
    print()

print(f"{'='*80}")
print(f"SUMMARY — RAW IMAGES ONLY")
print(f"  Total raw zone images : {raw_image_total}")
print(f"  Found in Temp locally : {local_found}")
print(f"  Missing locally       : {local_missing}")
print(f"{'='*80}")
