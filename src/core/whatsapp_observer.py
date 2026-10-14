import os
import sys
import re
import time
import ctypes
import ctypes.wintypes
from typing import Optional, Dict

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

def get_window_text(hwnd) -> str:
    """Mengambil judul window secara aman via Win32."""
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value.strip()

def get_process_name_from_hwnd(hwnd) -> str:
    """Mengambil nama file exe dari handle jendela."""
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""
    hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not hProcess:
        return ""
    buf = ctypes.create_unicode_buffer(1024)
    size = ctypes.wintypes.DWORD(1024)
    exe_name = ""
    try:
        if kernel32.QueryFullProcessImageNameW(hProcess, 0, buf, ctypes.byref(size)):
            exe_name = os.path.basename(buf.value).lower()
    finally:
        kernel32.CloseHandle(hProcess)
    return exe_name

def parse_whatsapp_title(title: str) -> Optional[Dict]:
    """
    Menganalisis judul jendela / tab WhatsApp di Google Chrome:
    - '(1) WhatsApp - Google Chrome'
    - '(2) Kevin - WhatsApp - Google Chrome'
    - '(1) Grup Coding - WhatsApp'
    - '(1) WhatsApp'
    - 'WhatsApp (3) - Google Chrome'
    Mengembalikan dict: {'count': int, 'sender': str, 'raw_title': str}
    """
    clean_t = title.strip()
    if "whatsapp" not in clean_t.lower():
        return None

    # Pola 1: (N) [Nama Pengirim / Grup] - WhatsApp - Google Chrome
    m1 = re.search(r'^\((\d+)\)\s*(.*?)(?:\s*-\s*WhatsApp)?(?:\s*-\s*Google Chrome)?$', clean_t, re.IGNORECASE)
    if m1:
        count = int(m1.group(1))
        sender = m1.group(2).strip()
        # Bersihkan jika nama pengirim tertangkap kata 'WhatsApp' atau 'Google Chrome'
        if sender.lower() in ["whatsapp", "google chrome", "chrome", ""]:
            sender = ""
        else:
            # Hapus trailing dashes
            sender = re.sub(r'[\-\|\s]+$', '', sender).strip()
        return {"count": count, "sender": sender, "raw_title": clean_t}

    # Pola 2: WhatsApp (N)
    m2 = re.search(r'whatsapp\s*\((\d+)\)', clean_t, re.IGNORECASE)
    if m2:
        count = int(m2.group(1))
        return {"count": count, "sender": "", "raw_title": clean_t}

    # Pola 3: (N) di awal judul tanpa kata WhatsApp di tengah (jika exe adalah Chrome dan URL WhatsApp)
    m3 = re.search(r'^\((\d+)\)\s*(.+?)(?:\s*-\s*Google Chrome)?$', clean_t, re.IGNORECASE)
    if m3 and "whatsapp" in clean_t.lower():
        count = int(m3.group(1))
        sender = m3.group(2).strip()
        if sender.lower() in ["whatsapp", "google chrome", ""]:
            sender = ""
        return {"count": count, "sender": sender, "raw_title": clean_t}

    return None

def extract_sender_via_uiautomation(hwnd) -> str:
    """
    Mengekstrak nama pengirim pesan unread dari UI Automation pohon elemen WhatsApp Web di Chrome.
    Digunakan saat judul tab hanya menampilkan '(1) WhatsApp' tanpa nama pengirim di judul.
    """
    try:
        import comtypes.client
        UIAutomationCore = comtypes.client.GetModule("UIAutomationCore.dll")
        uia = comtypes.client.CreateObject(UIAutomationCore.CUIAutomation, interface=UIAutomationCore.IUIAutomation)
        root = uia.ElementFromHandle(hwnd)
        if not root:
            return ""

        # Cari elemen-elemen teks / listitem di dalam halaman
        cond_true = uia.CreateTrueCondition()
        elems = root.FindAll(UIAutomationCore.TreeScope_Descendants, cond_true)
        if not elems:
            return ""

        count = elems.Length
        # Scan elemen untuk mencari atribut aria-label atau nama unread chat
        for i in range(min(count, 150)):
            try:
                el = elems.GetElement(i)
                name = el.CurrentName
                if not name:
                    continue

                # Pola aria-label WhatsApp Web:
                # - 'Chat with Kevin, 1 unread message'
                # - 'Obrolan dengan Kevin, 1 pesan belum dibaca'
                # - 'Obrolan dengan Kevin, 2 pesan belum dibaca'
                # - 'Kevin, 1 unread message'
                low_name = name.lower()
                if any(k in low_name for k in ["unread message", "pesan belum dibaca", "unread", "belum dibaca"]):
                    # Ekstrak nama kontak
                    match = re.search(r'(?:obrolan\s+dengan|chat\s+with|obrolan|chat)?\s*([A-Za-z0-9_\s\.\+]+?)(?:,|\s+-\s+|\s+pesan|\s+unread)', name, re.IGNORECASE)
                    if match:
                        found_sender = match.group(1).strip()
                        if found_sender and found_sender.lower() not in ["obrolan", "chat", "whatsapp", "pesan"]:
                            return found_sender
            except Exception:
                continue
    except Exception:
        pass
    return ""


