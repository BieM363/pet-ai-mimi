import os
import sys
import random
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)

try:
    from src.ui.markdown_helper import markdown_to_html
except ImportError:
    from ui.markdown_helper import markdown_to_html

# Definisi Bentuk & Warna 7 Tetromino Klasik
SHAPES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1],
          [1, 1]],
    'T': [[0, 1, 0],
          [1, 1, 1]],
    'S': [[0, 1, 1],
          [1, 1, 0]],
    'Z': [[1, 1, 0],
          [0, 1, 1]],
    'J': [[1, 0, 0],
          [1, 1, 1]],
    'L': [[0, 0, 1],
          [1, 1, 1]]
}

COLORS = {
    'I': QColor(0, 180, 216),    # Cyan
    'O': QColor(255, 190, 11),   # Kuning
    'T': QColor(157, 78, 221),   # Ungu
    'S': QColor(6, 214, 160),    # Hijau
    'Z': QColor(239, 71, 111),   # Merah
    'J': QColor(58, 134, 255),   # Biru
    'L': QColor(251, 86, 7)      # Oranye
}


class TetrisCanvas(QWidget):
    """Area gambar grid permainan Tetris (10 kolom x 20 baris)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cols = 10
        self.rows = 20
        self.block_size = 24
        self.setFixedSize(self.cols * self.block_size, self.rows * self.block_size)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        parent = self.parent()

        # 1. Gambar Latar Grid Gelap Hangat
        painter.fillRect(self.rect(), QColor(30, 24, 22))

        # Garis grid samar
        painter.setPen(QColor(48, 38, 35))
        for c in range(self.cols + 1):
            x = c * self.block_size
            painter.drawLine(x, 0, x, self.height())
        for r in range(self.rows + 1):
            y = r * self.block_size
            painter.drawLine(0, y, self.width(), y)

        if not parent:
            return

        # 2. Gambar Balok yang Sudah Terkunci di Papan
        for r in range(self.rows):
            for c in range(self.cols):
                shape_type = parent.board[r][c]
                if shape_type:
                    self._draw_block(painter, c, r, COLORS[shape_type])

        # 3. Gambar Ghost Piece (Bayangan Tempat Jatuh)
        if parent.current_piece and not parent.is_game_over:
            ghost_y = parent._get_ghost_y()
            ghost_color = QColor(COLORS[parent.current_piece_type])
            ghost_color.setAlpha(65)
            for r_idx, row in enumerate(parent.current_piece):
                for c_idx, val in enumerate(row):
                    if val:
                        self._draw_block(painter, parent.cur_x + c_idx, ghost_y + r_idx, ghost_color, is_ghost=True)

        # 4. Gambar Bidak Aktif yang Sedang Jatuh
        if parent.current_piece and not parent.is_game_over:
            color = COLORS[parent.current_piece_type]
            for r_idx, row in enumerate(parent.current_piece):
                for c_idx, val in enumerate(row):
                    if val:
                        self._draw_block(painter, parent.cur_x + c_idx, parent.cur_y + r_idx, color)

        # 5. Overlay Saat Game Over atau Pause
        if parent.is_game_over:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 185))
            painter.setPen(QColor(255, 230, 220))
            painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "GAME OVER!\n🐾")
        elif parent.is_paused:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
            painter.setPen(QColor(255, 230, 220))
            painter.setFont(QFont("Segoe UI", 15, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "PAUSED (Jeda)\nTekan 'P' untuk lanjut")

    def _draw_block(self, painter, c, r, color, is_ghost=False):
        """Menggambar kotak balok dengan efek 3D pixel bevel."""
        x = c * self.block_size
        y = r * self.block_size
        bs = self.block_size

        if is_ghost:
            painter.setPen(QPen(color, 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(x + 1, y + 1, bs - 2, bs - 2)
            return

        painter.fillRect(QRect(x, y, bs, bs), color)

        # Efek Bevel 3D Pixel
        painter.setPen(color.lighter(135))
        painter.drawLine(x, y, x + bs - 1, y)
        painter.drawLine(x, y, x, y + bs - 1)

        painter.setPen(color.darker(145))
        painter.drawLine(x + bs - 1, y, x + bs - 1, y + bs - 1)
        painter.drawLine(x, y + bs - 1, x + bs - 1, y + bs - 1)


class PiecePreviewWidget(QWidget):
    """Widget kecil untuk menampilkan preview balok berikutnya."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(96, 72)
        self.piece = None
        self.piece_type = None

    def set_piece(self, piece_type):
        self.piece_type = piece_type
        self.piece = SHAPES.get(piece_type, None)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(251, 244, 237))
        painter.setPen(QColor(232, 216, 200))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

        if not self.piece or not self.piece_type:
            return

        color = COLORS[self.piece_type]
        bs = 16
        p_rows = len(self.piece)
        p_cols = len(self.piece[0])
        start_x = (self.width() - p_cols * bs) // 2
        start_y = (self.height() - p_rows * bs) // 2

        for r_idx, row in enumerate(self.piece):
            for c_idx, val in enumerate(row):
                if val:
                    x = start_x + c_idx * bs
                    y = start_y + r_idx * bs
                    painter.fillRect(QRect(x, y, bs, bs), color)
                    painter.setPen(color.lighter(130))
                    painter.drawLine(x, y, x + bs - 1, y)
                    painter.drawLine(x, y, x, y + bs - 1)
                    painter.setPen(color.darker(140))
                    painter.drawLine(x + bs - 1, y, x + bs - 1, y + bs - 1)
                    painter.drawLine(x, y + bs - 1, x + bs - 1, y + bs - 1)


