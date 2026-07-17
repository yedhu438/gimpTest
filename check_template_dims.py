from psd_tools import PSDImage
import struct

# Also try reading raw PSD header for accurate dimensions
with open(r"C:\gimpTest\template\FootballShorts.psd", "rb") as f:
    header = f.read(26)
    sig = header[0:4]
    version = struct.unpack(">H", header[4:6])[0]
    channels = struct.unpack(">H", header[12:14])[0]
    height = struct.unpack(">I", header[14:18])[0]
    width = struct.unpack(">I", header[18:22])[0]
    depth = struct.unpack(">H", header[22:24])[0]
    color_mode = struct.unpack(">H", header[24:26])[0]

print(f"Raw PSD header:")
print(f"  Signature : {sig}")
print(f"  Version   : {version}")
print(f"  Width     : {width} px  = {width/320:.2f} cm")
print(f"  Height    : {height} px  = {height/320:.2f} cm")
print(f"  Bit depth : {depth}")
print(f"  Color mode: {color_mode}  (3=RGB, 4=CMYK)")

psd = PSDImage.open(r"C:\gimpTest\template\FootballShorts.psd")
print(f"\npsd-tools reports:")
print(f"  Width     : {psd.width} px  = {psd.width/320:.2f} cm")
print(f"  Height    : {psd.height} px  = {psd.height/320:.2f} cm")