def scan_whatsapp_status() -> Optional[Dict]:
    """
    Memindai semua jendela Google Chrome dan WhatsApp di Windows
    untuk memeriksa apakah ada pesan WhatsApp baru yang belum dibaca.
    Mengembalikan dict jika ditemukan jendela WhatsApp:
    {
        "has_unread": bool,
        "count": int,
        "sender": str,
        "hwnd": int,
        "raw_title": str
    }
    """
    whatsapp_info = None

    # Handler callback untuk EnumWindows
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

    def enum_cb(hwnd, lparam):
        nonlocal whatsapp_info
        if not user32.IsWindow(hwnd):
            return True

        title = get_window_text(hwnd)
        if not title:
            return True

        exe = get_process_name_from_hwnd(hwnd)
        # Fokus utama: Google Chrome (chrome.exe) dan WhatsApp Desktop (whatsapp.exe)
        if exe not in ["chrome.exe", "whatsapp.exe", "msedge.exe", "brave.exe"]:
            return True

        parsed = parse_whatsapp_title(title)
        if parsed:
            count = parsed.get("count", 0)
            sender = parsed.get("sender", "")

            # Jika judul hanya '(1) WhatsApp' tanpa nama pengirim, coba intip lewat UIAutomation
            if count > 0 and not sender:
                uia_sender = extract_sender_via_uiautomation(hwnd)
                if uia_sender:
                    sender = uia_sender

            whatsapp_info = {
                "has_unread": count > 0,
                "count": count,
                "sender": sender or "Kontak WhatsApp",
                "hwnd": hwnd,
                "raw_title": title
            }
            # Jika ditemukan unread, langsung prioritaskan jendela ini
            if count > 0:
                return False

        return True

    try:
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception:
        pass

    return whatsapp_info


from PyQt5.QtCore import QThread, pyqtSignal

class WhatsAppObserverThread(QThread):
    """
    QThread background worker yang memantau pesan masuk WhatsApp di Google Chrome
    secara real-time dan bebas lag.
    """
    whatsapp_notification = pyqtSignal(str, int)  # (sender_name, unread_count)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._last_count = 0
        self._last_sender = ""
        self._last_notify_time = 0.0

    def run(self):
        while self._running:
            try:
                info = scan_whatsapp_status()
                if info:
                    count = info.get("count", 0)
                    sender = info.get("sender", "Kontak WhatsApp")
                    now = time.time()

                    # Kondisi pemicu notifikasi baru:
                    # 1. Jumlah pesan bertambah (pesan baru masuk), ATAU
                    # 2. Ada pesan unread dan nama pengirimnya berganti orang lain
                    is_new_message = (count > self._last_count) or (count > 0 and sender != self._last_sender)
                    cooldown_ok = (now - self._last_notify_time) > 4.5

                    if is_new_message and cooldown_ok and count > 0:
                        self._last_count = count
                        self._last_sender = sender
                        self._last_notify_time = now
                        self.whatsapp_notification.emit(sender, count)
                    elif count == 0:
                        # Pengguna sudah membaca semua pesan (unread count menjadi 0)
                        self._last_count = 0
                        self._last_sender = ""
                else:
                    # WhatsApp tidak sedang dibuka
                    self._last_count = 0
                    self._last_sender = ""

            except Exception as e:
                pass

            # Polling santai setiap 1.8 detik
            time.sleep(1.8)

    def stop(self):
        self._running = False
        self.wait(1000)
