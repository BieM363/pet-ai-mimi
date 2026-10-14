import os
import sys
import random
import math
from PyQt5.QtCore import Qt, QRect, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPolygon, QPainterPath
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox
)

# Tangga & Ular Standar
LADDERS = {
    4: 14,
    9: 31,
    20: 38,
    28: 84,
    40: 59,
    63: 81,
    71: 91
}

SNAKES = {
    17: 7,
    54: 34,
    62: 19,
    64: 60,
    87: 24,
    93: 73,
    95: 75,
    99: 78
}


class DiceWidget(QWidget):
    """Widget Dadu 3D bergaya retro dengan titik dadu timbul."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self.value = 1
        self.is_rolling = False

    def set_value(self, val: int):
        self.value = max(1, min(6, val))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Kotak Dadu dengan Rounded Bevel
        rect = QRect(4, 4, 56, 56)
        painter.setPen(QPen(QColor(180, 160, 140), 2))
        painter.setBrush(QBrush(QColor(255, 252, 248)))
        painter.drawRoundedRect(rect, 12, 12)

        # Bayangan dalam dadu
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 12)))
        painter.drawRoundedRect(rect.adjusted(2, 48, -2, -2), 4, 4)

        # Titik Dadu
        dot_color = QColor(211, 84, 0) if self.value == 1 else QColor(45, 36, 36)
        painter.setBrush(QBrush(dot_color))
        painter.setPen(Qt.NoPen)

        r = 5
        cx, cy = 32, 32
        p_left, p_right = 18, 46
        p_top, p_bot = 18, 46

        dots = []
        if self.value == 1:
            dots = [(cx, cy)]
            r = 7
        elif self.value == 2:
            dots = [(p_left, p_top), (p_right, p_bot)]
        elif self.value == 3:
            dots = [(p_left, p_top), (cx, cy), (p_right, p_bot)]
        elif self.value == 4:
            dots = [(p_left, p_top), (p_right, p_top), (p_left, p_bot), (p_right, p_bot)]
        elif self.value == 5:
            dots = [(p_left, p_top), (p_right, p_top), (cx, cy), (p_left, p_bot), (p_right, p_bot)]
        elif self.value == 6:
            dots = [
                (p_left, p_top), (p_right, p_top),
                (p_left, cy), (p_right, cy),
                (p_left, p_bot), (p_right, p_bot)
            ]

        for dx, dy in dots:
            painter.drawEllipse(QPoint(dx, dy), r, r)


class SnakesLaddersBoardWidget(QWidget):
    """
    Widget visual papan 100 petak (10x10) Ular Tangga:
    - Petak 1 di pojok kiri bawah, berkelok zigzag hingga petak 100 di kiri atas.
    - Menggambar Tangga kayu bambu dan Ular hijau lucu dengan kurva lembut.
    - Menggambar pion Pemain (Tuan) dan Mimi (Kucing).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_size = 10
        self.cell_size = 46
        self.board_px = self.grid_size * self.cell_size  # 460 x 460
        self.setFixedSize(self.board_px, self.board_px)

        self.player_pos = 1
        self.mimi_pos = 1

    def tile_to_pixel(self, tile: int):
        """Mengonversi nomor petak 1-100 menjadi koordinat tengah piksel (cx, cy)."""
        tile = max(1, min(100, tile))
        row_from_bottom = (tile - 1) // 10
        row = 9 - row_from_bottom
        col_offset = (tile - 1) % 10

        if row_from_bottom % 2 == 0:
            col = col_offset
        else:
            col = 9 - col_offset

        cx = int(col * self.cell_size + self.cell_size / 2)
        cy = int(row * self.cell_size + self.cell_size / 2)
        return cx, cy

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        cs = self.cell_size

        # Palet Warna Petak Pastel Lembut
        tile_colors = [
            QColor(255, 252, 245),  # Krem
            QColor(253, 237, 226),  # Peach lembut
            QColor(234, 250, 234),  # Hijau mint pastel
            QColor(235, 245, 251)   # Biru langit pastel
        ]

        # 1. Gambar Petak 1-100
        font_num = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font_num)

        for tile in range(1, 101):
            cx, cy = self.tile_to_pixel(tile)
            rx = cx - cs // 2
            ry = cy - cs // 2
            rect = QRect(rx, ry, cs, cs)

            bg = tile_colors[tile % len(tile_colors)]
            if tile == 100:
                bg = QColor(255, 230, 160)  # Petak Kemenangan Emas
            elif tile == 1:
                bg = QColor(220, 245, 220)  # Petak Start Hijau

            painter.fillRect(rect, bg)
            painter.setPen(QColor(225, 212, 198))
            painter.drawRect(rect)

            # Gambar nomor petak
            painter.setPen(QColor(130, 110, 95))
            num_rect = QRect(rx + 2, ry + 2, cs - 4, 12)
            painter.drawText(num_rect, Qt.AlignLeft | Qt.AlignTop, str(tile))

        # 2. Gambar Tangga-Tangga (Ladders)
        for start, end in LADDERS.items():
            sx, sy = self.tile_to_pixel(start)
            ex, ey = self.tile_to_pixel(end)
            self._draw_ladder(painter, sx, sy, ex, ey)

        # 3. Gambar Ular-Ular (Snakes)
        for head, tail in SNAKES.items():
            hx, hy = self.tile_to_pixel(head)
            tx, ty = self.tile_to_pixel(tail)
            self._draw_snake(painter, hx, hy, tx, ty)

        # 4. Gambar Pion Pemain & Mimi
        px, py = self.tile_to_pixel(self.player_pos)
        mx, my = self.tile_to_pixel(self.mimi_pos)

        # Jika di petak yang sama, beri offset sedikit agar tidak saling tumpuk
        if self.player_pos == self.mimi_pos:
            px -= 8
            mx += 8

        # Pion Pemain (Tuan - Mahkota Biru)
        self._draw_player_token(painter, px, py)

        # Pion Mimi (Kucing Oranye)
        self._draw_mimi_token(painter, mx, my)

    def _draw_ladder(self, painter, x1, y1, x2, y2):
        """Menggambar tangga kayu retro dengan dua tiang dan anak tangga."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length < 1:
            return

        # Vektor normal tegak lurus
        nx = -dy / length * 6.0
        ny = dx / length * 6.0

        pen_rail = QPen(QColor(160, 100, 45), 3.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_rail)

        # Rel kiri & kanan
        painter.drawLine(int(x1 + nx), int(y1 + ny), int(x2 + nx), int(y2 + ny))
        painter.drawLine(int(x1 - nx), int(y1 - ny), int(x2 - nx), int(y2 - ny))

        # Anak tangga (rungs)
        pen_rung = QPen(QColor(200, 140, 70), 2.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_rung)
        steps = max(3, int(length // 18))
        for i in range(1, steps):
            t = i / steps
            rx = x1 + dx * t
            ry = y1 + dy * t
            painter.drawLine(int(rx + nx), int(ry + ny), int(rx - nx), int(ry - ny))

    def _draw_snake(self, painter, hx, hy, tx, ty):
        """Menggambar ular hijau meliuk dengan kepala dan mata."""
        dx = tx - hx
        dy = ty - hy
        length = math.hypot(dx, dy)
        if length < 1:
            return

        # Titik kontrol meliuk untuk kurva Bezier
        nx = -dy / length * (length * 0.28)
        ny = dx / length * (length * 0.28)

        ctrl1_x = hx + dx * 0.33 + nx
        ctrl1_y = hy + dy * 0.33 + ny
        ctrl2_x = hx + dx * 0.66 - nx
        ctrl2_y = hy + dy * 0.66 - ny

        path = QPainterPath()
        path.moveTo(hx, hy)
        path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, tx, ty)

        # Badan ular
        pen_body = QPen(QColor(39, 174, 96), 7.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_body)
        painter.drawPath(path)

        # Garis tengah punggung ular
        pen_inner = QPen(QColor(46, 204, 113), 3.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_inner)
        painter.drawPath(path)

        # Kepala ular
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(34, 153, 84)))
        painter.drawEllipse(QPoint(hx, hy), 7, 7)

        # Mata ular
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPoint(hx - 2, hy - 2), 2, 2)
        painter.drawEllipse(QPoint(hx + 2, hy - 2), 2, 2)
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(QPoint(hx - 2, hy - 2), 1, 1)
        painter.drawEllipse(QPoint(hx + 2, hy - 2), 1, 1)

    def _draw_player_token(self, painter, x, y):
        """Menggambar pion Tuan (Lingkaran biru cerah dengan border emas & ikon pion)."""
        painter.setPen(QPen(QColor(241, 196, 15), 2))
        painter.setBrush(QBrush(QColor(41, 128, 185)))
        painter.drawEllipse(QPoint(x, y), 10, 10)

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI Emoji", 8))
        painter.drawText(QRect(x - 10, y - 10, 20, 20), Qt.AlignCenter, "👤")

    def _draw_mimi_token(self, painter, x, y):
        """Menggambar pion Mimi (Lingkaran oranye ceria dengan wajah kucing)."""
        painter.setPen(QPen(QColor(230, 126, 34), 2))
        painter.setBrush(QBrush(QColor(243, 156, 18)))
        painter.drawEllipse(QPoint(x, y), 10, 10)

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI Emoji", 8))
        painter.drawText(QRect(x - 10, y - 10, 20, 20), Qt.AlignCenter, "🐱")


class MimiSnakesLaddersWindow(QDialog):
    """
    Jendela Game Ular Tangga Klasik (Pemain vs Kucing Mimi AI):
    - 100 Petak interaktif dengan tangga bambu & ular meliuk.
    - Dadu beranimasi lempar acak 1-6.
    - Animasi pion berjalan langkah demi langkah.
    - Celetukan dan reaksi kucing yang menghibur.
    """
    def __init__(self, pet_parent=None, pet_name="Mimi"):
        super().__init__(None, Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.pet_parent = pet_parent
        self.pet_name = pet_name

        self.setWindowTitle(f"🎲 Ular Tangga bersama {self.pet_name}")
        self.setFixedSize(760, 530)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFDF9;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # Status Permainan
        self.player_pos = 1
        self.mimi_pos = 1
        self.current_turn = "player"  # 'player' atau 'mimi'
        self.is_animating = False
        self.is_game_over = False

        # Timer animasi dadu
        self.roll_ticks = 0
        self.dice_timer = QTimer(self)
        self.dice_timer.setInterval(60)
        self.dice_timer.timeout.connect(self._on_dice_roll_tick)

        # Timer animasi langkah pion
        self.step_timer = QTimer(self)
        self.step_timer.setInterval(130)
        self.step_timer.timeout.connect(self._on_pawn_step_tick)
        self.step_target_tile = 1
        self.active_moving_pawn = "player"

        self._init_ui()
        self._start_new_game()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)

        # SISI KIRI: PAPAN ULAR TANGGA
        board_box = QVBoxLayout()
        self.board_widget = SnakesLaddersBoardWidget(self)
        board_box.addWidget(self.board_widget)

        lbl_note = QLabel("🏁 Petak 1: Mulai | Petak 100: Kemenangan! | Tangga: Naik 🚀 | Ular: Turun 🐍", self)
        lbl_note.setStyleSheet("font-size: 9.5px; color: #8A7264; margin-top: 3px;")
        board_box.addWidget(lbl_note)
        main_layout.addLayout(board_box)

        # SISI KANAN: KARTU MIMI, DADU, & STATUS GILIRAN
        side_layout = QVBoxLayout()
        side_layout.setSpacing(10)

        # Kartu Mimi
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
        self.lbl_avatar = QLabel("🐱", mimi_card)
        self.lbl_avatar.setStyleSheet("font-size: 24px;")
        header_row.addWidget(self.lbl_avatar)

        name_box = QVBoxLayout()
        lbl_name = QLabel(f"{self.pet_name} • Lawan Tanding", mimi_card)
        lbl_name.setStyleSheet("font-size: 11px; font-weight: bold; color: #D35400;")
        self.lbl_sub = QLabel("Siap berlomba ke petak 100! 🐾", mimi_card)
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
        self.chat_bubble.setText(f"Meow! Ayo main Ular Tangga, Tuan! Lempar dadumu duluan ya! 🎲🐾")
        m_layout.addWidget(self.chat_bubble)
        side_layout.addWidget(mimi_card)

        # Kartu Status Petak & Giliran
        status_card = QFrame(self)
        status_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EADDCF;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        s_layout = QVBoxLayout(status_card)
        s_layout.setSpacing(6)

        self.lbl_turn = QLabel("🎯 Giliran: Tuan (Pemain)", status_card)
        self.lbl_turn.setStyleSheet("font-size: 12px; font-weight: bold; color: #2980B9;")
        s_layout.addWidget(self.lbl_turn)

        self.lbl_player_pos = QLabel("👤 Posisi Tuan: Petak 1", status_card)
        self.lbl_player_pos.setStyleSheet("font-size: 11px; color: #4A3B32;")
        s_layout.addWidget(self.lbl_player_pos)

        self.lbl_mimi_pos = QLabel("🐱 Posisi Mimi: Petak 1", status_card)
        self.lbl_mimi_pos.setStyleSheet("font-size: 11px; color: #4A3B32;")
        s_layout.addWidget(self.lbl_mimi_pos)

        side_layout.addWidget(status_card)

        # Kartu Area Dadu
        dice_card = QFrame(self)
        dice_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EADDCF;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        d_layout = QVBoxLayout(dice_card)
        d_layout.setAlignment(Qt.AlignCenter)
        d_layout.setSpacing(10)

        self.dice_widget = DiceWidget(dice_card)
        d_layout.addWidget(self.dice_widget, alignment=Qt.AlignCenter)

        self.btn_roll = QPushButton("🎲 Lempar Dadu", dice_card)
        self.btn_roll.setCursor(Qt.PointingHandCursor)
        self.btn_roll.setStyleSheet("""
            QPushButton {
                background: #E07A5F; color: white;
                font-weight: bold; font-size: 12px;
                border: none; border-radius: 8px; padding: 9px 18px;
            }
            QPushButton:hover { background: #C74A27; }
            QPushButton:disabled { background: #E6C8B8; color: #8A7264; }
        """)
        self.btn_roll.clicked.connect(self._on_player_roll_clicked)
        d_layout.addWidget(self.btn_roll)

        side_layout.addWidget(dice_card)

        # Tombol Game Baru
        self.btn_new = QPushButton("🔄 Mulai Ulang Permainan", self)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setStyleSheet("""
            QPushButton {
                background: #3D405B; color: white;
                font-weight: bold; font-size: 11px;
                border: none; border-radius: 6px; padding: 8px 12px;
            }
            QPushButton:hover { background: #2F3247; }
        """)
        self.btn_new.clicked.connect(self._start_new_game)
        side_layout.addWidget(self.btn_new)

        side_layout.addStretch()
        main_layout.addLayout(side_layout)

    def _start_new_game(self):
        self.player_pos = 1
        self.mimi_pos = 1
        self.board_widget.player_pos = 1
        self.board_widget.mimi_pos = 1
        self.board_widget.update()

        self.current_turn = "player"
        self.is_animating = False
        self.is_game_over = False

        self.lbl_turn.setText("🎯 Giliran: Tuan (Pemain)")
        self.lbl_turn.setStyleSheet("font-size: 12px; font-weight: bold; color: #2980B9;")
        self.lbl_player_pos.setText("👤 Posisi Tuan: Petak 1")
        self.lbl_mimi_pos.setText("🐱 Posisi Mimi: Petak 1")
        self.btn_roll.setEnabled(True)

        self.lbl_avatar.setText("🐱")
        self.chat_bubble.setText(f"Meow! Permainan baru dimulai dari Petak 1! Silakan lempar dadumu, Tuan! 🎲🐾")
        if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
            self.pet_parent.cat_audio.play_talk()

    def _on_player_roll_clicked(self):
        if self.is_animating or self.is_game_over or self.current_turn != "player":
            return
        self._start_dice_roll("player")

    def _start_dice_roll(self, who: str):
        if not self.isVisible() or self.is_game_over:
            return
        self.is_animating = True
        self.active_moving_pawn = who
        self.btn_roll.setEnabled(False)
        self.roll_ticks = 0
        self.dice_timer.start()

    def _on_dice_roll_tick(self):
        if not self.isVisible() or self.is_game_over:
            self.dice_timer.stop()
            return
        self.roll_ticks += 1
        random_val = random.randint(1, 6)
        self.dice_widget.set_value(random_val)

        if self.roll_ticks >= 9:
            self.dice_timer.stop()
            final_roll = random.randint(1, 6)
            self.dice_widget.set_value(final_roll)
            self._handle_dice_result(final_roll)

    def _handle_dice_result(self, roll: int):
        who = self.active_moving_pawn
        current_pos = self.player_pos if who == "player" else self.mimi_pos
        target_pos = min(100, current_pos + roll)
        self.step_target_tile = target_pos

        if who == "player":
            self.chat_bubble.setText(f"Tuan melempar dadu dan mendapatkan angka {roll}! Melangkah maju... 👣")
        else:
            self.chat_bubble.setText(f"Mimi melempar dadu dan dapat angka {roll}! Meowww! 🐾")

        if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
            self.pet_parent.cat_audio.play_chirp()

        # Mulai animasi jalan per petak
        self.step_timer.start()

    def _on_pawn_step_tick(self):
        if not self.isVisible() or self.is_game_over:
            self.step_timer.stop()
            return
        who = self.active_moving_pawn
        cur = self.player_pos if who == "player" else self.mimi_pos

        if cur < self.step_target_tile:
            cur += 1
            if who == "player":
                self.player_pos = cur
                self.board_widget.player_pos = cur
                self.lbl_player_pos.setText(f"👤 Posisi Tuan: Petak {cur}")
            else:
                self.mimi_pos = cur
                self.board_widget.mimi_pos = cur
                self.lbl_mimi_pos.setText(f"🐱 Posisi Mimi: Petak {cur}")
            self.board_widget.update()
        else:
            self.step_timer.stop()
            self._check_ladder_or_snake(cur, who)

    def _check_ladder_or_snake(self, cur_pos: int, who: str):
        # 1. Cek Tangga
        if cur_pos in LADDERS:
            target = LADDERS[cur_pos]
            if who == "player":
                self.player_pos = target
                self.board_widget.player_pos = target
                self.lbl_player_pos.setText(f"👤 Posisi Tuan: Petak {target}")
                self.chat_bubble.setText(f"HOREEE! 🚀 Tuan menemukan tangga dari {cur_pos} naik ke petak {target}! Hebat sekali! 😻")
            else:
                self.mimi_pos = target
                self.board_widget.mimi_pos = target
                self.lbl_mimi_pos.setText(f"🐱 Posisi Mimi: Petak {target}")
                self.chat_bubble.setText(f"Nyahaha! Mimi melompat naik tangga ke petak {target}! Kejar Mimi ya Tuan! 🐾✨")

            self.board_widget.update()
            if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                self.pet_parent.cat_audio.play_chirp()

        # 2. Cek Ular
        elif cur_pos in SNAKES:
            target = SNAKES[cur_pos]
            if who == "player":
                self.player_pos = target
                self.board_widget.player_pos = target
                self.lbl_player_pos.setText(f"👤 Posisi Tuan: Petak {target}")
                self.chat_bubble.setText(f"Aduuuh! 🐍 Tuan digigit ular di petak {cur_pos} dan meluncur turun ke petak {target}! Hati-hati ya Tuan! 🙀")
            else:
                self.mimi_pos = target
                self.board_widget.mimi_pos = target
                self.lbl_mimi_pos.setText(f"🐱 Posisi Mimi: Petak {target}")
                self.chat_bubble.setText(f"Meowww! Mimi terpeleset ular dan meluncur turun ke {target}! Huwaa! 😿")

            self.board_widget.update()
            if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                self.pet_parent.cat_audio.play_hiss()

        # Cek Kemenangan
        final_pos = self.player_pos if who == "player" else self.mimi_pos
        if final_pos >= 100:
            self._handle_game_over(who)
            return

        # Cek bonus lempar dadu angka 6
        last_roll = self.dice_widget.value
        if last_roll == 6:
            if who == "player":
                self.chat_bubble.setText(f"Angka 6! 🎲 Tuan mendapatkan bonus satu lemparan dadu lagi!")
                self.is_animating = False
                self.btn_roll.setEnabled(True)
                return
            else:
                self.chat_bubble.setText(f"Angka 6! Mimi melempar dadu lagi meowww!")
                QTimer.singleShot(900, lambda: self._start_dice_roll("mimi"))
                return

        # Ganti Giliran
        if who == "player":
            self.current_turn = "mimi"
            self.lbl_turn.setText(f"🎯 Giliran: {self.pet_name} (Kucing AI)")
            self.lbl_turn.setStyleSheet("font-size: 12px; font-weight: bold; color: #D35400;")
            self.is_animating = False
            # Mimi otomatis melempar dadu setelah jeda santai
            QTimer.singleShot(1100, lambda: self._start_dice_roll("mimi"))
        else:
            self.current_turn = "player"
            self.lbl_turn.setText("🎯 Giliran: Tuan (Pemain)")
            self.lbl_turn.setStyleSheet("font-size: 12px; font-weight: bold; color: #2980B9;")
            self.is_animating = False
            self.btn_roll.setEnabled(True)

    def _handle_game_over(self, winner: str):
        self.is_game_over = True
        self.is_animating = False
        self.btn_roll.setEnabled(False)

        if winner == "player":
            self.lbl_avatar.setText("😻")
            self.chat_bubble.setText("🎉 SELAMAT TUAN! Tuan sampai di Petak 100 dan memenangkan Ular Tangga! Mimi bangga sekali! 🏆🐾")
            if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                self.pet_parent.cat_audio.play_chirp()
        else:
            self.lbl_avatar.setText("😸")
            self.chat_bubble.setText("Nyahaha! Mimi berhasil mencapai Petak 100 duluan! Pertandingan yang seru sekali Tuan! Ayo tanding lagi! 🐾")
            if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                self.pet_parent.cat_audio.play_purr()

    def closeEvent(self, event):
        self.is_game_over = True
        self.is_animating = False
        if hasattr(self, "dice_timer") and self.dice_timer.isActive():
            self.dice_timer.stop()
        if hasattr(self, "step_timer") and self.step_timer.isActive():
            self.step_timer.stop()
        if self.pet_parent and hasattr(self.pet_parent, "on_game_closed"):
            self.pet_parent.on_game_closed(self)
        super().closeEvent(event)
