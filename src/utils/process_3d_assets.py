# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.ndimage import label, gaussian_filter

BRAIN_DIR = r"C:\Users\kevin\.gemini\antigravity-ide\brain\83406593-93c7-4fc4-8561-0328596b55bc"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
TARGET_SIZE = (180, 180)

def extract_cutout(image_path, target_size=(160, 160)):
    """
    Mengekstrak karakter anjing 3D dari latar belakang putih studio menggunakan
    analisis label komponen terhubung dan anti-aliasing alpha mask.
    """
    im = Image.open(image_path).convert("RGBA")
    arr = np.array(im)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    
    # Deteksi putih studio
    is_light = (r > 240) & (g > 240) & (b > 240)
    labeled, _ = label(is_light)
    
    # Ambil label yang menyentuh pinggir gambar
    border_labels = set(np.unique(np.concatenate([
        labeled[0, :], labeled[-1, :], labeled[:, 0], labeled[:, -1]
    ])))
    border_labels.discard(0)
    bg_mask = np.isin(labeled, list(border_labels))

    # Masking alpha halus tanpa white halo
    alpha = np.where(bg_mask, 0.0, 1.0)
    alpha_smooth = gaussian_filter(alpha, sigma=0.8)
    alpha_crisp = np.clip((alpha_smooth - 0.22) / 0.58, 0.0, 1.0)
    arr[:, :, 3] = (alpha_crisp * 255).astype(np.uint8)

    res = Image.fromarray(arr)
    bbox = res.getbbox()
    if bbox:
        res = res.crop(bbox)
    
    # Resize proporsional dengan resampling lanczos berkualitas tinggi
    res.thumbnail(target_size, Image.LANCZOS)
    return res

def paste_centered(bg_canvas, fg_image, offset_x=0, offset_y=0):
    """Menempelkan cutout anjing tepat di tengah canvas transparan dengan offset."""
    cw, ch = bg_canvas.size
    fw, fh = fg_image.size
    px = (cw - fw) // 2 + offset_x
    py = (ch - fh) // 2 + offset_y
    bg_canvas.paste(fg_image, (px, py), fg_image)

def save_transparent_gif(frames, filepath, duration=120):
    """Menyimpan list Pillow Image RGBA ke format GIF transparan sempurna."""
    converted = []
    for f in frames:
        alpha = f.getchannel('A')
        p_frame = f.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=254)
        mask = Image.eval(alpha, lambda a: 255 if a <= 120 else 0)
        p_frame.paste(255, mask)
        p_frame.info['transparency'] = 255
        converted.append(p_frame)

    converted[0].save(
        filepath,
        save_all=True,
        append_images=converted[1:],
        duration=duration,
        loop=0,
        transparency=255,
        disposal=2
    )

def draw_soft_shadow(draw, cx, cy, rx, ry, opacity=50):
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(30, 20, 20, opacity))
    draw.ellipse([cx - rx * 0.7, cy - ry * 0.7, cx + rx * 0.7, cy + ry * 0.7], fill=(20, 15, 15, int(opacity * 1.5)))

