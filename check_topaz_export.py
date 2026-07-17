import sys
sys.path.insert(0, r"C:\gimpTest")
from db import get_connection

ALL_ORDER_IDS = [
    # DTF_FRONT
    "206-0765171-9435537","206-8320801-3516311","203-0958398-6908349","202-7535142-8209967",
    "203-8527305-8206760","202-1368265-9848315","206-5982109-9667503","203-4781098-5941959",
    "203-1494879-9981133","026-0212240-6430755","203-8990486-7580352","203-7154475-2834731",
    "205-4304095-4728322",
    # DTF_BLACK
    "026-8320691-7700315","204-5039273-2417166","206-3733229-0444322","206-5880772-8433134",
    "026-4644118-6006732","026-1772455-0177941","205-4862104-9561915","206-9663784-7689161",
    "203-4380503-5751535",
    # DTF_WHITE
    "202-1335807-9834726","026-6684671-7015512","202-2578485-9273155","203-4165960-9269919",
    "202-1017113-9763522","203-2617297-4925914","204-3602245-8582758","202-5524662-6600321",
    "206-2816408-1143507","203-4958037-9809947","206-5493308-5434767","204-0573699-9620349",
    "206-8511868-0021969","026-2794054-4272322","204-2840141-7993948",
    # AUTOMATED
    "026-4549518-0005966","204-5511522-3006702","205-2041094-9376349","202-1705310-7848337",
    "205-5675263-3073940","205-6704670-2746720","026-6215098-6374722","206-0227530-5873930",
    "204-3344772-4553937","205-2542593-4141968","203-3710077-7859526","204-7223834-2689947",
    "203-7929911-2921104","204-7988403-0493936","204-0879284-7151568",
    # SEMI_CUSTOM (successful)
    "204-6465372-6478715","204-7769811-0290751","205-3763394-0706717","026-9586109-7195542",
    "203-1654379-2851512","205-0588063-3845952","205-9045291-9444363","026-3536249-0361113",
]

placeholders = ",".join("?" * len(ALL_ORDER_IDS))
conn = get_connection()
cur = conn.cursor()

cur.execute(f"""
    SELECT o.OrderID, o.SKU,
           d.IsTopazImageProcess,
           d.FrontImage,  d.FrontTopazImage,
           d.BackImage,   d.BackTopazImage,
           d.PocketImage, d.PocketTopazImage,
           d.SleeveImage, d.SleeveTopazImage
    FROM tblCustomOrderDetails d
    JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
    WHERE o.OrderID IN ({placeholders})
    ORDER BY o.OrderID
""", ALL_ORDER_IDS)

rows = cur.fetchall()
conn.close()

# Count per DB row (one row = one item/size in the order)
topaz_rows = 0
raw_rows = 0
topaz_orders = set()
raw_orders = set()
topaz_image_count = 0  # number of individual zone images that are Topaz

for r in rows:
    order_id, sku, is_topaz, fi, fti, bi, bti, pi, pti, si, sti = r
    used_topaz = bool(is_topaz)

    if used_topaz:
        topaz_rows += 1
        topaz_orders.add(order_id)
        # Count how many zones actually have a Topaz image
        for orig, topaz in [(fi, fti), (bi, bti), (pi, pti), (si, sti)]:
            if topaz and topaz.strip():
                topaz_image_count += 1
    else:
        raw_rows += 1
        raw_orders.add(order_id)

print(f"Total DB rows checked  : {len(rows)}")
print(f"Total unique orders    : {len(set(r[0] for r in rows))}")
print()
print(f"Rows with Topaz images : {topaz_rows}  ({len(topaz_orders)} unique orders)")
print(f"Rows with RAW images   : {raw_rows}   ({len(raw_orders)} unique orders)")
print(f"Topaz zone images used : {topaz_image_count}")
print()

if topaz_orders:
    print("Orders that used Topaz:")
    for oid in sorted(topaz_orders):
        sku = next(r[1] for r in rows if r[0] == oid)
        print(f"  {oid}  ({sku})")
else:
    print("No orders used Topaz images.")
