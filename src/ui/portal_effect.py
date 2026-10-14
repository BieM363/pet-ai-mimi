# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import math
import random
import time
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QPen, QBrush
from PyQt5.QtWidgets import QWidget


class CosmicParticle:
    """Partikel stardust kosmik yang melayang dan berputar di sekitar portal."""
    def __init__(self, cx, cy, rx, ry):
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.angle = random.uniform(0, math.pi * 2)
        self.dist_factor = random.uniform(0.2, 1.1)
        self.speed = random.uniform(0.04, 0.09) * (1 if random.random() < 0.5 else -1)
        self.lift_y = random.uniform(-25, 5)
        self.size = random.uniform(2.0, 4.5)
        self.alpha = random.uniform(150, 255)
        colors = [
            QColor(0, 245, 212),   # Cyan nebula
            QColor(155, 93, 229),  # Neon purple
            QColor(254, 228, 64),  # Gold starlight
            QColor(241, 91, 181),  # Magenta magic
            QColor(255, 255, 255)  # White star
        ]
        self.color = random.choice(colors)

    def update(self):
        self.angle += self.speed
        self.lift_y -= random.uniform(0.4, 1.2)
        self.dist_factor *= 0.985
        self.alpha = max(0, self.alpha - 3.5)

    def draw(self, painter: QPainter):
        if self.alpha <= 5:
            return
        px = self.cx + math.cos(self.angle) * (self.rx * self.dist_factor)
        py = self.cy + math.sin(self.angle) * (self.ry * self.dist_factor) + self.lift_y
        c = QColor(self.color)
        c.setAlpha(int(self.alpha))
        painter.setBrush(QBrush(c))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(px - self.size / 2, py - self.size / 2, self.size, self.size))


