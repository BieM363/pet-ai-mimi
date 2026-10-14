import os
import sys
import re
import time
import ctypes
import threading
import subprocess
import webbrowser
import datetime
import urllib.parse
import urllib.request

# Integrasi library otomasi Windows
try:
    import pyautogui
    import pyperclip
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None
    pyperclip = None

try:
    import win32gui
    import win32con
    import win32process
    import win32service
except ImportError:
    win32gui = None
    win32con = None
    win32process = None
    win32service = None

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
NOTES_FILE = os.path.join(DATA_DIR, "catatan_mimi.txt")

# Thread timer untuk sleep komputer yang terjadwal
_ACTIVE_SLEEP_TIMER = None

# Daftar kata kunci judul browser populer di Windows
BROWSER_TITLE_KEYWORDS = [
    "microsoft edge", "edge", "google chrome", "chrome",
    "mozilla firefox", "firefox", "brave", "opera", "vivaldi"
]


# ==========================================
# 1. HELPER PARSING WAKTU & FORMATTER
# ==========================================
def parse_duration_seconds(text: str):
    """
    Menganalisis teks bahasa Indonesia untuk mencari durasi waktu (detik, menit, jam).
    Contoh: '30 menit', '1 jam', '45 detik', 'setengah jam', '1.5 jam'.
    Mengembalikan integer detik atau None jika tidak ditemukan.
    """
    low = text.lower()
    if "setengah jam" in low:
        return 1800

    match = re.search(r'(\d+(?:[\.,]\d+)?)\s*(detik|menit|jam|sec|min|m|h|hours?)', low)
    if match:
        val = float(match.group(1).replace(',', '.'))
        unit = match.group(2)
        if 'detik' in unit or 'sec' in unit:
            return int(val)
        elif 'menit' in unit or 'min' in unit or unit == 'm':
            return int(val * 60)
        elif 'jam' in unit or 'h' in unit:
            return int(val * 3600)
    return None


def format_duration_id(seconds: int) -> str:
    """Mengubah detik menjadi kalimat bahasa Indonesia yang rapi."""
    if seconds < 60:
        return f"{seconds} detik"
    hours = seconds // 3600
    remainder = seconds % 3600
    minutes = remainder // 60
    secs = remainder % 60
    parts = []
    if hours > 0:
        parts.append(f"{hours} jam")
    if minutes > 0:
        parts.append(f"{minutes} menit")
    if secs > 0:
        parts.append(f"{secs} detik")
    return " ".join(parts)


# ==========================================
# 2. SISTEM & COMMAND PROMPT (CMD)
# ==========================================
def shutdown_computer(delay_seconds: int = 0) -> str:
    """
    Mematikan komputer menggunakan perintah shutdown CMD Windows.
    Bisa langsung atau dengan timer waktu.
    """
    try:
        if delay_seconds > 0:
            # Gunakan utilitas shutdown bawaan Windows dengan timer
            ret = subprocess.run(
                ["shutdown", "/s", "/t", str(delay_seconds)],
                capture_output=True, text=True, shell=True
            )
            time_str = format_duration_id(delay_seconds)
            if ret.returncode == 0:
                return (
                    f"Siap Tuan! Mimi sudah menyetel timer shutdown di CMD ⏱️💤\n\n"
                    f"Komputer akan otomatis mati dalam **{time_str}** ({delay_seconds} detik).\n"
                    f"💡 *Catatan: Jika Tuan ingin membatalkannya, cukup katakan 'batalkan shutdown' ya!* 🐾"
                )
            else:
                return f"Gagal menyetel timer shutdown: {ret.stderr.strip() or ret.stdout.strip()}"
        else:
            # Matikan langsung
            subprocess.Popen(["shutdown", "/s", "/t", "0"], shell=True)
            return "Meow! Perintah shutdown telah dikirim ke CMD! Komputer akan segera mati sekarang... Sampai jumpa lagi, Tuan! 💤🐾"
    except Exception as e:
        return f"Gagal menjalankan perintah shutdown: {e}"


