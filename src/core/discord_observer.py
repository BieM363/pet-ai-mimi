# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import os
import sys
import re

try:
    from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
except ImportError:
    AudioUtilities = None
    IAudioMeterInformation = None

try:
    import psutil
except ImportError:
    psutil = None


def is_discord_process_running() -> bool:
    """Mengecek apakah proses discord.exe sedang aktif berjalan di Windows."""
    if psutil is None:
        return False
    try:
        for p in psutil.process_iter(['name']):
            if p.info['name'] and 'discord' in p.info['name'].lower():
                return True
    except Exception:
        pass
    return False


def parse_discord_window_title(title: str) -> dict:
    """
    Menganalisis judul jendela Discord (Desktop App maupun Browser Web):
    - Home / Teman: 'Discord'
    - DM / Obrolan Seseorang: '@Nama' atau 'Nama - Discord'
    - Server / Komunitas: '#channel | Nama Server - Discord'
    - Voice: mengandung 'Voice', 'RTC', '🔊', atau channel voice
    """
    clean_t = title.strip()
    res = {
        "type": "home",
        "raw_title": clean_t,
        "target": "",
        "channel": "",
        "is_voice": False
    }

    if not clean_t or clean_t.lower() == "discord":
        res["type"] = "home"
        return res

    # Bersihkan sufiks desktop '- Discord' atau prefiks web 'Discord |'
    t = clean_t
    if t.endswith(" - Discord"):
        t = t[:-10].strip()
    elif t.startswith("Discord |"):
        t = t[9:].strip()

    # Cek indikator Voice di judul
    voice_indicators = ["🔊", "voice", "vc", "rtc connected", "voice connected", "ruang suara"]
    if any(vi in clean_t.lower() for vi in voice_indicators):
        res["is_voice"] = True

    # 1. Format Server dengan Channel: #channel | Nama Server
    if " | " in t:
        parts = t.split(" | ")
        ch = parts[0].strip().lstrip("#")
        server = parts[-1].strip()
        res["type"] = "server"
        res["channel"] = ch
        res["target"] = server
        if any(vi in ch.lower() for vi in ["voice", "vc", "obrolan-suara", "nongkrong"]):
            res["is_voice"] = True
        return res

    # 2. Format DM / Direct Message seseorang (@Nama)
    if t.startswith("@"):
        target_name = t[1:].strip()
        res["type"] = "dm"
        res["target"] = target_name
        return res

    # 3. Format Channel tunggal (#channel)
    if t.startswith("#"):
        res["type"] = "server"
        res["channel"] = t[1:].strip()
        res["target"] = t[1:].strip()
        return res

    # 4. Filter tab non-chat bawaan Discord
    built_in_tabs = ["friends", "nitro", "shop", "explore", "settings", "direct messages"]
    if t.lower() in built_in_tabs:
        res["type"] = "home"
        return res

    # 5. Format Grup atau DM tanpa prefix @
    res["type"] = "dm" if not " " in t else "group"
    res["target"] = t
    return res


def check_discord_voice_active() -> tuple:
    """
    Mengecek apakah pengguna sedang berada di dalam Voice Channel Discord
    menggunakan kombinasi Windows Core Audio Session (pycaw) dan peak volume.
    Mengembalikan: (is_voice: bool, channel_hint: str)
    """
    if AudioUtilities is None:
        return (False, "")

    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if not session.Process:
                continue

            pname = session.Process.name().lower()
            if "discord" in pname:
                # State 1 = AudioSessionStateActive
                if session.State == 1:
                    # Discord membuka active audio session saat berada di Voice Channel / Call
                    try:
                        if IAudioMeterInformation:
                            meter = session._ctl.QueryInterface(IAudioMeterInformation)
                            peak = meter.GetPeakValue()
                            # Jika audio session active, pengguna terhubung ke Voice Channel
                            return (True, "Voice Channel Aktif")
                    except Exception:
                        return (True, "Voice Channel Aktif")
    except Exception:
        pass

    return (False, "")
