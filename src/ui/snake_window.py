import os
import sys
import random
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QComboBox
)

try:
    from src.ui.markdown_helper import markdown_to_html
except ImportError:
    from ui.markdown_helper import markdown_to_html


class SnakeCanvas(QWidget):
    """Kanvas visual grid permainan Snake (22 x 22 sel)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_size = 22
        self.cell_size = 18
        self.setFixedSize(self.grid_size * self.cell_size, self.grid_size * self.cell_size)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        parent = self.parent()

        # 1. Background Papan Hijau / Kolam Ikan Pixel
        painter.fillRect(self.rect(), QColor(28, 40, 38))

        # Garis grid halus
        painter.setPen(QColor(36, 52, 49))
        for i in range(self.grid_size + 1):
            coord = i * self.cell_size
            painter.drawLine(coord, 0, coord, self.height())
            painter.drawLine(0, coord, self.width(), coord)

        if not parent:
            return

        # 2. Gambar Makanan (Ikan / Udang / Susu)
        cs = self.cell_size
        food_font = QFont("Segoe UI Emoji", 11)
        painter.setFont(food_font)

        if parent.food_pos:
            fx, fy = parent.food_pos
            rect_f = QRect(fx * cs, fy * cs, cs, cs)
            painter.drawText(rect_f, Qt.AlignCenter, "🐟")

        if parent.bonus_pos:
            bx, by = parent.bonus_pos
            rect_b = QRect(bx * cs, by * cs, cs, cs)
            icon = "🍤" if parent.bonus_type == "udang" else "🥛"
            painter.drawText(rect_b, Qt.AlignCenter, icon)

        # 3. Gambar Ular (Kepala & Badan)
        body = parent.snake_body
        for idx, (seg_x, seg_y) in enumerate(body):
            rx = seg_x * cs
            ry = seg_y * cs
            rect_s = QRect(rx + 1, ry + 1, cs - 2, cs - 2)

            if idx == 0:
                # Kepala Ular (Warna Emas/Hijau Terang Bersinar)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(244, 162, 97)))
                painter.drawRoundedRect(rect_s, 5, 5)

                # Mata Ular
                painter.setBrush(QBrush(QColor(38, 24, 20)))
                eye_size = 3
                painter.drawEllipse(rx + 4, ry + 4, eye_size, eye_size)
                painter.drawEllipse(rx + cs - 7, ry + 4, eye_size, eye_size)
            else:
                # Badan Ular dengan gradien kehijauan lembut
                ratio = idx / max(1, len(body))
                r_c = int(42 + ratio * 30)
                g_c = int(157 - ratio * 40)
                b_c = int(143 - ratio * 30)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(r_c, g_c, b_c)))
                painter.drawRoundedRect(rect_s, 4, 4)

        # 4. Tampilan Game Over atau Pause
        if parent.is_game_over:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
            painter.setPen(QColor(255, 230, 220))
            painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "GAME OVER!\n🐾\nTekan Spasi untuk Main Lagi")
        elif parent.is_paused:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
            painter.setPen(QColor(255, 230, 220))
            painter.setFont(QFont("Segoe UI", 15, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "PAUSED (Jeda)\nTekan 'Spasi' untuk Lanjut")


class MimiSnakeWindow(QDialog):
    """
    Jendela Game Snake (Ular Tangkap Ikan) interaktif bersama Mimi.
    - Kontrol Panah / WASD
    - Makanan Ikan 🐟 & Bonus Udang 🍤 / Susu 🥛
    - Pilihan Kecepatan: Santai, Normal, Cepat
    - Celetukan kontekstual Mimi.
    """
    def __init__(self, pet_parent=None, pet_name="Mimi"):
        super().__init__(None, Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.pet_parent = pet_parent
        self.pet_name = pet_name

        self.setWindowTitle(f"🐍 Bermain Snake bersama {self.pet_name}")
        self.setFixedSize(650, 520)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFDF9;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # Game State
        self.grid_size = 22
        self.snake_body = [(11, 11), (11, 12), (11, 13)]
        self.direction = (0, -1)  # Bergerak ke atas saat mulai
        self.next_direction = (0, -1)
        self.food_pos = None
        self.bonus_pos = None
        self.bonus_type = "udang"
        self.bonus_timer_ticks = 0

        self.score = 0
        self.fish_eaten = 0
        self.high_score = 0
        self.is_game_over = False
        self.is_paused = False

        self._init_ui()

        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self._game_tick)

        self._start_new_game()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)

        # SISI KIRI: KANVAS GAME SNAKE
        canvas_box = QVBoxLayout()
        self.canvas = SnakeCanvas(self)
        canvas_box.addWidget(self.canvas)

        lbl_controls = QLabel("⌨️ Kontrol: Panah / W A S D | Spasi: Jeda / Mulai", self)
        lbl_controls.setStyleSheet("font-size: 9.5px; color: #8A7264; margin-top: 4px;")
        canvas_box.addWidget(lbl_controls)
        main_layout.addLayout(canvas_box)

        # SISI KANAN: STATS & CELETUKAN MIMI
        side_layout = QVBoxLayout()
        side_layout.setSpacing(10)

        # Kartu Mimi & Dialog
        mimi_card = QFrame(self)
        mimi_card.setStyleSheet("""
            QFrame {
                background: #FBF4ED;
                border: 1.5px solid #E8D8C8;
                border-radius: 12px;
                padding: 6px;
            }
        """)
        m_layout = QVBoxLayout(mimi_card)
        m_layout.setContentsMargins(8, 8, 8, 8)
        m_layout.setSpacing(6)

        header_row = QHBoxLayout()
        lbl_avatar = QLabel("🐱", mimi_card)
        lbl_avatar.setStyleSheet("font-size: 24px;")
        header_row.addWidget(lbl_avatar)

        name_box = QVBoxLayout()
        lbl_name = QLabel(f"{self.pet_name} • Pengawas Kolam", mimi_card)
        lbl_name.setStyleSheet("font-size: 11px; font-weight: bold; color: #D35400;")
        self.lbl_sub = QLabel("Menunggu ikan lezat 🐾", mimi_card)
        self.lbl_sub.setStyleSheet("font-size: 9.5px; color: #7B6858;")
        name_box.addWidget(lbl_name)
        name_box.addWidget(self.lbl_sub)
        header_row.addLayout(name_box)
        header_row.addStretch()
        m_layout.addLayout(header_row)

        self.chat_bubble = QLabel(mimi_card)
        self.chat_bubble.setWordWrap(True)
        self.chat_bubble.setStyleSheet("""
            QLabel {
                background: #FFFFFF;
                border: 1px solid #E0CDBC;
                border-radius: 8px;
                padding: 6px 8px;
                font-size: 10.5px;
                color: #2D2424;
                line-height: 130%;
            }
        """)
        self.chat_bubble.setText(f"Meow! Bantu ular tangkap ikan lezat di kolam ya Tuan! 🐟🐾")
        m_layout.addWidget(self.chat_bubble)
        side_layout.addWidget(mimi_card)

        # Kartu Skor & Kecepatan
        stats_card = QFrame(self)
        stats_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EADDCF;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        s_layout = QVBoxLayout(stats_card)
        s_layout.setSpacing(6)

        self.lbl_score = QLabel("🏆 Skor: 0", stats_card)
        self.lbl_score.setStyleSheet("font-size: 12px; font-weight: bold; color: #D35400;")
        s_layout.addWidget(self.lbl_score)

        self.lbl_fish = QLabel("🐟 Ikan Ditangkap: 0", stats_card)
        self.lbl_fish.setStyleSheet("font-size: 11px; color: #4A3B32;")
        s_layout.addWidget(self.lbl_fish)

        self.lbl_high = QLabel("⭐ Rekor Tertinggi: 0", stats_card)
        self.lbl_high.setStyleSheet("font-size: 11px; color: #4A3B32;")
        s_layout.addWidget(self.lbl_high)

        # Pilihan Kecepatan
        lbl_speed = QLabel("⚡ Kecepatan:", stats_card)
        lbl_speed.setStyleSheet("font-size: 10.5px; font-weight: bold; color: #4A3B32; margin-top: 4px;")
        s_layout.addWidget(lbl_speed)

        self.combo_speed = QComboBox(stats_card)
        self.combo_speed.addItem("🟢 Santai (Lambat)", 140)
        self.combo_speed.addItem("🟡 Normal (Sedang)", 100)
        self.combo_speed.addItem("🔴 Cepat (Tantangan)", 65)
        self.combo_speed.setCurrentIndex(1)
        self.combo_speed.setStyleSheet("""
            QComboBox {
                background: #FFFDF9; border: 1.5px solid #E07A5F;
                border-radius: 5px; padding: 3px 6px; font-size: 10.5px;
            }
        """)
        self.combo_speed.currentIndexChanged.connect(self._on_speed_changed)
        s_layout.addWidget(self.combo_speed)

        side_layout.addWidget(stats_card)

        # Tombol Aksi
        btn_box = QHBoxLayout()
        self.btn_new = QPushButton("🔄 Game Baru", self)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setStyleSheet("""
            QPushButton {
                background: #E07A5F; color: white;
                font-weight: bold; font-size: 10.5px;
                border: none; border-radius: 6px; padding: 6px 12px;
            }
            QPushButton:hover { background: #C74A27; }
        """)
        self.btn_new.clicked.connect(self._start_new_game)
        btn_box.addWidget(self.btn_new)

        self.btn_pause = QPushButton("⏸️ Jeda (Spasi)", self)
        self.btn_pause.setCursor(Qt.PointingHandCursor)
        self.btn_pause.setStyleSheet("""
            QPushButton {
                background: #F4EBE1; color: #8E3B20;
                font-weight: bold; font-size: 10.5px;
                border: 1px solid #D8C3A5; border-radius: 6px; padding: 6px 10px;
            }
            QPushButton:hover { background: #EAD8C7; }
        """)
        self.btn_pause.clicked.connect(self._toggle_pause)
        btn_box.addWidget(self.btn_pause)
        side_layout.addLayout(btn_box)

        side_layout.addStretch()
        main_layout.addLayout(side_layout)

    def _set_mimi_bubble(self, text):
        self.chat_bubble.setText(markdown_to_html(text))
        if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
            try:
                self.pet_parent.cat_audio.play_chirp()
            except Exception:
                pass

    def _start_new_game(self):
        self.snake_body = [(11, 11), (11, 12), (11, 13)]
        self.direction = (0, -1)
        self.next_direction = (0, -1)
        self.bonus_pos = None
        self.bonus_timer_ticks = 0
        self.score = 0
        self.fish_eaten = 0
        self.is_game_over = False
        self.is_paused = False

        self._spawn_food()
        self._update_stats_display()

        self._set_mimi_bubble("Meow! Game Snake dimulai! Tangkap ikan 🐟 sebanyak-banyaknya ya Tuan! 🐾")
        speed_ms = self.combo_speed.currentData()
        self.game_timer.start(speed_ms)
        self.canvas.setFocus()
        self.canvas.update()

    def _on_speed_changed(self):
        if not self.is_game_over and not self.is_paused:
            self.game_timer.setInterval(self.combo_speed.currentData())
        self.canvas.setFocus()

    def _spawn_food(self):
        empty_cells = [
            (x, y) for x in range(self.grid_size) for y in range(self.grid_size)
            if (x, y) not in self.snake_body and (x, y) != self.bonus_pos
        ]
        if empty_cells:
            self.food_pos = random.choice(empty_cells)

    def _maybe_spawn_bonus(self):
        if self.bonus_pos is None and random.random() < 0.25:
            empty_cells = [
                (x, y) for x in range(self.grid_size) for y in range(self.grid_size)
                if (x, y) not in self.snake_body and (x, y) != self.food_pos
            ]
            if empty_cells:
                self.bonus_pos = random.choice(empty_cells)
                self.bonus_type = "udang" if random.random() < 0.7 else "susu"
                self.bonus_timer_ticks = 40  # Tahan sekitar 4-5 detik
                self._set_mimi_bubble("✨ *Bonus Muncul!* Cepat tangkap makanan spesial sebelum menghilang! 🍤🐾")

    def _game_tick(self):
        if not self.isVisible() or self.is_game_over or self.is_paused:
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake_body[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # 1. Tabrakan dengan Dinding
        if new_head[0] < 0 or new_head[0] >= self.grid_size or new_head[1] < 0 or new_head[1] >= self.grid_size:
            self._trigger_game_over("menabrak dinding pembatas kolam")
            return

        # 2. Tabrakan dengan Diri Sendiri
        if new_head in self.snake_body[:-1]:
            self._trigger_game_over("menabrak ekornya sendiri")
            return

        # Masukkan kepala baru
        self.snake_body.insert(0, new_head)

        # 3. Cek Makan Ikan Biasa
        if new_head == self.food_pos:
            self.score += 10
            self.fish_eaten += 1
            self._spawn_food()
            self._maybe_spawn_bonus()

            if self.score > self.high_score:
                self.high_score = self.score

            self._update_stats_display()

            comments = [
                "🐾 *Nyam!* Ikan lezat tertangkap! (+10) 🐟",
                "Purrrr~ Ular makin panjang dan kenyang! ✨",
                "Meow! Gerakan lincah sekali, Tuan! 🐟🐾"
            ]
            if self.fish_eaten % 5 == 0:
                self._set_mimi_bubble(f"🔥 *Mantap!* Sudah {self.fish_eaten} ikan berhasil diamankan! Hati-hati ekor ya! 😼")
            else:
                self._set_mimi_bubble(random.choice(comments))
        # 4. Cek Makan Bonus
        elif self.bonus_pos and new_head == self.bonus_pos:
            pts = 30 if self.bonus_type == "udang" else 50
            self.score += pts
            self.bonus_pos = None
            if self.score > self.high_score:
                self.high_score = self.score
            self._update_stats_display()
            self._set_mimi_bubble(f"🎉 *WOW!* Makanan super tertangkap! (+{pts} Poin)! Meoww! 🍤🐾")
        else:
            # Tidak makan, potong ujung ekor
            self.snake_body.pop()

        # Update durasi bonus
        if self.bonus_pos:
            self.bonus_timer_ticks -= 1
            if self.bonus_timer_ticks <= 0:
                self.bonus_pos = None

        self.canvas.update()

    def _trigger_game_over(self, reason):
        self.is_game_over = True
        self.game_timer.stop()
        if self.score > self.high_score:
            self.high_score = self.score
        self._update_stats_display()
        self._set_mimi_bubble(f"😿 *Aduh!* Ularmu {reason}! Skor akhir: **{self.score}** (Ikan: {self.fish_eaten})! Tekan Spasi untuk coba lagi ya Tuan! 🐾")
        self.canvas.update()

    def _toggle_pause(self):
        if self.is_game_over:
            self._start_new_game()
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.game_timer.stop()
            self.btn_pause.setText("▶️ Lanjut (Spasi)")
            self._set_mimi_bubble("⏸️ Permainan dijeda. Tarik napas dulu sejenak, Tuan! ☕🐾")
        else:
            self.game_timer.start()
            self.btn_pause.setText("⏸️ Jeda (Spasi)")
            self._set_mimi_bubble("▶️ Lanjut tangkap ikan! Fokus dan jangan sampai menabrak! 🐟🐾")
        self.canvas.update()

    def _update_stats_display(self):
        self.lbl_score.setText(f"🏆 Skor: {self.score}")
        self.lbl_fish.setText(f"🐟 Ikan Ditangkap: {self.fish_eaten}")
        self.lbl_high.setText(f"⭐ Rekor Tertinggi: {self.high_score}")

    def keyPressEvent(self, event):
        k = event.key()

        if self.is_game_over:
            if k in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
                self._start_new_game()
            return

        if k == Qt.Key_Space:
            self._toggle_pause()
            return

        if self.is_paused:
            return

        # Cegah gerakan membalik langsung 180 derajat
        cur_dx, cur_dy = self.direction

        if k in (Qt.Key_Up, Qt.Key_W):
            if cur_dy != 1:
                self.next_direction = (0, -1)
        elif k in (Qt.Key_Down, Qt.Key_S):
            if cur_dy != -1:
                self.next_direction = (0, 1)
        elif k in (Qt.Key_Left, Qt.Key_A):
            if cur_dx != 1:
                self.next_direction = (-1, 0)
        elif k in (Qt.Key_Right, Qt.Key_D):
            if cur_dx != -1:
                self.next_direction = (1, 0)
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if hasattr(self, "game_timer") and self.game_timer.isActive():
            self.game_timer.stop()
        if self.pet_parent and hasattr(self.pet_parent, "on_game_closed"):
            self.pet_parent.on_game_closed(self)
        super().closeEvent(event)

