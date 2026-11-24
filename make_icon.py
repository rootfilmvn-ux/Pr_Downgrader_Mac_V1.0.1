import os, subprocess
from PIL import Image, ImageDraw, ImageFont

size = 1024
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.rounded_rectangle([48, 48, 976, 976], radius=208, fill=(26, 16, 51, 255), outline=(153, 153, 255, 255), width=40)
try:
    font_lg = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 420)
    font_sm = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 132)
except Exception:
    font_lg = ImageFont.load_default()
    font_sm = ImageFont.load_default()

bbox = draw.textbbox((0, 0), "Pr", font=font_lg)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(((size - tw) / 2, 168), "Pr", fill=(153, 153, 255, 255), font=font_lg)

draw.rounded_rectangle([192, 696, 832, 872], radius=40, fill=(16, 185, 129, 255))
bbox2 = draw.textbbox((0, 0), "DOWNGRADE", font=font_sm)
tw2, th2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
draw.text(((size - tw2) / 2, 696 + (176 - th2) / 2 - 16), "DOWNGRADE", fill=(15, 18, 24, 255), font=font_sm)

os.makedirs("app.iconset", exist_ok=True)
for px, fname in [(16,"icon_16x16.png"),(32,"icon_16x16@2x.png"),(32,"icon_32x32.png"),(64,"icon_32x32@2x.png"),(128,"icon_128x128.png"),(256,"icon_128x128@2x.png"),(256,"icon_256x256.png"),(512,"icon_256x256@2x.png"),(512,"icon_512x512.png"),(1024,"icon_512x512@2x.png")]:
    img.resize((px, px), Image.Resampling.LANCZOS).save(os.path.join("app.iconset", fname))
subprocess.run(["iconutil", "-c", "icns", "app.iconset", "-o", "app_icon.icns"], check=False)