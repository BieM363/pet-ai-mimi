import os
import math
from PIL import Image, ImageDraw

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
GRID_SIZE = 32
CANVAS_SCALE = 4  # 32 * 4 = 128x128 px (ukuran sedang yang pas & proporsional untuk desktop pet)
FINAL_SIZE = (128, 128)

# Palet warna retro pixel art
C_OUTLINE = (38, 26, 20, 255)       # Outline cokelat gelap hangat
C_FUR_MAIN = (244, 162, 97, 255)    # Oranye jahe lembut (ginger cat)
C_FUR_SHADOW = (214, 115, 50, 255)  # Bayangan bulu
C_FUR_LIGHT = (255, 205, 150, 255)  # Highlight bulu
C_BELLY = (255, 246, 235, 255)      # Bulu dada/perut & moncong putih krem
C_EAR_PINK = (255, 170, 175, 255)   # Merah muda telinga & hidung
C_EYE_GREEN = (42, 157, 143, 255)   # Mata zamrud berkilau
C_EYE_DARK = (20, 60, 55, 255)      # Pupil mata
C_WHITE = (255, 255, 255, 255)      # Kilau mata / gigi / debu
C_MOUTH_OPEN = (220, 70, 90, 255)   # Lidah/mulut terbuka saat bicara
C_HEART = (239, 71, 111, 255)       # Partikel hati merah muda
C_SLEEP_Z = (90, 190, 240, 255)     # Huruf Z tidur biru muda
C_BULB_YELLOW = (255, 209, 102, 255)# Lampu ide / tanda tanya kuning cerah
C_DUST = (200, 190, 180, 255)       # Debu mendarat
C_SWEAT = (100, 200, 255, 255)      # Keringat kaget saat diangkat
C_NOTE_CYAN = (72, 202, 228, 255)   # Biru muda not musik
C_NOTE_PINK = (255, 117, 143, 255)  # Merah muda nada musik
C_NOTE_PURPLE = (170, 120, 245, 255)# Ungu not balok musik
C_CLEAR = (0, 0, 0, 0)


def create_base_canvas():
    return Image.new("RGBA", (GRID_SIZE, GRID_SIZE), C_CLEAR)


def draw_pixel(draw, x, y, color):
    """Menggambar 1 pixel tunggal pada koordinat grid."""
    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
        draw.point((x, y), fill=color)


def draw_rect(draw, x1, y1, x2, y2, color):
    """Menggambar blok persegi pixel."""
    draw.rectangle([x1, y1, x2, y2], fill=color)


