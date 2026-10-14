# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import os
import sys
import ctypes
import signal
import warnings

# 1. Konfigurasi path root & modul src
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 2. Sembunyikan window console hitam di Windows jika dijalankan secara silent/background
if sys.platform == "win32" and ("--silent" in sys.argv or "--hide-console" in sys.argv):
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
    except Exception:
        pass

# Saring warning library agar terminal tidak kotor
warnings.filterwarnings("ignore")

# Pastikan encoding Unicode/Emoji aman di Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import QApplication

# Import modul internal dari arsitektur modular src/
from src.core.cat_audio import CatAudioEngine
from src.core.ai_handler import AIHandler
from src.core import autostart
from src.ui.pet_window import CatPetWindow
from src.utils import generate_assets
from src.utils import generate_cat_audio


def ensure_admin_privileges():
    """
    Mengecek apakah aplikasi sudah berjalan dengan hak akses Administrator di Windows.
    Hanya meminta izin UAC jika parameter '--require-admin' disertakan secara eksplisit.
    Secara default, aplikasi berjalan langsung tanpa bertanya (seperti IDM).
    """
    if "--require-admin" not in sys.argv:
        return

    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        is_admin = False

    if not is_admin:
        script_path = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        py_exe = pythonw_path if os.path.exists(pythonw_path) else sys.executable

        try:
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                py_exe,
                f'"{script_path}" {params}'.strip(),
                os.path.dirname(script_path),
                0  # SW_HIDE
            )
            if ret > 32:
                sys.exit(0)
        except Exception:
            pass


def setup_environment() -> dict:
    """Membaca konfigurasi file .env"""
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()
    pet_name = os.getenv("PET_NAME", "Mimi").strip()
    tts_enabled = os.getenv("TTS_ENABLED", "true").strip().lower() in ["true", "1", "yes"]
    tts_rate = int(os.getenv("TTS_RATE", "175"))

    return {
        "api_key": api_key,
        "model_name": model_name,
        "pet_name": pet_name,
        "tts_enabled": tts_enabled,
        "tts_rate": tts_rate
    }


_MUTEX_HANDLE = None

def acquire_single_instance_lock() -> bool:
    """
    Memastikan hanya 1 instance aplikasi Mimi yang dapat berjalan secara bersamaan di Windows.
    Mencegah bug pembukaan aplikasi ganda / duplicate Mimi saat startup Windows.
    """
    global _MUTEX_HANDLE
    if sys.platform != "win32":
        return True
    try:
        ERROR_ALREADY_EXISTS = 183
        mutex_name = "Global\\MimiPixelCatAssistant_SingleInstance_Mutex"
        kernel32 = ctypes.windll.kernel32
        _MUTEX_HANDLE = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        if last_error == ERROR_ALREADY_EXISTS:
            return False
        return True
    except Exception:
        return True


def main():
    """Titik masuk utama (Main Entry Point) aplikasi Virtual Pixel Cat AI."""
    # 0. Cegah Instance Ganda (Single Instance Lock)
    if not acquire_single_instance_lock():
        print("\n🐾 [Mimi] Aplikasi Mimi SUDAH AKTIF dan sedang berjalan di layar desktop Tuan!")
        print("💡 Silakan cek pojok kanan bawah layar desktop Tuan atau System Tray Windows.")
        print("   Jika ingin menjalankan ulang, tutup dulu Mimi lewat klik kanan -> '❌ Keluar (Exit)' atau Task Manager.\n")
        sys.exit(0)

    # 1. Elevasi Administrator Windows (UAC)
    ensure_admin_privileges()

    # 2. Verifikasi kesiapan aset visual & suara di folder assets/
    assets_dir = os.path.join(PROJECT_ROOT, "assets")
    required_gifs = [
        "cat_idle.gif", "cat_idle_left.gif", "cat_look_left.gif", "cat_look_right.gif", "cat_listen.gif",
        "cat_talk.gif", "cat_think.gif", "cat_sleep.gif",
        "cat_happy.gif", "cat_walk_right.gif", "cat_walk_left.gif", "cat_sniff.gif",
        "cat_picked.gif", "cat_landing.gif", "cat_stretch.gif", "cat_dance.gif",
        "cat_run_right.gif", "cat_run_left.gif", "cat_jump.gif", "cat_pounce.gif",
        "cat_bye.gif", "cat_popcorn.gif", "prey_mouse.gif", "prey_fly.gif"
    ]
    if not os.path.exists(assets_dir) or any(not os.path.exists(os.path.join(assets_dir, f)) for f in required_gifs):
        generate_assets.generate_all_cat_gifs()

    sounds_dir = os.path.join(assets_dir, "sounds")
    if not os.path.exists(sounds_dir) or not os.path.exists(os.path.join(sounds_dir, "meow_talk.wav")):
        generate_cat_audio.generate_all_sounds()

    # 3. Konfigurasi High-DPI Display
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Virtual Pixel Cat AI Companion")
    app.setQuitOnLastWindowClosed(False)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    config = setup_environment()
    print(f"\n🐾 [Mimi] Virtual Pixel Cat AI Companion by BieM363 (https://github.com/BieM363)")
    print(f"🐾 Memulai asisten kucing '{config['pet_name']}' di desktop...")

    # 4. Inisialisasi Backend Audio Kucing & AI Engine
    cat_audio_engine = CatAudioEngine(enabled=config["tts_enabled"])
    ai_handler = AIHandler(
        api_key=config["api_key"],
        model_name=config["model_name"],
        pet_name=config["pet_name"]
    )
    print(f"✨ Status: {ai_handler.get_mode_status()}")
    print("🎮 Mimi aktif di desktop! Tekan Ctrl+C di terminal ini jika ingin menutup.\n")

    # 5. Tampilkan GUI Pixel Cat Desktop Pet (128x128)
    pet_win = CatPetWindow(
        ai_handler=ai_handler,
        speech_engine=cat_audio_engine,
        pet_name=config["pet_name"]
    )
    pet_win.show()

    # Pastikan auto-start di Windows aktif
    try:
        if not autostart.is_autostart_enabled():
            autostart.enable_autostart()
    except Exception:
        pass

    # 6. Jalankan Event Loop
    exit_code = app.exec_()
    cat_audio_engine.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