def cancel_shutdown() -> str:
    """Membatalkan proses shutdown yang sedang berjadwal (shutdown /a)."""
    global _ACTIVE_SLEEP_TIMER
    cancelled_sleep = False
    if _ACTIVE_SLEEP_TIMER and _ACTIVE_SLEEP_TIMER.is_alive():
        _ACTIVE_SLEEP_TIMER.cancel()
        _ACTIVE_SLEEP_TIMER = None
        cancelled_sleep = True

    try:
        ret = subprocess.run(["shutdown", "/a"], capture_output=True, text=True, shell=True)
        if ret.returncode == 0:
            return "Beres Tuan! Rencana shutdown berhasil dibatalkan di CMD! Komputer tetap menyala dengan aman ya! ✨🐾"
        else:
            err = ret.stderr.strip()
            if "1116" in err or "no shutdown" in err.lower() or "tidak ada" in err.lower():
                if cancelled_sleep:
                    return "Beres Tuan! Timer sleep komputer berhasil dibatalkan! Komputer tetap aktif! ✨"
                return "Meow! Saat ini tidak ada timer shutdown yang aktif di sistem, Tuan! Komputer aman terkendali! ✨"
            return f"Status pembatalan: {err}"
    except Exception as e:
        return f"Gagal membatalkan shutdown: {e}"


def _execute_sleep_now():
    """Memicu mode Sleep Windows secara aman tanpa bentrok dengan hibernate."""
    try:
        ps_cmd = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "[System.Windows.Forms.Application]::SetSuspendState([System.Windows.Forms.PowerState]::Suspend, $false, $false)"
        )
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_cmd], shell=True, creationflags=0x08000000) # CREATE_NO_WINDOW
    except Exception:
        # Fallback rundll32
        try:
            subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], shell=True)
        except Exception:
            pass


def sleep_computer(delay_seconds: int = 0) -> str:
    """Menidurkan komputer (Sleep / Suspend) langsung atau terjadwal."""
    global _ACTIVE_SLEEP_TIMER
    if delay_seconds > 0:
        time_str = format_duration_id(delay_seconds)
        if _ACTIVE_SLEEP_TIMER and _ACTIVE_SLEEP_TIMER.is_alive():
            _ACTIVE_SLEEP_TIMER.cancel()

        _ACTIVE_SLEEP_TIMER = threading.Timer(delay_seconds, _execute_sleep_now)
        _ACTIVE_SLEEP_TIMER.daemon = True
        _ACTIVE_SLEEP_TIMER.start()

        return (
            f"Siap Tuan! Mimi sudah menyetel timer sleep: Komputer akan tidur dalam **{time_str}**! 💤🌙\n"
            f"(Katakan 'batalkan shutdown' jika ingin membatalkan timer ini!)"
        )
    else:
        # Eksekusi dengan jeda 1 detik agar suara/dialog sempat muncul
        threading.Timer(1.2, _execute_sleep_now).start()
        return "Meow! Menidurkan komputer sekarang... Selamat beristirahat Tuan! Zzz... 💤🌙"


def restart_computer(delay_seconds: int = 0) -> str:
    """Merestart komputer Windows (shutdown /r)."""
    try:
        if delay_seconds > 0:
            ret = subprocess.run(["shutdown", "/r", "/t", str(delay_seconds)], capture_output=True, text=True, shell=True)
            time_str = format_duration_id(delay_seconds)
            if ret.returncode == 0:
                return f"Siap Tuan! Komputer akan restart dalam **{time_str}** ({delay_seconds} detik)! 🔄"
            return f"Gagal restart: {ret.stderr.strip()}"
        else:
            subprocess.Popen(["shutdown", "/r", "/t", "0"], shell=True)
            return "Meow! Komputer sedang bersiap untuk restart sekarang... Sampai jumpa sebentar lagi Tuan! 🔄🐾"
    except Exception as e:
        return f"Gagal menjalankan restart: {e}"


