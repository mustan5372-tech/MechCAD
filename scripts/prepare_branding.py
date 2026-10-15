"""
Prepare MechCAD Branding Assets
Creates:
- assets/branding/mechcad-logo.png (Full original branding logo)
- assets/branding/mechcad-emblem.png (Cropped emblem for desktop icon)
- assets/branding/mechcad.ico (Windows multi-resolution icon: 16, 24, 32, 48, 64, 128, 256)
- assets/branding/installer-wizard.bmp (Inno Setup wizard left panel 164x314)
- assets/branding/installer-small.bmp (Inno Setup top right small icon 55x58)
"""

import os
from PIL import Image, ImageOps, ImageDraw

def main():
    branding_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "branding")
    os.makedirs(branding_dir, exist_ok=True)

    src_logo_path = os.path.join(os.path.dirname(__file__), "..", "MechCAD_ Futuristic Engineering Logo.png")
    if not os.path.exists(src_logo_path):
        raise FileNotFoundError(f"Source logo not found at {src_logo_path}")

    # 1. Save Full Logo
    full_logo = Image.open(src_logo_path).convert("RGBA")
    full_logo_dest = os.path.join(branding_dir, "mechcad-logo.png")
    full_logo.save(full_logo_dest, "PNG")
    print(f"Saved full logo to {full_logo_dest}")

    # 2. Crop Emblem (Upper symbol: M + Gear + Blueprint)
    crop_emblem = full_logo.crop((220, 120, 1084, 820))
    ew, eh = crop_emblem.size
    bg_color = full_logo.getpixel((10, 10))
    sq = Image.new("RGBA", (ew, ew), bg_color)
    paste_y = (ew - eh) // 2
    sq.paste(crop_emblem, (0, paste_y))
    emblem_img = sq

    emblem_dest = os.path.join(branding_dir, "mechcad-emblem.png")
    emblem_img.save(emblem_dest, "PNG")
    print(f"Saved emblem to {emblem_dest}")

    # 3. Create Multi-Resolution Windows ICO
    # Resolutions: 16, 24, 32, 48, 64, 128, 256
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_dest = os.path.join(branding_dir, "mechcad.ico")
    emblem_img.save(ico_dest, format="ICO", sizes=icon_sizes)
    print(f"Saved Windows ICO to {ico_dest}")

    # Also save full logo as ico for reference if needed
    full_ico_dest = os.path.join(branding_dir, "mechcad-full.ico")
    full_logo.save(full_ico_dest, format="ICO", sizes=icon_sizes)

    # 4. Inno Setup Wizard BMPs
    # WizardImageFile (Large left banner): 164 x 314
    # We create a sleek dark technical banner with the emblem
    banner_w, banner_h = 164, 314
    banner = Image.new("RGB", (banner_w, banner_h), color=(18, 22, 28))
    # Paste scaled emblem in the upper portion
    scaled_emb = emblem_img.convert("RGB").resize((140, 140), Image.Resampling.LANCZOS)
    banner.paste(scaled_emb, (12, 40))
    wizard_bmp = os.path.join(branding_dir, "installer-wizard.bmp")
    banner.save(wizard_bmp, "BMP")
    print(f"Saved Inno Setup wizard banner to {wizard_bmp}")

    # WizardSmallImageFile (Small top-right icon): 55 x 58
    small_w, small_h = 55, 58
    small_banner = Image.new("RGB", (small_w, small_h), color=(24, 28, 35))
    small_emb = emblem_img.convert("RGB").resize((48, 48), Image.Resampling.LANCZOS)
    small_banner.paste(small_emb, (3, 5))
    small_bmp = os.path.join(branding_dir, "installer-small.bmp")
    small_banner.save(small_bmp, "BMP")
    print(f"Saved Inno Setup small icon to {small_bmp}")

    print("Branding asset preparation complete!")

if __name__ == "__main__":
    main()
