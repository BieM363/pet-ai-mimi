import os
import sys
import datetime
import subprocess

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
APP_NAME = "MimiPetAssistant"
REG_RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def get_startup_dir() -> str:
    """Mengambil path folder Startup Windows pengguna saat ini."""
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
    return ""

def get_vbs_launcher_path() -> str:
    startup_dir = get_startup_dir()
    if startup_dir:
        return os.path.join(startup_dir, f"{APP_NAME}.vbs")
    return ""

def is_autostart_enabled() -> bool:
    """Mengecek apakah auto-start aktif di Windows Registry Run."""
    # Bersihkan file VBS startup lama jika ada untuk mencegah eksekusi ganda
    vbs_path = get_vbs_launcher_path()
    if vbs_path and os.path.exists(vbs_path):
        try:
            os.remove(vbs_path)
        except Exception:
            pass

    if HAS_WINREG:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, APP_NAME)
                return True
        except (FileNotFoundError, OSError):
            pass

    return False

def enable_autostart() -> tuple:
    """
    Mengaktifkan program agar otomatis berjalan di background saat Windows dinyalakan/login.
    Menggunakan jalur tunggal yang bersih via Windows Registry Run (mencegah instance ganda).
    """
    if not HAS_WINREG:
        return False, "Modul winreg Windows tidak tersedia."

    # Pastikan file VBS di Startup dihapus agar tidak terjadi duplikasi pembukaan aplikasi
    vbs_path = get_vbs_launcher_path()
    if vbs_path and os.path.exists(vbs_path):
        try:
            os.remove(vbs_path)
        except Exception:
            pass

    pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    py_exe = pythonw_path if os.path.exists(pythonw_path) else sys.executable
    main_py = os.path.join(PROJECT_ROOT, "main.py")

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_SET_VALUE) as key:
            cmd = f'"{py_exe}" "{main_py}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
    except Exception as e:
        return False, f"Gagal mendaftarkan auto-start di Registry: {e}"

    return True, "Meow! Horeee! Mimi sekarang akan otomatis aktif saat komputer Windows dinyalakan! 🚀🐾"

def disable_autostart() -> tuple:
    """Menonaktifkan auto-start saat Windows menyala."""
    vbs_path = get_vbs_launcher_path()
    removed = False

    if vbs_path and os.path.exists(vbs_path):
        try:
            os.remove(vbs_path)
            removed = True
        except Exception:
            pass

    if HAS_WINREG:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, APP_NAME)
                removed = True
        except (FileNotFoundError, OSError):
            pass

    if removed:
        return True, "Meow! Auto-start dinonaktifkan. Mimi hanya akan muncul saat Tuan membukanya secara manual ya! 🐾"
    return True, "Auto-start sudah dalam keadaan nonaktif, Tuan!"

def get_time_greeting() -> str:
    """Menghasilkan sapaan berdasarkan waktu lokal saat komputer dinyalakan."""
    hour = datetime.datetime.now().hour
    if 4 <= hour < 11:
        return "pagi 🌅"
    elif 11 <= hour < 15:
        return "siang ☀️"
    elif 15 <= hour < 18:
        return "sore 🌇"
    else:
        return "malam 🌙"

def generate_startup_greeting(user_name: str, is_secret: bool = False) -> str:
    """
    Menghasilkan kalimat sapaan hangat dan ceria saat komputer Windows baru menyala.
    Memperhatikan waktu hari dan status kerahasiaan nama pengguna.
    """
    waktu = get_time_greeting()
    
    if is_secret:
        return (
            f"Meoww! Selamat {waktu}, Tuan! *menggeliat bangun dengan mata berbinar lalu kibas ekor manis* ☀️🐾\n\n"
            f"Senang sekali melihat Tuan menyalakan komputer hari ini! Tenang saja, rahasia nama Tuan tetap aman terkunci di dalam brankas Mimi. "
            f"Mimi siap setia menemani dan membantu Tuan seharian penuh! ✨"
        )
    elif user_name:
        return (
            f"Meoww! Selamat {waktu}, Tuan {user_name}! *menggeliat bangun ceria lalu kibas ekor riang* ☀️🐾\n\n"
            f"Senang sekali melihat Tuan menyalakan komputer hari ini! Mimi siap setia menemani dan membantu Tuan berkarya seharian penuh! ✨"
        )
    else:
        return (
            f"Meoww! Selamat {waktu}, Tuan! *menggeliat bangun imut lalu kibas ekor manis* ☀️🐾\n\n"
            f"Senang sekali melihat Tuan menyalakan komputer hari ini! Mimi siap setia menemani dan membantu Tuan seharian penuh! ✨"
        )
