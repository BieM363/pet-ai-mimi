import os
import sys
import time
import threading
import logging

try:
    from pypresence import Presence
except ImportError:
    Presence = None

logger = logging.getLogger("DiscordRPC")

# Client ID default atau bisa diisi pengguna melalui .env (DISCORD_CLIENT_ID)
# Pengguna dapat membuat Discord App di https://discord.com/developers/applications bernama "Mimi Agent Pet"
DEFAULT_CLIENT_ID = "1349880173629472788"


class DiscordRPCManager:
    """
    Pengelola koneksi Discord Rich Presence (RPC) untuk menampilkan
    aktivitas 'Playing Mimi Agent Pet' di profil Discord pengguna secara live.
    - Thread-safe dan berjalan di latar belakang (background thread).
    - Tidak memblokir UI dan aman dari crash bila Discord ditutup.
    - Menyesuaikan status activity secara dinamis (santai, voice channel, game, tidur).
    """

    def __init__(self, client_id: str = "", enabled: bool = True):
        self.enabled = enabled
        self.client_id = client_id.strip() if client_id and client_id.strip() else DEFAULT_CLIENT_ID
        self.rpc = None
        self.connected = False
        self.is_running = False
        self.start_time = int(time.time())

        # Status terkini
        self.current_details = "Menemani Tuan di Desktop 🐾"
        self.current_state = "Virtual Pixel Cat AI Companion"
        self.current_small_image = None
        self.current_small_text = None

        self._lock = threading.Lock()
        self._worker_thread = None
        self._need_update = False

    def start(self):
        """Memulai thread background pemantau koneksi Discord RPC."""
        if not self.enabled or Presence is None:
            return

        self.is_running = True
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()

    def _connect_rpc(self) -> bool:
        """Mencoba menghubungkan IPC pipe ke Discord desktop."""
        if not self.client_id:
            return False

        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            print(f"[DiscordRPC] Berhasil terhubung ke Discord! Activity 'Mimi Agent Pet' aktif.")
            return True
        except Exception as e:
            self.connected = False
            self.rpc = None
            return False

    def _run_loop(self):
        """Loop latar belakang untuk menjaga koneksi dan memperbarui status RPC."""
        last_heartbeat = 0
        while self.is_running:
            now = time.time()
            if not self.connected:
                # Coba koneksi ke Discord setiap 10 detik jika belum terhubung
                if self._connect_rpc():
                    self._send_presence_update()
                    last_heartbeat = now
                else:
                    time.sleep(10)
                    continue

            # Jika terhubung dan ada permintaan update status atau interval heartbeat 15 detik
            with self._lock:
                need_update = self._need_update
                self._need_update = False

            if need_update or (now - last_heartbeat >= 15.0):
                self._send_presence_update()
                last_heartbeat = now

            # Heartbeat sleep
            time.sleep(3)

    def _send_presence_update(self):
        """Mengirim data Rich Presence ke Discord."""
        if not self.connected or not self.rpc:
            return

        try:
            with self._lock:
                details = self.current_details
                state = self.current_state
                small_img = self.current_small_image
                small_txt = self.current_small_text

            kwargs = {
                "details": details[:127] if details else "Mimi Cat Companion 🐾",
                "state": state[:127] if state else "",
                "start": self.start_time,
                "large_image": "cat_idle",
                "large_text": "Mimi Agent Pet • Virtual Pixel Cat AI",
            }
            if small_img:
                kwargs["small_image"] = small_img
                kwargs["small_text"] = small_txt or "Mimi"

            try:
                self.rpc.update(**kwargs)
            except Exception:
                # Fallback jika asset cat_idle belum diupload di Rich Presence Art Assets
                kwargs.pop("large_image", None)
                kwargs.pop("small_image", None)
                self.rpc.update(**kwargs)
        except Exception as e:
            # Jika Discord ditutup pengguna saat aplikasi berjalan
            self.connected = False
            self.rpc = None

    def update_activity(self, details: str, state: str = "", small_image: str = None, small_text: str = None):
        """Memperbarui informasi status yang tampil di Discord."""
        with self._lock:
            self.current_details = details
            self.current_state = state
            self.current_small_image = small_image
            self.current_small_text = small_text
            self._need_update = True

    def set_idle_status(self):
        """Mengatur status santai menemani di desktop."""
        self.update_activity(
            details="Menemani Tuan di Desktop 🐾",
            state="Virtual Pixel Cat AI Companion",
            small_image="idle",
            small_text="Santai & Waspada"
        )

    def set_discord_browse_status(self, channel_or_user: str = ""):
        """Mengatur status saat Tuan sedang membuka obrolan di Discord."""
        if channel_or_user:
            self.update_activity(
                details="Kepoin Discord Tuan 🔍",
                state=f"Membuka: {channel_or_user}"[:127],
                small_image="chat",
                small_text="Discord Chat"
            )
        else:
            self.update_activity(
                details="Kepoin Discord Tuan 🔍",
                state="Menyimak obrolan dengan antusias",
                small_image="chat",
                small_text="Discord Chat"
            )

    def set_voice_status(self, in_voice: bool, channel_name: str = ""):
        """Mengatur status saat Tuan berada di Voice Channel Discord."""
        if in_voice:
            state_str = f"Voice: {channel_name}" if channel_name else "Menyimak percakapan dengan tenang 🤫"
            self.update_activity(
                details="Duduk Diam di Voice Channel 🎧",
                state=state_str,
                small_image="listen",
                small_text="Duduk Manis Menyimak"
            )
        else:
            self.set_idle_status()

    def set_game_status(self, game_name: str):
        """Mengatur status saat Tuan bermain mini-game bersama Mimi."""
        self.update_activity(
            details=f"Bermain Game: {game_name} 🎮",
            state="Tanding seru bareng Tuan!",
            small_image="game",
            small_text=game_name
        )

    def set_sleep_status(self):
        """Mengatur status saat Mimi tertidur."""
        self.update_activity(
            details="Sedang Tidur Pulas Zzz... 💤",
            state="Mimpi menangkap banyak ikan tuna 🐟",
            small_image="sleep",
            small_text="Tidur Nyenyak"
        )

    def close(self):
        """Menutup koneksi Discord RPC secara rapi."""
        self.is_running = False
        if self.rpc and self.connected:
            try:
                self.rpc.clear()
                self.rpc.close()
            except Exception:
                pass
            self.connected = False
            self.rpc = None
