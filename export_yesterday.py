import sys
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')

from batch_processor import run_batch

print("Exporting orders for 2026-06-15...")
print("=" * 60)

run_batch(
    date_filter = '2026-06-15',
    upload_nas  = False,
    limit       = None,
)

print("Done.")
