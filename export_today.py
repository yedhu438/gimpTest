import sys
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')

from batch_processor import run_batch

print("Exporting 5 orders for 2026-06-11...")
print("=" * 60)

run_batch(
    date_filter = '2026-06-11',
    upload_nas  = False,   # re-enable once NAS is reachable
    limit       = 5,
)

print("Done.")
