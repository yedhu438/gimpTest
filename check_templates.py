import os, sys
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')
from pathlib import Path

base    = os.environ.get('VARSANY_BASE', r'C:\Varsany')
tpl_dir = Path(os.environ.get('VARSANY_TEMPLATES', os.path.join(base, 'template')))
print(f'Template dir : {tpl_dir}')
print(f'Exists       : {tpl_dir.exists()}')
print()

products = [
    'adulttshirt','kidstshirt','adulthoodie','kidshoodie','totebag',
    'backpack','makeupbag','shoebag','shoebag2','stringbag','knittingbag',
    'buckethat','beanie','socks','seatbelt','babyvest','sleepsuit',
    'hodieblanket','cushion','memorialplaque','golftowel','golfcase','slipper',
]

found = missing = 0
for p in products:
    path = tpl_dir / f'{p}.psd'
    if path.exists():
        size_mb = path.stat().st_size / 1024 / 1024
        print(f'  OK      {p}.psd  ({size_mb:.1f} MB)')
        found += 1
    else:
        print(f'  MISSING {p}.psd')
        missing += 1

print(f'\n{found} found, {missing} missing')
print(f'combined_template.psd : {(tpl_dir / "combined_template.psd").exists()}')
