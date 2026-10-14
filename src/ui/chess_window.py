import os
import sys
import threading
import chess
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal, QObject, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QFrame, QMessageBox, QSplitter
)

try:
    from src.core.chess_engine import MimiChessEngine
    from src.ui.markdown_helper import markdown_to_html
except ImportError:
    from core.chess_engine import MimiChessEngine
    from ui.markdown_helper import markdown_to_html


# Peta simbol Unicode untuk Bidak Catur
PIECE_UNICODE = {
    chess.PAWN: {"white": "♙", "black": "♟"},
    chess.KNIGHT: {"white": "♘", "black": "♞"},
    chess.BISHOP: {"white": "♗", "black": "♝"},
    chess.ROOK: {"white": "♖", "black": "♜"},
    chess.QUEEN: {"white": "♕", "black": "♛"},
    chess.KING: {"white": "♔", "black": "♚"}
}

class AIMoveBridge(QObject):
    """Bridge Qt thread-safe untuk mengalirkan langkah AI Mimi ke GUI thread."""
    sig_move_ready = pyqtSignal(object, str)


class ChessBoardWidget(QWidget):
    """
    Widget Papan Catur 8x8 Kustom:
    - Palet kayu krem & coklat hangat serasi dengan tema Mimi
    - Sorotan kotak langkah terakhir, kotak terpilih, dan langkah legal
    - Render bidak catur yang tajam dengan bayangan & kontras tinggi
    """
    square_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = chess.Board()
        self.flipped = False  # False = Putih di bawah, True = Hitam di bawah
        self.selected_square = None
        self.legal_targets = []
        self.last_move = None
        self.setMinimumSize(420, 420)
        self.setCursor(Qt.PointingHandCursor)

    def set_board(self, board, flipped=False):
        self.board = board
        self.flipped = flipped
        self.selected_square = None
        self.legal_targets = []
        self.update()

    def set_last_move(self, move):
        self.last_move = move
        self.update()

    def select_square(self, sq):
        self.selected_square = sq
        if sq is not None:
            self.legal_targets = [m.to_square for m in self.board.legal_moves if m.from_square == sq]
        else:
            self.legal_targets = []
        self.update()

    def square_to_coord(self, square):
        """Mengonversi chess.Square (0-63) menjadi koordinat visual (col, row)."""
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)
        if not self.flipped:
            col = file_idx
            row = 7 - rank_idx
        else:
            col = 7 - file_idx
            row = rank_idx
        return col, row

    def coord_to_square(self, col, row):
        """Mengonversi koordinat visual (col, row) menjadi chess.Square (0-63)."""
        if col < 0 or col > 7 or row < 0 or row > 7:
            return None
        if not self.flipped:
            file_idx = col
            rank_idx = 7 - row
        else:
            file_idx = 7 - col
            rank_idx = row
        return chess.square(file_idx, rank_idx)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            sq_size = min(self.width(), self.height()) / 8.0
            col = int(event.x() // sq_size)
            row = int(event.y() // sq_size)
            sq = self.coord_to_square(col, row)
            if sq is not None:
                self.square_clicked.emit(sq)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        sq_size = min(self.width(), self.height()) / 8.0

        # Palet Warna Papan Kayu Hangat
        color_light = QColor(248, 237, 222)   # Krem hangat
        color_dark = QColor(196, 143, 98)     # Kayu walnut hangat
        color_select = QColor(244, 162, 97, 180)  # Oranye terpilih
        color_last = QColor(233, 196, 106, 140)   # Kuning keemasan langkah terakhir
        color_check = QColor(230, 57, 70, 160)    # Merah skak

        king_in_check_sq = None
        if self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            king_in_check_sq = king_sq

        # 1. Gambar Petak-Petak Catur
        for row in range(8):
            for col in range(8):
                sq = self.coord_to_square(col, row)
                rect = QRect(int(col * sq_size), int(row * sq_size), int(sq_size + 1), int(sq_size + 1))

                is_light = ((row + col) % 2 == 0)
                base_color = color_light if is_light else color_dark
                painter.fillRect(rect, base_color)

                # Highlight langkah terakhir
                if self.last_move and sq in (self.last_move.from_square, self.last_move.to_square):
                    painter.fillRect(rect, color_last)

                # Highlight petak yang sedang dipilih
                if sq == self.selected_square:
                    painter.fillRect(rect, color_select)

                # Highlight raja jika sedang skak
                if sq == king_in_check_sq:
                    painter.fillRect(rect, color_check)

        # 2. Gambar Indikator Langkah Legal
        for sq in self.legal_targets:
            col, row = self.square_to_coord(sq)
            cx = int(col * sq_size + sq_size / 2)
            cy = int(row * sq_size + sq_size / 2)
            dest_piece = self.board.piece_at(sq)

            if dest_piece:
                # Target memakan bidak: lingkaran cincin merah-oranye
                painter.setPen(QPen(QColor(218, 53, 32, 210), 3.5))
                painter.setBrush(Qt.NoBrush)
                rad = int(sq_size * 0.42)
                painter.drawEllipse(QPoint(cx, cy), rad, rad)
            else:
                # Petak kosong yang legal: titik bulat di tengah
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(142, 68, 40, 160)))
                rad = int(sq_size * 0.16)
                painter.drawEllipse(QPoint(cx, cy), rad, rad)

        # 3. Gambar Koordinat Tepi (a-h, 1-8)
        coord_font = QFont("Segoe UI", int(sq_size * 0.16), QFont.Bold)
        painter.setFont(coord_font)
        for i in range(8):
            # Huruf kolom (di baris paling bawah)
            file_char = chr(ord('h') - i) if self.flipped else chr(ord('a') + i)
            c_color = color_dark if (i % 2 == 0) else color_light
            painter.setPen(c_color)
            painter.drawText(
                QRect(int(i * sq_size + 3), int(7 * sq_size + sq_size - 18), int(sq_size), 16),
                Qt.AlignLeft | Qt.AlignBottom, file_char
            )

            # Angka baris (di kolom paling kiri)
            rank_num = str(i + 1) if self.flipped else str(8 - i)
            r_color = color_dark if (i % 2 == 1) else color_light
            painter.setPen(r_color)
            painter.drawText(
                QRect(int(3), int(i * sq_size + 2), int(sq_size), 16),
                Qt.AlignLeft | Qt.AlignTop, rank_num
            )

        # 4. Gambar Bidak Catur
        piece_font = QFont("Segoe UI Symbol", int(sq_size * 0.62))
        painter.setFont(piece_font)

        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if not piece:
                continue

            col, row = self.square_to_coord(sq)
            rect = QRect(int(col * sq_size), int(row * sq_size) - 2, int(sq_size), int(sq_size))

            is_white = (piece.color == chess.WHITE)
            glyph = PIECE_UNICODE[piece.piece_type]["white" if is_white else "black"]

            # Gambar bayangan bidak agar kontras di petak gelap/terang
            painter.setPen(QColor(20, 15, 10, 140))
            shadow_rect = QRect(rect.x() + 1, rect.y() + 2, rect.width(), rect.height())
            painter.drawText(shadow_rect, Qt.AlignCenter, glyph)

            # Gambar warna utama bidak
            if is_white:
                painter.setPen(QColor(255, 253, 248))
            else:
                painter.setPen(QColor(36, 24, 20))

            painter.drawText(rect, Qt.AlignCenter, glyph)