class MimiTetrisWindow(QDialog):
    """
    Jendela Game Tetris Mini interaktif bersama Mimi.
    - Kontrol Arrow Keys & Spasi
    - Peningkatan Level & Kecepatan
    - Celetukan kontekstual Mimi saat mencetak Tetris atau game over.
    """
    def __init__(self, pet_parent=None, pet_name="Mimi"):
        super().__init__(None, Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.pet_parent = pet_parent
        self.pet_name = pet_name

        self.setWindowTitle(f"🧱 Bermain Tetris bersama {self.pet_name}")
        self.setFixedSize(580, 550)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFDF9;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # Game State
        self.cols = 10
        self.rows = 20
        self.board = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.is_game_over = False
        self.is_paused = False

        self.current_piece = None
        self.current_piece_type = None
        self.cur_x = 0
        self.cur_y = 0
        self.next_piece_type = None

        self._init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._game_tick)

        self._start_new_game()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)

        # SISI KIRI: KANVAS TETRIS
        board_box = QVBoxLayout()
        self.canvas = TetrisCanvas(self)
        board_box.addWidget(self.canvas)

        lbl_controls = QLabel("⌨️ Panah: Geser & Putar | Spasi: Jatuh Cepat | P: Jeda", self)
        lbl_controls.setStyleSheet("font-size: 9.5px; color: #8A7264; margin-top: 4px;")
        board_box.addWidget(lbl_controls)
        main_layout.addLayout(board_box)

        # SISI KANAN: STATS & CELETUKAN MIMI
        side_layout = QVBoxLayout()
        side_layout.setSpacing(10)

        # Kartu Mimi & Celetukan
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
        lbl_name = QLabel(f"{self.pet_name} • Suporter Tetris", mimi_card)
        lbl_name.setStyleSheet("font-size: 11px; font-weight: bold; color: #D35400;")
        self.lbl_sub = QLabel("Menyemangati Tuan 🐾", mimi_card)
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
        self.chat_bubble.setText(f"Meow! Selamat datang di Tetris! Susun baloknya yang rapi ya Tuan! 🧱🐾")
        m_layout.addWidget(self.chat_bubble)
        side_layout.addWidget(mimi_card)

        # Kartu Stats & Next Piece
        stats_card = QFrame(self)
        stats_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EADDCF;
                border-radius: 10px;
                padding: 8px;
            }
        """)
        s_layout = QVBoxLayout(stats_card)
        s_layout.setSpacing(6)

        lbl_next = QLabel("Bidak Berikutnya:", stats_card)
        lbl_next.setStyleSheet("font-size: 10.5px; font-weight: bold; color: #4A3B32;")
        s_layout.addWidget(lbl_next)

        self.preview = PiecePreviewWidget(stats_card)
        s_layout.addWidget(self.preview, alignment=Qt.AlignCenter)

        # Skor & Level
        self.lbl_score = QLabel("🏆 Skor: 0", stats_card)
        self.lbl_score.setStyleSheet("font-size: 12px; font-weight: bold; color: #D35400;")
        s_layout.addWidget(self.lbl_score)

        self.lbl_lines = QLabel("📏 Baris: 0", stats_card)
        self.lbl_lines.setStyleSheet("font-size: 11px; color: #4A3B32;")
        s_layout.addWidget(self.lbl_lines)

        self.lbl_level = QLabel("⚡ Level: 1", stats_card)
        self.lbl_level.setStyleSheet("font-size: 11px; color: #4A3B32;")
        s_layout.addWidget(self.lbl_level)

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

        self.btn_pause = QPushButton("⏸️ Jeda (P)", self)
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
                self.pet_parent.cat_audio.play_talk()
            except Exception:
                pass

    def _start_new_game(self):
        self.board = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.is_game_over = False
        self.is_paused = False

        self._update_stats_display()
        self.next_piece_type = random.choice(list(SHAPES.keys()))
        self._spawn_piece()

        self._set_mimi_bubble("Meow! Game baru dimulai! Yuk susun baloknya setinggi-tingginya tanpa roboh! 🧱🐾")
        self.timer.start(500)
        self.canvas.setFocus()
        self.canvas.update()

    def _spawn_piece(self):
        self.current_piece_type = self.next_piece_type
        self.current_piece = [row[:] for row in SHAPES[self.current_piece_type]]
        self.next_piece_type = random.choice(list(SHAPES.keys()))
        self.preview.set_piece(self.next_piece_type)

        p_width = len(self.current_piece[0])
        self.cur_x = (self.cols - p_width) // 2
        self.cur_y = 0

        # Jika langsung tabrakan saat spawn -> Game Over!
        if self._check_collision(self.current_piece, self.cur_x, self.cur_y):
            self._trigger_game_over()

    def _get_ghost_y(self):
        ghost_y = self.cur_y
        while not self._check_collision(self.current_piece, self.cur_x, ghost_y + 1):
            ghost_y += 1
        return ghost_y

    def _check_collision(self, piece, x, y):
        for r_idx, row in enumerate(piece):
            for c_idx, val in enumerate(row):
                if val:
                    target_x = x + c_idx
                    target_y = y + r_idx
                    if target_x < 0 or target_x >= self.cols or target_y >= self.rows:
                        return True
                    if target_y >= 0 and self.board[target_y][target_x] is not None:
                        return True
        return False

    def _lock_piece(self):
        for r_idx, row in enumerate(self.current_piece):
            for c_idx, val in enumerate(row):
                if val:
                    target_y = self.cur_y + r_idx
                    target_x = self.cur_x + c_idx
                    if target_y >= 0:
                        self.board[target_y][target_x] = self.current_piece_type

        self._clear_lines()
        self._spawn_piece()
        self.canvas.update()

    def _clear_lines(self):
        new_board = [row for row in self.board if any(cell is None for cell in row)]
        cleared = self.rows - len(new_board)

        if cleared > 0:
            for _ in range(cleared):
                new_board.insert(0, [None for _ in range(self.cols)])
            self.board = new_board

            # Sistem Poin Klasik Tetris
            pts_map = {1: 100, 2: 300, 3: 500, 4: 800}
            pts = pts_map.get(cleared, cleared * 100) * self.level
            self.score += pts
            self.lines += cleared
            self.level = 1 + self.lines // 10

            self._update_stats_display()

            # Kecepatan makin bertambah seiring level
            new_interval = max(120, 500 - (self.level - 1) * 35)
            self.timer.setInterval(new_interval)

            if cleared == 4:
                self._set_mimi_bubble("🎉 *TETRIS!!* Meoww! 4 baris lenyap seketika! Tuan luar biasa jenius! 🏆✨🐾")
            elif cleared == 3:
                self._set_mimi_bubble("🔥 *TRIPLE!* Wuihh 3 baris bersih sekaligus! Lanjutkan Tuan! 🐾")
            else:
                self._set_mimi_bubble("✨ *Bagus Tuan!* Baloknya makin rapi dan luas lagi! Nyaa~ 🐾")

    def _trigger_game_over(self):
        self.is_game_over = True
        self.timer.stop()
        self._set_mimi_bubble(f"😿 *Game Over!* Baloknya sudah sampai atas, Tuan! Skor akhir: **{self.score}** (Baris: {self.lines})! Mau coba lagi? 🐾")
        self.canvas.update()

    def _toggle_pause(self):
        if self.is_game_over:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.timer.stop()
            self.btn_pause.setText("▶️ Lanjut (P)")
            self._set_mimi_bubble("⏸️ Permainan dijeda. Mimi tunggu Tuan santai dulu sebentar ya! ☕🐾")
        else:
            self.timer.start()
            self.btn_pause.setText("⏸️ Jeda (P)")
            self._set_mimi_bubble("▶️ Lanjut lagi! Fokus rapikan baloknya, Tuan! 🧱🐾")
        self.canvas.update()

    def _game_tick(self):
        if not self.isVisible() or self.is_game_over or self.is_paused:
            return
        if not self._check_collision(self.current_piece, self.cur_x, self.cur_y + 1):
            self.cur_y += 1
            self.canvas.update()
        else:
            self._lock_piece()

    def _update_stats_display(self):
        self.lbl_score.setText(f"🏆 Skor: {self.score}")
        self.lbl_lines.setText(f"📏 Baris: {self.lines}")
        self.lbl_level.setText(f"⚡ Level: {self.level}")

    def keyPressEvent(self, event):
        if self.is_game_over:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                self._start_new_game()
            return

        k = event.key()

        if k == Qt.Key_P:
            self._toggle_pause()
            return

        if self.is_paused:
            return

        if k == Qt.Key_Left:
            if not self._check_collision(self.current_piece, self.cur_x - 1, self.cur_y):
                self.cur_x -= 1
                self.canvas.update()
        elif k == Qt.Key_Right:
            if not self._check_collision(self.current_piece, self.cur_x + 1, self.cur_y):
                self.cur_x += 1
                self.canvas.update()
        elif k == Qt.Key_Down:
            if not self._check_collision(self.current_piece, self.cur_x, self.cur_y + 1):
                self.cur_y += 1
                self.score += 1
                self._update_stats_display()
                self.canvas.update()
        elif k == Qt.Key_Up:
            # Rotasi 90 derajat searah jarum jam
            rotated = [list(row) for row in zip(*self.current_piece[::-1])]
            # Wall Kick sederhana
            if not self._check_collision(rotated, self.cur_x, self.cur_y):
                self.current_piece = rotated
            elif not self._check_collision(rotated, self.cur_x - 1, self.cur_y):
                self.cur_x -= 1
                self.current_piece = rotated
            elif not self._check_collision(rotated, self.cur_x + 1, self.cur_y):
                self.cur_x += 1
                self.current_piece = rotated
            self.canvas.update()
        elif k == Qt.Key_Space:
            # Hard Drop: Langsung jatuh ke posisi ghost piece
            drop_dist = 0
            while not self._check_collision(self.current_piece, self.cur_x, self.cur_y + 1):
                self.cur_y += 1
                drop_dist += 1
            self.score += drop_dist * 2
            self._update_stats_display()
            self._lock_piece()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
        if self.pet_parent and hasattr(self.pet_parent, "on_game_closed"):
            self.pet_parent.on_game_closed(self)
        super().closeEvent(event)

