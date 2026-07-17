"""
Detailed Topaz processing analysis across the entire database.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\gimpTest")
from db import get_connection

conn = get_connection()
cur = conn.cursor()

# ── 1. Overall counts ──────────────────────────────────────────────────────────
cur.execute("""
    SELECT
        COUNT(*)                                                         AS total_rows,

        -- Has at least one image field (image order, not text-only)
        SUM(CASE WHEN (FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(FrontImage))) > 0)
                   OR  (BackImage  IS NOT NULL AND LEN(LTRIM(RTRIM(BackImage)))  > 0)
                   OR  (PocketImage IS NOT NULL AND LEN(LTRIM(RTRIM(PocketImage))) > 0)
                   OR  (SleeveImage IS NOT NULL AND LEN(LTRIM(RTRIM(SleeveImage))) > 0)
                 THEN 1 ELSE 0 END)                                      AS has_image,

        -- IsTopazImageProcess states
        SUM(CASE WHEN IsTopazImageProcess = 1  THEN 1 ELSE 0 END)       AS topaz_flag_1,
        SUM(CASE WHEN IsTopazImageProcess = 0  THEN 1 ELSE 0 END)       AS topaz_flag_0,
        SUM(CASE WHEN IsTopazImageProcess IS NULL THEN 1 ELSE 0 END)    AS topaz_flag_null,

        -- Topaz_Processed (separate flag)
        SUM(CASE WHEN Topaz_Processed = 1  THEN 1 ELSE 0 END)           AS topaz_proc_true,
        SUM(CASE WHEN Topaz_Processed = 0  THEN 1 ELSE 0 END)           AS topaz_proc_false,
        SUM(CASE WHEN Topaz_Processed IS NULL THEN 1 ELSE 0 END)        AS topaz_proc_null,

        -- Has FrontTopazImage populated
        SUM(CASE WHEN FrontTopazImage IS NOT NULL
                   AND LEN(LTRIM(RTRIM(FrontTopazImage))) > 0 THEN 1 ELSE 0 END) AS front_topaz_set,

        -- Has BackTopazImage populated
        SUM(CASE WHEN BackTopazImage IS NOT NULL
                   AND LEN(LTRIM(RTRIM(BackTopazImage))) > 0 THEN 1 ELSE 0 END)  AS back_topaz_set

    FROM tblCustomOrderDetails
""")
r = cur.fetchone()
total, has_img, tp1, tp0, tpnull, tprt, tprf, tprnull, ft_set, bt_set = r

print("=" * 72)
print("TOPAZ PROCESSING ANALYSIS — FULL DATABASE")
print("=" * 72)
print(f"\n[1] OVERALL")
print(f"  Total detail rows          : {total:,}")
print(f"  Rows with image data       : {has_img:,}  ({has_img/total*100:.1f}%)")
print(f"  Text-only rows (no image)  : {total-has_img:,}  ({(total-has_img)/total*100:.1f}%)")

print(f"\n[2] IsTopazImageProcess flag (on rows WITH images)")
# Recount on image rows only
cur.execute("""
    SELECT
        SUM(CASE WHEN IsTopazImageProcess = 1     THEN 1 ELSE 0 END),
        SUM(CASE WHEN IsTopazImageProcess = 0     THEN 1 ELSE 0 END),
        SUM(CASE WHEN IsTopazImageProcess IS NULL THEN 1 ELSE 0 END),
        COUNT(*)
    FROM tblCustomOrderDetails
    WHERE (FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(FrontImage))) > 0)
       OR (BackImage  IS NOT NULL AND LEN(LTRIM(RTRIM(BackImage)))  > 0)
       OR (PocketImage IS NOT NULL AND LEN(LTRIM(RTRIM(PocketImage))) > 0)
       OR (SleeveImage IS NOT NULL AND LEN(LTRIM(RTRIM(SleeveImage))) > 0)
""")
r2 = cur.fetchone()
i1, i0, inull, itotal = r2
print(f"  Image rows total           : {itotal:,}")
print(f"  IsTopazImageProcess = 1    : {i1:,}  ({i1/itotal*100:.1f}%)  ← Topaz done")
print(f"  IsTopazImageProcess = 0    : {i0:,}  ({i0/itotal*100:.1f}%)  ← not sent / failed")
print(f"  IsTopazImageProcess = NULL : {inull:,}  ({inull/itotal*100:.1f}%)  ← never attempted")

print(f"\n[3] Topaz_Processed flag (on image rows)")
cur.execute("""
    SELECT
        SUM(CASE WHEN Topaz_Processed = 1     THEN 1 ELSE 0 END),
        SUM(CASE WHEN Topaz_Processed = 0     THEN 1 ELSE 0 END),
        SUM(CASE WHEN Topaz_Processed IS NULL THEN 1 ELSE 0 END)
    FROM tblCustomOrderDetails
    WHERE (FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(FrontImage))) > 0)
       OR (BackImage  IS NOT NULL AND LEN(LTRIM(RTRIM(BackImage)))  > 0)
       OR (PocketImage IS NOT NULL AND LEN(LTRIM(RTRIM(PocketImage))) > 0)
       OR (SleeveImage IS NOT NULL AND LEN(LTRIM(RTRIM(SleeveImage))) > 0)
