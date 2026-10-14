import os
import sys
import random
import math
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QPoint
from PyQt5.QtGui import QMovie, QCursor
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_CURRENT_DIR)
_ROOT_DIR = os.path.dirname(_SRC_DIR)
for _p in [_ROOT_DIR, _SRC_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


class PreyWidget(QWidget):
    """
    Widget target mangsa mini (tikus 🐭 atau lalat 🪰) yang berkeliaran di layar desktop
    untuk dikejar, diburu, dan diterkam oleh Mimi.
    """
    sig_caught = pyqtSignal()
    sig_escaped = pyqtSignal()

    def __init__(self, prey_type: str = "mouse", parent=None):
        super().__init__(parent)
        self.prey_type = prey_type.lower()
        self.assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))

        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.WindowTransparentForInput  # Klik mouse tembus agar tidak menghalangi pengguna bekerja
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(36, 36)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Setup GIF animasi
        filename = "prey_mouse.gif" if self.prey_type == "mouse" else "prey_fly.gif"
        gif_path = os.path.join(self.assets_dir, filename)
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            scale_sz = QSize(32, 32) if self.prey_type == "mouse" else QSize(24, 24)
            self.movie.setScaledSize(scale_sz)
            self.label.setMovie(self.movie)
            self.movie.start()
        else:
            self.movie = None
            self.label.setText("🐭" if self.prey_type == "mouse" else "🪰")

        self.screen_geo = QApplication.primaryScreen().geometry()
        self._target_x = self.x()
        self._target_y = self.y()
        self._speed = 5
        self._active = False
        self._fleeing = False
        self._is_caught = False

        # Timer pergerakan autonomous mangsa
        self.move_timer = QTimer(self)
        self.move_timer.setInterval(40)
        self.move_timer.timeout.connect(self._on_move_tick)

    def spawn(self, start_x: int = None, start_y: int = None):
        """Memunculkan mangsa di layar."""
        self._is_caught = False
        self._fleeing = False
        self._active = True

        screen_w = self.screen_geo.width()
        screen_h = self.screen_geo.height()

        if self.prey_type == "mouse":
            # Tikus berlari di area dekat dasar layar / taskbar
            floor_y = screen_h - 75
            spawn_x = start_x if start_x is not None else random.randint(150, screen_w - 200)
            spawn_y = floor_y
            self._target_x = spawn_x + random.choice([-250, 250])
            self._target_y = floor_y
            self._speed = random.randint(4, 7)
        else:
            # Lalat terbang berputar di area bawah sampai tengah
            spawn_x = start_x if start_x is not None else random.randint(150, screen_w - 200)
            spawn_y = start_y if start_y is not None else random.randint(screen_h - 250, screen_h - 90)
            self._target_x = spawn_x + random.randint(-180, 180)
            self._target_y = max(100, spawn_y + random.randint(-120, 120))
            self._speed = random.randint(5, 9)

        self.move(spawn_x, spawn_y)
        self.show()
        self.move_timer.start()

    def _on_move_tick(self):
        if not self._active or self._is_caught:
            return

        cx = self.x()
        cy = self.y()
        dx = self._target_x - cx
        dy = self._target_y - cy
        dist = math.hypot(dx, dy)

        if dist < self._speed + 2:
            # Sampai di target tujuan -> tentukan tujuan acak baru
            screen_w = self.screen_geo.width()
            screen_h = self.screen_geo.height()

            if self.prey_type == "mouse":
                floor_y = screen_h - 75
                # Bergerak acak ke kiri atau kanan
                self._target_x = max(50, min(screen_w - 90, cx + random.choice([-220, -140, 140, 220])))
                self._target_y = floor_y
                self._speed = random.randint(4, 7)
            else:
                # Lalat terbang berputar acak
                self._target_x = max(50, min(screen_w - 90, cx + random.randint(-200, 200)))
                self._target_y = max(100, min(screen_h - 85, cy + random.randint(-140, 140)))
                self._speed = random.randint(5, 9)
        else:
            step_x = int((dx / dist) * self._speed)
            step_y = int((dy / dist) * self._speed)
            self.move(cx + step_x, cy + step_y)

    def flee_from(self, hunter_x: int, hunter_y: int):
        """Mangsa panik dan berlari menjauhi posisi pemburu (Mimi)."""
        self._fleeing = True
        self._speed = 9 if self.prey_type == "mouse" else 11
        screen_w = self.screen_geo.width()
        screen_h = self.screen_geo.height()

        # Arah menjauh
        dir_x = 1 if self.x() >= hunter_x else -1
        self._target_x = max(20, min(screen_w - 50, self.x() + dir_x * random.randint(250, 450)))

        if self.prey_type == "fly":
            # Lalat melesat ke atas
            self._target_y = max(40, self.y() - random.randint(80, 200))

    def get_center_pos(self) -> QPoint:
        return QPoint(self.x() + self.width() // 2, self.y() + self.height() // 2)

    def caught(self):
        """Dipanggil saat Mimi sukses menerkam mangsa ini."""
        self._is_caught = True
        self._active = False
        self.move_timer.stop()
        self.sig_caught.emit()
        # Hilang setelah tertangkap
        QTimer.singleShot(400, self.hide)

    def escape(self):
        """Dipanggil jika mangsa berhasil meloloskan diri keluar layar."""
        self._active = False
        self.move_timer.stop()
        self.sig_escaped.emit()
        self.hide()
