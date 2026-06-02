# Product canvas sizes from Canvases.xlsx
# All sizes in pixels at 320 DPI (320/2.54 px per cm)

def cm(v):
    return int(v * 320 / 2.54)

PRODUCT_CANVAS = {
    # T-shirts
    "adulttshirt":    {"front": (cm(30), cm(30)), "back": (cm(30), cm(30)), "pocket": (cm(9), cm(9))},
    "kidstshirt":     {"front": (cm(23), cm(30)), "back": (cm(23), cm(30)), "pocket": (cm(9), cm(9))},
    # Hoodies
    "adulthoodie":    {"front": (cm(25), cm(25)), "back": (cm(25), cm(25)), "pocket": (cm(9), cm(9)), "sleeve": (cm(9), cm(7))},
    "kidshoodie":     {"front": (cm(23), cm(20)), "back": (cm(23), cm(20)), "pocket": (cm(9), cm(9))},
    # Bags
    "totebag":        {"front": (cm(28), cm(28)), "back": (cm(28), cm(28))},
    "backpack":       {"front": (cm(18), cm(12))},
    "makeupbag":      {"front": (cm(23), cm(14))},
    "shoebag":        {"front": (cm(23), cm(14))},
    "shoebag2":       {"front": (cm(14), cm(14))},
    "stringbag":      {"front": (cm(22), cm(24))},
    "knittingbag":    {"front": (cm(25), cm(21))},
    # Accessories
    "buckethat":      {"front": (cm(18), cm(5))},
    "beanie":         {"front": (cm(9.5), cm(4.5))},
    "socks":          {"front": (cm(6),  cm(12))},
    "seatbelt":       {"front": (cm(18), cm(4))},
    # Baby / Kids
    "babyvest":       {"front": (cm(15), cm(17))},
    "sleepsuit":      {"front": (cm(13), cm(18))},
    "hodieblanket":   {"front": (cm(17), cm(5))},
    # Home / Other
    "cushion":        {"front": (cm(30), cm(30))},
    "memorialplaque": {"front": (cm(13), cm(8))},
    "golftowel":      {"front": (cm(17), cm(17))},
    "golfcase":       {"front": (cm(15), cm(6))},
    "slipper":        {"front": (cm(6),  cm(6))},
}

if __name__ == "__main__":
    print(f"{'Product':<20} {'Zone':<10} {'Width px':>10} {'Height px':>10} {'Width cm':>10} {'Height cm':>10}")
    print("="*75)
    for prod, zones in PRODUCT_CANVAS.items():
        for zone, (w, h) in zones.items():
            wcm = round(w * 2.54 / 320, 1)
            hcm = round(h * 2.54 / 320, 1)
            print(f"{prod:<20} {zone:<10} {w:>10} {h:>10} {wcm:>10} {hcm:>10}")
