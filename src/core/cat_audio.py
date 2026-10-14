# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import os
import sys
import threading
import time

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOUNDS_DIR = os.path.join(PROJECT_ROOT, "assets", "sounds")

class CatAudioEngine:
    """
    Mesin Audio Kucing Alami:
    - Menggantikan suara robotik TTS dengan suara meong imut kucing asli
    - Non-blocking (asynchronous) dengan Windows winsound
    - Mendukung mode Mute/Unmute
    """
    def __init__(self, enabled=True):
        self._enabled = enabled
        self._on_start = None
        self._on_finish = None
        self._ensure_sounds()

    def _ensure_sounds(self):
        """Memastikan file suara kucing tersedia."""
        req_sounds = ["meow_talk.wav", "meow_happy.wav", "meow_chirp.wav", "meow_picked.wav", "meow_purr.wav"]
        missing = not os.path.exists(SOUNDS_DIR) or any(not os.path.exists(os.path.join(SOUNDS_DIR, s)) for s in req_sounds)
        if missing:
            try:
                try:
                    from src.utils import generate_cat_audio
                except ImportError:
                    from utils import generate_cat_audio
                generate_cat_audio.generate_all_sounds()
            except Exception as e:
                print(f"[CatAudio] Gagal membuat suara: {e}")

    def set_callbacks(self, on_start=None, on_finish=None):
        self._on_start = on_start
        self._on_finish = on_finish

    def _play_wav(self, filename: str, duration_sec: float = 0.4):
        if not self._enabled or not HAS_WINSOUND:
            return

        wav_path = os.path.join(SOUNDS_DIR, filename)
        if not os.path.exists(wav_path):
            return

        try:
            winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception:
            pass

        # Trigger callback animasi bicara secara halus
        def notify_cycle():
            if self._on_start:
                try:
                    self._on_start()
                except Exception:
                    pass
            time.sleep(duration_sec)
            if self._on_finish:
                try:
                    self._on_finish()
                except Exception:
                    pass

        t = threading.Thread(target=notify_cycle, daemon=True)
        t.start()

    def play_talk(self):
        """Meong manis saat kucing berbicara di balon dialog."""
        self._play_wav("meow_talk.wav", duration_sec=0.38)

    def play_happy(self):
        """Meong gembira saat dielus atau diberi makan ikan."""
        self._play_wav("meow_happy.wav", duration_sec=0.48)

    def play_chirp(self):
        """Meong ceria pendek saat mendarat atau bangun tidur."""
        self._play_wav("meow_chirp.wav", duration_sec=0.25)

    def play_picked(self):
        """Meong kaget imut saat diangkat dengan kursor."""
        self._play_wav("meow_picked.wav", duration_sec=0.32)

    def play_purr(self):
        """Mendengkur hangat saat santai."""
        self._play_wav("meow_purr.wav", duration_sec=0.65)

    def play_hiss(self):
        """Suara desis/peringatan imut saat ada kesalahan atau bentrok angka."""
        if os.path.exists(os.path.join(SOUNDS_DIR, "meow_hiss.wav")):
            self._play_wav("meow_hiss.wav", duration_sec=0.30)
        else:
            self.play_picked()

    def speak(self, text: str):
        """
        Kompatibilitas: menggantikan pembacaan teks TTS robotik
        dengan suara meong alami kucing yang imut!
        """
        self.play_talk()

    def toggle_mute(self) -> bool:
        self._enabled = not self._enabled
        return self._enabled

    def is_muted(self) -> bool:
        return not self._enabled

    def close(self):
        pass


# Alias kompatibilitas
SpeechEngine = CatAudioEngine
