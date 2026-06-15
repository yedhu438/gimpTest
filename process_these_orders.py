import sys, os
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')

from batch_processor import run_batch

ORDER_IDS = [
    '202-0171858-2639527',
    '205-2485658-0653912',
    '203-7566644-8139520',
]

for order_id in ORDER_IDS:
    print(f"\n{'='*60}")
    print(f"Processing: {order_id}")
    print('='*60)
    run_batch(order_id_filter=order_id)

print("\nAll done.")
