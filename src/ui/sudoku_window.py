# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import os
import sys
import random
import time
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame, QGridLayout, QMessageBox
)

try:
    from src.ui.markdown_helper import markdown_to_html
except ImportError:
    from ui.markdown_helper import markdown_to_html


def is_valid_placement(grid, row, col, num):
    """Memeriksa apakah num valid ditempatkan di grid[row][col]."""
    for c in range(9):
        if grid[row][c] == num:
            return False
    for r in range(9):
        if grid[r][col] == num:
            return False
    br = (row // 3) * 3
    bc = (col // 3) * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if grid[r][c] == num:
                return False
    return True


def solve_sudoku(grid):
    """Menyelesaikan sudoku dengan backtracking sederhana."""
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for num in nums:
                    if is_valid_placement(grid, r, col=c, num=num):
                        grid[r][c] = num
                        if solve_sudoku(grid):
                            return True
                        grid[r][c] = 0
                return False
    return True


def generate_sudoku(clues_count=32):
    """Menghasilkan board awal dan board solusi penuh."""
    board = [[0 for _ in range(9)] for _ in range(9)]
    # Isi blok diagonal utama (3 blok 3x3) yang saling independen
    for b in range(0, 9, 3):
        nums = list(range(1, 10))
        random.shuffle(nums)
        idx = 0
        for r in range(b, b + 3):
            for c in range(b, b + 3):
                board[r][c] = nums[idx]
                idx += 1

    # Selesaikan board untuk mendapatkan solusi valid acak
    solve_sudoku(board)
    solution = [row[:] for row in board]

    # Hapus angka untuk menghasilkan puzzle sesuai jumlah clue
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    to_remove = 81 - clues_count

    puzzle = [row[:] for row in solution]
    for i in range(to_remove):
        r, c = cells[i]
        puzzle[r][c] = 0

    return puzzle, solution


class SudokuBoardWidget(QWidget):
    """
    Widget visual papan Sudoku 9x9:
    - Ukuran presisi sel 48x48 px (total 432x432 px).
    - Sorotan sel aktif, angka sama, dan baris/kolom.
    - Menampilkan angka awal (clue), angka tebakan pemain, dan catatan kecil.
    """
    cell_clicked = pyqtSignal(int, int)
    cell_value_changed = pyqtSignal(int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cell_size = 48
        self.board_size = self.cell_size * 9
        self.setFixedSize(self.board_size, self.board_size)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)

        self.initial_puzzle = [[0 for _ in range(9)] for _ in range(9)]
        self.current_board = [[0 for _ in range(9)] for _ in range(9)]
        self.notes = [[set() for _ in range(9)] for _ in range(9)]
        self.selected_cell = (0, 0)
        self.pencil_mode = False
        self.conflict_cells = set()

    def set_puzzle(self, puzzle):
        self.initial_puzzle = [row[:] for row in puzzle]
        self.current_board = [row[:] for row in puzzle]
        self.notes = [[set() for _ in range(9)] for _ in range(9)]
        self.conflict_cells.clear()
        self.selected_cell = (0, 0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        cs = self.cell_size

        sel_r, sel_c = self.selected_cell
        sel_val = self.current_board[sel_r][sel_c] if (0 <= sel_r < 9 and 0 <= sel_c < 9) else 0

        # 1. Gambar latar belakang sel
        for r in range(9):
            for c in range(9):
                rect = QRect(c * cs, r * cs, cs, cs)
                is_sel = (r == sel_r and c == sel_c)
                is_initial = (self.initial_puzzle[r][c] != 0)
                val = self.current_board[r][c]
                is_conflict = (r, c) in self.conflict_cells

                if is_conflict:
                    bg = QColor(253, 237, 236)  # Merah lembut
                elif is_sel:
                    bg = QColor(248, 225, 212)  # Peach oranye Mimi
                elif val != 0 and val == sel_val:
                    bg = QColor(254, 243, 235)  # Sorotan angka yang sama
                elif r == sel_r or c == sel_c or (r // 3 == sel_r // 3 and c // 3 == sel_c // 3):
                    bg = QColor(255, 252, 247)  # Sorotan baris/kolom/blok
                elif is_initial:
                    bg = QColor(249, 244, 237)  # Kotak angka awal
                else:
                    bg = QColor(255, 255, 255)

                painter.fillRect(rect, bg)

        # 2. Gambar garis grid halus dan tebal (3x3)
        for i in range(10):
            pos = i * cs
            if i % 3 == 0:
                pen = QPen(QColor(141, 110, 99), 3)
            else:
                pen = QPen(QColor(228, 215, 201), 1)
            painter.setPen(pen)
            # Garis vertikal
            painter.drawLine(pos, 0, pos, self.board_size)
            # Garis horizontal
            painter.drawLine(0, pos, self.board_size, pos)

        # 3. Gambar angka & catatan
        font_initial = QFont("Segoe UI", 17, QFont.Bold)
        font_player = QFont("Segoe UI", 17, QFont.DemiBold)
        font_note = QFont("Segoe UI", 8)

        for r in range(9):
            for c in range(9):
                val = self.current_board[r][c]
                rect = QRect(c * cs, r * cs, cs, cs)

                if val != 0:
                    is_initial = (self.initial_puzzle[r][c] != 0)
                    is_conflict = (r, c) in self.conflict_cells

                    if is_conflict:
                        painter.setPen(QColor(192, 57, 43))
                        painter.setFont(font_player)
                    elif is_initial:
                        painter.setPen(QColor(45, 36, 36))
                        painter.setFont(font_initial)
                    else:
                        painter.setPen(QColor(211, 84, 0))  # Oranye Terracotta untuk langkah pemain
                        painter.setFont(font_player)

                    painter.drawText(rect, Qt.AlignCenter, str(val))
                elif self.notes[r][c]:
                    # Gambar catatan kecil 1-9
                    painter.setFont(font_note)
                    painter.setPen(QColor(140, 123, 112))
                    note_set = self.notes[r][c]
                    sub_s = cs / 3
                    for n in range(1, 10):
                        if n in note_set:
                            sub_r = (n - 1) // 3
                            sub_c = (n - 1) % 3
                            sub_rect = QRect(int(c * cs + sub_c * sub_s), int(r * cs + sub_r * sub_s), int(sub_s), int(sub_s))
                            painter.drawText(sub_rect, Qt.AlignCenter, str(n))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            c = int(event.x() // self.cell_size)
            r = int(event.y() // self.cell_size)
            if 0 <= r < 9 and 0 <= c < 9:
                self.selected_cell = (r, c)
                self.cell_clicked.emit(r, c)
                self.update()

    def keyPressEvent(self, event):
        k = event.key()
        r, c = self.selected_cell

        # Navigasi keyboard
        if k == Qt.Key_Up:
            self.selected_cell = ((r - 1) % 9, c)
            self.update()
            return
        elif k == Qt.Key_Down:
            self.selected_cell = ((r + 1) % 9, c)
            self.update()
            return
        elif k == Qt.Key_Left:
            self.selected_cell = (r, (c - 1) % 9)
            self.update()
            return
        elif k == Qt.Key_Right:
            self.selected_cell = (r, (c + 1) % 9)
            self.update()
            return

        # Input angka
        if Qt.Key_1 <= k <= Qt.Key_9:
            num = k - Qt.Key_0
            self.apply_number(num)
        elif k in (Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_0):
            self.clear_current_cell()
        else:
            super().keyPressEvent(event)

    def apply_number(self, num: int):
        r, c = self.selected_cell
        if self.initial_puzzle[r][c] != 0:
            return  # Kotak bawaan tidak dapat diedit

        if self.pencil_mode:
            # Toggle catatan
            if num in self.notes[r][c]:
                self.notes[r][c].remove(num)
            else:
                self.notes[r][c].add(num)
        else:
            # Set nilai
            if self.current_board[r][c] == num:
                self.current_board[r][c] = 0  # Toggle off
            else:
                self.current_board[r][c] = num
                self.notes[r][c].clear()
            self.cell_value_changed.emit(r, c, self.current_board[r][c])

        self.update()

    def clear_current_cell(self):
        r, c = self.selected_cell
        if self.initial_puzzle[r][c] == 0:
            self.current_board[r][c] = 0
            self.notes[r][c].clear()
            self.conflict_cells.discard((r, c))
            self.cell_value_changed.emit(r, c, 0)
            self.update()


class MimiSudokuWindow(QDialog):
    """
    Jendela Game Sudoku Interaktif bersama Kucing Mimi AI:
    - 3 Tingkat Kesulitan: Mudah (~38 clue), Sedang (~30 clue), Sulit (~24 clue).
    - Tombol Bantuan Mimi (Hint), Pemeriksa Kesalahan, dan Mode Catatan Pensil.
    - Celetukan dan pendampingan interaktif dari Mimi.
    """
    def __init__(self, pet_parent=None, pet_name="Mimi", default_difficulty="Sedang"):
        super().__init__(None, Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.pet_parent = pet_parent
        self.pet_name = pet_name
        self.difficulty = default_difficulty

        self.setWindowTitle(f"🧩 Bermain Sudoku bersama {self.pet_name}")
        self.setFixedSize(770, 525)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFDF9;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        self.puzzle = []
        self.solution = []
        self.start_time = time.time()
        self.is_completed = False

        self._init_ui()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update_timer)
        self.timer.start()

        self._start_new_game(self.difficulty)

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # SISI KIRI: PAPAN SUDOKU (432x432 px)
        board_box = QVBoxLayout()
        board_box.setSpacing(8)

        self.board_widget = SudokuBoardWidget(self)
        self.board_widget.cell_clicked.connect(self._on_cell_clicked)
        self.board_widget.cell_value_changed.connect(self._on_cell_value_changed)
        board_box.addWidget(self.board_widget)

        lbl_controls = QLabel("⌨️ Panah: Pindah Sel | 1-9: Isi Angka | Del/Backspace: Hapus", self)
        lbl_controls.setAlignment(Qt.AlignCenter)
        lbl_controls.setStyleSheet("font-size: 10px; color: #8A7264; padding: 2px;")
        board_box.addWidget(lbl_controls)

        main_layout.addLayout(board_box)

        # SISI KANAN: KARTU MIMI, KEYPAD, & KONTROL
        side_layout = QVBoxLayout()
        side_layout.setSpacing(8)

        # 1. Kartu Pendamping Mimi
        mimi_card = QFrame(self)
        mimi_card.setStyleSheet("""
            QFrame {
                background: #FBF4ED;
                border: 1.5px solid #E8D8C8;
                border-radius: 12px;
            }
        """)
        m_layout = QVBoxLayout(mimi_card)
        m_layout.setContentsMargins(10, 8, 10, 8)
        m_layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        self.lbl_avatar = QLabel("🐱", mimi_card)
        self.lbl_avatar.setStyleSheet("""
            background: #FFFDF9;
            border: 1px solid #E8D8C8;
            border-radius: 16px;
            font-size: 20px;
            padding: 2px 6px;
        """)
        header_row.addWidget(self.lbl_avatar)

        name_box = QVBoxLayout()
        name_box.setSpacing(1)
        lbl_name = QLabel(f"{self.pet_name} • Ahli Sudoku", mimi_card)
        lbl_name.setStyleSheet("font-size: 11.5px; font-weight: bold; color: #D35400; border: none; background: transparent;")
        self.lbl_sub = QLabel("Menganalisis teka-teki logika 🐾", mimi_card)
        self.lbl_sub.setStyleSheet("font-size: 9.5px; color: #7B6858; border: none; background: transparent;")
        name_box.addWidget(lbl_name)
        name_box.addWidget(self.lbl_sub)
        header_row.addLayout(name_box)
        header_row.addStretch()
        m_layout.addLayout(header_row)

        self.chat_bubble = QLabel(mimi_card)
        self.chat_bubble.setWordWrap(True)
        self.chat_bubble.setMinimumHeight(42)
        self.chat_bubble.setStyleSheet("""
            QLabel {
                background: #FFFFFF;
                border: 1px solid #E0CDBC;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 10.5px;
                color: #2D2424;
                line-height: 130%;
            }
        """)
        self.chat_bubble.setText(f"Meow! Mari latih logika bersama Mimi! Pilih angka 1 sampai 9 ya Tuan! 🐾🧩")
        m_layout.addWidget(self.chat_bubble)
        side_layout.addWidget(mimi_card)

        # 2. Panel Info (Timer & Kesulitan)
        info_card = QFrame(self)
        info_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EADDCF;
                border-radius: 10px;
            }
        """)
        info_layout = QHBoxLayout(info_card)
        info_layout.setContentsMargins(10, 6, 10, 6)

        self.lbl_timer = QLabel("⏱️ 00:00", info_card)
        self.lbl_timer.setStyleSheet("font-size: 12.5px; font-weight: bold; color: #3D405B; border: none;")
        info_layout.addWidget(self.lbl_timer)
        info_layout.addStretch()

        self.combo_diff = QComboBox(info_card)
        self.combo_diff.addItem("🟢 Mudah")
        self.combo_diff.addItem("🟡 Sedang")
        self.combo_diff.addItem("🔴 Sulit")
        diff_idx = 0 if self.difficulty == "Mudah" else (2 if self.difficulty == "Sulit" else 1)
        self.combo_diff.setCurrentIndex(diff_idx)
        self.combo_diff.setStyleSheet("""
            QComboBox {
                background: #FFFDF9; border: 1.5px solid #E07A5F;
                border-radius: 6px; padding: 3px 10px; font-size: 11px;
                font-weight: bold; color: #2D2424;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.combo_diff.currentIndexChanged.connect(self._on_diff_changed)
        info_layout.addWidget(self.combo_diff)
        side_layout.addWidget(info_card)

        # 3. Keypad Angka 1-9 Rapi (Grid 3x3 Standar Sudoku)
        keypad_card = QFrame(self)
        keypad_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EADDCF;
                border-radius: 12px;
            }
        """)
        keypad_vbox = QVBoxLayout(keypad_card)
        keypad_vbox.setContentsMargins(10, 8, 10, 8)
        keypad_vbox.setSpacing(6)

        lbl_kp_title = QLabel("🔢 Papan Angka", keypad_card)
        lbl_kp_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #8A7264; border: none;")
        keypad_vbox.addWidget(lbl_kp_title)

        grid_keypad = QGridLayout()
        grid_keypad.setSpacing(6)

        # 9 Tombol Angka (3x3 Grid: 1-9 lengkap tanpa tertimpa)
        btn_num_style = """
            QPushButton {
                background: #FAF0E6; color: #2D2424;
                font-weight: bold; font-size: 14px;
                border: 1.5px solid #D8C3A5; border-radius: 8px;
                min-height: 34px;
            }
            QPushButton:hover { background: #F8E1D4; color: #8E3B20; border-color: #E07A5F; }
            QPushButton:pressed { background: #E07A5F; color: white; }
        """
        for i in range(1, 10):
            btn = QPushButton(str(i), keypad_card)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(btn_num_style)
            btn.clicked.connect(lambda _, n=i: self.board_widget.apply_number(n))
            row = (i - 1) // 3
            col = (i - 1) % 3
            grid_keypad.addWidget(btn, row, col)

        keypad_vbox.addLayout(grid_keypad)

        # Baris Tombol Utilitas (Hapus & Catatan Pensil)
        util_row = QHBoxLayout()
        util_row.setSpacing(6)

        btn_clear = QPushButton("⌫ Hapus (Del)", keypad_card)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet("""
            QPushButton {
                background: #FDEBD0; color: #9C5221;
                font-size: 11px; font-weight: bold;
                border: 1.5px solid #F5CBA7; border-radius: 8px;
                min-height: 32px; padding: 4px 8px;
            }
            QPushButton:hover { background: #FAD7A0; border-color: #E67E22; color: #78340F; }
            QPushButton:pressed { background: #E67E22; color: white; }
        """)
        btn_clear.clicked.connect(self.board_widget.clear_current_cell)
        util_row.addWidget(btn_clear, 1)

        self.btn_pencil = QPushButton("✏️ Catatan: OFF", keypad_card)
        self.btn_pencil.setCursor(Qt.PointingHandCursor)
        self.btn_pencil.setStyleSheet("""
            QPushButton {
                background: #F4F1EA; color: #6D594F;
                font-size: 11px; font-weight: bold;
                border: 1.5px solid #D8C3A5; border-radius: 8px;
                min-height: 32px; padding: 4px 8px;
            }
            QPushButton:hover { background: #EAE5DC; }
        """)
        self.btn_pencil.clicked.connect(self._toggle_pencil)
        util_row.addWidget(self.btn_pencil, 1)

        keypad_vbox.addLayout(util_row)
        side_layout.addWidget(keypad_card)

        # 4. Baris Tombol Aksi (Bantuan, Cek, Baru)
        action_row = QHBoxLayout()
        action_row.setSpacing(6)

        self.btn_hint = QPushButton("💡 Bantuan", self)
        self.btn_hint.setCursor(Qt.PointingHandCursor)
        self.btn_hint.setStyleSheet("""
            QPushButton {
                background: #81B29A; color: white;
                font-weight: bold; font-size: 11px;
                border: none; border-radius: 8px; min-height: 34px; padding: 6px 10px;
            }
            QPushButton:hover { background: #699881; }
            QPushButton:pressed { background: #527A67; }
        """)
        self.btn_hint.clicked.connect(self._action_hint)
        action_row.addWidget(self.btn_hint, 1)

        self.btn_check = QPushButton("🔍 Cek Papan", self)
        self.btn_check.setCursor(Qt.PointingHandCursor)
        self.btn_check.setStyleSheet("""
            QPushButton {
                background: #3D405B; color: white;
                font-weight: bold; font-size: 11px;
                border: none; border-radius: 8px; min-height: 34px; padding: 6px 10px;
            }
            QPushButton:hover { background: #2F3247; }
            QPushButton:pressed { background: #212332; }
        """)
        self.btn_check.clicked.connect(self._action_check)
        action_row.addWidget(self.btn_check, 1)

        self.btn_new = QPushButton("🔄 Baru", self)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setStyleSheet("""
            QPushButton {
                background: #E07A5F; color: white;
                font-weight: bold; font-size: 11px;
                border: none; border-radius: 8px; min-height: 34px; padding: 6px 10px;
            }
            QPushButton:hover { background: #C74A27; }
            QPushButton:pressed { background: #A33B1E; }
        """)
        self.btn_new.clicked.connect(lambda: self._start_new_game(self.difficulty))
        action_row.addWidget(self.btn_new, 1)

        side_layout.addLayout(action_row)

        main_layout.addLayout(side_layout)

    def _start_new_game(self, diff_name: str):
        self.difficulty = diff_name
        clues = 38 if diff_name == "Mudah" else (24 if diff_name == "Sulit" else 30)
        self.puzzle, self.solution = generate_sudoku(clues_count=clues)
        self.board_widget.set_puzzle(self.puzzle)
        self.start_time = time.time()
        self.is_completed = False
        self.lbl_avatar.setText("🐱")
        self.chat_bubble.setText(f"Meow! Teka-teki Sudoku {diff_name} sudah siap! Selamat berpikir cerdas, Tuan! 🐾🧩")
        if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
            self.pet_parent.cat_audio.play_talk()

    def _update_timer(self):
        if not self.isVisible() or self.is_completed:
            return
        elapsed = int(time.time() - self.start_time)
        m = elapsed // 60
        s = elapsed % 60
        self.lbl_timer.setText(f"⏱️ {m:02d}:{s:02d}")

    def _toggle_pencil(self):
        self.board_widget.pencil_mode = not self.board_widget.pencil_mode
        if self.board_widget.pencil_mode:
            self.btn_pencil.setText("✏️ Catatan: ON")
            self.btn_pencil.setStyleSheet("""
                QPushButton {
                    background: #E07A5F; color: white;
                    font-size: 10px; font-weight: bold;
                    border: 1px solid #C74A27; border-radius: 6px; padding: 4px;
                }
            """)
        else:
            self.btn_pencil.setText("✏️ Catatan: OFF")
            self.btn_pencil.setStyleSheet("""
                QPushButton {
                    background: #F4F1EA; color: #6D594F;
                    font-size: 10px; font-weight: bold;
                    border: 1px solid #D8C3A5; border-radius: 6px; padding: 4px;
                }
            """)

    def _on_diff_changed(self, idx):
        diff_names = ["Mudah", "Sedang", "Sulit"]
        if 0 <= idx < len(diff_names):
            self._start_new_game(diff_names[idx])

    def _on_cell_clicked(self, r, c):
        pass

    def _safe_play_audio(self, sound_name: str):
        """Memutar efek suara kucing secara aman tanpa risiko crash jika method tidak tersedia."""
        if not self.pet_parent or not hasattr(self.pet_parent, "cat_audio"):
            return
        ca = self.pet_parent.cat_audio
        fn = getattr(ca, sound_name, None)
        if callable(fn):
            try:
                fn()
                return
            except Exception:
                pass
        for alt in ["play_chirp", "play_talk"]:
            alt_fn = getattr(ca, alt, None)
            if callable(alt_fn):
                try:
                    alt_fn()
                    return
                except Exception:
                    pass

    def _on_cell_value_changed(self, r, c, val):
        self.board_widget.conflict_cells.clear()
        if val == 0:
            return

        # Cek apakah ada konflik langsung
        conflicts = set()
        for col in range(9):
            if col != c and self.board_widget.current_board[r][col] == val:
                conflicts.add((r, col))
                conflicts.add((r, c))
        for row in range(9):
            if row != r and self.board_widget.current_board[row][c] == val:
                conflicts.add((row, c))
                conflicts.add((r, c))
        br = (r // 3) * 3
        bc = (c // 3) * 3
        for row in range(br, br + 3):
            for col in range(bc, bc + 3):
                if (row, col) != (r, c) and self.board_widget.current_board[row][col] == val:
                    conflicts.add((row, col))
                    conflicts.add((r, c))

        if conflicts:
            self.board_widget.conflict_cells = conflicts
            self.lbl_avatar.setText("🙀")
            self.chat_bubble.setText(f"Aduh Tuan! Angka {val} bertabrakan dengan kotak lain di baris/kolom/blok ini! 🐾")
            self._safe_play_audio("play_hiss")
        else:
            self.lbl_avatar.setText("😸")
            self._check_completion()

    def _action_hint(self):
        """Mimi memberikan satu angka yang benar pada kotak kosong atau salah."""
        if self.is_completed:
            return

        empty_cells = []
        for r in range(9):
            for c in range(9):
                if self.board_widget.current_board[r][c] != self.solution[r][c]:
                    empty_cells.append((r, c))

        if not empty_cells:
            self._check_completion()
            return

        # Pilih kotak secara acak
        r, c = random.choice(empty_cells)
        correct_val = self.solution[r][c]
        self.board_widget.current_board[r][c] = correct_val
        self.board_widget.notes[r][c].clear()
        self.board_widget.conflict_cells.discard((r, c))
        self.board_widget.selected_cell = (r, c)
        self.board_widget.update()

        self.lbl_avatar.setText("😻")
        self.chat_bubble.setText(f"Meow! Mimi bantu intip satu kotak! Baris {r+1} Kolom {c+1} isinya {correct_val}! Semangat Tuan! 💡🐾")
        self._safe_play_audio("play_chirp")

        self._check_completion()

    def _action_check(self):
        """Memeriksa semua sel yang sudah terisi apakah sesuai solusi."""
        errors = 0
        conflicts = set()
        for r in range(9):
            for c in range(9):
                val = self.board_widget.current_board[r][c]
                if val != 0 and val != self.solution[r][c]:
                    conflicts.add((r, c))
                    errors += 1

        self.board_widget.conflict_cells = conflicts
        self.board_widget.update()

        if errors > 0:
            self.lbl_avatar.setText("🙀")
            self.chat_bubble.setText(f"Meow! Mimi menemukan {errors} kotak yang belum tepat (kotak berlatar merah). Jangan menyerah ya Tuan! 🐾")
            self._safe_play_audio("play_hiss")
        else:
            self.lbl_avatar.setText("😸")
            self.chat_bubble.setText("Meow! Semua angka yang sudah Tuan isi sejauh ini 100% benar dan tepat! Mantap! 🐾✨")
            self._safe_play_audio("play_purr")
            self._check_completion()

    def _check_completion(self):
        for r in range(9):
            for c in range(9):
                if self.board_widget.current_board[r][c] != self.solution[r][c]:
                    return

        self.is_completed = True
        self.lbl_avatar.setText("😻")
        elapsed = int(time.time() - self.start_time)
        m = elapsed // 60
        s = elapsed % 60
        self.chat_bubble.setText(f"🎉 HOREEE! Tuan berhasil menuntaskan Sudoku dalam waktu {m} menit {s} detik! Otak Tuan sangat jenius! 🏆🐾")
        self._safe_play_audio("play_happy")

    def closeEvent(self, event):
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
        if self.pet_parent and hasattr(self.pet_parent, "on_game_closed"):
            self.pet_parent.on_game_closed(self)
        super().closeEvent(event)
