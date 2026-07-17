import sys
sys.path.insert(0, r"C:\gimpTest")
from db import get_connection as get_db

conn = get_db()
cur = conn.cursor()

queries = {
    "DTF_FRONT": """
        SELECT TOP 20 o.OrderID, o.SKU FROM tblCustomOrderDetails d
        JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
        WHERE (d.Topaz_Processed=0 OR d.Topaz_Processed IS NULL)
          AND d.IsDesignComplete=0
          AND (d.FrontImage IS NOT NULL AND d.FrontImage != '')
          AND (d.FrontText IS NOT NULL AND d.FrontText != '')
          AND o.SKU NOT LIKE '%blk%' AND o.SKU NOT LIKE '%Blk%' AND o.SKU NOT LIKE '%BLK%'
          AND o.SKU NOT LIKE '%wht%' AND o.SKU NOT LIKE '%Wht%' AND o.SKU NOT LIKE '%WHT%'
          AND o.SKU NOT LIKE '%Kids%' AND o.SKU NOT LIKE '%kids%'
          AND (d.BackImage IS NULL OR d.BackImage = '')
          AND (d.BackText IS NULL OR d.BackText = '')
          AND (d.SleeveImage IS NULL OR d.SleeveImage = '')
          AND (d.SleeveText IS NULL OR d.SleeveText = '')
          AND (d.CustomizationCategory IS NULL OR d.CustomizationCategory != 'Semicustomized')
        ORDER BY d.DateAdd DESC
    """,
    "DTF_BLACK": """
        SELECT TOP 20 o.OrderID, o.SKU FROM tblCustomOrderDetails d
        JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
        WHERE (d.Topaz_Processed=0 OR d.Topaz_Processed IS NULL)
          AND d.IsDesignComplete=0
          AND (d.FrontImage IS NOT NULL AND d.FrontImage != '')
          AND (d.FrontText IS NOT NULL AND d.FrontText != '')
          AND (o.SKU LIKE '%blk%' OR o.SKU LIKE '%Blk%' OR o.SKU LIKE '%BLK%')
          AND o.SKU NOT LIKE '%Kids%' AND o.SKU NOT LIKE '%kids%'
          AND (d.BackImage IS NULL OR d.BackImage = '')
          AND (d.BackText IS NULL OR d.BackText = '')
          AND (d.CustomizationCategory IS NULL OR d.CustomizationCategory != 'Semicustomized')
        ORDER BY d.DateAdd DESC
    """,
    "DTF_WHITE": """
        SELECT TOP 20 o.OrderID, o.SKU FROM tblCustomOrderDetails d
        JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
        WHERE (d.Topaz_Processed=0 OR d.Topaz_Processed IS NULL)
          AND d.IsDesignComplete=0
          AND (d.FrontImage IS NOT NULL AND d.FrontImage != '')
          AND (d.FrontText IS NOT NULL AND d.FrontText != '')
          AND (o.SKU LIKE '%wht%' OR o.SKU LIKE '%Wht%' OR o.SKU LIKE '%WHT%')
          AND o.SKU NOT LIKE '%Kids%' AND o.SKU NOT LIKE '%kids%'
          AND (d.BackImage IS NULL OR d.BackImage = '')
          AND (d.BackText IS NULL OR d.BackText = '')
          AND (d.CustomizationCategory IS NULL OR d.CustomizationCategory != 'Semicustomized')
        ORDER BY d.DateAdd DESC
    """,
    "KIDS_HOODIE": """
        SELECT TOP 20 o.OrderID, o.SKU FROM tblCustomOrderDetails d
        JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
        WHERE (d.Topaz_Processed=0 OR d.Topaz_Processed IS NULL)
          AND d.IsDesignComplete=0
          AND (d.FrontImage IS NOT NULL AND d.FrontImage != '')
          AND (o.SKU LIKE '%KidsHoodie%' OR o.SKU LIKE '%KidsHdie%'
               OR o.SKU LIKE '%kidshoodie%' OR o.SKU LIKE '%KidsSweat%'
               OR o.SKU LIKE '%KidSweat%' OR o.SKU LIKE '%KidHodie%')
        ORDER BY d.DateAdd DESC
    """,
    "AUTOMATED": """
        SELECT TOP 20 o.OrderID, o.SKU FROM tblCustomOrderDetails d
        JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
        WHERE (d.Topaz_Processed=0 OR d.Topaz_Processed IS NULL)
          AND d.IsDesignComplete=0
          AND (d.FrontImage IS NOT NULL AND d.FrontImage != '')
          AND (d.BackImage IS NOT NULL AND d.BackImage != '')
          AND (d.CustomizationCategory IS NULL OR d.CustomizationCategory != 'Semicustomized')
        ORDER BY d.DateAdd DESC
    """,
    "SEMI_CUSTOM": """
        SELECT TOP 20 o.OrderID, o.SKU FROM tblCustomOrderDetails d
        JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
        WHERE (d.Topaz_Processed=0 OR d.Topaz_Processed IS NULL)
          AND d.IsDesignComplete=0
          AND d.CustomizationCategory = 'Semicustomized'
        ORDER BY d.DateAdd DESC
    """,
}

all_orders = {}
for cat, sql in queries.items():
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        ids = [r[0] for r in rows]
        skus = [r[1] for r in rows]
        print(f"\n=== {cat} ({len(ids)} orders) ===")
        for oid, sku in zip(ids, skus):
            print(f"  {oid}  ({sku})")
        all_orders[cat] = ids
    except Exception as e:
        print(f"{cat}: ERROR - {e}")

conn.close()
