import sys
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')
import pyodbc

JERSEY_PREFIXES = [
    "FootballAdultTee", "FootballKidsTee", "FootballEngAdultTee", "FootballEngKidsTee",
    "EngFootball_Tee", "EngFootballKids_Tee", "EngFootballKidsTee", "EngFBallset01Kids",
    "KidsEngSet", "PPFBall01_Tee", "PPFBall01KidsTee", "PIFBall01_Tee", "PIFBall01KidsTee",
    "PNFBall01_Tee", "PNFBall01KidsTee", "PWFBall01_Tee", "UKOlympicKids_Tee",
    "FootballPortKidsTee", "FootballWalAdultTee", "FootballGerKidsTee",
    "Scotland_Football", "Scotland_FootballKids", "FootballScot3KidsTee",
    "FootballScoKidsTee", "ScotFBallset01Kids", "FootballbabyVscot",
    "PerFrance01", "PerBrazil01", "PerSpain01", "PerNetherlands01", "PerArgentina01",
    "PerPortugal01", "PerGermany01", "PerItalia01", "PinkCymru01KidsTee",
    "PerChampARSENAL01", "Lvrpool201_Tee", "VillaperChamps2601", "PalacePer01_Tee",
    "LBalls01Tee", "LBalls02Tee",
    "ScotlandRugby01", "WalesRugby01", "IrelandRugby01", "EngRugby01", "ERugby01", "EngFBallset01",
    "PEngFB01PoloJersy", "PEngR01PoloJersy", "PSct01PoloJersy", "PWals01PoloJersy", "PWFBall01PoloJersy",
]

def has_jersey_template(sku):
    for prefix in JERSEY_PREFIXES:
        if (sku or "").startswith(prefix):
            return True
    return False

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};SERVER=tcp:81.0.219.26,1433;'
    'DATABASE=dbAmazonCustomOrders;UID=CustOrderUser;PWD=CjxcWx9g,ie8?!9PM;'
    'TrustServerCertificate=yes;Encrypt=yes;', timeout=20)
cur = conn.cursor()
cur.execute("""
    SELECT o.SKU, COUNT(DISTINCT o.OrderID) as orders
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON d.idCustomOrder = o.idCustomOrder
    WHERE d.CustomizationCategory = 'Semicustomized'
    GROUP BY o.SKU
    ORDER BY orders DESC
""")
rows = cur.fetchall()
conn.close()

print(f"{'ORDERS':>7}  SKU")
print("-" * 60)
total = 0
for sku, cnt in rows:
    if not has_jersey_template(sku):
        print(f"{cnt:>7}  {sku}")
        total += cnt
print(f"\nTOTAL: {total} orders -> will fall back to normal processing")
