"""Generate high-resolution application icons and Inno Setup installer artwork."""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate():
    res_dir = Path(__file__).resolve().parents[1] / 'resources'
    res_dir.mkdir(parents=True, exist_ok=True)

    # 1. Main Icon (512x512)
    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Rounded base tile with Autodesk Navisworks blue gradient
    # Gradient background
    for y in range(size):
        ratio = y / size
        # From #0078d4 to #003a66
        r = int(0 + (0 - 0) * ratio)
        g = int(120 + (58 - 120) * ratio)
        b = int(212 + (102 - 212) * ratio)
        d.line([(32, y), (size - 32, y)], fill=(r, g, b, 255))

    # Rounded corners mask
    mask = Image.new('L', (size, size), 0)
    d_mask = ImageDraw.Draw(mask)
    d_mask.rounded_rectangle([32, 32, size - 32, size - 32], radius=80, fill=255)
    img.putalpha(mask)

    # Draw 3D Isometric Industrial Pipe & Vessel Lines
    d = ImageDraw.Draw(img)
    # Bevel border
    d.rounded_rectangle([32, 32, size - 32, size - 32], radius=80, outline=(115, 185, 255, 220), width=6)

    # 3D Vessel & Piping Grid
    # Piping lines
    p_color = (80, 220, 120, 240)    # Green piping
    d.line([(120, 360), (220, 310), (320, 360)], fill=p_color, width=16)
    d.line([(220, 310), (220, 200)], fill=p_color, width=16)
    
    # Flange / valve
    d.ellipse([204, 184, 236, 216], fill=(240, 100, 60, 255), outline=(255, 255, 255, 255), width=4)

    # Bold "PV" Monogram
    # "P"
    d.rectangle([130, 140, 166, 320], fill=(255, 255, 255, 255))
    d.arc([130, 140, 240, 230], 270, 90, fill=(255, 255, 255, 255), width=36)
    d.line([(148, 140), (185, 140)], fill=(255, 255, 255, 255), width=36)
    d.line([(148, 230), (185, 230)], fill=(255, 255, 255, 255), width=36)

    # "V"
    d.line([(260, 140), (330, 320)], fill=(255, 255, 255, 255), width=36)
    d.line([(330, 320), (400, 140)], fill=(255, 255, 255, 255), width=36)

    # Subtitle: 3D PLANT
    d.text((155, 390), "PLANTVIEW", fill=(210, 235, 255, 255))

    # Save PNG
    png_path = res_dir / 'plantview.png'
    img.save(png_path, format='PNG')
    print(f'Generated: {png_path}')

    # Save Multi-resolution ICO
    ico_path = res_dir / 'plantview.ico'
    img.save(ico_path, format='ICO', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f'Generated: {ico_path}')

    # 2. Inno Setup Wizard Left Banner (164 x 314 BMP)
    wiz = Image.new('RGB', (164, 314), (0, 75, 140))
    d_wiz = ImageDraw.Draw(wiz)
    for y in range(314):
        ratio = y / 314
        r = int(0 + 20 * ratio)
        g = int(65 + 40 * ratio)
        b = int(130 + 30 * ratio)
        d_wiz.line([(0, y), (164, y)], fill=(r, g, b))
    # Small icon stamp in center
    icon_small = img.resize((96, 96), Image.Resampling.LANCZOS)
    wiz.paste(icon_small, (34, 60), icon_small)
    d_wiz.text((28, 180), "PLANTVIEW", fill=(255, 255, 255))
    d_wiz.text((38, 205), "STUDIO 3D", fill=(180, 220, 255))
    d_wiz.text((45, 235), "v0.0.2", fill=(120, 190, 240))
    wiz_path = res_dir / 'installer_wizard.bmp'
    wiz.save(wiz_path, format='BMP')
    print(f'Generated: {wiz_path}')

    # 3. Inno Setup Small Top Banner (55 x 55 BMP)
    ban = img.resize((55, 55), Image.Resampling.LANCZOS)
    ban_rgb = Image.new('RGB', (55, 55), (255, 255, 255))
    ban_rgb.paste(ban, (0, 0), ban)
    ban_path = res_dir / 'installer_banner.bmp'
    ban_rgb.save(ban_path, format='BMP')
    print(f'Generated: {ban_path}')

if __name__ == '__main__':
    generate()