""")
tp1r, tp0r, tpnr = cur.fetchone()
print(f"  Topaz_Processed = 1        : {tp1r:,}  ({tp1r/itotal*100:.1f}%)")
print(f"  Topaz_Processed = 0        : {tp0r:,}  ({tp0r/itotal*100:.1f}%)")
print(f"  Topaz_Processed = NULL     : {tpnr:,}  ({tpnr/itotal*100:.1f}%)")

# ── 2. Mismatch: Topaz_Processed=1 but IsTopazImageProcess=0/NULL ─────────────
print(f"\n[4] FLAG MISMATCHES (potential failures)")
cur.execute("""
    SELECT COUNT(*) FROM tblCustomOrderDetails
    WHERE Topaz_Processed = 1
      AND (IsTopazImageProcess IS NULL OR IsTopazImageProcess = 0)
      AND (FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(FrontImage))) > 0)
""")
mismatch1 = cur.fetchone()[0]
print(f"  Topaz_Processed=1 but IsTopazImageProcess=0/NULL : {mismatch1:,}")

cur.execute("""
    SELECT COUNT(*) FROM tblCustomOrderDetails
    WHERE IsTopazImageProcess = 1
      AND (Topaz_Processed IS NULL OR Topaz_Processed = 0)
      AND (FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(FrontImage))) > 0)
""")
mismatch2 = cur.fetchone()[0]
print(f"  IsTopazImageProcess=1 but Topaz_Processed=0/NULL : {mismatch2:,}")

# ── 3. Topaz flag set but TopazImage columns are EMPTY ────────────────────────
print(f"\n[5] IsTopazImageProcess=1 but TopazImage columns EMPTY")
cur.execute("""
    SELECT COUNT(*) FROM tblCustomOrderDetails
    WHERE IsTopazImageProcess = 1
      AND (FrontTopazImage  IS NULL OR LEN(LTRIM(RTRIM(FrontTopazImage)))  = 0)
      AND (BackTopazImage   IS NULL OR LEN(LTRIM(RTRIM(BackTopazImage)))   = 0)
      AND (PocketTopazImage IS NULL OR LEN(LTRIM(RTRIM(PocketTopazImage))) = 0)
      AND (SleeveTopazImage IS NULL OR LEN(LTRIM(RTRIM(SleeveTopazImage))) = 0)
""")
flag_but_empty = cur.fetchone()[0]
print(f"  Count : {flag_but_empty:,}  ← flag says done but no Topaz filename stored")

# ── 4. TopazImage set but FrontImage also empty (no original) ─────────────────
print(f"\n[6] FrontTopazImage set, FrontImage is EMPTY")
cur.execute("""
    SELECT COUNT(*) FROM tblCustomOrderDetails
    WHERE FrontTopazImage IS NOT NULL AND LEN(LTRIM(RTRIM(FrontTopazImage))) > 0
      AND (FrontImage IS NULL OR LEN(LTRIM(RTRIM(FrontImage))) = 0)
""")
topaz_no_orig = cur.fetchone()[0]
print(f"  Count : {topaz_no_orig:,}")

# ── 5. Per-zone breakdown of Topaz coverage ───────────────────────────────────
print(f"\n[7] PER-ZONE TOPAZ COVERAGE")
cur.execute("""
    SELECT
        -- Front
        SUM(CASE WHEN FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(FrontImage))) > 0 THEN 1 ELSE 0 END)       AS front_raw,
        SUM(CASE WHEN FrontTopazImage IS NOT NULL AND LEN(LTRIM(RTRIM(FrontTopazImage))) > 0 THEN 1 ELSE 0 END) AS front_topaz,
        -- Back
        SUM(CASE WHEN BackImage IS NOT NULL AND LEN(LTRIM(RTRIM(BackImage))) > 0 THEN 1 ELSE 0 END)         AS back_raw,
        SUM(CASE WHEN BackTopazImage IS NOT NULL AND LEN(LTRIM(RTRIM(BackTopazImage))) > 0 THEN 1 ELSE 0 END)   AS back_topaz,
        -- Pocket
        SUM(CASE WHEN PocketImage IS NOT NULL AND LEN(LTRIM(RTRIM(PocketImage))) > 0 THEN 1 ELSE 0 END)     AS pocket_raw,
        SUM(CASE WHEN PocketTopazImage IS NOT NULL AND LEN(LTRIM(RTRIM(PocketTopazImage))) > 0 THEN 1 ELSE 0 END) AS pocket_topaz,
        -- Sleeve
        SUM(CASE WHEN SleeveImage IS NOT NULL AND LEN(LTRIM(RTRIM(SleeveImage))) > 0 THEN 1 ELSE 0 END)     AS sleeve_raw,
        SUM(CASE WHEN SleeveTopazImage IS NOT NULL AND LEN(LTRIM(RTRIM(SleeveTopazImage))) > 0 THEN 1 ELSE 0 END) AS sleeve_topaz
    FROM tblCustomOrderDetails