def lock_computer() -> str:
    """Mengunci layar desktop Windows (Lock Workstation)."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Layar komputer sudah Mimi kunci (Lock Screen), Tuan! Privasi dan data Tuan tetap aman! 🔒✨"
    except Exception as e:
        return f"Gagal mengunci komputer: {e}"


def open_cmd_terminal() -> str:
    """Membuka jendela Command Prompt (CMD) interaktif."""
    try:
        subprocess.Popen("start cmd.exe", shell=True)
        return "Jendela Command Prompt (CMD) sudah Mimi buka, Tuan! Silakan mengetik perintah di sana! 💻✨"
    except Exception as e:
        return f"Gagal membuka CMD: {e}"


def run_cmd_command(command: str) -> str:
    """
    Menjalankan perintah CMD Windows langsung dari Mimi dan mengembalikan outputnya.
    """
    clean_cmd = command.strip()
    if not clean_cmd:
        return "Tuan belum menyebutkan perintah CMD apa yang ingin dijalankan. Contoh: 'cmd: ipconfig'"

    # Cek perintah terlarang / berbahaya
    low = clean_cmd.lower()
    if any(danger in low for danger in ["del /f /s /q c:", "format c:", "rd /s /q c:"]):
        return "⚠️ Meow! Perintah ini sangat berbahaya dan bisa merusak sistem Tuan, Mimi tolak ya demi keselamatan!"

    try:
        # Jalankan perintah dengan batas waktu 15 detik
        proc = subprocess.run(
            clean_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()

        result_text = out if out else err
        if not result_text:
            result_text = "(Perintah selesai dijalankan tanpa output)"

        # Pangkas jika output terlalu panjang untuk balon dialog
        if len(result_text) > 480:
            result_text = result_text[:480] + "\n... [output dipangkas agar rapi]"

        return f"Meow! Hasil perintah CMD (`{clean_cmd}`):\n\n```\n{result_text}\n```\n🐾 Selesai dieksekusi, Tuan!"
    except subprocess.TimeoutExpired:
        return f"Meow! Perintah CMD `{clean_cmd}` memakan waktu terlalu lama (>15 detik). Mimi hentikan prosesnya ya!"
    except Exception as e:
        return f"Gagal mengeksekusi perintah CMD: {e}"


# ==========================================
# 3. INTERAKSI & OTOMASI BROWSER WINDOWS
# ==========================================
def find_open_browser_window():
    """
    Mendeteksi jendela browser yang sedang terbuka di desktop pengguna
    (Microsoft Edge, Chrome, Firefox, Brave, Opera, Vivaldi).
    Mengembalikan (hwnd, title) atau None.
    """
    if not win32gui:
        return None

    # Pastikan thread terhubung ke Desktop pengguna aktif
    if win32service:
        try:
            desk = win32service.OpenInputDesktop(0, False, win32con.MAXIMUM_ALLOWED)
            desk.SetThreadDesktop()
        except Exception:
            pass

    found_window = None

    def enum_cb(hwnd, _):
        nonlocal found_window
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                low = title.lower()
                for bkw in BROWSER_TITLE_KEYWORDS:
                    if bkw in low:
                        found_window = (hwnd, title)
                        return False # Berhenti jika sudah ketemu
        return True

    try:
        win32gui.EnumWindows(enum_cb, None)
    except Exception:
        pass

    return found_window


def focus_window(hwnd) -> bool:
    """Membawa jendela tertentu ke bagian paling depan layar (Foreground)."""
    if not win32gui or not hwnd:
        return False

    try:
        # Jika diminimalkan (minimized/iconic), pulihkan ukurannya
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

        # Bypass Windows Focus Lock menggunakan teknik AttachThreadInput
        user32 = ctypes.windll.user32
        fore_hwnd = user32.GetForegroundWindow()
        fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, 0)
        app_thread = user32.GetCurrentThreadId()

        if fore_thread != app_thread:
            user32.AttachThreadInput(fore_thread, app_thread, True)
            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
            user32.AttachThreadInput(fore_thread, app_thread, False)
        else:
            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)

        return True
    except Exception:
        try:
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            return False


def type_in_active_browser(text: str, press_enter: bool = True) -> str:
    """
    Mengetikkan teks secara otomatis ke jendela browser yang sedang aktif
    menggunakan simulasi keyboard dan clipboard Unicode.
    """
    browser_info = find_open_browser_window()
    if browser_info:
        hwnd, title = browser_info
        focus_window(hwnd)
        time.sleep(0.2)

    if pyautogui and pyperclip:
        try:
            # Salin ke clipboard lalu paste (Ctrl+V) agar mendukung karakter Unicode, spasi, simbol sempurna
            pyperclip.copy(text)
            time.sleep(0.08)
            pyautogui.hotkey('ctrl', 'v')
            if press_enter:
                time.sleep(0.12)
                pyautogui.press('enter')
            return f"Beres Tuan! Mimi sudah mengetikkan \"{text}\" ke dalam browser! ✍️🌐"
        except Exception as e:
            return f"Gagal mengetik di browser: {e}"
    else:
        return "Library pyautogui/pyperclip belum tersedia untuk pengetikan otomatis."


def browser_search(query: str, is_image: bool = False) -> str:
    """
    Membuka atau menggunakan browser yang sudah ada untuk mencari kueri di Google atau Google Images.
    Mimi akan memfokuskan browser ke depan dan membuka halaman pencarian.
    """
    clean_query = query.strip()
    if not clean_query:
        return "Tuan belum menyebutkan apa yang ingin dicari nih. Coba: 'Mimi cari saham BBRI hari ini'"

    # Buat URL target
    encoded = urllib.parse.quote(clean_query)
    if is_image:
        # Google Image Search modern
        url = f"https://www.google.com/search?udm=2&q={encoded}"
    else:
        # Google Search umum
        url = f"https://www.google.com/search?q={encoded}"

    # Cari apakah browser sudah terbuka
    browser_win = find_open_browser_window()

    try:
        # Buka URL di browser (jika browser sudah ada, Windows membuka tab baru di browser tersebut)
        webbrowser.open(url)

        # Beri jeda singkat lalu fokuskan jendela browser ke depan layar
        time.sleep(0.3)
        if browser_win:
            focus_window(browser_win[0])

        if is_image:
            return (
                f"Nyaa~ Beres Tuan! Mimi sudah membuka browser dan mencari gambar **\"{clean_query}\"** di Google Images! 🖼️🏎️\n\n"
                f"Silakan dilihat gambarnya di layar browser ya!"
            )
        else:
            return (
                f"Siap Tuan! Mimi sudah membuka browser dan mencarikan info **\"{clean_query}\"** di Google! 🔍📈\n\n"
                f"Hasil pencarian langsung tampil di browser Tuan!"
            )
    except Exception as e:
        return f"Gagal melakukan pencarian di browser: {e}"


# ==========================================
# 4. MANAJEMEN BUKU CATATAN (NOTEPAD)
# ==========================================
def ensure_notes_file():
    """Membuat file catatan default jika belum ada."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            f.write("# === CATATAN MIMI & TUAN ===\n")
            f.write(f"# Dibuat pada: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")


