import re
import queue
import threading
import time

class SpeechEngine:
    """
    Engine TTS (Text-to-Speech) offline berbasis pyttsx3 dengan arsitektur non-blocking.
    Dijalankan di thread terpisah agar UI PyQt5 tetap mulus tanpa lag.
    """
    def __init__(self, rate: int = 175, enabled: bool = True):
        self.rate = rate
        self.enabled = enabled
        self._queue = queue.Queue()
        self._running = True
        self._is_speaking = False
        self._on_start_callback = None
        self._on_finish_callback = None
        
        # Inisialisasi thread pekerja
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()

    def set_callbacks(self, on_start=None, on_finish=None):
        """Callback ketika mulai bicara dan selesai bicara."""
        self._on_start_callback = on_start
        self._on_finish_callback = on_finish

    def toggle_mute(self) -> bool:
        """Mengaktifkan / menonaktifkan suara."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop()
        return self.enabled

    def is_muted(self) -> bool:
        return not self.enabled

    def clean_text_for_speech(self, text: str) -> str:
        """
        Membersihkan markdown dan deskripsi aksi dalam tanda bintang (misal: *mengibaskan ekor*),
        tetapi mempertahankan suara ekspresi kucing seperti *Meow!*, *Purrrr~*, atau *Nyaa!*.
        """
        if not text:
            return ""
        try:
            from src.ui.markdown_helper import clean_text_for_speech as helper_clean
            return helper_clean(text)
        except Exception:
            pass

        clean = re.sub(r'https?://\S+', '', text)
        clean = re.sub(r'\*\*\*([^\*]+)\*\*\*', r'\1', clean)
        clean = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean)

        def filter_action(match):
            content = match.group(1).strip()
            low = content.lower()
            cat_sounds = ['meow!', 'meow', 'purrrr~', 'purrrr', 'purr~', 'purr', 'nyaa!', 'nyaa', 'nya', 'mrrp', 'hehe']
            for cs in cat_sounds:
                if cs in low or low in cs:
                    return content
            return ""

        clean = re.sub(r'\*([^*]+)\*', filter_action, clean)
        clean = re.sub(r'[#`~><\*\^\$]', ' ', clean)
        clean = re.sub(r'[^\x00-\x7F\u00A0-\u024F\u1E00-\u1EFF\s\.,!\?:;\-\'\"]+', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def speak(self, text: str):
        """Menambahkan teks ke antrean suara TTS."""
        clean_text = self.clean_text_for_speech(text)
        if not clean_text:
            clean_text = text

        if not self.enabled:
            # Jika suara dimute, panggil callback simulasi waktu selesai bicara
            duration = max(2.0, min(len(text) * 0.06, 8.0))
            if self._on_start_callback:
                self._on_start_callback()
            
            def delayed_finish():
                time.sleep(duration)
                if self._on_finish_callback:
                    self._on_finish_callback()
            threading.Thread(target=delayed_finish, daemon=True).start()
            return

        self._queue.put(clean_text)

    def stop(self):
        """Hentikan antrean saat ini."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

    def _run_loop(self):
        """Loop thread pekerja pyttsx3."""
        engine = None
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            # Coba pilih suara wanita atau default yang ramah
            voices = engine.getProperty('voices')
            if voices:
                # Preferensi suara Indonesia atau suara dengan nama ramah/Zira/David
                selected_voice = voices[0].id
                for v in voices:
                    if 'indonesia' in v.name.lower() or 'id' in getattr(v, 'languages', []):
                        selected_voice = v.id
                        break
                    if 'zira' in v.name.lower() or 'female' in v.name.lower():
                        selected_voice = v.id
                engine.setProperty('voice', selected_voice)
        except Exception as e:
            print(f"[SpeechEngine] Warning: Inisialisasi pyttsx3 gagal: {e}. Menggunakan mode simulasi.")
            engine = None

        while self._running:
            try:
                text = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if not self.enabled or not text:
                self._queue.task_done()
                continue

            self._is_speaking = True
            if self._on_start_callback:
                try:
                    self._on_start_callback()
                except Exception:
                    pass

            if engine:
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as err:
                    print(f"[SpeechEngine] Error bicara: {err}")
                    # Jika error, re-inisialisasi pyttsx3 driver
                    try:
                        import pyttsx3
                        engine = pyttsx3.init()
                        engine.setProperty('rate', self.rate)
                    except Exception:
                        pass
            else:
                # Mode fallback jika pyttsx3 tidak bersuara
                time.sleep(max(1.5, len(text) * 0.05))

            self._is_speaking = False
            if self._on_finish_callback:
                try:
                    self._on_finish_callback()
                except Exception:
                    pass

            self._queue.task_done()

    def close(self):
        self._running = False
        self.stop()