""")
zr = cur.fetchone()
fraw, ftop, braw, btop, praw, ptop, sraw, stop = zr
def pct(a, b): return f"{a/b*100:.1f}%" if b else "n/a"
print(f"  {'Zone':<8}  {'Raw images':>12}  {'Topaz images':>14}  {'Coverage':>10}")
print(f"  {'-'*52}")
print(f"  {'Front':<8}  {fraw:>12,}  {ftop:>14,}  {pct(ftop,fraw):>10}")
print(f"  {'Back':<8}  {braw:>12,}  {btop:>14,}  {pct(btop,braw):>10}")
print(f"  {'Pocket':<8}  {praw:>12,}  {ptop:>14,}  {pct(ptop,praw):>10}")
print(f"  {'Sleeve':<8}  {sraw:>12,}  {stop:>14,}  {pct(stop,sraw):>10}")

# ── 6. Recent trend: last 7 days ──────────────────────────────────────────────
print(f"\n[8] RECENT TREND — last 7 days (by DateAdd)")
cur.execute("""
    SELECT
        CAST(DateAdd AS DATE)                                            AS day,
        COUNT(*)                                                         AS img_rows,
        SUM(CASE WHEN IsTopazImageProcess = 1  THEN 1 ELSE 0 END)       AS topaz_done,
        SUM(CASE WHEN IsTopazImageProcess = 0  THEN 1 ELSE 0 END)       AS topaz_zero,
        SUM(CASE WHEN IsTopazImageProcess IS NULL THEN 1 ELSE 0 END)    AS topaz_null
    FROM tblCustomOrderDetails
    WHERE DateAdd >= DATEADD(DAY, -7, GETDATE())
      AND (FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(FrontImage))) > 0)
    GROUP BY CAST(DateAdd AS DATE)
    ORDER BY day DESC
""")
rows = cur.fetchall()
print(f"  {'Date':<12}  {'Img rows':>9}  {'Topaz done':>11}  {'Flag=0':>8}  {'NULL':>8}  {'Done%':>8}")
print(f"  {'-'*64}")
for row in rows:
    day, img, done, zero, null = row
    print(f"  {str(day):<12}  {img:>9}  {done:>11,}  {zero:>8,}  {null:>8,}  {pct(done,img):>8}")

# ── 7. TopazImageStartTime vs IsTopazImageProcess: stuck orders ───────────────
print(f"\n[9] STUCK / FAILED TOPAZ JOBS")
print(f"  (TopazImageStartTime set but IsTopazImageProcess still 0/NULL)")
cur.execute("""
    SELECT COUNT(*) FROM tblCustomOrderDetails
    WHERE TopazImageStartTime IS NOT NULL
      AND (IsTopazImageProcess IS NULL OR IsTopazImageProcess = 0)
      AND (FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(FrontImage))) > 0)
""")
stuck = cur.fetchone()[0]
print(f"  Stuck/failed jobs : {stuck:,}")

cur.execute("""
    SELECT TOP 10
        o.OrderID, o.SKU,
        d.TopazImageStartTime,
        d.IsTopazImageProcess,
        d.Topaz_Processed,
        d.FrontImage,
        d.FrontTopazImage
    FROM tblCustomOrderDetails d
    JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
    WHERE d.TopazImageStartTime IS NOT NULL
      AND (d.IsTopazImageProcess IS NULL OR d.IsTopazImageProcess = 0)
      AND (d.FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(d.FrontImage))) > 0)
    ORDER BY d.TopazImageStartTime DESC
""")
rows = cur.fetchall()
if rows:
    print(f"\n  Sample stuck orders:")
    for row in rows:
        oid, sku, start, flag, proc, fimg, ftopaz = row
        print(f"    {oid}  {sku}")
        print(f"      StartTime={start}  flag={flag}  proc={proc}")
        print(f"      FrontImage={fimg}")
        print(f"      FrontTopazImage={ftopaz}")

# ── 8. IsDesignComplete=0 but IsTopazImageProcess=1: ready to export ──────────
print(f"\n[10] READY TO EXPORT (Topaz done, design not yet complete)")
cur.execute("""
    SELECT COUNT(*) FROM tblCustomOrderDetails d
    JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
    WHERE d.IsTopazImageProcess = 1
      AND d.IsDesignComplete = 0
      AND (d.FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(d.FrontImage))) > 0)
""")
ready = cur.fetchone()[0]
print(f"  Orders ready (Topaz done, design pending) : {ready:,}")

cur.execute("""
    SELECT COUNT(*) FROM tblCustomOrderDetails d
    JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
    WHERE (d.IsTopazImageProcess IS NULL OR d.IsTopazImageProcess = 0)
      AND d.IsDesignComplete = 0
      AND (d.FrontImage IS NOT NULL AND LEN(LTRIM(RTRIM(d.FrontImage))) > 0)
""")
waiting = cur.fetchone()[0]
print(f"  Orders waiting on Topaz (design pending)  : {waiting:,}")

conn.close()
print(f"\n{'='*72}")