def create_all_3d_gifs():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    print("[3D Engine] Mengekstrak dan memproses model 3D CGI BonziBuddy-style...")

    # Cari file master 3D render di brain directory
    master_files = {}
    for f in os.listdir(BRAIN_DIR):
        if f.startswith("dog_3d_idle") and f.endswith(".jpg"):
            master_files["idle"] = os.path.join(BRAIN_DIR, f)
        elif f.startswith("dog_3d_walk") and f.endswith(".jpg"):
            master_files["walk"] = os.path.join(BRAIN_DIR, f)
        elif f.startswith("dog_3d_think") and f.endswith(".jpg"):
            master_files["think"] = os.path.join(BRAIN_DIR, f)
        elif f.startswith("dog_3d_sleep") and f.endswith(".jpg"):
            master_files["sleep"] = os.path.join(BRAIN_DIR, f)
        elif f.startswith("dog_3d_happy") and f.endswith(".jpg"):
            master_files["happy"] = os.path.join(BRAIN_DIR, f)

    print(f"[3D Engine] Ditemukan {len(master_files)} master render 3D!")

    # Ekstrak cutout transparan
    cutout_idle = extract_cutout(master_files["idle"], (155, 160))
    cutout_walk = extract_cutout(master_files["walk"], (160, 155))
    cutout_think = extract_cutout(master_files["think"], (155, 160))
    cutout_sleep = extract_cutout(master_files["sleep"], (165, 130))
    cutout_happy = extract_cutout(master_files["happy"], (155, 160))

    # 1. DOG IDLE (6 frames) - Bernapas lembut 3D, mata berkedip
    idle_frames = []
    for i in range(6):
        im = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        draw_soft_shadow(d, 90, 168, 48, 8, opacity=45)
        
        # Nafas vertikal halus
        breathe_y = int(math.sin(i / 6.0 * math.pi * 2) * 2)
        paste_centered(im, cutout_idle, offset_x=0, offset_y=4 + breathe_y)
        
        # Kedip mata di frame ke-3
        if i == 3:
            # Gambar kelopak mata terpejam lucu
            d.arc([75, 48 + breathe_y, 89, 58 + breathe_y], start=200, end=340, fill=(70, 45, 30, 240), width=3)
            d.arc([98, 48 + breathe_y, 112, 58 + breathe_y], start=200, end=340, fill=(70, 45, 30, 240), width=3)

        idle_frames.append(im)
    save_transparent_gif(idle_frames, os.path.join(ASSETS_DIR, "dog_idle.gif"), duration=140)

    # 2. DOG TALK (6 frames) - Gerak mulut dan kepala bicara 3D
    talk_frames = []
    for i in range(6):
        im = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        draw_soft_shadow(d, 90, 168, 48, 8, opacity=50)

        # Ayunan berbicara
        bob_y = -3 if i % 2 == 1 else 0
        paste_centered(im, cutout_idle, offset_x=0, offset_y=4 + bob_y)

        # Variasi mulut berbicara
        if i % 2 == 1:
            d.ellipse([88, 77 + bob_y, 98, 87 + bob_y], fill=(240, 100, 120, 240)) # Lidah bobs up
        talk_frames.append(im)
    save_transparent_gif(talk_frames, os.path.join(ASSETS_DIR, "dog_talk.gif"), duration=120)

    # 3. DOG THINK (6 frames) - Kepala miring bertopang dagu 3D dengan partikel ide
    think_frames = []
    for i in range(6):
        im = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        draw_soft_shadow(d, 90, 168, 48, 8, opacity=45)

        bob_y = int(math.sin(i / 6.0 * math.pi * 2) * 1.5)
        paste_centered(im, cutout_think, offset_x=0, offset_y=4 + bob_y)

        # Partikel pemikiran mengapung
        for p_idx in range((i % 3) + 1):
            px = 142 + p_idx * 9
            py = 38 - p_idx * 7
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(80, 160, 255, 230))
            d.ellipse([px - 1, py - 1, px + 1, py + 1], fill=(255, 255, 255, 240))
        think_frames.append(im)
    save_transparent_gif(think_frames, os.path.join(ASSETS_DIR, "dog_think.gif"), duration=160)

    # 4. DOG SLEEP (8 frames) - Meringkuk tidur lelap 3D + gelembung Zzz
    sleep_frames = []
    for i in range(8):
        im = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        draw_soft_shadow(d, 90, 164, 56, 10, opacity=50)

        breathe_y = int(math.sin(i / 8.0 * math.pi * 2) * 2)
        paste_centered(im, cutout_sleep, offset_x=0, offset_y=16 + breathe_y)

        # Gelembung Zzz melayang
        zx = 126 + int(i * 3.2)
        zy = 58 - int(i * 4.2)
        d.text((zx, zy), "z", fill=(110, 150, 240, 210))
        if i > 2:
            d.text((zx - 16, zy + 14), "Z", fill=(140, 180, 255, 230))
        sleep_frames.append(im)
    save_transparent_gif(sleep_frames, os.path.join(ASSETS_DIR, "dog_sleep.gif"), duration=180)

    # 5. DOG HAPPY (6 frames) - Melambaikan cakar gembira 3D + kilau bintang
    happy_frames = []
    for i in range(6):
        im = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        draw_soft_shadow(d, 90, 168, 48, 8, opacity=50)

        jump_y = -6 if i in [1, 2, 4] else 0
        paste_centered(im, cutout_happy, offset_x=0, offset_y=4 + jump_y)

        # Kilau bintang emas
        if i % 2 == 0:
            d.polygon([(36, 42), (38, 47), (43, 49), (38, 51), (36, 56), (34, 51), (29, 49), (34, 47)], fill=(255, 215, 0, 240))
            d.polygon([(142, 48), (144, 53), (149, 55), (144, 57), (142, 62), (140, 57), (135, 55), (140, 53)], fill=(255, 120, 160, 240))
        happy_frames.append(im)
    save_transparent_gif(happy_frames, os.path.join(ASSETS_DIR, "dog_happy.gif"), duration=100)

    # 6. DOG WALK RIGHT (6 frames) - Melangkah ke kanan 3D
    walk_r_frames = []
    for i in range(6):
        im = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        draw_soft_shadow(d, 90, 168, 52, 9, opacity=50)

        # Irama langkah kaki 3D
        step_bounce = -4 if i in [1, 4] else 0
        step_x = (i % 3) * 2 - 2
        paste_centered(im, cutout_walk, offset_x=step_x, offset_y=6 + step_bounce)
        walk_r_frames.append(im)
    save_transparent_gif(walk_r_frames, os.path.join(ASSETS_DIR, "dog_walk_right.gif"), duration=110)

    # 7. DOG WALK LEFT (6 frames) - Melangkah ke kiri 3D (flip horizontal)
    walk_l_frames = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in walk_r_frames]
    save_transparent_gif(walk_l_frames, os.path.join(ASSETS_DIR, "dog_walk_left.gif"), duration=110)

    # 8. DOG SNIFF (6 frames) - Mengendus layar 3D
    sniff_frames = []
    for i in range(6):
        im = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        draw_soft_shadow(d, 90, 168, 52, 9, opacity=50)

        sniff_down = 8 + (i % 3) * 2
        paste_centered(im, cutout_walk, offset_x=0, offset_y=6 + sniff_down)

        # Gelombang endus udara
        if i % 2 == 0:
            d.arc([145, 145, 155, 155], start=270, end=90, fill=(120, 180, 255, 220), width=2)
            d.arc([152, 142, 164, 158], start=270, end=90, fill=(120, 180, 255, 160), width=2)
        sniff_frames.append(im)
    save_transparent_gif(sniff_frames, os.path.join(ASSETS_DIR, "dog_sniff.gif"), duration=150)

    print("[3D Engine] Sukses! Seluruh 8 aset animasi 3D CGI kini aktif di folder 'assets/'!")

if __name__ == "__main__":
    create_all_3d_gifs()