def draw_cat_frame(
    head_y_offset=0,
    head_x_offset=0,
    mouth_state="closed",      # "closed", "open_smile", "open_talk", "surprised", "yawn"
    eye_state="open",          # "open", "blink", "happy", "sleep", "look_up", "surprised"
    tail_angle=0,              # -2, -1, 0, 1, 2
    body_y_offset=0,
    body_stretch_y=0,
    paw_front_l=(0, 0),
    paw_front_r=(0, 0),
    paw_back_l=(0, 0),
    paw_back_r=(0, 0),
    flip_x=False,
    crouch=False,
    sniffing=False,
    dangling=False,
    extra_items=None           # list of (type, x, y, extra_data)
):
    """
    Fungsi render modular sprite kucing 2D pixel art pada grid 32x32.
    """
    img = create_base_canvas()
    d = ImageDraw.Draw(img)

    base_cy = 18 + body_y_offset
    if crouch:
        base_cy += 2

    # 1. EKOR (TAIL)
    tail_base_x = 6
    tail_base_y = base_cy + 4
    tail_curve = tail_angle

    if dangling:
        # Ekor menjuntai ke bawah saat diangkat
        tail_pixels = [
            (tail_base_x, tail_base_y),
            (tail_base_x, tail_base_y + 1),
            (tail_base_x + tail_curve, tail_base_y + 3),
            (tail_base_x + tail_curve, tail_base_y + 5),
            (tail_base_x + tail_curve + 1, tail_base_y + 6)
        ]
    else:
        tail_pixels = [
            (tail_base_x, tail_base_y),
            (tail_base_x - 1, tail_base_y - 1),
            (tail_base_x - 2, tail_base_y - 3 - tail_curve),
            (tail_base_x - 1 + tail_curve, tail_base_y - 5 - tail_curve * 2),
            (tail_base_x + tail_curve, tail_base_y - 6 - tail_curve * 2),
        ]

    for tx, ty in tail_pixels:
        for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]:
            draw_pixel(d, tx+ox, ty+oy, C_OUTLINE)
    for tx, ty in tail_pixels:
        draw_pixel(d, tx, ty, C_FUR_MAIN)
        if ty > tail_base_y - 2:
            draw_pixel(d, tx, ty, C_FUR_SHADOW)

    # 2. KAKI BELAKANG
    b_pl_x = 8 + paw_back_l[0]
    b_pl_y = base_cy + 7 + paw_back_l[1] + body_stretch_y
    b_pr_x = 18 + paw_back_r[0]
    b_pr_y = base_cy + 7 + paw_back_r[1] + body_stretch_y

    for px, py in [(b_pl_x, b_pl_y), (b_pr_x, b_pr_y)]:
        draw_rect(d, px-1, py-1, px+3, py+2, C_OUTLINE)
        draw_rect(d, px, py, px+2, py+1, C_BELLY)

    # 3. BADAN (BODY)
    bx1 = 8
    by1 = base_cy - 1
    bx2 = 20
    by2 = base_cy + 7 + body_stretch_y

    draw_rect(d, bx1 - 1, by1 - 1, bx2 + 1, by2 + 1, C_OUTLINE)
    draw_rect(d, bx1, by1, bx2, by2, C_FUR_MAIN)
    draw_rect(d, bx1, by2 - 1, bx2, by2, C_FUR_SHADOW)
    draw_rect(d, bx1 + 2, by1 + 1, bx1 + 3, by1 + 3, C_FUR_SHADOW)
    draw_rect(d, bx1 + 5, by1 + 1, bx1 + 6, by1 + 3, C_FUR_SHADOW)
    draw_rect(d, bx1 + 6, by1 + 2, bx2 - 2, by2 - 1, C_BELLY)

    # 4. KAKI DEPAN
    f_pl_x = 11 + paw_front_l[0]
    f_pl_y = base_cy + 7 + paw_front_l[1] + body_stretch_y
    f_pr_x = 15 + paw_front_r[0]
    f_pr_y = base_cy + 7 + paw_front_r[1] + body_stretch_y

    for px, py in [(f_pl_x, f_pl_y), (f_pr_x, f_pr_y)]:
        draw_rect(d, px-1, py-1, px+3, py+2, C_OUTLINE)
        draw_rect(d, px, py, px+2, py+1, C_BELLY)

    # 5. KEPALA (HEAD)
    hx = 15 + head_x_offset
    hy = 10 + head_y_offset + body_y_offset
    if crouch:
        hy += 2
        hx += 1
    if sniffing:
        hy += 3
        hx += 2

    hw = 7
    hh = 6

    # Outline kepala
    draw_rect(d, hx - hw - 1, hy - hh - 1, hx + hw + 1, hy + hh + 1, C_OUTLINE)

    # Telinga Kiri
    draw_rect(d, hx - hw + 1, hy - hh - 3, hx - hw + 3, hy - hh, C_OUTLINE)
    draw_pixel(d, hx - hw + 2, hy - hh - 4, C_OUTLINE)
    draw_rect(d, hx - hw + 2, hy - hh - 2, hx - hw + 3, hy - hh, C_FUR_MAIN)
    draw_pixel(d, hx - hw + 2, hy - hh - 3, C_FUR_MAIN)
    draw_pixel(d, hx - hw + 2, hy - hh - 1, C_EAR_PINK)

    # Telinga Kanan
    draw_rect(d, hx + hw - 3, hy - hh - 3, hx + hw - 1, hy - hh, C_OUTLINE)
    draw_pixel(d, hx + hw - 2, hy - hh - 4, C_OUTLINE)
    draw_rect(d, hx + hw - 3, hy - hh - 2, hx + hw - 2, hy - hh, C_FUR_MAIN)
    draw_pixel(d, hx + hw - 2, hy - hh - 3, C_FUR_MAIN)
    draw_pixel(d, hx + hw - 2, hy - hh - 1, C_EAR_PINK)

    # Warna dasar kepala & loreng
    draw_rect(d, hx - hw, hy - hh, hx + hw, hy + hh, C_FUR_MAIN)
    draw_rect(d, hx - hw + 2, hy - hh, hx + hw - 2, hy - hh, C_FUR_LIGHT)
    draw_rect(d, hx - 1, hy - hh + 1, hx + 1, hy - hh + 2, C_FUR_SHADOW)

    # Pipi & moncong putih
    draw_rect(d, hx - 4, hy + 1, hx + 4, hy + 4, C_BELLY)

    # Hidung merah muda mungil
    draw_rect(d, hx - 1, hy + 1, hx + 1, hy + 2, C_EAR_PINK)

    # Kumis
    draw_pixel(d, hx - 6, hy + 2, C_OUTLINE)
    draw_pixel(d, hx - 7, hy + 1, C_OUTLINE)
    draw_pixel(d, hx - 6, hy + 3, C_OUTLINE)
    draw_pixel(d, hx + 6, hy + 2, C_OUTLINE)
    draw_pixel(d, hx + 7, hy + 1, C_OUTLINE)
    draw_pixel(d, hx + 6, hy + 3, C_OUTLINE)

    # 6. MATA (EYES)
    eye_lx = hx - 4
    eye_rx = hx + 2
    eye_y = hy - 2

    if eye_state == "open":
        draw_rect(d, eye_lx, eye_y, eye_lx + 2, eye_y + 2, C_EYE_GREEN)
        draw_rect(d, eye_lx + 1, eye_y, eye_lx + 1, eye_y + 2, C_EYE_DARK)
        draw_pixel(d, eye_lx, eye_y, C_WHITE)
        draw_rect(d, eye_rx, eye_y, eye_rx + 2, eye_y + 2, C_EYE_GREEN)
        draw_rect(d, eye_rx + 1, eye_y, eye_rx + 1, eye_y + 2, C_EYE_DARK)
        draw_pixel(d, eye_rx, eye_y, C_WHITE)
    elif eye_state == "surprised":
        # Mata membulat kaget (O_O) saat diangkat kursor
        draw_rect(d, eye_lx - 1, eye_y - 1, eye_lx + 2, eye_y + 2, C_OUTLINE)
        draw_rect(d, eye_lx, eye_y, eye_lx + 1, eye_y + 1, C_WHITE)
        draw_pixel(d, eye_lx, eye_y, C_EYE_DARK)
        draw_rect(d, eye_rx, eye_y - 1, eye_rx + 3, eye_y + 2, C_OUTLINE)
        draw_rect(d, eye_rx + 1, eye_y, eye_rx + 2, eye_y + 1, C_WHITE)
        draw_pixel(d, eye_rx + 1, eye_y, C_EYE_DARK)
    elif eye_state == "blink":
        draw_rect(d, eye_lx - 1, eye_y + 1, eye_lx + 2, eye_y + 1, C_OUTLINE)
        draw_rect(d, eye_rx, eye_y + 1, eye_rx + 3, eye_y + 1, C_OUTLINE)
    elif eye_state == "happy":
        draw_pixel(d, eye_lx - 1, eye_y + 1, C_OUTLINE)
        draw_pixel(d, eye_lx, eye_y, C_OUTLINE)
        draw_pixel(d, eye_lx + 1, eye_y, C_OUTLINE)
        draw_pixel(d, eye_lx + 2, eye_y + 1, C_OUTLINE)
        draw_pixel(d, eye_rx + 1, eye_y, C_OUTLINE)
        draw_pixel(d, eye_rx + 2, eye_y, C_OUTLINE)
        draw_pixel(d, eye_rx + 3, eye_y + 1, C_OUTLINE)
    elif eye_state == "sleep":
        draw_rect(d, eye_lx, eye_y + 1, eye_lx + 2, eye_y + 1, C_OUTLINE)
        draw_rect(d, eye_rx, eye_y + 1, eye_rx + 2, eye_y + 1, C_OUTLINE)
    elif eye_state == "look_up":
        draw_rect(d, eye_lx, eye_y - 1, eye_lx + 2, eye_y + 1, C_EYE_GREEN)
        draw_rect(d, eye_lx + 1, eye_y - 1, eye_lx + 2, eye_y, C_EYE_DARK)
        draw_pixel(d, eye_lx, eye_y - 1, C_WHITE)
        draw_rect(d, eye_rx, eye_y - 1, eye_rx + 2, eye_y + 1, C_EYE_GREEN)
        draw_rect(d, eye_rx + 1, eye_y - 1, eye_rx + 2, eye_y, C_EYE_DARK)
        draw_pixel(d, eye_rx, eye_y - 1, C_WHITE)

    # 7. MULUT
    mouth_y = hy + 3
    if mouth_state == "closed":
        draw_pixel(d, hx - 2, mouth_y + 1, C_OUTLINE)
        draw_pixel(d, hx - 1, mouth_y, C_OUTLINE)
        draw_pixel(d, hx, mouth_y + 1, C_OUTLINE)
        draw_pixel(d, hx + 1, mouth_y, C_OUTLINE)
        draw_pixel(d, hx + 2, mouth_y + 1, C_OUTLINE)
    elif mouth_state == "open_talk":
        draw_rect(d, hx - 2, mouth_y, hx + 2, mouth_y + 2, C_OUTLINE)
        draw_rect(d, hx - 1, mouth_y, hx + 1, mouth_y + 1, C_MOUTH_OPEN)
        draw_pixel(d, hx, mouth_y + 1, C_WHITE)
    elif mouth_state == "open_smile":
        draw_rect(d, hx - 2, mouth_y, hx + 2, mouth_y + 2, C_OUTLINE)
        draw_rect(d, hx - 1, mouth_y + 1, hx + 1, mouth_y + 2, C_MOUTH_OPEN)
    elif mouth_state == "surprised":
        # Mulut kecil kaget 'o'
        draw_rect(d, hx - 1, mouth_y, hx + 1, mouth_y + 2, C_OUTLINE)
        draw_pixel(d, hx, mouth_y + 1, C_MOUTH_OPEN)
    elif mouth_state == "yawn":
        # Menguap lebar saat meregangkan badan
        draw_rect(d, hx - 2, mouth_y, hx + 2, mouth_y + 3, C_OUTLINE)
        draw_rect(d, hx - 1, mouth_y + 1, hx + 1, mouth_y + 2, C_MOUTH_OPEN)

    # 8. ITEM TAMBAHAN (Hearts, Zzz, Bulb, Dust, Sweat)
    if extra_items:
        for item in extra_items:
            itype = item[0]
            ix, iy = item[1], item[2]
            if itype == "heart":
                draw_rect(d, ix+1, iy, ix+2, iy, C_HEART)
                draw_rect(d, ix+4, iy, ix+5, iy, C_HEART)
                draw_rect(d, ix, iy+1, ix+6, iy+2, C_HEART)
                draw_rect(d, ix+1, iy+3, ix+5, iy+3, C_HEART)
                draw_rect(d, ix+2, iy+4, ix+4, iy+4, C_HEART)
                draw_pixel(d, ix+3, iy+5, C_HEART)
            elif itype == "z":
                draw_rect(d, ix, iy, ix+3, iy, C_SLEEP_Z)
                draw_pixel(d, ix+2, iy+1, C_SLEEP_Z)
                draw_pixel(d, ix+1, iy+2, C_SLEEP_Z)
                draw_rect(d, ix, iy+3, ix+3, iy+3, C_SLEEP_Z)
            elif itype == "question":
                draw_rect(d, ix+1, iy, ix+3, iy, C_BULB_YELLOW)
                draw_pixel(d, ix+4, iy+1, C_BULB_YELLOW)
                draw_rect(d, ix+2, iy+2, ix+3, iy+3, C_BULB_YELLOW)
                draw_pixel(d, ix+2, iy+5, C_BULB_YELLOW)
            elif itype == "dust":
                # Partikel debu mendarat
                draw_pixel(d, ix, iy, C_DUST)
                draw_pixel(d, ix+1, iy-1, C_DUST)
                draw_pixel(d, ix+2, iy, C_DUST)
            elif itype == "sweat":
                # Keringat kaget di dekat kepala
                draw_pixel(d, ix, iy, C_SWEAT)
                draw_pixel(d, ix, iy+1, C_SWEAT)
                draw_pixel(d, ix-1, iy+1, C_SWEAT)
            elif itype == "music_note":
                # Partikel not musik retro (♪)
                color = item[3] if len(item) > 3 else C_NOTE_CYAN
                draw_pixel(d, ix+2, iy, color)
                draw_pixel(d, ix+3, iy, color)
                draw_pixel(d, ix+2, iy+1, color)
                draw_pixel(d, ix+3, iy+1, color)
                draw_pixel(d, ix+2, iy+2, color)
                draw_rect(d, ix, iy+2, ix+2, iy+3, color)
            elif itype == "double_note":
                # Partikel sepasang not balok musik retro (♫)
                color = item[3] if len(item) > 3 else C_NOTE_PINK
                draw_rect(d, ix, iy, ix+4, iy, color)
                draw_pixel(d, ix, iy+1, color)
                draw_pixel(d, ix, iy+2, color)
                draw_pixel(d, ix+4, iy+1, color)
                draw_pixel(d, ix+4, iy+2, color)
                draw_rect(d, ix-1, iy+2, ix+1, iy+3, color)
                draw_rect(d, ix+3, iy+2, ix+5, iy+3, color)
            elif itype == "sparkle":
                # Partikel kilau bintang retro (+)
                color = item[3] if len(item) > 3 else C_BULB_YELLOW
                draw_pixel(d, ix, iy-1, color)
                draw_pixel(d, ix-1, iy, color)
                draw_pixel(d, ix, iy, C_WHITE)
                draw_pixel(d, ix+1, iy, color)
                draw_pixel(d, ix, iy+1, color)
            elif itype == "popcorn_bucket":
                # Ember popcorn bergaris merah-putih retro
                draw_rect(d, ix, iy+2, ix+7, iy+9, C_OUTLINE)
                draw_rect(d, ix+1, iy+3, ix+2, iy+8, (235, 55, 55, 255))
                draw_rect(d, ix+3, iy+3, ix+3, iy+8, (255, 255, 255, 255))
                draw_rect(d, ix+4, iy+3, ix+5, iy+8, (235, 55, 55, 255))
                draw_rect(d, ix+6, iy+3, ix+6, iy+8, (255, 255, 255, 255))
                draw_pixel(d, ix+1, iy+1, (255, 240, 130, 255))
                draw_pixel(d, ix+2, iy,   (255, 215, 60, 255))
                draw_pixel(d, ix+3, iy+1, (255, 245, 170, 255))
                draw_pixel(d, ix+4, iy,   (255, 215, 60, 255))
                draw_pixel(d, ix+5, iy+1, (255, 240, 130, 255))
                draw_pixel(d, ix+6, iy+1, (255, 220, 80, 255))
                draw_pixel(d, ix+2, iy-1, C_OUTLINE)
                draw_pixel(d, ix+4, iy-1, C_OUTLINE)
            elif itype == "popcorn_piece":
                # Sepotong butir popcorn di cakar / melayang
                draw_pixel(d, ix, iy, (255, 240, 130, 255))
                draw_pixel(d, ix+1, iy, (255, 215, 60, 255))
                draw_pixel(d, ix, iy+1, (240, 180, 40, 255))
            elif itype == "sound_wave":
                # Partikel getar gelombang suara audio
                color = item[3] if len(item) > 3 else C_NOTE_CYAN
                draw_pixel(d, ix, iy, color)
                draw_pixel(d, ix+1, iy+1, color)
                draw_pixel(d, ix+1, iy+2, color)
                draw_pixel(d, ix, iy+3, color)
            elif itype == "disco_sparkle":
                # Partikel bintang disko berkilau terang 8-titik
                color = item[3] if len(item) > 3 else C_BULB_YELLOW
                draw_pixel(d, ix, iy, C_WHITE)
                draw_pixel(d, ix-1, iy, color)
                draw_pixel(d, ix+1, iy, color)
                draw_pixel(d, ix, iy-1, color)
                draw_pixel(d, ix, iy+1, color)
                draw_pixel(d, ix-2, iy, color)
                draw_pixel(d, ix+2, iy, color)
                draw_pixel(d, ix, iy-2, color)
                draw_pixel(d, ix, iy+2, color)
            elif itype == "drink_cup":
                # Gelas minuman dingin bioskop (soda / boba) dengan sedotan melengkung
                draw_rect(d, ix, iy+2, ix+6, iy+8, C_OUTLINE)
                draw_rect(d, ix+1, iy+3, ix+5, iy+7, (50, 140, 235, 255))
                draw_rect(d, ix+2, iy+4, ix+4, iy+6, (255, 255, 255, 255))
                draw_pixel(d, ix+3, iy+5, (235, 60, 70, 255))
                draw_rect(d, ix-1, iy+1, ix+7, iy+1, C_OUTLINE)
                draw_rect(d, ix, iy+1, ix+6, iy+1, (245, 245, 250, 255))
                draw_pixel(d, ix+3, iy, (235, 55, 55, 255))
                draw_pixel(d, ix+2, iy-1, (255, 255, 255, 255))
                draw_pixel(d, ix+1, iy-2, (235, 55, 55, 255))
                draw_pixel(d, ix, iy-3, (255, 255, 255, 255))
                draw_pixel(d, ix-1, iy-3, (235, 55, 55, 255))
            elif itype == "drink_bubble":
                # Gelembung soda melayang di udara
                color = item[3] if len(item) > 3 else (140, 220, 255, 230)
                draw_pixel(d, ix, iy, color)
                draw_pixel(d, ix+1, iy, C_WHITE)
            elif itype == "glasses_3d":
                # Kacamata bioskop 3D retro (lensa kiri merah, lensa kanan cyan)
                draw_rect(d, hx-6, eye_y-1, hx+6, eye_y-1, (245, 245, 250, 255))
                draw_rect(d, hx-5, eye_y, hx-1, eye_y+1, (235, 45, 60, 220))
                draw_rect(d, hx+1, eye_y, hx+5, eye_y+1, (45, 200, 240, 220))
                draw_pixel(d, hx, eye_y, (245, 245, 250, 255))
                draw_pixel(d, hx-6, eye_y, (245, 245, 250, 255))
                draw_pixel(d, hx-6, eye_y+1, (245, 245, 250, 255))
                draw_pixel(d, hx+6, eye_y, (245, 245, 250, 255))
                draw_pixel(d, hx+6, eye_y+1, (245, 245, 250, 255))
                draw_rect(d, hx-5, eye_y+2, hx-1, eye_y+2, (245, 245, 250, 255))
                draw_rect(d, hx+1, eye_y+2, hx+5, eye_y+2, (245, 245, 250, 255))
                draw_pixel(d, hx-7, eye_y, (245, 245, 250, 255))
                draw_pixel(d, hx+7, eye_y, (245, 245, 250, 255))
            elif itype == "gaming_headset":
                # Headset gaming Discord dengan mic boom & lampu LED
                draw_rect(d, hx-6, hy-7, hx+6, hy-7, (45, 45, 55, 255))
                draw_rect(d, hx-5, hy-8, hx+5, hy-8, (72, 202, 228, 255))
                draw_rect(d, hx-9, hy-2, hx-7, hy+2, (45, 45, 55, 255))
                draw_pixel(d, hx-8, hy, (72, 202, 228, 255))
                draw_rect(d, hx+7, hy-2, hx+9, hy+2, (45, 45, 55, 255))
                draw_pixel(d, hx+8, hy, (72, 202, 228, 255))
                draw_pixel(d, hx+7, hy+3, (45, 45, 55, 255))
                draw_pixel(d, hx+6, hy+4, (45, 45, 55, 255))
                draw_pixel(d, hx+4, hy+4, (45, 45, 55, 255))
                draw_pixel(d, hx+3, hy+4, (255, 117, 143, 255))
            elif itype == "listening_dots":
                # Balon dots menyimak obrolan
                count = item[3] if len(item) > 3 else 3
                draw_rect(d, ix, iy, ix+8, iy+4, C_OUTLINE)
                draw_rect(d, ix+1, iy+1, ix+7, iy+3, (255, 255, 255, 240))
                draw_pixel(d, ix+2, iy+5, C_OUTLINE)
                dot_c = (60, 60, 75, 255)
                if count >= 1:
                    draw_pixel(d, ix+2, iy+2, dot_c)
                if count >= 2:
                    draw_pixel(d, ix+4, iy+2, dot_c)
                if count >= 3:
                    draw_pixel(d, ix+6, iy+2, dot_c)

    if flip_x:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    # Upscale 4x Nearest-Neighbor: 32x32 -> 128x128 px (ukuran sedang yang tajam)
    scaled_img = img.resize(FINAL_SIZE, Image.NEAREST)
    return scaled_img


