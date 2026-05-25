import pyodbc

orders = [
    '205-0566876-9421157','203-6358377-5149163','205-2691200-9247540','204-6175815-6319532',
    '203-6284984-6990709','202-5695826-6730730','026-8004060-7205938','026-4661817-9808356',
    '206-9033679-6700336','206-6488151-1826726','203-2458418-7929130','204-4569084-6908347',
    '205-0059283-7026714','026-4475985-6335540','206-2926729-8227561','204-3469590-1981138',
    '206-9723138-1409930','203-8747701-8063565','203-0769824-7278706','026-5143928-4717107',
    '203-6571540-0545964','203-8924177-8962765','204-0419638-5629924','202-2824278-7705925',
    '203-4981507-1861105','202-6124476-9078763','202-3323535-1500315','205-1154029-0940352',
    '026-7146966-6097961','206-2241169-3359538','205-8140696-3841927','026-6740262-6427546',
    '026-5475912-1484340','204-4095286-2648341','203-9840841-5309961','203-9378047-6519554',
    '206-7735743-4561927','204-4746318-5023501','206-6341133-4615518','202-6427196-7237960',
    '204-8636254-8865137','202-5259558-3858706','202-6309329-4917906','203-0810994-9265903',
    '026-9457376-0923510','204-7983874-1353127','206-2344667-8010745','026-9196554-2289153',
    '204-4315130-9513115','203-2549626-1342766','202-7408691-1417967','204-7151839-2420342',
    '026-6055312-2469150','202-2205717-9074741'
]

ids = "','".join(orders)
sql = (
    "SELECT o.OrderID, o.SKU,"
    " ISNULL(d.FrontImage,'') AS FrontImage,"
    " ISNULL(d.BackImage,'') AS BackImage,"
    " ISNULL(d.PocketImage,'') AS PocketImage,"
    " ISNULL(d.SleeveImage,'') AS SleeveImage"
    " FROM tblCustomOrder o"
    " JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder"
    " WHERE o.OrderID IN ('" + ids + "')"
    " AND (ISNULL(d.FrontImage,'') <> '' OR ISNULL(d.BackImage,'') <> ''"
    " OR ISNULL(d.PocketImage,'') <> '' OR ISNULL(d.SleeveImage,'') <> '')"
    " ORDER BY o.OrderID"
)

from db import get_connection
conn = get_connection(timeout=10)
cursor = conn.cursor()
cursor.execute(sql)
rows = cursor.fetchall()
conn.close()

print(f'Orders with images: {len(rows)}\n')
print(f'{"#":<4} {"OrderID":<30} {"SKU":<38} {"Image Zones"}')
print('-' * 95)
for i, r in enumerate(rows, 1):
    zones = []
    if r[2]: zones.append('Front')
    if r[3]: zones.append('Back')
    if r[4]: zones.append('Pocket')
    if r[5]: zones.append('Sleeve')
    print(f'{i:<4} {r[0]:<30} {r[1]:<38} {", ".join(zones)}')