class MimiChessWindow(QDialog):
    """
    Jendela Game Catur Interaktif melawan Kucing Mimi AI.
    - 3 Tingkat Kesulitan: Mudah (Anak Kucing), Normal (Cerdik), Sulit (Master).
    - Desain premium tema kayu hangat & aksen terracotta.
    - Mimi memberikan dialog dan celetukan langsung di panel samping.
    """
    def __init__(self, pet_parent=None, pet_name="Mimi", default_difficulty="Normal"):
        super().__init__(None, Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.pet_parent = pet_parent
        self.pet_name = pet_name
        self.difficulty = default_difficulty
        self.engine = MimiChessEngine(pet_name=pet_name)

        self.board = chess.Board()
        self.player_is_white = True
        self.is_ai_thinking = False
        self.selected_sq = None

        self.ai_bridge = AIMoveBridge()
        self.ai_bridge.sig_move_ready.connect(self._on_ai_move_ready)

        self.setAttribute(Qt.WA_QuitOnClose, False)
        self._is_closed = False

        self.setWindowTitle(f"♟️ Bermain Catur bersama {self.pet_name}")
        self.setFixedSize(760, 560)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFDF9;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        self._init_ui()
        self._start_new_game(self.difficulty)

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)

        # 1. SISI KIRI: PAPAN CATUR
        board_container = QVBoxLayout()
        board_container.setSpacing(8)

        self.board_widget = ChessBoardWidget(self)
        self.board_widget.square_clicked.connect(self._on_square_clicked)
        board_container.addWidget(self.board_widget)

        # Status Bar di Bawah Papan
        self.status_label = QLabel("Giliranmu, Tuan! Silakan melangkah.", self)
        self.status_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #8E3B20;")
        board_container.addWidget(self.status_label)

        main_layout.addLayout(board_container, stretch=3)

        # 2. SISI KANAN: PANEL KONTROL & CELETUKAN MIMI
        side_panel = QVBoxLayout()
        side_panel.setSpacing(12)

        # Kartu Mimi & Dialog
        mimi_card = QFrame(self)
        mimi_card.setStyleSheet("""
            QFrame {
                background: #FBF4ED;
                border: 1.5px solid #E8D8C8;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        mimi_card_layout = QVBoxLayout(mimi_card)
        mimi_card_layout.setContentsMargins(10, 10, 10, 10)
        mimi_card_layout.setSpacing(8)

        # Header Mimi
        mimi_header = QHBoxLayout()
        self.avatar_label = QLabel("🐱", mimi_card)
        self.avatar_label.setStyleSheet("font-size: 26px;")
        mimi_header.addWidget(self.avatar_label)

        mimi_info = QVBoxLayout()
        self.lbl_mimi_name = QLabel(f"{self.pet_name} • Lawan Catur", mimi_card)
        self.lbl_mimi_name.setStyleSheet("font-size: 12px; font-weight: bold; color: #D35400;")
        self.lbl_mimi_status = QLabel("Siap melangkah 🐾", mimi_card)
        self.lbl_mimi_status.setStyleSheet("font-size: 10px; color: #7B6858;")
        mimi_info.addWidget(self.lbl_mimi_name)
        mimi_info.addWidget(self.lbl_mimi_status)
        mimi_header.addLayout(mimi_info)
        mimi_header.addStretch()
        mimi_card_layout.addLayout(mimi_header)

        # Balon Dialog Celetukan Mimi di dalam Catur
        self.chat_bubble = QLabel(mimi_card)
        self.chat_bubble.setWordWrap(True)
        self.chat_bubble.setStyleSheet("""
            QLabel {
                background: #FFFFFF;
                border: 1px solid #E0CDBC;
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 11px;
                color: #2D2424;
                line-height: 135%;
            }
        """)
        self.chat_bubble.setText(f"Meow! Selamat datang di papan catur, Tuan! Pilih mode kesulitan dan ayo mulai! 🐾")
        mimi_card_layout.addWidget(self.chat_bubble)

        side_panel.addWidget(mimi_card)

        # Pengaturan Mode & Sisi
        control_frame = QFrame(self)
        control_frame.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EADDCF;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        ctrl_layout = QVBoxLayout(control_frame)
        ctrl_layout.setSpacing(8)

        lbl_diff = QLabel("🎯 Tingkat Kesulitan AI Mimi:", control_frame)
        lbl_diff.setStyleSheet("font-size: 11px; font-weight: bold; color: #4A3B32;")
        ctrl_layout.addWidget(lbl_diff)

        self.combo_diff = QComboBox(control_frame)
        self.combo_diff.addItem("🟢 Mudah (Anak Kucing Santai)", "Mudah")
        self.combo_diff.addItem("🟡 Normal (Kucing Cerdik)", "Normal")
        self.combo_diff.addItem("🔴 Sulit (Kucing Master)", "Sulit")
        
        # Set default
        idx = 1 if self.difficulty == "Normal" else (0 if self.difficulty == "Mudah" else 2)
        self.combo_diff.setCurrentIndex(idx)
        self.combo_diff.setStyleSheet("""
            QComboBox {
                background: #FFFDF9;
                border: 1.5px solid #E07A5F;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                color: #2D2424;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.combo_diff.currentIndexChanged.connect(self._on_difficulty_changed)
        ctrl_layout.addWidget(self.combo_diff)

        # Tombol-tombol Game
        btn_layout = QHBoxLayout()
        self.btn_new_game = QPushButton("🔄 Game Baru", control_frame)
        self.btn_new_game.setCursor(Qt.PointingHandCursor)
        self.btn_new_game.setStyleSheet("""
            QPushButton {
                background: #E07A5F; color: white;
                font-weight: bold; font-size: 10.5px;
                border: none; border-radius: 6px; padding: 6px 12px;
            }
            QPushButton:hover { background: #C74A27; }
        """)
        self.btn_new_game.clicked.connect(lambda: self._start_new_game(self.combo_diff.currentData()))
        btn_layout.addWidget(self.btn_new_game)

        self.btn_flip = QPushButton("⇄ Tukar Sisi", control_frame)
        self.btn_flip.setCursor(Qt.PointingHandCursor)
        self.btn_flip.setStyleSheet("""
            QPushButton {
                background: #F4EBE1; color: #8E3B20;
                font-weight: bold; font-size: 10.5px;
                border: 1px solid #D8C3A5; border-radius: 6px; padding: 6px 10px;
            }
            QPushButton:hover { background: #EAD8C7; }
        """)
        self.btn_flip.clicked.connect(self._toggle_side)
        btn_layout.addWidget(self.btn_flip)

        ctrl_layout.addLayout(btn_layout)
        side_panel.addWidget(control_frame)

        # Daftar Riwayat Langkah
        lbl_history = QLabel("📜 Riwayat Langkah:", self)
        lbl_history.setStyleSheet("font-size: 11px; font-weight: bold; color: #4A3B32;")
        side_panel.addWidget(lbl_history)

        self.history_list = QListWidget(self)
        self.history_list.setStyleSheet("""
            QListWidget {
                background: #FFFFFF;
                border: 1px solid #EADDCF;
                border-radius: 8px;
                padding: 4px;
                font-family: Consolas, monospace;
                font-size: 10.5px;
                color: #2D2424;
            }
            QListWidget::item { padding: 3px 6px; border-bottom: 1px solid #FAF4EE; }
        """)
        side_panel.addWidget(self.history_list, stretch=1)

        # Tombol Buka Catatan & Tutup
        bottom_actions = QHBoxLayout()
        self.btn_open_notes = QPushButton("📝 Buka Catatan", self)
        self.btn_open_notes.setCursor(Qt.PointingHandCursor)
        self.btn_open_notes.setStyleSheet("""
            QPushButton {
                background: #F4EBE1; color: #8E3B20;
                border: 1px solid #D8C3A5; border-radius: 6px; padding: 5px 8px; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background: #EAD8C7; }
        """)
        self.btn_open_notes.clicked.connect(self._on_click_notes)
        bottom_actions.addWidget(self.btn_open_notes)

        self.btn_close = QPushButton("✕ Tutup", self)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent; color: #A08880;
                border: none; padding: 5px; font-size: 10px;
            }
            QPushButton:hover { color: #C0392B; }
        """)
        self.btn_close.clicked.connect(self.close)
        bottom_actions.addWidget(self.btn_close)

        side_panel.addLayout(bottom_actions)
        main_layout.addLayout(side_panel, stretch=2)

    def _on_click_notes(self):
        try:
            from src.ui import desktop_actions
            desktop_actions.open_notes()
            self._set_mimi_bubble("Buku catatan sudah Mimi buka di Notepad, Tuan! Silakan dilihat ya 📝")
        except Exception:
            pass

    def _set_mimi_bubble(self, text):
        html_content = markdown_to_html(text)
        self.chat_bubble.setText(html_content)
        # Putar suara meong Mimi jika ada parent
        if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
            try:
                self.pet_parent.cat_audio.play_talk()
            except Exception:
                pass

    def _on_difficulty_changed(self):
        self.difficulty = self.combo_diff.currentData()
        self._start_new_game(self.difficulty)

    def _toggle_side(self):
        self.player_is_white = not self.player_is_white
        self._start_new_game(self.difficulty)

    def _start_new_game(self, difficulty):
        self.difficulty = difficulty
        self.board = chess.Board()
        self.selected_sq = None
        self.is_ai_thinking = False
        self.history_list.clear()

        self.board_widget.set_board(self.board, flipped=(not self.player_is_white))
        self.board_widget.set_last_move(None)

        greet = self.engine.get_greeting(self.difficulty)
        role_txt = "Putih (Melangkah Pertama)" if self.player_is_white else "Hitam (Melangkah Kedua)"
        self._set_mimi_bubble(f"{greet}\n\n*Tuan bermain sebagai: {role_txt}*")

        self.lbl_mimi_status.setText(f"Mode: {self.difficulty} 🎯")
        self.status_label.setText("Giliran Tuan melangkah! Klik bidak untuk melihat langkah legal.")

        # Jika pemain memilih hitam, Mimi melangkah pertama
        if not self.player_is_white:
            self._trigger_ai_move()

    def _on_square_clicked(self, sq):
        if self.is_ai_thinking or self.board.is_game_over():
            return

        is_player_turn = (self.board.turn == (chess.WHITE if self.player_is_white else chess.BLACK))
        if not is_player_turn:
            return

        piece = self.board.piece_at(sq)

        # 1. Jika belum ada bidak terpilih
        if self.selected_sq is None:
            if piece and piece.color == self.board.turn:
                self.selected_sq = sq
                self.board_widget.select_square(sq)
            return

        # 2. Jika mengklik bidak sendiri yang lain -> ganti seleksi
        if piece and piece.color == self.board.turn:
            self.selected_sq = sq
            self.board_widget.select_square(sq)
            return

        # 3. Coba lakukan langkah dari selected_sq ke sq
        move = chess.Move(self.selected_sq, sq)
        
        # Cek kemungkinan promosi pion (default ke Ratu/Queen)
        pawn_piece = self.board.piece_at(self.selected_sq)
        if pawn_piece and pawn_piece.piece_type == chess.PAWN:
            target_rank = chess.square_rank(sq)
            if (pawn_piece.color == chess.WHITE and target_rank == 7) or (pawn_piece.color == chess.BLACK and target_rank == 0):
                move = chess.Move(self.selected_sq, sq, promotion=chess.QUEEN)

        if move in self.board.legal_moves:
            self._execute_player_move(move)
        else:
            # Batalkan seleksi jika bukan langkah legal
            self.selected_sq = None
            self.board_widget.select_square(None)

    def _execute_player_move(self, move):
        san = self.board.san(move)
        self.board.push(move)
        self.selected_sq = None
        self.board_widget.select_square(None)
        self.board_widget.set_last_move(move)
        self.board_widget.update()

        # Tambahkan ke history
        move_num = (len(self.board.move_stack) + 1) // 2
        side_str = "Tuan (P)" if self.player_is_white else "Tuan (H)"
        self.history_list.addItem(f"{move_num}. {side_str}: {san}")
        self.history_list.scrollToBottom()

        if self._check_game_over():
            return

        self._trigger_ai_move()

    def _trigger_ai_move(self):
        self.is_ai_thinking = True
        self.lbl_mimi_status.setText("Sedang berpikir... 🤔")
        self.status_label.setText(f"{self.pet_name} sedang memikirkan langkah terbaiknya...")

        # Jalankan AI di worker thread terpisah agar GUI tetap responsif
        self.worker_thread = threading.Thread(target=self._run_ai_thread, daemon=True)
        self.worker_thread.start()

    def _run_ai_thread(self):
        try:
            threading.Event().wait(0.15)
            if getattr(self, "_is_closed", False):
                return
            move, comment = self.engine.select_move(self.board, self.difficulty)
            if not getattr(self, "_is_closed", False):
                self.ai_bridge.sig_move_ready.emit(move, comment)
        except Exception:
            pass

    def _on_ai_move_ready(self, move, comment):
        if getattr(self, "_is_closed", False) or not self.isVisible():
            return
        self.is_ai_thinking = False
        self.lbl_mimi_status.setText("Siap melangkah 🐾")

        if move and move in self.board.legal_moves:
            san = self.board.san(move)
            self.board.push(move)
            self.board_widget.set_last_move(move)
            self.board_widget.update()

            move_num = (len(self.board.move_stack) + 1) // 2
            side_str = "Mimi (H)" if self.player_is_white else "Mimi (P)"
            self.history_list.addItem(f"{move_num}. {side_str}: {san}")
            self.history_list.scrollToBottom()

            self._set_mimi_bubble(comment)

            if not self._check_game_over():
                self.status_label.setText("Giliran Tuan! Silakan tentukan langkahmu.")
        else:
            self._check_game_over()

    def _check_game_over(self) -> bool:
        if self.board.is_game_over():
            comment = self.engine.get_game_over_comment(self.board, self.player_is_white)
            self._set_mimi_bubble(comment)
            self.status_label.setText("Permainan Selesai!")
            return True
        return False

    def closeEvent(self, event):
        self._is_closed = True
        if self.pet_parent and hasattr(self.pet_parent, "on_game_closed"):
            self.pet_parent.on_game_closed(self)
        super().closeEvent(event)