class DimensionalPortalOverlay(QWidget):
    """
    Overlay efek visual Portal Dimensi Kosmik:
    - Muncul dan berputar anggun tepat di bawah cakar Mimi.
    - Cincin energi berputar bertingkat (vortex), inti void hitam, dan partikel debu bintang.
    - Mengatur fase masuknya Mimi ke dalam portal lalu menutup rapi sebelum keluar aplikasi.
    """
    finished = pyqtSignal()

    def __init__(self, pet_window, on_finished=None):
        super().__init__()
        self.pet_window = pet_window
        self.on_finished = on_finished

        # Konfigurasi widget transparan tanpa bingkai dan selalu di atas
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        # Ukuran overlay portal (cukup luas mengelilingi Mimi 128x128)
        self.overlay_w = 260
        self.overlay_h = 240
        self.resize(self.overlay_w, self.overlay_h)

        # Posisikan overlay agar pusat portal berada tepat di bawah kaki Mimi
        mimi_pos = pet_window.pos()
        mimi_w = pet_window.width()
        mimi_h = pet_window.height()

        target_x = mimi_pos.x() + (mimi_w - self.overlay_w) // 2
        # Bagian bawah Mimi berada di ketinggian sekitar 75% dari overlay
        target_y = mimi_pos.y() + mimi_h - int(self.overlay_h * 0.65)
        self.move(target_x, target_y)

        # Parameter Portal
        self.portal_cx = self.overlay_w / 2
        self.portal_cy = self.overlay_h * 0.62
        self.max_rx = 95.0
        self.max_ry = 36.0

        # Status Fase
        self.portal_scale = 0.0
        self.rotation_angle = 0.0
        self.particles = []
        self.phase = "OPENING"  # "OPENING", "SINKING", "CLOSING", "DONE"
        self.start_time = time.time()

        # Posisi awal Mimi untuk animasi masuk ke dalam lubang
        self.mimi_initial_pos = QPoint(mimi_pos)
        self.mimi_sink_progress = 0.0

        # Timer animasi 60 FPS
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(16)
        self.anim_timer.timeout.connect(self._on_anim_frame)

    def start_animation(self):
        """Memulai rangkaian animasi portal keluar."""
        self.show()
        self.raise_()
        # Pastikan jendela pet tetap berada di atas portal agar efek masuk terasa pas
        self.pet_window.raise_()
        self.anim_timer.start()

    def _on_anim_frame(self):
        now = time.time()
        elapsed = now - self.start_time
        self.rotation_angle += 0.07

        # 1. Spawn partikel berkala
        if len(self.particles) < 55 and self.phase != "DONE":
            rx = self.max_rx * self.portal_scale
            ry = self.max_ry * self.portal_scale
            if rx > 5 and ry > 2:
                self.particles.append(CosmicParticle(self.portal_cx, self.portal_cy, rx, ry))

        # Update partikel
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alpha > 5]

        # 2. Transisi Fase
        if elapsed < 0.75:
            # Fase 1: Portal membuka dan membesar
            self.phase = "OPENING"
            progress = min(1.0, elapsed / 0.75)
            # Smooth ease-out back
            self.portal_scale = math.sin(progress * math.pi / 2)

        elif elapsed < 2.3:
            # Fase 2: Mimi tersedot / melangkah turun ke dalam portal
            self.phase = "SINKING"
            self.portal_scale = 1.0 + 0.05 * math.sin(elapsed * 7) # denyut stabil
            sink_p = (elapsed - 0.75) / 1.55
            self.mimi_sink_progress = min(1.0, sink_p)

            # Geser Mimi ke bawah (masuk ke dalam pusaran) dan turunkan opasitasnya
            drop_y = int(self.mimi_sink_progress * 42)
            cur_x = self.mimi_initial_pos.x()
            cur_y = self.mimi_initial_pos.y() + drop_y
            self.pet_window.move(cur_x, cur_y)

            # Opacity Mimi berkurang seiring masuk ke portal
            mimi_opacity = max(0.02, 1.0 - (self.mimi_sink_progress ** 1.3))
            self.pet_window.setWindowOpacity(mimi_opacity)

            # Balon kata juga meredup
            if hasattr(self.pet_window, 'speech_bubble') and self.pet_window.speech_bubble.isVisible():
                self.pet_window.speech_bubble.setWindowOpacity(max(0.0, 1.0 - self.mimi_sink_progress * 1.5))

        elif elapsed < 2.9:
            # Fase 3: Portal menyusut cepat menjadi titik cahaya bintang lalu lenyap
            self.phase = "CLOSING"
            close_p = (elapsed - 2.3) / 0.6
            self.portal_scale = max(0.0, (1.0 - close_p) ** 2)

            # Mimi sudah sepenuhnya masuk ke dimensi lain
            self.pet_window.setWindowOpacity(0.0)

        else:
            # Selesai
            self.phase = "DONE"
            self.anim_timer.stop()
            self.hide()
            if self.on_finished:
                self.on_finished()
            elif hasattr(self, 'finished'):
                self.finished.emit()
            return

        self.update()

    def paintEvent(self, event):
        if self.portal_scale <= 0.001:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        cx = self.portal_cx
        cy = self.portal_cy
        rx = self.max_rx * self.portal_scale
        ry = self.max_ry * self.portal_scale

        # 1. Pendaran Aura Luar (Nebula Glow)
        glow_grad = QRadialGradient(cx, cy, rx * 1.3)
        glow_grad.setColorAt(0.0, QColor(0, 245, 212, int(110 * self.portal_scale)))
        glow_grad.setColorAt(0.5, QColor(155, 93, 229, int(70 * self.portal_scale)))
        glow_grad.setColorAt(1.0, QColor(13, 2, 33, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - rx * 1.3, cy - ry * 1.3, rx * 2.6, ry * 2.6))

        # 2. Inti Lubang Hitam Kosmik (Void Center)
        void_grad = QRadialGradient(cx, cy, rx * 0.75)
        void_grad.setColorAt(0.0, QColor(8, 2, 20, 245))
        void_grad.setColorAt(0.7, QColor(24, 7, 50, 220))
        void_grad.setColorAt(1.0, QColor(114, 9, 183, 160))
        painter.setBrush(QBrush(void_grad))
        painter.setPen(QPen(QColor(155, 93, 229, 200), 2.0))
        painter.drawEllipse(QRectF(cx - rx * 0.75, cy - ry * 0.75, rx * 1.5, ry * 1.5))

        # 3. Garis-garis Pusaran Vortex Berputar (Spiral Energy Arms)
        num_arms = 6
        for i in range(num_arms):
            arm_angle = self.rotation_angle + (i * (math.pi * 2 / num_arms))
            points = []
            steps = 14
            for s in range(steps):
                t = s / float(steps)
                r_step_x = rx * (0.15 + 0.85 * t)
                r_step_y = ry * (0.15 + 0.85 * t)
                theta = arm_angle + (t * 2.1)
                px = cx + math.cos(theta) * r_step_x
                py = cy + math.sin(theta) * r_step_y
                points.append(QPoint(int(px), int(py)))

            if len(points) > 1:
                col = QColor(0, 245, 212) if i % 2 == 0 else QColor(254, 228, 64)
                col.setAlpha(int(180 * self.portal_scale))
                pen = QPen(col, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                for j in range(len(points) - 1):
                    painter.drawLine(points[j], points[j+1])

        # 4. Cincin Luar Berpendar (Portal Rim)
        rim_pen = QPen(QColor(0, 245, 212, int(220 * self.portal_scale)), 2.5)
        painter.setPen(rim_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - rx, cy - ry, rx * 2, ry * 2))

        # Cincin Sekunder Berdenyut
        inner_rx = rx * 0.88
        inner_ry = ry * 0.88
        inner_rim_pen = QPen(QColor(241, 91, 181, int(180 * self.portal_scale)), 1.8, Qt.DashLine)
        painter.setPen(inner_rim_pen)
        painter.drawEllipse(QRectF(cx - inner_rx, cy - inner_ry, inner_rx * 2, inner_ry * 2))

        # 5. Gambar Partikel Stardust
        for p in self.particles:
            p.draw(painter)

        # 6. Kilatan Bintang Sentral jika fase pembukaan / penutupan
        if self.phase in ["OPENING", "CLOSING"]:
            spark_size = rx * 0.3
            spark_color = QColor(255, 255, 255, int(230 * self.portal_scale))
            painter.setPen(QPen(spark_color, 2.0))
            painter.drawLine(int(cx - spark_size), int(cy), int(cx + spark_size), int(cy))
            painter.drawLine(int(cx), int(cy - spark_size * 0.5), int(cx), int(cy + spark_size * 0.5))