def save_transparent_gif(frames, filepath, duration=150):
    """Menyimpan list Pillow Image RGBA ke format GIF transparan sempurna."""
    converted = []
    for f in frames:
        alpha = f.getchannel('A')
        p_frame = f.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=254)
        mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
        p_frame.paste(255, mask)
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
    print(f"[Aset 128px] Berhasil membuat: {os.path.basename(filepath)}")


def generate_all_cat_gifs():
    """Menghasilkan seluruh animasi Kucing 2D Pixel Art ukuran sedang (128x128 px)."""
    os.makedirs(ASSETS_DIR, exist_ok=True)

    # 1. IDLE
    frames_idle = [
        draw_cat_frame(head_y_offset=0, tail_angle=0, eye_state="open"),
        draw_cat_frame(head_y_offset=-1, body_y_offset=-1, tail_angle=1, eye_state="open"),
        draw_cat_frame(head_y_offset=-1, body_y_offset=-1, tail_angle=2, eye_state="open"),
        draw_cat_frame(head_y_offset=0, tail_angle=1, eye_state="blink"),
        draw_cat_frame(head_y_offset=0, tail_angle=0, eye_state="open"),
        draw_cat_frame(head_y_offset=0, tail_angle=-1, eye_state="open"),
    ]
    save_transparent_gif(frames_idle, os.path.join(ASSETS_DIR, "cat_idle.gif"), duration=220)

    # 1B. IDLE LEFT (Kucing diam menghadap kiri dengan kaki tenang & ekor bergoyang lembut)
    frames_idle_l = [
        draw_cat_frame(head_y_offset=0, tail_angle=0, eye_state="open", flip_x=True),
        draw_cat_frame(head_y_offset=-1, body_y_offset=-1, tail_angle=1, eye_state="open", flip_x=True),
        draw_cat_frame(head_y_offset=-1, body_y_offset=-1, tail_angle=2, eye_state="open", flip_x=True),
        draw_cat_frame(head_y_offset=0, tail_angle=1, eye_state="blink", flip_x=True),
        draw_cat_frame(head_y_offset=0, tail_angle=0, eye_state="open", flip_x=True),
        draw_cat_frame(head_y_offset=0, tail_angle=-1, eye_state="open", flip_x=True),
    ]
    save_transparent_gif(frames_idle_l, os.path.join(ASSETS_DIR, "cat_idle_left.gif"), duration=220)

    # 1C. LOOK LEFT & LOOK RIGHT (Menatap penasaran ke arah jendela tanpa gerak kaki jalan)
    frames_look_l = [
        draw_cat_frame(head_y_offset=0, tail_angle=0, eye_state="look_up", flip_x=True),
        draw_cat_frame(head_y_offset=0, tail_angle=1, eye_state="open", flip_x=True),
        draw_cat_frame(head_y_offset=-1, body_y_offset=-1, tail_angle=2, eye_state="look_up", flip_x=True),
        draw_cat_frame(head_y_offset=0, tail_angle=1, eye_state="blink", flip_x=True),
    ]
    save_transparent_gif(frames_look_l, os.path.join(ASSETS_DIR, "cat_look_left.gif"), duration=250)

    frames_look_r = [
        draw_cat_frame(head_y_offset=0, tail_angle=0, eye_state="look_up", flip_x=False),
        draw_cat_frame(head_y_offset=0, tail_angle=1, eye_state="open", flip_x=False),
        draw_cat_frame(head_y_offset=-1, body_y_offset=-1, tail_angle=2, eye_state="look_up", flip_x=False),
        draw_cat_frame(head_y_offset=0, tail_angle=1, eye_state="blink", flip_x=False),
    ]
    save_transparent_gif(frames_look_r, os.path.join(ASSETS_DIR, "cat_look_right.gif"), duration=250)

    # 1D. CAT LISTEN (DUDUK DIAM MENYIMAK DI VOICE CHANNEL DISCORD)
    frames_listen = [
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=1, eye_state="open", extra_items=[("sparkle", 22, 4, C_NOTE_CYAN)]),
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=0, eye_state="look_up", extra_items=[]),
        draw_cat_frame(crouch=True, head_y_offset=-1, body_y_offset=1, tail_angle=-1, eye_state="open", extra_items=[("sparkle", 23, 5, C_NOTE_CYAN)]),
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=0, eye_state="blink", extra_items=[]),
    ]
    save_transparent_gif(frames_listen, os.path.join(ASSETS_DIR, "cat_listen.gif"), duration=280)

    # 2. TALK
    frames_talk = [
        draw_cat_frame(head_y_offset=0, mouth_state="open_talk", eye_state="open", tail_angle=1),
        draw_cat_frame(head_y_offset=-1, mouth_state="closed", eye_state="open", tail_angle=0),
        draw_cat_frame(head_y_offset=0, mouth_state="open_talk", eye_state="happy", tail_angle=2),
        draw_cat_frame(head_y_offset=-1, mouth_state="open_smile", eye_state="open", tail_angle=1),
    ]
    save_transparent_gif(frames_talk, os.path.join(ASSETS_DIR, "cat_talk.gif"), duration=140)

    # 3. THINK
    frames_think = []
    for i in range(6):
        bob = -1 if i % 2 == 1 else 0
        q_y = 2 + (i % 3)
        extra = [("question", 22, q_y)]
        frames_think.append(draw_cat_frame(head_y_offset=bob, eye_state="look_up", tail_angle=-1 if i < 3 else 0, extra_items=extra))
    save_transparent_gif(frames_think, os.path.join(ASSETS_DIR, "cat_think.gif"), duration=200)

    # 4. SLEEP
    frames_sleep = []
    for i in range(6):
        b_off = 1 if i in [2, 3] else 0
        z1_y = 8 - i * 2
        extras = []
        if z1_y > 0:
            extras.append(("z", 20, z1_y))
        frames_sleep.append(draw_cat_frame(crouch=True, body_y_offset=b_off, eye_state="sleep", tail_angle=-1, extra_items=extras))
    save_transparent_gif(frames_sleep, os.path.join(ASSETS_DIR, "cat_sleep.gif"), duration=320)

    # 5. HAPPY
    frames_happy = []
    for i in range(6):
        jump_y = -2 if i in [1, 2] else 0
        h_y = 5 - (i % 4) * 2
        extra = [("heart", 20, h_y)]
        frames_happy.append(draw_cat_frame(head_y_offset=jump_y, body_y_offset=jump_y, eye_state="happy", mouth_state="open_smile", tail_angle=2 if i % 2 == 0 else -1, extra_items=extra))
    save_transparent_gif(frames_happy, os.path.join(ASSETS_DIR, "cat_happy.gif"), duration=150)

    # 6. WALK RIGHT & LEFT
    walk_paws = [
        ((1, 0), (-1, -1), (0, 0), (0, 0), 0),
        ((0, -1), (1, 0), (1, 0), (-1, -1), -1),
        ((-1, 0), (0, -1), (0, -1), (1, 0), 0),
        ((0, 0), (0, 0), (-1, 0), (0, -1), -1),
    ]
    frames_walk_r = [draw_cat_frame(body_y_offset=by, paw_front_l=fl, paw_front_r=fr, paw_back_l=bl, paw_back_r=br, tail_angle=1 if by == 0 else 0, eye_state="open", flip_x=False) for fl, fr, bl, br, by in walk_paws]
    save_transparent_gif(frames_walk_r, os.path.join(ASSETS_DIR, "cat_walk_right.gif"), duration=130)

    frames_walk_l = [draw_cat_frame(body_y_offset=by, paw_front_l=fl, paw_front_r=fr, paw_back_l=bl, paw_back_r=br, tail_angle=1 if by == 0 else 0, eye_state="open", flip_x=True) for fl, fr, bl, br, by in walk_paws]
    save_transparent_gif(frames_walk_l, os.path.join(ASSETS_DIR, "cat_walk_left.gif"), duration=130)

    # 7. SNIFF
    frames_sniff = [
        draw_cat_frame(crouch=True, sniffing=True, head_y_offset=1, tail_angle=1, eye_state="open"),
        draw_cat_frame(crouch=True, sniffing=True, head_y_offset=2, tail_angle=2, eye_state="blink"),
        draw_cat_frame(crouch=True, sniffing=True, head_y_offset=1, tail_angle=1, eye_state="open"),
    ]
    save_transparent_gif(frames_sniff, os.path.join(ASSETS_DIR, "cat_sniff.gif"), duration=200)

    # 8. CAT PICKED (DIANGKAT KURSOR: Dangling pasrah di udara, kaki bergoyang, mata kaget membulat)
    frames_picked = []
    # 4 frame kaki bergoyang di udara saat diangkat
    picked_seq = [
        (0, (-1, 1), (1, 2), (-1, 1), (1, 2), -1, [("sweat", 22, 6)]),
        (1, (0, 2), (0, 1), (0, 2), (0, 1), 0, [("sweat", 22, 5)]),
        (2, (1, 2), (-1, 1), (1, 2), (-1, 1), 1, [("sweat", 22, 6)]),
        (1, (0, 1), (0, 2), (0, 1), (0, 2), 0, [("sweat", 22, 7)]),
    ]
    for b_str, pfl, pfr, pbl, pbr, tang, extr in picked_seq:
        frames_picked.append(draw_cat_frame(
            head_y_offset=-1,
            body_stretch_y=b_str,
            dangling=True,
            paw_front_l=pfl,
            paw_front_r=pfr,
            paw_back_l=pbl,
            paw_back_r=pbr,
            tail_angle=tang,
            eye_state="surprised",
            mouth_state="surprised",
            extra_items=extr
        ))
    save_transparent_gif(frames_picked, os.path.join(ASSETS_DIR, "cat_picked.gif"), duration=140)

    # 9. CAT LANDING (DIJATUHKAN / MENDARAT: Mendarat di 4 kaki dengan pantulan & debu kartun)
    frames_landing = [
        # Frame 1: Kontak dengan lantai, sedikit jongkok menyerap benturan + partikel debu kiri kanan
        draw_cat_frame(crouch=True, body_y_offset=2, eye_state="blink", tail_angle=-1, extra_items=[("dust", 4, 27), ("dust", 24, 27)]),
        # Frame 2: Memantul sedikit ke atas
        draw_cat_frame(crouch=False, body_y_offset=-1, eye_state="open", mouth_state="open_smile", tail_angle=1),
        # Frame 3: Berdiri kokoh bangga di 4 kaki (kucing selalu mendarat dengan selamat!)
        draw_cat_frame(crouch=False, body_y_offset=0, eye_state="happy", mouth_state="open_smile", tail_angle=2),
    ]
    save_transparent_gif(frames_landing, os.path.join(ASSETS_DIR, "cat_landing.gif"), duration=160)

    # 10. CAT STRETCH (MEREGANGKAN BADAN & MENGUAP)
    frames_stretch = [
        draw_cat_frame(crouch=True, head_y_offset=1, body_y_offset=0, mouth_state="closed", eye_state="open", tail_angle=1),
        draw_cat_frame(crouch=True, head_y_offset=2, body_y_offset=1, mouth_state="yawn", eye_state="sleep", tail_angle=2),
        draw_cat_frame(crouch=True, head_y_offset=2, body_y_offset=1, mouth_state="yawn", eye_state="sleep", tail_angle=2),
        draw_cat_frame(crouch=True, head_y_offset=1, body_y_offset=0, mouth_state="open_smile", eye_state="happy", tail_angle=1),
    ]
    save_transparent_gif(frames_stretch, os.path.join(ASSETS_DIR, "cat_stretch.gif"), duration=240)

    # 11. CAT DANCE (JOGET SPOTIFY: Bergoyang kiri-kanan, menghentak ritmik, melompat riang dengan not musik)
    frames_dance = [
        # Frame 0: Goyang kiri, kaki kiri angkat, ekor kibas kiri, not cyan kanan
        draw_cat_frame(head_y_offset=0, head_x_offset=-1, body_y_offset=0, paw_front_l=(-1, -2), paw_front_r=(0, 0), tail_angle=-2, eye_state="happy", mouth_state="open_smile", extra_items=[("music_note", 22, 5, C_NOTE_CYAN)]),
        # Frame 1: Lompat beat ritmis ke atas, kedua tangan melambai, double note pink
        draw_cat_frame(head_y_offset=-2, head_x_offset=0, body_y_offset=-2, paw_front_l=(0, -2), paw_front_r=(0, -2), tail_angle=1, eye_state="happy", mouth_state="open_smile", extra_items=[("double_note", 20, 3, C_NOTE_PINK)]),
        # Frame 2: Goyang kanan, kaki kanan angkat, ekor kibas kanan, not ungu kiri
        draw_cat_frame(head_y_offset=0, head_x_offset=1, body_y_offset=0, paw_front_l=(0, 0), paw_front_r=(1, -2), tail_angle=2, eye_state="happy", mouth_state="open_smile", extra_items=[("music_note", 4, 6, C_NOTE_PURPLE)]),
        # Frame 3: Beat drop sedikit jongkok, bernyanyi riang, not balok kanan
        draw_cat_frame(crouch=True, head_y_offset=1, head_x_offset=0, body_y_offset=1, tail_angle=0, eye_state="open", mouth_state="open_talk", extra_items=[("music_note", 23, 7, C_NOTE_CYAN)]),
        # Frame 4: Goyang kiri dengan kedipan mata centil, double note kiri
        draw_cat_frame(head_y_offset=0, head_x_offset=-1, body_y_offset=0, paw_front_l=(-1, -2), paw_front_r=(0, 0), tail_angle=-2, eye_state="blink", mouth_state="open_smile", extra_items=[("double_note", 3, 4, C_NOTE_PINK)]),
        # Frame 5: Puncak lompatan riang bersama kedua tangan ke atas & partikel nada musik
        draw_cat_frame(head_y_offset=-2, head_x_offset=0, body_y_offset=-2, paw_front_l=(-1, -2), paw_front_r=(1, -2), tail_angle=2, eye_state="happy", mouth_state="open_talk", extra_items=[("music_note", 21, 4, C_NOTE_PURPLE), ("music_note", 5, 8, C_NOTE_CYAN)]),
    ]
    save_transparent_gif(frames_dance, os.path.join(ASSETS_DIR, "cat_dance.gif"), duration=140)

    # 12. CAT RUN (SPRINT / BERLARI KENCANG KE KANAN & KIRI)
    run_paws = [
        ((2, -1), (1, 0), (-2, -1), (-1, 0), 1, 1, [("dust", 3, 27)]),
        ((0, -2), (0, -2), (0, 0), (0, 0), -2, 2, []),
        ((-1, 0), (-2, 0), (2, -1), (1, 0), 0, 1, [("dust", 2, 27)]),
        ((1, -1), (0, -1), (-1, -1), (-2, 0), -1, 2, [("dust", 4, 26)]),
    ]
    frames_run_r = [
        draw_cat_frame(body_y_offset=by, paw_front_l=fl, paw_front_r=fr, paw_back_l=bl, paw_back_r=br,
                       tail_angle=tang, eye_state="open", mouth_state="open_smile", extra_items=ext, flip_x=False)
        for fl, fr, bl, br, by, tang, ext in run_paws
    ]
    save_transparent_gif(frames_run_r, os.path.join(ASSETS_DIR, "cat_run_right.gif"), duration=95)

    frames_run_l = [
        draw_cat_frame(body_y_offset=by, paw_front_l=fl, paw_front_r=fr, paw_back_l=bl, paw_back_r=br,
                       tail_angle=tang, eye_state="open", mouth_state="open_smile", extra_items=ext, flip_x=True)
        for fl, fr, bl, br, by, tang, ext in run_paws
    ]
    save_transparent_gif(frames_run_l, os.path.join(ASSETS_DIR, "cat_run_left.gif"), duration=95)

    # 13. CAT JUMP (LOMPAT TINGGI MELENGKUNG DI UDARA)
    frames_jump = [
        draw_cat_frame(crouch=True, body_y_offset=2, head_y_offset=1, tail_angle=-1, eye_state="open", extra_items=[("dust", 4, 27), ("dust", 24, 27)]),
        draw_cat_frame(head_y_offset=-3, body_y_offset=-3, paw_front_l=(1, -2), paw_front_r=(1, -2), tail_angle=2, eye_state="happy", mouth_state="open_smile"),
        draw_cat_frame(head_y_offset=-4, body_y_offset=-4, paw_front_l=(2, -2), paw_front_r=(2, -2), paw_back_l=(-1, 1), paw_back_r=(-1, 1), tail_angle=2, eye_state="happy", mouth_state="open_talk", extra_items=[("sparkle", 23, 4)]),
        draw_cat_frame(head_y_offset=-1, body_y_offset=-1, paw_front_l=(0, 0), paw_front_r=(0, 0), tail_angle=1, eye_state="open"),
    ]
    save_transparent_gif(frames_jump, os.path.join(ASSETS_DIR, "cat_jump.gif"), duration=140)

    # 14. CAT POUNCE (MENGENDAP-ENDAP GOYANG PINGGUL LALU MENERKAM MANGSA)
    frames_pounce = [
        draw_cat_frame(crouch=True, body_y_offset=2, head_y_offset=1, tail_angle=-1, eye_state="surprised"),
        draw_cat_frame(crouch=True, body_y_offset=2, head_y_offset=1, tail_angle=-2, eye_state="surprised"),
        draw_cat_frame(crouch=True, body_y_offset=2, head_y_offset=1, tail_angle=2, eye_state="surprised"),
        draw_cat_frame(crouch=True, body_y_offset=1, head_y_offset=0, tail_angle=1, eye_state="open", mouth_state="open_talk"),
        draw_cat_frame(head_y_offset=-2, body_y_offset=-2, paw_front_l=(3, -2), paw_front_r=(3, -2), tail_angle=2, eye_state="happy", mouth_state="open_talk", extra_items=[("dust", 2, 27)]),
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(1, 0), tail_angle=2, eye_state="happy", mouth_state="open_smile", extra_items=[("dust", 18, 27), ("dust", 24, 27)]),
    ]
    save_transparent_gif(frames_pounce, os.path.join(ASSETS_DIR, "cat_pounce.gif"), duration=140)

    # 15. CAT BYE (MELAMBAIKAN CAKAR PAMIT SAAT APLIKASI DITUTUP)
    frames_bye = [
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_r=(1, -1), tail_angle=1, eye_state="happy", mouth_state="open_smile"),
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_r=(0, -3), tail_angle=2, eye_state="happy", mouth_state="open_smile", extra_items=[("sparkle", 22, 5)]),
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_r=(2, -3), tail_angle=1, eye_state="blink", mouth_state="open_smile", extra_items=[("sparkle", 24, 4)]),
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_r=(1, -3), tail_angle=2, eye_state="happy", mouth_state="open_smile", extra_items=[("heart", 21, 4)]),
    ]
    save_transparent_gif(frames_bye, os.path.join(ASSETS_DIR, "cat_bye.gif"), duration=180)

    # 15B. CAT POPCORN (MENONTON VIDEO SAMBIL MAKAN POPCORN)
    frames_popcorn = [
        # Frame 1: Mimi menatap layar memegang ember popcorn, mata bulat penasaran
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(4, 0), tail_angle=1, eye_state="open", mouth_state="closed", extra_items=[("popcorn_bucket", 18, 19)]),
        # Frame 2: Cakar kanan mengambil sebutir popcorn dari ember
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(3, -2), tail_angle=2, eye_state="look_up", mouth_state="open_smile", extra_items=[("popcorn_bucket", 18, 19), ("popcorn_piece", 17, 16)]),
        # Frame 3: Membawa popcorn ke mulut, mulut terbuka mau makan
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(1, -4), tail_angle=1, eye_state="happy", mouth_state="open_talk", extra_items=[("popcorn_bucket", 18, 19), ("popcorn_piece", 15, 12)]),
        # Frame 4: Mengunyah nikmat, mata tersenyum bahagia, kilau bintang
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(3, 0), tail_angle=2, eye_state="happy", mouth_state="open_smile", extra_items=[("popcorn_bucket", 18, 19), ("sparkle", 22, 10)]),
        # Frame 5: Mengunyah sambil menatap layar kembali dengan riang
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(4, 0), tail_angle=1, eye_state="open", mouth_state="closed", extra_items=[("popcorn_bucket", 18, 19), ("sparkle", 12, 6)]),
    ]
    save_transparent_gif(frames_popcorn, os.path.join(ASSETS_DIR, "cat_popcorn.gif"), duration=220)

    # 15C. CAT DANCE DISCO (JOGET SPOTIFY 2: GAYA RETRO DISCO & TUNJUK CAKAR KE ATAS)
    frames_disco = [
        # Frame 0: Persiapan pose disco, pinggul goyang kiri, notasi cyan kiri
        draw_cat_frame(head_y_offset=0, head_x_offset=-1, body_y_offset=0, paw_front_l=(-1, -1), paw_front_r=(1, 0), tail_angle=-2, eye_state="open", mouth_state="open_smile", extra_items=[("music_note", 3, 5, C_NOTE_CYAN), ("disco_sparkle", 26, 4, C_NOTE_PINK)]),
        # Frame 1: Cakar kanan menunjuk tinggi diagonal ke kanan atas (Saturday Night Fever!), badan naik sedikit
        draw_cat_frame(head_y_offset=-2, head_x_offset=1, body_y_offset=-1, paw_front_l=(-1, 0), paw_front_r=(4, -6), tail_angle=1, eye_state="blink", mouth_state="open_smile", extra_items=[("disco_sparkle", 25, 2, C_BULB_YELLOW), ("music_note", 27, 8, C_NOTE_PURPLE)]),
        # Frame 2: Pinggul goyang kanan, kepala angguk santai, double note pink
        draw_cat_frame(head_y_offset=0, head_x_offset=1, body_y_offset=0, paw_front_l=(0, 0), paw_front_r=(1, -2), tail_angle=2, eye_state="happy", mouth_state="open_talk", extra_items=[("double_note", 22, 5, C_NOTE_PINK), ("disco_sparkle", 4, 6, C_NOTE_CYAN)]),
        # Frame 3: Cakar kiri menunjuk tinggi diagonal ke kiri atas, mata riang bahagia
        draw_cat_frame(head_y_offset=-2, head_x_offset=-1, body_y_offset=-1, paw_front_l=(-4, -6), paw_front_r=(1, 0), tail_angle=-1, eye_state="happy", mouth_state="open_smile", extra_items=[("disco_sparkle", 4, 2, C_BULB_YELLOW), ("music_note", 2, 8, C_NOTE_CYAN)]),
        # Frame 4: Shuffle step tengah / jongkok ritmik, bernyanyi riang
        draw_cat_frame(crouch=True, head_y_offset=1, head_x_offset=0, body_y_offset=1, paw_front_l=(-1, 0), paw_front_r=(1, 0), tail_angle=0, eye_state="open", mouth_state="open_talk", extra_items=[("sparkle", 24, 7, C_NOTE_PURPLE), ("sparkle", 5, 8, C_BULB_YELLOW)]),
        # Frame 5: Puncak pose disco: kedua cakar diangkat serong melambai, lompat gembira bersama kilau bintang disko
        draw_cat_frame(head_y_offset=-2, head_x_offset=0, body_y_offset=-2, paw_front_l=(-2, -4), paw_front_r=(2, -4), tail_angle=2, eye_state="happy", mouth_state="open_smile", extra_items=[("disco_sparkle", 23, 3, C_NOTE_PINK), ("disco_sparkle", 5, 4, C_NOTE_CYAN)]),
    ]
    save_transparent_gif(frames_disco, os.path.join(ASSETS_DIR, "cat_dance_disco.gif"), duration=150)

    # 15D. CAT DANCE ROCK (JOGET SPOTIFY 3: ENERGETIK HEADBANG, DRUM BEAT & BEAT DROP JUMP)
    frames_rock = [
        # Frame 0: Headbang ke bawah, kepala rendah, telinga turun, gelombang suara kiri kanan
        draw_cat_frame(crouch=True, head_y_offset=2, body_y_offset=1, tail_angle=-1, eye_state="happy", mouth_state="open_talk", extra_items=[("sound_wave", 3, 15, C_NOTE_CYAN), ("sound_wave", 27, 15, C_NOTE_PINK)]),
        # Frame 1: Headbang lenting ke atas! Kepala naik tinggi, kedua cakar pompa beat drum/DJ
        draw_cat_frame(head_y_offset=-2, body_y_offset=-1, paw_front_l=(-1, -3), paw_front_r=(1, -3), tail_angle=1, eye_state="happy", mouth_state="open_talk", extra_items=[("double_note", 21, 3, C_NOTE_PINK), ("music_note", 4, 5, C_NOTE_CYAN)]),
        # Frame 2: Hentak beat kanan, cakar kanan menghentak, telinga mantul
        draw_cat_frame(head_y_offset=0, head_x_offset=1, body_y_offset=0, paw_front_l=(0, 0), paw_front_r=(1, -1), tail_angle=2, eye_state="open", mouth_state="open_smile", extra_items=[("sound_wave", 28, 14, C_NOTE_PURPLE)]),
        # Frame 3: Headbang ke bawah lagi dengan cepat menghentak lantai!
        draw_cat_frame(crouch=True, head_y_offset=2, body_y_offset=1, tail_angle=0, eye_state="happy", mouth_state="closed", extra_items=[("dust", 4, 27), ("dust", 24, 27)]),
        # Frame 4: Beat drop jump! Lompat tinggi di udara, cakar pumping di udara, nada musik berpendar
        draw_cat_frame(head_y_offset=-3, body_y_offset=-3, paw_front_l=(-1, -4), paw_front_r=(1, -4), tail_angle=2, eye_state="happy", mouth_state="open_talk", extra_items=[("music_note", 22, 3, C_BULB_YELLOW), ("music_note", 5, 4, C_NOTE_CYAN)]),
        # Frame 5: Mendarat kokoh di tanah, kepala mendongak bangga, senyum rocker imut
        draw_cat_frame(crouch=False, head_y_offset=-1, body_y_offset=0, paw_front_l=(0, 0), paw_front_r=(0, 0), tail_angle=1, eye_state="happy", mouth_state="open_smile", extra_items=[("sound_wave", 2, 16, C_NOTE_CYAN), ("sound_wave", 28, 16, C_NOTE_CYAN)]),
    ]
    save_transparent_gif(frames_rock, os.path.join(ASSETS_DIR, "cat_dance_rock.gif"), duration=120)

    # 15E. CAT WATCH DRINK (MENONTON YOUTUBE 2: MENONTON SAMBIL MENYERUPUT MINUMAN DINGIN / SODA DENGAN SEDOTAN)
    frames_drink = [
        # Frame 0: Duduk tenang memegang cangkir minuman soda/boba, menatap layar video
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(4, 0), tail_angle=1, eye_state="look_up", mouth_state="closed", extra_items=[("drink_cup", 18, 18)]),
        # Frame 1: Menyeruput lewat sedotan, mata kedip santai menikmati rasa segar
        draw_cat_frame(crouch=True, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(3, -1), tail_angle=1, eye_state="blink", mouth_state="open_smile", extra_items=[("drink_cup", 18, 18), ("drink_bubble", 20, 16)]),
        # Frame 2: Slurp segar! Gelembung soda naik ke udara, mata tersenyum bahagia
        draw_cat_frame(crouch=True, head_y_offset=-1, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(3, -1), tail_angle=2, eye_state="happy", mouth_state="open_talk", extra_items=[("drink_cup", 18, 18), ("drink_bubble", 19, 14), ("drink_bubble", 21, 12)]),
        # Frame 3: Rasa puas & segar, senyum tersungging, kilau bintang segar di pipi
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(4, 0), tail_angle=2, eye_state="happy", mouth_state="open_smile", extra_items=[("drink_cup", 18, 18), ("sparkle", 12, 8, C_BULB_YELLOW)]),
        # Frame 4: Kembali fokus menatap layar video dengan seksama, ekor melambai pelan
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(4, 0), tail_angle=0, eye_state="open", mouth_state="closed", extra_items=[("drink_cup", 18, 18), ("drink_bubble", 20, 15)]),
        # Frame 5: Menatap penasaran ke adegan seru di layar sambil cangkir tetap dipegang erat
        draw_cat_frame(crouch=True, head_y_offset=1, body_y_offset=1, paw_front_l=(1, 0), paw_front_r=(4, 0), tail_angle=1, eye_state="look_up", mouth_state="closed", extra_items=[("drink_cup", 18, 18), ("sparkle", 24, 10, C_NOTE_CYAN)]),
    ]
    save_transparent_gif(frames_drink, os.path.join(ASSETS_DIR, "cat_watch_drink.gif"), duration=230)

    # 15F. CAT WATCH GLASSES (MENONTON YOUTUBE 3: KACAMATA BIOSKOP 3D RETRO & REAKSI SERU KAGUM)
    frames_glasses = [
        # Frame 0: Memakai kacamata 3D retro (merah & cyan), duduk tegak menatap layar bioskop
        draw_cat_frame(crouch=False, head_y_offset=0, body_y_offset=0, tail_angle=1, eye_state="open", mouth_state="closed", extra_items=[("glasses_3d", 0, 0)]),
        # Frame 1: Efek 3D muncul dari layar! Kepala condong maju, mulut terbuka takjub ("wah!")
        draw_cat_frame(crouch=True, head_y_offset=1, head_x_offset=1, body_y_offset=1, paw_front_r=(2, -2), tail_angle=2, eye_state="surprised", mouth_state="surprised", extra_items=[("glasses_3d", 0, 0), ("sparkle", 24, 7, C_BULB_YELLOW)]),
        # Frame 2: Menoleh miring penasaran mengikuti objek 3D di layar, ekor kibas kiri
        draw_cat_frame(crouch=False, head_y_offset=0, head_x_offset=-1, body_y_offset=0, paw_front_l=(-1, -1), tail_angle=-2, eye_state="look_up", mouth_state="open_smile", extra_items=[("glasses_3d", 0, 0), ("sparkle", 4, 8, C_NOTE_CYAN)]),
        # Frame 3: Adegan sangat seru! Kucing tertawa senang, kedua cakar tepuk tangan riang
        draw_cat_frame(crouch=False, head_y_offset=-1, body_y_offset=-1, paw_front_l=(0, -2), paw_front_r=(0, -2), tail_angle=2, eye_state="happy", mouth_state="open_smile", extra_items=[("glasses_3d", 0, 0), ("sparkle", 22, 5, C_NOTE_PINK), ("sparkle", 6, 6, C_BULB_YELLOW)]),
        # Frame 4: Duduk santai kembali, tersenyum kagum menatap kelanjutan adegan
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=1, eye_state="open", mouth_state="open_smile", extra_items=[("glasses_3d", 0, 0)]),
        # Frame 5: Kedip mata di balik kacamata 3D, ekor melingkar nyaman menikmati film
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=0, eye_state="blink", mouth_state="closed", extra_items=[("glasses_3d", 0, 0), ("sparkle", 12, 5, C_WHITE)]),
    ]
    save_transparent_gif(frames_glasses, os.path.join(ASSETS_DIR, "cat_watch_glasses.gif"), duration=210)

    # 15G. CAT LISTEN HEADSET (MENYIMAK DISCORD 2: MEMAKAI GAMING HEADSET & MIC BOOM DI VOICE CHANNEL)
    frames_headset = [
        # Frame 0: Mimi memakai headset gaming di Discord Voice, duduk tenang menyimak
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=1, eye_state="open", mouth_state="closed", extra_items=[("gaming_headset", 0, 0)]),
        # Frame 1: Ada suara teman masuk di VC! Gelombang suara kiri, kepala sedikit miring kiri menyimak
        draw_cat_frame(crouch=True, head_y_offset=0, head_x_offset=-1, body_y_offset=1, tail_angle=0, eye_state="look_up", mouth_state="closed", extra_items=[("gaming_headset", 0, 0), ("sound_wave", 3, 9, C_NOTE_CYAN)]),
        # Frame 2: Gelombang suara kanan, Mimi mengangguk kecil paham, mata berkedip lembut
        draw_cat_frame(crouch=True, head_y_offset=1, head_x_offset=0, body_y_offset=1, tail_angle=1, eye_state="blink", mouth_state="open_smile", extra_items=[("gaming_headset", 0, 0), ("sound_wave", 26, 9, C_NOTE_CYAN)]),
        # Frame 3: Obrolan lucu di Discord! Tersenyum senang mendengarkan teman bicara
        draw_cat_frame(crouch=True, head_y_offset=-1, body_y_offset=1, tail_angle=2, eye_state="happy", mouth_state="open_smile", extra_items=[("gaming_headset", 0, 0), ("sparkle", 22, 4, C_NOTE_CYAN)]),
        # Frame 4: Kepala miring kanan menyimak penjelasan serius teman, ekor tenang
        draw_cat_frame(crouch=True, head_y_offset=0, head_x_offset=1, body_y_offset=1, tail_angle=0, eye_state="look_up", mouth_state="closed", extra_items=[("gaming_headset", 0, 0), ("sound_wave", 27, 8, C_NOTE_PINK)]),
        # Frame 5: Pose menyimak stabil dan nyaman di voice channel, headset berpendar tenang
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=1, eye_state="open", mouth_state="closed", extra_items=[("gaming_headset", 0, 0), ("sparkle", 5, 8, C_BULB_YELLOW)]),
    ]
    save_transparent_gif(frames_headset, os.path.join(ASSETS_DIR, "cat_listen_headset.gif"), duration=250)

    # 15H. CAT LISTEN NOD (MENYIMAK DISCORD 3: MENGANGGUK-ANGGUK PAHAM DENGAN BALON TITIK-TITIK MENYIMAK)
    frames_nod = [
        # Frame 0: Duduk sopan dan fokus mendengarkan obrolan Discord, mata terbuka jernih
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=1, eye_state="open", mouth_state="closed", extra_items=[]),
        # Frame 1: Angguk pertama ke bawah ("mengerti..."), mata kedip lembut, 1 titik menyimak muncul
        draw_cat_frame(crouch=True, head_y_offset=1, body_y_offset=1, tail_angle=0, eye_state="blink", mouth_state="closed", extra_items=[("listening_dots", 21, 3, 1)]),
        # Frame 2: Kepala terangkat kembali, mata terbuka menyimak, 2 titik menyimak muncul
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=1, eye_state="look_up", mouth_state="open_smile", extra_items=[("listening_dots", 21, 3, 2)]),
        # Frame 3: Angguk kedua lebih mantap ("oh begitu!"), 3 titik menyimak lengkap, senyum setuju
        draw_cat_frame(crouch=True, head_y_offset=1, body_y_offset=1, tail_angle=-1, eye_state="happy", mouth_state="open_smile", extra_items=[("listening_dots", 21, 3, 3)]),
        # Frame 4: Kepala kembali normal, titik menghilang berganti bintang pemahaman
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=1, eye_state="open", mouth_state="closed", extra_items=[("sparkle", 24, 4, C_BULB_YELLOW)]),
        # Frame 5: Duduk tenang menikmati percakapan, ekor bergoyang lembut ke kanan
        draw_cat_frame(crouch=True, head_y_offset=0, body_y_offset=1, tail_angle=2, eye_state="happy", mouth_state="closed", extra_items=[("sparkle", 4, 6, C_NOTE_CYAN)]),
    ]
    save_transparent_gif(frames_nod, os.path.join(ASSETS_DIR, "cat_listen_nod.gif"), duration=260)

    # 16. PREY SPRITES (TIKUS & LALAT PIXEL RETRO)
    generate_prey_assets()

