import os
import sys
import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# Judul standar Spotify saat idle/jeda (tidak memutar lagu)
NON_PLAYING_TITLES = {
    "", "spotify", "spotify free", "spotify premium",
    "default ime", "msctfime ui", "gdi+ window (spotify.exe)"
}


def _ensure_desktop_access():
    """Memastikan thread terhubung ke desktop interaktif Windows (Default)."""
    try:
        hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


def is_spotify_process_running() -> bool:
    """Mengecek apakah proses spotify.exe sedang berjalan di Windows."""
    try:
        import win32process
        # Cek cepat melalui snapshot process
        h_snap = kernel32.CreateToolhelp32Snapshot(0x00000002, 0) # TH32CS_SNAPPROCESS
        if h_snap == -1:
            return False

        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ('dwSize', ctypes.wintypes.DWORD),
                ('cntUsage', ctypes.wintypes.DWORD),
                ('th32ProcessID', ctypes.wintypes.DWORD),
                ('th32DefaultHeapID', ctypes.c_void_p),
                ('th32ModuleID', ctypes.wintypes.DWORD),
                ('cntThreads', ctypes.wintypes.DWORD),
                ('th32ParentProcessID', ctypes.wintypes.DWORD),
                ('pcPriClassBase', ctypes.c_long),
                ('dwFlags', ctypes.wintypes.DWORD),
                ('szExeFile', ctypes.c_wchar * 260)
            ]

        pe32 = PROCESSENTRY32()
        pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)
        has_proc = kernel32.Process32FirstW(h_snap, ctypes.byref(pe32))
        found = False
        while has_proc:
            if pe32.szExeFile.lower() == "spotify.exe":
                found = True
                break
            has_proc = kernel32.Process32NextW(h_snap, ctypes.byref(pe32))
        kernel32.CloseHandle(h_snap)
        return found
    except Exception:
        return False


def get_spotify_playback() -> dict:
    """
    Mengambil status pemutaran lagu Spotify di Windows.
    Mengembalikan dict:
    {
        "is_running": bool,
        "is_playing": bool,
        "track": str
    }
    """
    result = {
        "is_running": False,
        "is_playing": False,
        "track": ""
    }

    _ensure_desktop_access()

    try:
        import win32gui
        import win32process

        active_track = None
        spotify_found = False

        def enum_win_proc(hwnd, _):
            nonlocal active_track, spotify_found
            if not win32gui.IsWindow(hwnd):
                return True

            cls = win32gui.GetClassName(hwnd)
            # Window utama Spotify menggunakan Chrome_WidgetWin_0 atau Chrome_WidgetWin_1
            if "Chrome_WidgetWin" in cls:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                if hProcess:
                    buf = ctypes.create_unicode_buffer(1024)
                    size = ctypes.wintypes.DWORD(1024)
                    if kernel32.QueryFullProcessImageNameW(hProcess, 0, buf, ctypes.byref(size)):
                        exe = os.path.basename(buf.value).lower()
                        if exe == "spotify.exe":
                            spotify_found = True
                            title = win32gui.GetWindowText(hwnd).strip()
                            # Jika Spotify sedang memutar lagu, title berisi "[Artist] - [Title]"
                            if title and title.lower() not in NON_PLAYING_TITLES:
                                active_track = title
                    kernel32.CloseHandle(hProcess)
            return True

        win32gui.EnumWindows(enum_win_proc, None)

        result["is_running"] = spotify_found
        if active_track:
            result["is_playing"] = True
            result["track"] = active_track

    except Exception as e:
        # Fallback error handling
        pass

    return result


if __name__ == "__main__":
    status = get_spotify_playback()
    print("Spotify Status:", status)