def open_notes():
    """Membuka file catatan dengan aplikasi Notepad bawaan Windows."""
    ensure_notes_file()
    try:
        subprocess.Popen(["notepad.exe", NOTES_FILE])
        return "Buku catatan sudah Mimi buka di Notepad, Tuan! Silakan dilihat atau diedit ya. 📝"
    except Exception as e:
        return f"Gagal membuka Notepad: {e}"


def add_note(content: str):
    """Menambahkan catatan baru berstempel waktu ke file catatan."""
    ensure_notes_file()
    clean_text = content.strip()
    if not clean_text:
        return "Tuan belum menyebutkan apa yang ingin dicatat nih. Coba: 'Mimi catat: ...'"

    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    entry = f"[{timestamp}] {clean_text}\n"
    try:
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        return f"Nyaa~ Beres Tuan! Catatan baru sudah Mimi tulis:\n\"{clean_text}\" 🐾"
    except Exception as e:
        return f"Gagal menambahkan catatan: {e}"


def read_notes(max_lines=5):
    """Membaca beberapa catatan terakhir."""
    ensure_notes_file()
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith("#")]

        if not lines:
            return "Catatan Tuan masih kosong melompong nih! Mau Mimi catatkan sesuatu? 🐾"

        recent = lines[-max_lines:]
        summary = "\n".join([f"• {l}" for l in recent])
        return f"Berikut beberapa catatan terakhir Tuan di Notepad:\n{summary}\n\n(Katakan 'buka note' jika ingin membuka Notepad lengkap ya!)"
    except Exception as e:
        return f"Gagal membaca catatan: {e}"


