import os
import shutil
from PIL import Image

src_dir = r'C:\Users\Administrator\.gemini\antigravity\brain\0a1072b0-6c72-41ed-9038-4ddbc2c18e5e'
proj_dir = r'C:\Users\Administrator\Desktop\ImgBatch'

img_icon = os.path.join(src_dir, 'imgbatch_app_icon_1784621910259.jpg')
img_banner = os.path.join(src_dir, 'imgbatch_installer_banner_1784621926990.jpg')
img_logo = os.path.join(src_dir, 'imgbatch_vector_logo_1784621941206.jpg')

# Output dirs
assets_dir = os.path.join(proj_dir, 'assets')
tauri_icons = os.path.join(proj_dir, 'src-tauri', 'icons')
public_dir = os.path.join(proj_dir, 'frontend', 'public')

for d in [assets_dir, tauri_icons, public_dir]:
    os.makedirs(d, exist_ok=True)

# 1. Save PNG & ICO for App Icon
with Image.open(img_icon) as im:
    im.save(os.path.join(assets_dir, 'app_icon.png'))
    im.save(os.path.join(public_dir, 'logo.png'))
    # Save multi-size ICO
    im.save(os.path.join(tauri_icons, 'icon.ico'), format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    im.save(os.path.join(public_dir, 'favicon.ico'), format='ICO', sizes=[(16,16),(32,32),(48,48)])
    im.resize((32, 32)).save(os.path.join(tauri_icons, '32x32.png'))
    im.resize((128, 128)).save(os.path.join(tauri_icons, '128x128.png'))
    im.resize((256, 256)).save(os.path.join(tauri_icons, '128x128@2x.png'))
    im.resize((512, 512)).save(os.path.join(tauri_icons, 'icon.png'))

# 2. Save Banner
with Image.open(img_banner) as im:
    im.save(os.path.join(assets_dir, 'installer_banner.png'))

# 3. Save Vector Logo
with Image.open(img_logo) as im:
    im.save(os.path.join(assets_dir, 'vector_logo.png'))

print('All app logos, icons, and installer graphics saved successfully!')