def generate_prey_assets():
    """Membuat aset sprite mangsa mini (tikus dan lalat) berukuran pixel art."""
    # Mouse / Tikus Pixel (24x24 px)
    mouse_frames = []
    for f in range(4):
        img = Image.new("RGBA", (16, 16), C_CLEAR)
        d = ImageDraw.Draw(img)
        # Ekor tikus melengkung
        tail_ox = -1 if f % 2 == 0 else 0
        draw_pixel(d, 2 + tail_ox, 10, C_OUTLINE)
        draw_pixel(d, 3 + tail_ox, 9, C_OUTLINE)
        draw_pixel(d, 4, 10, C_OUTLINE)
        # Badan tikus abu-abu
        draw_rect(d, 5, 8, 11, 11, C_OUTLINE)
        draw_rect(d, 6, 9, 10, 11, (160, 160, 170, 255))
        # Telinga merah muda
        draw_pixel(d, 7, 7, C_EAR_PINK)
        draw_pixel(d, 8, 7, C_OUTLINE)
        # Moncong & hidung
        draw_pixel(d, 12, 10, C_EAR_PINK)
        # Mata hitam
        draw_pixel(d, 10, 9, (20, 20, 20, 255))
        # Kaki bergerak
        leg_off = (f % 2)
        draw_pixel(d, 6 + leg_off, 12, C_OUTLINE)
        draw_pixel(d, 10 - leg_off, 12, C_OUTLINE)
        scaled = img.resize((32, 32), Image.NEAREST)
        mouse_frames.append(scaled)
    save_transparent_gif(mouse_frames, os.path.join(ASSETS_DIR, "prey_mouse.gif"), duration=90)

    # Fly / Lalat Pixel (20x20 px)
    fly_frames = []
    for f in range(4):
        img = Image.new("RGBA", (12, 12), C_CLEAR)
        d = ImageDraw.Draw(img)
        # Badan hitam lalat
        draw_rect(d, 5, 5, 7, 7, (30, 30, 35, 255))
        # Mata merah
        draw_pixel(d, 8, 5, (220, 40, 50, 255))
        # Sayap transparan getar
        wing_color = (180, 230, 255, 200)
        if f % 2 == 0:
            draw_pixel(d, 4, 4, wing_color)
            draw_pixel(d, 5, 3, wing_color)
            draw_pixel(d, 6, 4, wing_color)
        else:
            draw_pixel(d, 4, 3, wing_color)
            draw_pixel(d, 5, 2, wing_color)
            draw_pixel(d, 6, 3, wing_color)
        scaled = img.resize((24, 24), Image.NEAREST)
        fly_frames.append(scaled)
    save_transparent_gif(fly_frames, os.path.join(ASSETS_DIR, "prey_fly.gif"), duration=70)

    print("\n[Aset 128px Selesai] Seluruh animasi Kucing 2D Pixel Art berhasil diperbarui ke ukuran sedang!")


if __name__ == "__main__":
    generate_all_cat_gifs()