def clear_notes():
    """Mengosongkan isi file catatan."""
    ensure_notes_file()
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            f.write("# === CATATAN MIMI & TUAN ===\n")
            f.write(f"# Dikosongkan pada: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        return "Beres Tuan! Semua catatan lama sudah Mimi bersihkan. Kertasnya kini bersih kembali! ✨"
    except Exception as e:
        return f"Gagal mengosongkan catatan: {e}"


# ==========================================
# 5. INTEGRASI BROWSER UMUM & ANTIGRAVITY
# ==========================================
def open_browser(target=None):
    """Membuka browser default ke Google, YouTube, atau URL tertentu."""
    try:
        if not target or target.strip() == "":
            webbrowser.open("https://www.google.com")
            # Coba fokuskan browser jika sudah terbuka
            time.sleep(0.3)
            bwin = find_open_browser_window()
            if bwin:
                focus_window(bwin[0])
            return "Browser sudah Mimi buka, Tuan! Mau berselancar ke mana kita? 🌐"

        target = target.strip()
        low = target.lower()
        if low in ["youtube", "yt"]:
            return open_youtube()
        elif low.startswith("youtube ") or low.startswith("yt "):
            yt_q = target.split(" ", 1)[1].strip()
            return open_youtube(yt_q)
        elif low in ["google"]:
            webbrowser.open("https://www.google.com")
            return "Google sudah Mimi buka di browser, Tuan! 🔍"
        elif low in ["github"]:
            webbrowser.open("https://www.github.com")
            return "GitHub sudah Mimi buka! Semangat codingnya Tuan! 💻"
        elif target.startswith("http://") or target.startswith("https://"):
            webbrowser.open(target)
            return f"Siap Tuan, tautan {target} sudah Mimi luncurkan di browser! 🚀"
        else:
            # Gunakan fungsi browser search
            return browser_search(target, is_image=False)
    except Exception as e:
        return f"Gagal membuka browser: {e}"


def smart_browser_search(query: str) -> str:
    """
    Pencarian otomatis cerdas:
    - Jika kosong: Buka browser ke Google/beranda.
    - Jika mengandung kata gambar/foto: Langsung cari di Google Images.
    - Jika mengandung kata YouTube / putar lagu: Alihkan ke YouTube.
    - Jika berupa link URL: Langsung buka situs web tersebut.
    - Selain itu: Cari info di Google Search.
    """
    clean_query = query.strip()
    if not clean_query:
        return open_browser()

    low = clean_query.lower()

    # 1. Cek Permintaan YouTube
    if any(k in low for k in ["youtube", "putar lagu", "putar video", "setel lagu", "setel video", "play lagu", "play video"]):
        yt_term = re.sub(r'^(?:buka\s+youtube|cari\s+di\s+youtube|putar\s+lagu|putar\s+video|setel\s+lagu|setel\s+video|play\s+lagu|play\s+video|youtube)\s*[:\-]?\s*', '', clean_query, flags=re.IGNORECASE).strip()
        if not yt_term:
            return explore_youtube()
        if any(w in low for w in ["putar", "play", "setel", "mainkan"]):
            return play_youtube(yt_term)
        return search_youtube(yt_term)

    # 2. Cek Pencarian Gambar Google Images
    if any(k in low for k in ["gambar", "foto", "image", "wallpaper"]):
        img_term = re.sub(r'^(?:cari\s+gambar|carikan\s+gambar|cari\s+foto|carikan\s+foto|search\s+image|lihat\s+gambar|gambar)\s*[:\-]?\s*', '', clean_query, flags=re.IGNORECASE).strip()
        if not img_term:
            img_term = clean_query
        return browser_search(img_term, is_image=True)

    # 3. Cek apakah berupa URL langsung
    if low.startswith("http://") or low.startswith("https://") or low.startswith("www.") or any(low.endswith(tld) for tld in [".com", ".net", ".org", ".id", ".io", ".co.id", ".edu", ".gov"]):
        url = clean_query if clean_query.startswith("http://") or clean_query.startswith("https://") else f"https://{clean_query}"
        try:
            webbrowser.open(url)
            time.sleep(0.3)
            bwin = find_open_browser_window()
            if bwin:
                focus_window(bwin[0])
            return f"Situs web **{clean_query}** sudah Mimi luncurkan di browser, Tuan! 🚀🌐"
        except Exception as e:
            return f"Gagal membuka URL: {e}"

    # 4. Pencarian Google Umum
    return browser_search(clean_query, is_image=False)


def explore_youtube(section: str = "home") -> str:
    """
    Membuka YouTube untuk dijelajahi (Beranda atau Trending).
    """
    sec = (section or "home").lower().strip()
    if sec in ["trending", "viral", "populer"]:
        url = "https://www.youtube.com/feed/trending"
        desc = "YouTube Trending (Video Populer Hari Ini) 🔥🎬"
    elif sec in ["explore", "eksplor", "jelajah"]:
        url = "https://www.youtube.com/feed/explore"
        desc = "Eksplorasi YouTube 🌐🎬"
    else:
        url = "https://www.youtube.com"
        desc = "Beranda YouTube 🎬🍿"

    try:
        webbrowser.open(url)
        time.sleep(0.3)
        bwin = find_open_browser_window()
        if bwin:
            focus_window(bwin[0])
        return (
            f"Nyaa~ Beres Tuan! Mimi sudah membuka **{desc}** di browser!\n\n"
            f"Selamat berselancar dan menemukan video-video seru ya! ✨🐾"
        )
    except Exception as e:
        return f"Gagal menjelajah YouTube: {e}"


def search_youtube(query: str) -> str:
    """
    Mencari video di YouTube dan menampilkan daftar hasil pencarian di browser,
    sehingga pengguna bisa bebas melihat semua pilihan video yang ada.
    """
    clean_query = query.strip()
    clean_query = re.sub(r'^(?:cari\s+di\s+youtube|search\s+youtube|searching\s+youtube|carikan\s+di\s+youtube|cari\s+video|search)\s*[:\-]?\s*', '', clean_query, flags=re.IGNORECASE).strip()
    clean_query = re.sub(r'\s+di\s+youtube\s*$', '', clean_query, flags=re.IGNORECASE).strip()

    if not clean_query:
        return explore_youtube()

    encoded = urllib.parse.quote(clean_query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"

    try:
        webbrowser.open(search_url)
        time.sleep(0.3)
        bwin = find_open_browser_window()
        if bwin:
            focus_window(bwin[0])
        return (
            f"Siap Tuan! Mimi sudah membukakan hasil pencarian YouTube untuk:\n"
            f"🔍 **\"{clean_query}\"**\n\n"
            f"Daftar videonya langsung tampil di browser, silakan pilih yang ingin ditonton ya! 🎬🍿"
        )
    except Exception as e:
        return f"Gagal mencari di YouTube: {e}"


def play_youtube(query_or_url: str) -> str:
    """
    Memutar video atau musik di YouTube secara instan.
    Mimi akan mengekstrak video ID terbaik dan membukanya dengan autoplay.
    """
    target = query_or_url.strip()
    target = re.sub(r'^(?:putar\s+lagu|putar\s+video|setel\s+lagu|setel\s+video|play\s+lagu|play\s+video|mainkan\s+lagu|mainkan\s+video|tonton\s+video|tonton|putar|play|setel|mainkan)\s*[:\-]?\s*', '', target, flags=re.IGNORECASE).strip()
    target = re.sub(r'\s+di\s+youtube\s*$', '', target, flags=re.IGNORECASE).strip()

    if not target:
        return explore_youtube()

    # Cek apakah target sudah merupakan URL YouTube langsung
    if "youtube.com/watch" in target or "youtu.be/" in target:
        try:
            webbrowser.open(target)
            time.sleep(0.3)
            bwin = find_open_browser_window()
            if bwin:
                focus_window(bwin[0])
            return "Nyaa~ Tautan YouTube langsung Mimi putarkan di layar browser! Selamat menikmati ya Tuan! 🍿🎶"
        except Exception as e:
            return f"Gagal membuka tautan video: {e}"

    encoded = urllib.parse.quote(target)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"
    target_url = search_url
    video_title = None
    is_direct_play = False

    try:
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            
            # Cari video ID pertama dari data YouTube
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if not video_ids:
                video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)

            if video_ids:
                first_id = video_ids[0]
                target_url = f"https://www.youtube.com/watch?v={first_id}&autoplay=1"
                is_direct_play = True

                # Ekstrak judul video jika ada
                titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"', html)
                if titles:
                    video_title = titles[0]
    except Exception:
        target_url = search_url

    try:
        webbrowser.open(target_url)
        time.sleep(0.3)
        bwin = find_open_browser_window()
        if bwin:
            focus_window(bwin[0])

        display_name = video_title if video_title else target
        if is_direct_play:
            return (
                f"Nyaa~ Beres Tuan! Mimi sudah memutarkan video YouTube untukmu:\n"
                f"🎬 **\"{display_name}\"** 🎶\n\n"
                f"Videonya langsung berputar di browser Tuan! Selamat bersantai dan menonton! 🍿✨"
            )
        else:
            return (
                f"Siap Tuan! Mimi sudah membukakan hasil pencarian video **\"{target}\"** di YouTube! "
                f"Silakan langsung klik untuk memutarnya ya! 🎬🍿"
            )
    except Exception as e:
        return f"Gagal memutar video YouTube: {e}"


def open_youtube(query: str = None) -> str:
    """Membuka YouTube di browser (kompatibilitas mundur)."""
    if not query or query.strip() == "" or query.strip().upper() == "HOME":
        return explore_youtube()
    return play_youtube(query)


def open_antigravity():
    """Membuka workspace Antigravity IDE atau folder project saat ini."""
    project_dir = PROJECT_ROOT
    try:
        ret = subprocess.run(["where", "antigravity"], capture_output=True, text=True)
        if ret.returncode == 0:
            subprocess.Popen(["antigravity", project_dir])
            return "Antigravity IDE untuk project ini sudah Mimi buka, Tuan! Selamat ngoding! 🚀"

        ret_code = subprocess.run(["where", "code"], capture_output=True, text=True)
        if ret_code.returncode == 0:
            subprocess.Popen(["code", project_dir], shell=True)
            return "Editor project sudah Mimi buka, Tuan! Selamat berkarya! 💻"

        os.startfile(project_dir)
        return f"Folder project Antigravity sudah Mimi buka di File Explorer, Tuan! 📂"
    except Exception as e:
        try:
            os.startfile(project_dir)
            return "Folder project sudah Mimi buka di File Explorer! 📂"
        except Exception as e2:
            return f"Gagal membuka Antigravity/Folder: {e2}"
