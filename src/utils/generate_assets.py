# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import os
import sys

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_CURRENT_DIR)
_ROOT_DIR = os.path.dirname(_SRC_DIR)
for _p in [_ROOT_DIR, _SRC_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.utils import generate_pixel_cat
except ImportError:
    from utils import generate_pixel_cat

def generate_all_cat_gifs():
    """Menghasilkan seluruh aset animasi Kucing 2D Pixel Art."""
    generate_pixel_cat.generate_all_cat_gifs()

def generate_all_dog_gifs():
    """Alias kompatibilitas: memanggil pembuatan aset kucing pixel."""
    generate_all_cat_gifs()

if __name__ == "__main__":
    generate_all_cat_gifs()
