import os
import sys
import time
import random
import datetime
import ctypes
from PyQt5.QtCore import Qt, QPoint, QTimer, QSize, QObject, pyqtSignal
from PyQt5.QtGui import (
    QMovie, QFont, QCursor, QPainter, QColor, QPolygon,
    QPen, QBrush, QIcon, QPixmap, QTextDocument
)
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QPushButton, QMenu, QAction, QApplication,
    QScrollArea, QFrame, QInputDialog, QMessageBox,
    QDialog, QListWidget, QListWidgetItem, QSystemTrayIcon
)
# Pastikan path modul src dan root dikenali dengan aman
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_CURRENT_DIR)
_ROOT_DIR = os.path.dirname(_SRC_DIR)
for _p in [_ROOT_DIR, _SRC_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.ui import desktop_actions
    from src.ui.markdown_helper import markdown_to_html
    from src.ui.prey_widget import PreyWidget
    from src.ui.portal_effect import DimensionalPortalOverlay
    from src.ui.hermes_window import HermesStatusWindow
    from src.core import cat_audio
    from src.core import cat_memory
    from src.core import autostart
    from src.core import window_observer
    from src.core import spotify_observer
    from src.core import discord_rpc
    from src.core import discord_observer
    from src.core import hermes_agent
    from src.core import whatsapp_observer
except ImportError:
    from ui import desktop_actions
    from ui.markdown_helper import markdown_to_html
    from ui.prey_widget import PreyWidget
    from ui.portal_effect import DimensionalPortalOverlay
    from ui.hermes_window import HermesStatusWindow
    from core import cat_audio
    from core import cat_memory
    from core import autostart
    from core import window_observer
    from core import spotify_observer
    from core import discord_rpc
    from core import discord_observer
    from core import hermes_agent
    from core import whatsapp_observer

class TTSBridge(QObject):
    """Bridge thread-safe untuk mengalirkan event TTS/Audio ke Qt GUI Event Loop."""
    sig_start = pyqtSignal()
    sig_finish = pyqtSignal()

class MemoryDialog(QDialog):
    """
    Dialog GUI interaktif untuk melihat, melatih (training data),
    dan mengelola memori jangka panjang Kucing AI Mimi.
    """
    def __init__(self, parent=None, on_memory_updated=None):
        super().__init__(parent)
        self.on_memory_updated = on_memory_updated
        self.setWindowTitle("🧠 Pusat Pembelajaran & Memori AI Mimi")
        self.setFixedSize(390, 450)
        self.setStyleSheet("""
            QDialog { background-color: #FFFDF9; font-family: 'Segoe UI'; }
            QLabel { color: #2D2424; }
            QLineEdit {
                background: white; border: 1.5px solid #E07A5F; border-radius: 6px;
                padding: 6px; font-size: 11px;
            }
            QListWidget {
                background: white; border: 1.5px solid #D8C3A5; border-radius: 8px;
                padding: 6px; font-size: 11px; color: #2D2424;
            }
            QListWidget::item { padding: 5px; border-bottom: 1px solid #F4EBE1; }
            QListWidget::item:selected { background-color: #F8E1D4; color: #8E3B20; }
            QPushButton {
                background: #E07A5F; color: white; border: none; border-radius: 6px;
                padding: 6px 12px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background: #C74A27; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("🧠 <b>Pusat Pembelajaran & Memori AI Mimi</b>", self)
        title.setStyleSheet("font-size: 13px; color: #D35400;")
        layout.addWidget(title)

        desc = QLabel("Mimi mengingat fakta & pengetahuan ini secara permanen:", self)
        desc.setStyleSheet("font-size: 10px; color: #7F6D63;")
        layout.addWidget(desc)

        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget)

        # Input untuk mengajari hal baru
        inp_label = QLabel("<b>Ajarkan Fakta / Informasi Baru ke Mimi:</b>", self)
        inp_label.setStyleSheet("font-size: 10.5px; color: #2D2424;")
        layout.addWidget(inp_label)

        inp_row = QHBoxLayout()
        self.inp_field = QLineEdit(self)
        self.inp_field.setPlaceholderText("Contoh: nama saya Kevin / saya suka kopi hitam")
        self.inp_field.returnPressed.connect(self._on_add)
        inp_row.addWidget(self.inp_field)

        btn_add = QPushButton("Ajarkan 🐾", self)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._on_add)
        inp_row.addWidget(btn_add)
        layout.addLayout(inp_row)

        btn_row = QHBoxLayout()
        btn_delete = QPushButton("Hapus Pilihan", self)
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet("background: #C0392B;")
        btn_delete.clicked.connect(self._on_delete)
        btn_row.addWidget(btn_delete)

        btn_clear = QPushButton("Reset Semua", self)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet("background: #7F8C8D;")
        btn_clear.clicked.connect(self._on_clear)
        btn_row.addWidget(btn_clear)

        btn_close = QPushButton("Tutup", self)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self._refresh_list()

    def _refresh_list(self):
        self.list_widget.clear()
        facts = cat_memory.list_memories()
        prof = cat_memory.load_memory().get("user_profile", {})
        if prof.get("name"):
            lock_label = " 🔒 [Terkunci di Brankas Rahasia]" if prof.get("is_secret") else ""
            item = QListWidgetItem(f"👤 Nama Asli Tuan: {prof['name']}{lock_label}")
            item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.list_widget.addItem(item)

        if prof.get("nickname"):
            item_nick = QListWidgetItem(f"🕶️ Nama Samaran / Panggilan: {prof['nickname']}")
            item_nick.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.list_widget.addItem(item_nick)

        for f in facts:
            item = QListWidgetItem(f"• [{f.get('date', '')}] {f.get('fact', '')}")
            self.list_widget.addItem(item)

        if self.list_widget.count() == 0:
            self.list_widget.addItem(QListWidgetItem("Belum ada memori. Tulis fakta di bawah untuk melatih Mimi!"))

    def _on_add(self):
        txt = self.inp_field.text().strip()
        if txt:
            alias = cat_memory.extract_alias_from_text(txt)
            if alias:
                res = cat_memory.set_nickname(alias)
            else:
                res = cat_memory.learn_fact(txt)
            self.inp_field.clear()
            self._refresh_list()
            if self.on_memory_updated:
                self.on_memory_updated(res)

    def _on_delete(self):
        row = self.list_widget.currentRow()
        facts = cat_memory.list_memories()
        prof = cat_memory.load_memory().get("user_profile", {})
        offset = 0
        if prof.get("name"):
            offset += 1
        if prof.get("nickname"):
            offset += 1
        fact_idx = row - offset
        if 0 <= fact_idx < len(facts):
            cat_memory.delete_memory(fact_idx)
            self._refresh_list()
            if self.on_memory_updated:
                self.on_memory_updated("Meow! Memori tersebut sudah Mimi hapus! 🐾")

    def _on_clear(self):
        reply = QMessageBox.question(self, "Reset Memori", "Yakin ingin menghapus semua memori yang telah diajarkan?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            res = cat_memory.clear_memories()
            self._refresh_list()
            if self.on_memory_updated:
                self.on_memory_updated(res)


class ChatTextEdit(QTextEdit):
    """
    Kotak teks multiline modern yang nyaman untuk mengetik komentar/perintah panjang.
    Tekan Enter untuk kirim, Shift+Enter untuk baris baru.
    """
    submit_requested = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.submit_requested.emit()
                event.accept()
        elif event.key() == Qt.Key_Escape:
            if self.parent():
                self.parent().keyPressEvent(event)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)


class SpeechBubbleWindow(QWidget):
    """
    Balon dialog melayang tepat di atas kepala Kucing 2D Pixel Mimi.
    """
    def __init__(self, parent_pet):
        super().__init__()
        self.parent_pet = parent_pet
        self.is_pointing_down = True
        self.mode = "message"

        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedWidth(310)

        self._init_ui()

        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.hide_bubble)

    def is_input_active(self) -> bool:
        """Mengecek apakah kotak dialog input sedang terbuka dan aktif."""
        return self.isVisible() and self.mode == "input"

    def _init_ui(self):
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(12, 8, 12, 16)
        self.outer_layout.setSpacing(4)

        # MODE 1: PESAN TEKS
        self.msg_container = QWidget(self)
        self.msg_container.setStyleSheet("background: transparent;")
        msg_layout = QVBoxLayout(self.msg_container)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(3)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(4)
        self.pet_title = QLabel(f"🐾 {self.parent_pet.pet_name} • Pixel Cat AI", self.msg_container)
        self.pet_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #D35400; font-family: 'Segoe UI';")
        top_bar.addWidget(self.pet_title)
        top_bar.addStretch()

        btn_note = QPushButton("📝 Note", self.msg_container)
        btn_note.setCursor(Qt.PointingHandCursor)
        btn_note.setToolTip("Buka Catatan Notepad (Windows)")
        btn_note.setStyleSheet("""
            QPushButton {
                background: #F4EBE1; color: #8E3B20; font-size: 8.5px; font-weight: bold;
                border: 1px solid #D8C3A5; border-radius: 4px; padding: 2px 6px;
            }
            QPushButton:hover { background: #EAD8C7; color: #6E2B15; }
        """)
        btn_note.clicked.connect(self._on_quick_note)
        top_bar.addWidget(btn_note)

        self.btn_games = QPushButton("🎮 Game ▾", self.msg_container)
        self.btn_games.setCursor(Qt.PointingHandCursor)
        self.btn_games.setToolTip("Pilih Game Seru bersama Mimi (Catur, Tetris, Snake)")
        self.btn_games.setStyleSheet("""
            QPushButton {
                background: #F4EBE1; color: #8E3B20; font-size: 8.5px; font-weight: bold;
                border: 1px solid #D8C3A5; border-radius: 4px; padding: 2px 6px;
            }
            QPushButton:hover { background: #EAD8C7; color: #6E2B15; }
        """)
        self.btn_games.clicked.connect(self._on_quick_games_menu)
        top_bar.addWidget(self.btn_games)

        self.btn_close = QPushButton("✕", self.msg_container)
        self.btn_close.setFixedSize(18, 18)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setToolTip("Tutup balasan / konfirmasi menutup (Esc / Klik)")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: #F4EBE1; color: #8E3B20; font-size: 10px; font-weight: bold;
                border: 1px solid #D8C3A5; border-radius: 9px; padding: 0px;
            }
            QPushButton:hover {
                background: #E07A5F; color: white; border: 1px solid #C74A27;
            }
        """)
        self.btn_close.clicked.connect(self.hide_bubble)
        top_bar.addWidget(self.btn_close)
        msg_layout.addLayout(top_bar)

        self.scroll_area = QScrollArea(self.msg_container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                border: none; background: #F4EBE1; width: 5px; border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #E07A5F; min-height: 18px; border-radius: 2px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 3, 0)

        self.msg_label = QLabel("", scroll_content)
        self.msg_label.setWordWrap(True)
        self.msg_label.setFont(QFont("Segoe UI", 9, QFont.Normal))
        self.msg_label.setStyleSheet("color: #2D2424; line-height: 135%; background: transparent;")
        self.msg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.msg_label.setTextFormat(Qt.RichText)
        self.msg_label.setOpenExternalLinks(False)
        self.msg_label.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextSelectableByMouse)
        self.msg_label.linkActivated.connect(self._on_link_activated)
        scroll_layout.addWidget(self.msg_label)

        self.scroll_area.setWidget(scroll_content)
        msg_layout.addWidget(self.scroll_area)
        self.outer_layout.addWidget(self.msg_container)

        # MODE 2: INPUT DIALOG
        self.input_container = QWidget(self)
        self.input_container.setStyleSheet("background: transparent;")
        input_main_layout = QVBoxLayout(self.input_container)
        input_main_layout.setContentsMargins(0, 0, 0, 0)
        input_main_layout.setSpacing(5)

        header_input = QHBoxLayout()
        prompt_label = QLabel(f"💬 Perintah / Tanya {self.parent_pet.pet_name}:", self.input_container)
        prompt_label.setStyleSheet("font-size: 9.5px; font-weight: bold; color: #D35400; font-family: 'Segoe UI';")
        header_input.addWidget(prompt_label)
        header_input.addStretch()

        btn_close_inp = QPushButton("✕", self.input_container)
        btn_close_inp.setFixedSize(18, 18)
        btn_close_inp.setCursor(Qt.PointingHandCursor)
        btn_close_inp.setToolTip("Tutup dialog (Esc / Klik)")
        btn_close_inp.setStyleSheet("""
            QPushButton {
                background: #F4EBE1; color: #8E3B20; font-size: 10px; font-weight: bold;
                border: 1px solid #D8C3A5; border-radius: 9px; padding: 0px;
            }
            QPushButton:hover {
                background: #E07A5F; color: white; border: 1px solid #C74A27;
            }
        """)
        btn_close_inp.clicked.connect(self.hide_bubble)
        header_input.addWidget(btn_close_inp)
        input_main_layout.addLayout(header_input)

        input_row = QHBoxLayout()
        input_row.setSpacing(5)

        self.input_field = ChatTextEdit(self.input_container)
        self.input_field.setPlaceholderText("Tanya, perintah CMD, atau komentar panjang untuk Mimi...\n(Enter: kirim, Shift+Enter: baris baru)")
        self.input_field.setStyleSheet("""
            QTextEdit {
                background: #FFFFFF;
                border: 1.5px solid #E07A5F;
                border-radius: 7px;
                padding: 4px 7px;
                font-family: 'Segoe UI';
                font-size: 10px;
                color: #2D2424;
            }
            QTextEdit:focus { border: 1.5px solid #B25A38; }
        """)
        self.input_field.setFixedHeight(48)
        self.input_field.submit_requested.connect(self._on_submit_input)
        input_row.addWidget(self.input_field)

        self.btn_send = QPushButton("Kirim", self.input_container)
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setFixedHeight(48)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background: #E07A5F; color: white;
                font-size: 10px; font-weight: bold;
                border: none; border-radius: 7px; padding: 4px 10px;
            }
            QPushButton:hover { background: #C74A27; }
        """)
        self.btn_send.clicked.connect(self._on_submit_input)
        input_row.addWidget(self.btn_send)

        input_main_layout.addLayout(input_row)
        self.outer_layout.addWidget(self.input_container)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide_bubble()
            event.accept()
        else:
            super().keyPressEvent(event)

    def show_message(self, text: str, duration_ms: int = 6000, persistent: bool = False, force: bool = False):
        # KRUSIAL: Jangan pernah menimpa atau membatalkan dialog input saat pengguna sedang mengetik perintah!
        if self.is_input_active() and not force:
            return

        self.mode = "message"
        self.input_container.hide()
        self.msg_container.show()

        # Konversi markdown menjadi HTML bergaya hangat tanpa tanda baca aneh
        formatted_html = markdown_to_html(text)
        self.msg_label.setText(formatted_html)

        # Hitung tinggi akurat konten HTML menggunakan QTextDocument
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Segoe UI", 9))
        doc.setTextWidth(275)
        doc.setHtml(formatted_html)
        target_h = max(45, min(220, int(doc.size().height()) + 12))
        self.scroll_area.setFixedHeight(target_h)

        self._apply_margins()
        self.adjustSize()
        self.update_position()
        self.show()
        self.parent_pet._enforce_topmost()
        self.update()

        self.auto_hide_timer.stop()
        # Jika bukan pesan persisten dan duration_ms > 0, aktifkan auto-close
        if not persistent and duration_ms > 0:
            dyn_duration = max(3500, min(len(text) * 70, 16000))
            self.auto_hide_timer.start(dyn_duration)

    def show_ai_answer(self, text: str):
        """Menampilkan jawaban dari AI setelah bertanya: jendela tetap terbuka selamanya sampai diklik silang oleh pengguna."""
        self.show_message(text, duration_ms=0, persistent=True, force=True)

    def _on_quick_note(self):
        self.parent_pet.say_message(desktop_actions.open_notes())

    def _on_quick_games_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFDF9; color: #2D2424;
                border: 1.5px solid #D8C3A5; border-radius: 8px;
                padding: 4px; font-family: 'Segoe UI'; font-size: 11px;
            }
            QMenu::item { padding: 5px 16px 5px 8px; border-radius: 4px; }
            QMenu::item:selected { background-color: #F8E1D4; color: #8E3B20; }
        """)
        act_chess = menu.addAction("♟️ Catur (Chess)")
        act_chess.triggered.connect(lambda: self.parent_pet.open_chess_game("Normal"))
        act_tetris = menu.addAction("🧱 Tetris (Balok)")
        act_tetris.triggered.connect(lambda: self.parent_pet.open_tetris_game())
        act_snake = menu.addAction("🐍 Snake (Tangkap Ikan)")
        act_snake.triggered.connect(lambda: self.parent_pet.open_snake_game())
        act_sudoku = menu.addAction("🧩 Sudoku (Teka-Teki)")
        act_sudoku.triggered.connect(lambda: self.parent_pet.open_sudoku_game("Sedang"))
        act_snakes = menu.addAction("🎲 Ular Tangga (Ladders)")
        act_snakes.triggered.connect(lambda: self.parent_pet.open_ular_tangga_game())
        act_battleship = menu.addAction("🚢 Battleship (Perang Laut)")
        act_battleship.triggered.connect(lambda: self.parent_pet.open_battleship_game())
        menu.exec_(self.btn_games.mapToGlobal(QPoint(0, self.btn_games.height() + 2)))

    def _on_link_activated(self, link: str):
        if link == "action:open_notes":
            self.parent_pet.say_message(desktop_actions.open_notes())
        elif link == "action:play_chess":
            self.parent_pet.open_chess_game("Normal")
        elif link == "action:play_tetris":
            self.parent_pet.open_tetris_game()
        elif link == "action:play_snake":
            self.parent_pet.open_snake_game()
        elif link == "action:play_sudoku":
            self.parent_pet.open_sudoku_game("Sedang")
        elif link == "action:play_ular_tangga":
            self.parent_pet.open_ular_tangga_game()
        elif link == "action:play_battleship":
            self.parent_pet.open_battleship_game()
        elif link.startswith("http://") or link.startswith("https://"):
            desktop_actions.open_browser(link)

    def show_input(self):
        self.auto_hide_timer.stop()
        self.mode = "input"
        self.msg_container.hide()
        self.input_container.show()
        # Jangan hapus teks yang sedang diketik pengguna jika pengguna membuka kembali dialog!

        self._apply_margins()
        self.adjustSize()
        self.update_position()
        self.show()
        self.parent_pet._enforce_topmost()
        self.input_field.setFocus()
        self.update()

    def hide_bubble(self):
        self.auto_hide_timer.stop()
        self.hide()

    def _apply_margins(self):
        if self.is_pointing_down:
            self.outer_layout.setContentsMargins(12, 8, 12, 16)
        else:
            self.outer_layout.setContentsMargins(12, 16, 12, 8)

    def update_position(self):
        pet_rect = self.parent_pet.geometry()
        bw = self.width()
        bh = self.height()

        bx = pet_rect.x() + (pet_rect.width() - bw) // 2
        by = pet_rect.y() - bh - 6

        screen = QApplication.primaryScreen().availableGeometry()
        bx = max(screen.left() + 10, min(bx, screen.right() - bw - 10))

        if by < screen.top() + 15:
            by = pet_rect.y() + pet_rect.height() + 6
            self.is_pointing_down = False
        else:
            self.is_pointing_down = True

        self._apply_margins()
        self.move(bx, by)

    def _on_submit_input(self):
        query = self.input_field.toPlainText().strip()
        if not query:
            return
        self.input_field.clear()
        self.mode = "message"
        self.hide_bubble()
        self.parent_pet.handle_user_prompt(query)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        tail_h = 9
        bg_color = QColor(255, 253, 248)
        border_color = QColor(225, 205, 185)
        tip_x = w // 2

        if self.is_pointing_down:
            box_rect = [2, 2, w - 4, h - tail_h - 4]
            triangle = QPolygon([
                QPoint(tip_x - 8, h - tail_h - 2),
                QPoint(tip_x + 8, h - tail_h - 2),
                QPoint(tip_x, h - 2)
            ])
            line1 = (tip_x - 8, h - tail_h - 2, tip_x, h - 2)
            line2 = (tip_x + 8, h - tail_h - 2, tip_x, h - 2)
        else:
            box_rect = [2, tail_h + 2, w - 4, h - tail_h - 4]
            triangle = QPolygon([
                QPoint(tip_x - 8, tail_h + 2),
                QPoint(tip_x + 8, tail_h + 2),
                QPoint(tip_x, 2)
            ])
            line1 = (tip_x - 8, tail_h + 2, tip_x, 2)
            line2 = (tip_x + 8, tail_h + 2, tip_x, 2)

        painter.setPen(QPen(border_color, 1.8))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(box_rect[0], box_rect[1], box_rect[2], box_rect[3], 10, 10)

        painter.setPen(Qt.NoPen)
        painter.drawPolygon(triangle)

        painter.setPen(QPen(border_color, 1.8))
        painter.drawLine(*line1)
        painter.drawLine(*line2)


class RagdollPetLabel(QLabel):
    """
    Label khusus karakter Mimi yang mengimplementasikan visual fisika Ragdoll:
    - Rotasi ayunan inersia (pendulum tilt) saat diseret mouse / melayang.
    - Deformasi squash & stretch (peregangan saat jatuh & pemipihan saat impak).
    - Dynamic pivot anchor: tengkuk leher saat diangkat tangan, tengah tubuh saat jatuh,
      dan telapak kaki saat membentur lantai agar tidak melayang ke atas.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.movie_ref = None
        self.ragdoll_angle = 0.0          # Sudut kemiringan (derajat)
        self.ragdoll_scale_x = 1.0        # Skala horizontal (squash/stretch)
        self.ragdoll_scale_y = 1.0        # Skala vertikal
        self.ragdoll_anchor = "center"    # "scruff", "center", atau "bottom"

    def setMovie(self, movie):
        super().setMovie(movie)
        self.movie_ref = movie
        if movie:
            movie.frameChanged.connect(self.update)

    def set_movie(self, movie):
        self.setMovie(movie)

    def set_ragdoll(self, angle: float, scale_x: float, scale_y: float, anchor: str = "center"):
        self.ragdoll_angle = angle
        self.ragdoll_scale_x = scale_x
        self.ragdoll_scale_y = scale_y
        self.ragdoll_anchor = anchor
        self.update()

    def reset_ragdoll(self):
        self.ragdoll_angle = 0.0
        self.ragdoll_scale_x = 1.0
        self.ragdoll_scale_y = 1.0
        self.ragdoll_anchor = "center"
        self.update()

    def paintEvent(self, event):
        if not self.movie_ref or not self.movie_ref.isValid():
            super().paintEvent(event)
            return

        pm = self.movie_ref.currentPixmap()
        if pm.isNull():
            super().paintEvent(event)
            return

        # Jika ragdoll dalam posisi netral, gambar normal untuk efisiensi
        if abs(self.ragdoll_angle) < 0.1 and abs(self.ragdoll_scale_x - 1.0) < 0.01 and abs(self.ragdoll_scale_y - 1.0) < 0.01:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            w, h = self.width(), self.height()
            pw, ph = pm.width(), pm.height()
            painter.drawPixmap((w - pw) // 2, (h - ph) // 2, pm)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        w, h = self.width(), self.height()
        pw, ph = pm.width(), pm.height()
        img_x = (w - pw) / 2.0
        img_y = (h - ph) / 2.0

        # Tentukan titik tumpu (pivot anchor) transformasi
        if self.ragdoll_anchor == "scruff":
            # Tengkuk leher saat diangkat tangan pengguna
            pivot_x = w / 2.0
            pivot_y = img_y + ph * 0.28
        elif self.ragdoll_anchor == "bottom":
            # Telapak kaki saat membentur lantai agar memipih rapat di atas tanah
            pivot_x = w / 2.0
            pivot_y = img_y + ph * 0.95
        else:
            # Titik tengah tubuh saat melayang / berputar di udara
            pivot_x = w / 2.0
            pivot_y = h / 2.0

        painter.translate(pivot_x, pivot_y)
        painter.rotate(self.ragdoll_angle)
        painter.scale(self.ragdoll_scale_x, self.ragdoll_scale_y)
        painter.translate(-pivot_x, -pivot_y)

        painter.drawPixmap(int(img_x), int(img_y), pm)


# KELOMPOK STATE ANIMASI DINAMIS & ANTI-NABRAK
DANCE_STATES = ["DANCE", "DANCE_DISCO", "DANCE_ROCK"]
WATCH_STATES = ["POPCORN", "WATCH_DRINK", "WATCH_GLASSES"]
LISTEN_STATES = ["LISTEN", "LISTEN_HEADSET", "LISTEN_NOD"]


class CatPetWindow(QWidget):
    """
    Karakter Kucing 2D Pixel Art Desktop Pet (Ukuran Sedang 128x128 px):
    - Dilengkapi suara meong kucing imut (bukan TTS robot)
    - Sistem Memori Pembelajaran AI (Learning & Training Data)
    - Draggable dengan animasi DIANGKAT (PICKED UP)
    - DIJATUHKAN dengan simulasi gravitasi dan pantulan mendarat (LANDING BOUNCE)
    - Terhubung dengan perintah desktop lokal: Notepad, Browser, Antigravity
    - AI lebih hidup dengan celetukan spontan berkala
    """
    def __init__(self, ai_handler, speech_engine=None, pet_name="Mimi"):
        super().__init__()
        self.ai_handler = ai_handler
        # Inisialisasi mesin audio kucing alami
        if isinstance(speech_engine, cat_audio.CatAudioEngine):
            self.cat_audio = speech_engine
        else:
            self.cat_audio = cat_audio.CatAudioEngine()
        self.speech_engine = self.cat_audio # alias kompatibilitas
        self.pet_name = pet_name
        self.chess_window = None
        self.tetris_window = None
        self.snake_window = None
        self.sudoku_window = None
        self.snakes_ladders_window = None
        self.battleship_window = None
        self.active_game_window = None

        # Interaksi Kursor Mouse
        self.cursor_chase_mode = False
        self._pet_stroke_distance = 0
        self._last_hover_pos = QPoint()
        self._last_pet_time = 0

        # Timer Pelacakan Kursor untuk Mode Kejar Kursor & Interaksi Dekat
        self.cursor_track_timer = QTimer(self)
        self.cursor_track_timer.setInterval(200)
        self.cursor_track_timer.timeout.connect(self._track_cursor_interaction)
        self.cursor_track_timer.start()

        # Pemantauan & Interaksi Aplikasi Aktif di Windows
        self.app_observer_enabled = True
        self._last_active_hwnd = None
        self._last_active_title = ""
        self._last_app_interact_time = time.time()
        self._app_focus_start_time = time.time()
        self._pending_app_info = None

        self._pending_app_timer = QTimer(self)
        self._pending_app_timer.setSingleShot(True)
        self._pending_app_timer.timeout.connect(self._trigger_pending_app_interaction)

        self.app_observer_timer = QTimer(self)
        self.app_observer_timer.setInterval(1500)
        self.app_observer_timer.timeout.connect(self._check_active_application)
        self.app_observer_timer.start()

        # Variasi & Rotasi Acak Animasi Spotify, YouTube, dan Discord (Anti-Nabrak)
        self._last_dance_switch_time = 0.0
        self._next_dance_duration = random.uniform(6.0, 10.0)
        self._last_watch_switch_time = 0.0
        self._next_watch_duration = random.uniform(7.0, 12.0)
        self._last_listen_switch_time = 0.0
        self._next_listen_duration = random.uniform(8.0, 14.0)

        # Pemantauan Spotify (Mimi Joget saat Spotify memutar lagu)
        self.spotify_enabled = True
        self.is_spotify_dancing = False
        self._last_spotify_track = ""
        self._last_spotify_dance_toast = 0.0
        self.spotify_timer = QTimer(self)
        self.spotify_timer.setInterval(2000)
        self.spotify_timer.timeout.connect(self._check_spotify_music)
        self.spotify_timer.start()

        # Pemantauan Discord (Rich Presence Activity & Voice Channel Observer)
        discord_rpc_on = os.getenv("DISCORD_RPC_ENABLED", "true").strip().lower() in ["true", "1", "yes"]
        discord_client_id = os.getenv("DISCORD_CLIENT_ID", "").strip()
        self.discord_rpc = discord_rpc.DiscordRPCManager(client_id=discord_client_id, enabled=discord_rpc_on)
        self.discord_rpc.start()

        self.is_in_discord_voice = False
        self.discord_voice_timer = QTimer(self)
        self.discord_voice_timer.setInterval(2000)
        self.discord_voice_timer.timeout.connect(self._check_discord_voice)
        self.discord_voice_timer.start()

        # Pemantauan Pesan Masuk WhatsApp di Google Chrome & Desktop
        self._pending_wa_notification = None
        try:
            self.whatsapp_thread = whatsapp_observer.WhatsAppObserverThread(self)
            self.whatsapp_thread.whatsapp_notification.connect(self._on_whatsapp_message)
            self.whatsapp_thread.start()
        except Exception as e:
            self.whatsapp_thread = None

        # Interaksi Berburu Mangsa Mini (Tikus & Lalat)
        self.prey_widget = None
        self.is_hunting = False
        self._hunt_step_timer = QTimer(self)
        self._hunt_step_timer.setInterval(30)
        self._hunt_step_timer.timeout.connect(self._on_hunt_tick)

        # Spontaneous Play Timer (Mimi secara acak dan otomatis bermain: tikus, lalat, sprint zoomies, atau lompat)
        self.spontaneous_play_timer = QTimer(self)
        self.spontaneous_play_timer.setInterval(random.randint(35000, 60000))
        self.spontaneous_play_timer.timeout.connect(self._maybe_spontaneous_play)
        self.spontaneous_play_timer.start()

        # Mode Nonton Video & Popcorn
        self.is_watching_video = False
        self._last_video_title = ""

        # Hermes Agent Autonomous Evolution Engine (Self-Learning over Time)
        api_key = getattr(self.ai_handler, 'api_key', '')
        model_name = getattr(self.ai_handler, 'model_name', 'gemini-3.5-flash-lite')
        self.hermes_engine = hermes_agent.HermesEvolutionEngine(api_key=api_key, model_name=model_name)
        self.hermes_engine.evolution_leveled_up.connect(self._on_hermes_leveled_up)
        self.hermes_engine.spontaneous_insight_ready.connect(self._on_hermes_spontaneous_insight)
        self.hermes_window = None

        # Intro & Outro
        self._intro_played = False
        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(40)
        self._fade_opacity = 1.0

        self.current_state = "IDLE"
        self._drag_pos = QPoint()
        self._is_dragging = False
        self._inactivity_seconds = 0
        self.assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))

        # Fisika Jatuh Gravitasi & Ragdoll
        self._velocity_y = 0.0
        self._velocity_x = 0.0
        self._drag_velocity_x = 0.0
        self._drag_velocity_y = 0.0
        self._last_drag_pos = None
        self._last_drag_time = 0.0
        self._ragdoll_angle = 0.0
        self._ragdoll_angular_vel = 0.0
        self._ragdoll_squash = 0.0
        self._ragdoll_squash_vel = 0.0
        self._dangle_phase = 0.0

        self._fall_timer = QTimer(self)
        self._fall_timer.setInterval(16)
        self._fall_timer.timeout.connect(self._on_gravity_tick)

        self._ragdoll_timer = QTimer(self)
        self._ragdoll_timer.setInterval(16)
        self._ragdoll_timer.timeout.connect(self._on_ragdoll_tick)

        # Autonomous Wanderer
        self.auto_wander_enabled = True
        self._target_x = 0
        self._step_timer = QTimer(self)
        self._step_timer.setInterval(30)
        self._step_timer.timeout.connect(self._on_walk_step)

        self.wander_timer = QTimer(self)
        self.wander_timer.setInterval(7000)
        self.wander_timer.timeout.connect(self._maybe_wander)
        self.wander_timer.start()

        # Timer Celetukan Spontan
        self.spontaneous_timer = QTimer(self)
        self.spontaneous_timer.setInterval(180000)
        self.spontaneous_timer.timeout.connect(self._on_spontaneous_thought)
        self.spontaneous_timer.start()

        # Window Flags & Ukuran Sedang 128x128 px
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(128, 128)

        self._init_ui()
        self._init_timers()
        self._init_audio_bridge()
        self._init_tray()

        self.speech_bubble = SpeechBubbleWindow(self)

        QApplication.setQuitOnLastWindowClosed(False)
        self.set_state("IDLE")
        self._set_initial_position()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.pet_label = RagdollPetLabel(self)
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.setFixedSize(128, 128)
        self.pet_label.setCursor(Qt.OpenHandCursor)
        self.pet_label.setToolTip(f"🐱 {self.pet_name} • Pixel Cat AI\n- Dobel klik untuk perintah teks (CMD, Browser, Shutdown Timer, dsb)\n- Angkat untuk geser & lepaskan untuk jatuh!\n- Klik kanan untuk menu lengkap, Kontrol CMD, & Memori AI")
        layout.addWidget(self.pet_label)

        self.movie = None
        self.setMouseTracking(True)
        self.pet_label.setMouseTracking(True)

    def _init_timers(self):
        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(1000)
        self.idle_timer.timeout.connect(self._check_inactivity)
        self.idle_timer.start()

        # Watchdog Topmost: Memastikan Mimi selalu berada di depan aplikasi lain tanpa mencuri fokus
        self._topmost_timer = QTimer(self)
        self._topmost_timer.setInterval(1000)
        self._topmost_timer.timeout.connect(self._enforce_topmost)
        self._topmost_timer.start()

    def _init_audio_bridge(self):
        self.tts_bridge = TTSBridge()
        self.tts_bridge.sig_start.connect(self._on_audio_start_safe)
        self.tts_bridge.sig_finish.connect(self._on_audio_finish_safe)

        self.cat_audio.set_callbacks(
            on_start=lambda: self.tts_bridge.sig_start.emit(),
            on_finish=lambda: self.tts_bridge.sig_finish.emit()
        )

    def _init_tray(self):
        """Inisialisasi icon System Tray di taskbar pojok jam Windows."""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            tray_pixmap = QPixmap(32, 32)
            tray_pixmap.fill(Qt.transparent)
            p = QPainter(tray_pixmap)
            p.setRenderHint(QPainter.Antialiasing)
            p.setBrush(QBrush(QColor(244, 162, 97)))
            p.setPen(QPen(QColor(38, 26, 20), 1.5))
            p.drawEllipse(2, 2, 28, 28)
            p.setFont(QFont("Segoe UI", 12))
            p.drawText(tray_pixmap.rect(), Qt.AlignCenter, "🐱")
            p.end()

            self.tray_icon.setIcon(QIcon(tray_pixmap))
            self.tray_icon.setToolTip(f"🐱 {self.pet_name} • Virtual Pixel Cat AI Companion")

            tray_menu = QMenu()
            tray_menu.setStyleSheet("""
                QMenu {
                    background-color: #FFFDF9; color: #2D2424;
                    border: 1.5px solid #D8C3A5; border-radius: 8px;
                    padding: 5px; font-family: 'Segoe UI'; font-size: 11px;
                }
                QMenu::item { padding: 5px 20px 5px 10px; border-radius: 4px; }
                QMenu::item:selected { background-color: #F8E1D4; color: #8E3B20; }
                QMenu::separator { height: 1px; background: #E8D8C8; margin: 4px 5px; }
            """)

            act_show = QAction("🐱 Tampilkan Mimi di Layar", self)
            act_show.triggered.connect(self._bring_to_front)
            tray_menu.addAction(act_show)

            act_feed = QAction(f"🐟 Beri Makan Ikan / 🐾 Elus {self.pet_name}", self)
            act_feed.triggered.connect(self._action_pet_cat)
            tray_menu.addAction(act_feed)

            act_tray_hermes = QAction("🧬 Evolusi Hermes Agent Mimi", self)
            act_tray_hermes.triggered.connect(self._open_hermes_window)
            tray_menu.addAction(act_tray_hermes)

            act_notes = QAction("📝 Buka Catatan Notepad", self)
            act_notes.triggered.connect(lambda: self.say_message(desktop_actions.open_notes()))
            tray_menu.addAction(act_notes)

            # SUBMENU GAME DI TRAY
            menu_tray_games = tray_menu.addMenu("🎮 Game Seru bersama Mimi")
            menu_tray_games.setStyleSheet(tray_menu.styleSheet())

            act_tray_chess = QAction("♟️ Bermain Catur (Chess)", self)
            act_tray_chess.triggered.connect(lambda: self.open_chess_game("Normal"))
            menu_tray_games.addAction(act_tray_chess)

            act_tray_tetris = QAction("🧱 Bermain Tetris (Balok)", self)
            act_tray_tetris.triggered.connect(self.open_tetris_game)
            menu_tray_games.addAction(act_tray_tetris)

            act_tray_snake = QAction("🐍 Bermain Snake (Tangkap Ikan)", self)
            act_tray_snake.triggered.connect(self.open_snake_game)
            menu_tray_games.addAction(act_tray_snake)

            act_tray_sudoku = QAction("🧩 Bermain Sudoku (Angka)", self)
            act_tray_sudoku.triggered.connect(lambda: self.open_sudoku_game("Sedang"))
            menu_tray_games.addAction(act_tray_sudoku)

            act_tray_snakes = QAction("🎲 Bermain Ular Tangga", self)
            act_tray_snakes.triggered.connect(self.open_ular_tangga_game)
            menu_tray_games.addAction(act_tray_snakes)

            act_tray_battleship = QAction("🚢 Bermain Battleship (Kapal)", self)
            act_tray_battleship.triggered.connect(self.open_battleship_game)
            menu_tray_games.addAction(act_tray_battleship)


            act_cmd = QAction("💻 Buka Command Prompt (CMD)", self)
            act_cmd.triggered.connect(lambda: self.say_message(desktop_actions.open_cmd_terminal()))
            tray_menu.addAction(act_cmd)

            act_cancel_sd = QAction("❌ Batalkan Timer Shutdown", self)
            act_cancel_sd.triggered.connect(lambda: self.say_message(desktop_actions.cancel_shutdown()))
            tray_menu.addAction(act_cancel_sd)

            act_sleep = QAction("💤 Tidurkan Komputer (Sleep)", self)
            act_sleep.triggered.connect(lambda: self.say_message(desktop_actions.sleep_computer(0)))
            tray_menu.addAction(act_sleep)

            tray_menu.addSeparator()

            is_auto = autostart.is_autostart_enabled()
            auto_label = "🚀 Aktif Otomatis saat Windows Menyala: [ON]" if is_auto else "🚀 Aktif Otomatis saat Windows Menyala: [OFF]"
            self.act_tray_auto = QAction(auto_label, self)
            self.act_tray_auto.triggered.connect(self._toggle_autostart)
            tray_menu.addAction(self.act_tray_auto)

            tray_menu.addSeparator()

            act_exit = QAction("❌ Keluar (Exit)", self)
            act_exit.triggered.connect(self._exit_app)
            tray_menu.addAction(act_exit)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._on_tray_activated)
            self.tray_icon.show()
        except Exception as e:
            print(f"[TrayIcon] Warning: Gagal inisialisasi tray icon: {e}")

    def _enforce_topmost(self):
        """Memastikan Mimi dan Balon Percakapan selalu berada di lapisan terdepan (Topmost) di atas semua aplikasi."""
        self.raise_()
        if sys.platform == "win32":
            try:
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                user32.SetWindowPos.argtypes = [
                    wintypes.HWND, wintypes.HWND,
                    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                    ctypes.c_uint
                ]
                user32.SetWindowPos.restype = wintypes.BOOL
                hwnd_topmost = ctypes.c_void_p(-1).value
                flags = 0x0001 | 0x0002 | 0x0010 | 0x0040  # SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW

                hwnd = int(self.winId())
                user32.SetWindowPos(hwnd, hwnd_topmost, 0, 0, 0, 0, flags)

                if hasattr(self, 'speech_bubble') and self.speech_bubble.isVisible():
                    sb_hwnd = int(self.speech_bubble.winId())
                    user32.SetWindowPos(sb_hwnd, hwnd_topmost, 0, 0, 0, 0, flags)
            except Exception:
                pass

    def _bring_to_front(self):
        """Menampilkan kembali dan memfokuskan Mimi ke depan layar."""
        self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()
        self._enforce_topmost()
        self.say_message(f"Meow! Mimi selalu aktif di sini menemani Tuan! 🐾✨")

    def _on_tray_activated(self, reason):
        if reason in [QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick]:
            self._bring_to_front()

    def _get_floor_y(self):
        avail = QApplication.primaryScreen().availableGeometry()
        return avail.bottom() - self.height() + 1

    def _start_entrance_fall(self):
        """Animasi masuk: Mimi meluncur jatuh dari atas kanan dan mendarat mulus di bawah kanan layar."""
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - 45
        start_y = -self.height() - 20
        self.move(x, start_y)
        self.set_state("PICKED")
        self._velocity_y = 5.0
        self._is_entrance_falling = True
        self._fall_timer.start()

    def _set_initial_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - 45
        y = self._get_floor_y()
        self.move(x, y)

    def _greet_user(self):
        """Menyapa Tuan saat aplikasi mulai dengan sapaan waktu dan peregangan imut."""
        prof = cat_memory.load_memory().get("user_profile", {})
        is_secret = prof.get("is_secret", False)
        user_name = prof.get("name", "")

        greeting = autostart.generate_startup_greeting(user_name, is_secret=is_secret)

        # Animasi peregangan bangun tidur (stretch) & suara meong ceria
        self.cat_audio.play_chirp()
        self.set_state("STRETCH")

        def finish_greet():
            self.set_state("IDLE")
            self.say_message(greeting)

        QTimer.singleShot(2400, finish_greet)

    # --- SIMULASI FISIKA GRAVITASI, LEMPARAN & RAGDOLL ---
    def _on_gravity_tick(self):
        floor_y = self._get_floor_y()
        screen = QApplication.primaryScreen().geometry()

        # Percepatan gravitasi vertikal
        self._velocity_y += 2.4
        new_y = self.y() + int(self._velocity_y)

        # Pergerakan horizontal akibat momentum lemparan
        new_x = self.x() + int(self._velocity_x)
        self._velocity_x *= 0.968  # Hambatan gesekan udara realistis

        # Pantulan elastis jika membentur sisi monitor kiri / kanan
        if new_x < 5:
            new_x = 5
            self._velocity_x = -self._velocity_x * 0.65
            self.cat_audio.play_chirp()
        elif new_x > screen.width() - self.width() - 5:
            new_x = screen.width() - self.width() - 5
            self._velocity_x = -self._velocity_x * 0.65
            self.cat_audio.play_chirp()

        if new_y >= floor_y:
            impact_speed = abs(self._velocity_y)
            # Efek deformasi impak lentur (Impact Squash) sebanding kecepatan jatuh
            self._ragdoll_squash = min(0.42, impact_speed * 0.024)
            self._ragdoll_squash_vel = -0.05

            if impact_speed > 6.0:
                # Memantul kembali ke atas (Bounce)
                self.move(new_x, floor_y)
                self._velocity_y = -self._velocity_y * 0.36
                self._velocity_x *= 0.72  # Gesekan lantai
                self.set_state("LANDING")
            else:
                # Mendarat stabil di lantai
                self.move(new_x, floor_y)
                self._fall_timer.stop()
                self._velocity_y = 0.0
                self._velocity_x = 0.0
                self.set_state("LANDING")
                if getattr(self, "_is_entrance_falling", False):
                    self._is_entrance_falling = False
                    self.cat_audio.play_chirp()
                    QTimer.singleShot(600, self._greet_user)
                else:
                    QTimer.singleShot(750, self._after_landing)
        else:
            self.move(new_x, new_y)
            if self.speech_bubble.isVisible():
                self.speech_bubble.update_position()

    def _on_ragdoll_tick(self):
        """Loop fisika ragdoll 60 FPS: inersia ayunan saat diangkat, rotasi melayang, dan rebound benturan."""
        import math

        if self._is_dragging:
            # 1. KONDISI DIANGKAT (HELD / DRAGGED BY MOUSE)
            # Inersia pendulum: bergerak ke kanan (vx > 0) -> tubuh berayun tertinggal ke KIRI (angle > 0 di koordinat layar Qt)
            target_angle = max(-38.0, min(self._drag_velocity_x * 2.8, 38.0))

            # Goyangan alami saat diam dipegang
            self._dangle_phase += 0.14
            target_angle += math.sin(self._dangle_phase) * 3.5

            # Damped spring pendulum oscillation
            angle_error = target_angle - self._ragdoll_angle
            spring_acc = angle_error * 0.24 - self._ragdoll_angular_vel * 0.20
            self._ragdoll_angular_vel += spring_acc
            self._ragdoll_angle += self._ragdoll_angular_vel

            # Peregangan vertikal (stretch) akibat gravitasi dan kecepatan seretan kursor
            speed = math.hypot(self._drag_velocity_x, self._drag_velocity_y)
            stretch = min(0.24, speed * 0.008) + 0.06
            scale_y = 1.0 + stretch
            scale_x = 1.0 / math.sqrt(scale_y)

            self.pet_label.set_ragdoll(self._ragdoll_angle, scale_x, scale_y, anchor="scruff")

            # Reduksi bertahap jika kursor berhenti bergerak
            self._drag_velocity_x *= 0.82
            self._drag_velocity_y *= 0.82

        elif self._fall_timer.isActive():
            # 2. KONDISI JATUH MELAYANG DI UDARA (FREE FALL / TOSS)
            # Gaya sentrifugal & Tolakan angin: saat dilempar ke KANAN (vx > 0), tubuh Mimi terdorong/berayun ke KIRI (angle > 0).
            # Saat dilempar ke KIRI (vx < 0), tubuh Mimi terdorong/berayun ke KANAN (angle < 0).
            wind_flutter = math.sin(time.time() * 26.0) * min(4.0, abs(self._velocity_x) * 0.22)
            target_angle = max(-48.0, min(self._velocity_x * 2.6, 48.0)) + wind_flutter
            self._ragdoll_angle += (target_angle - self._ragdoll_angle) * 0.24

            # Peregangan jatuh vertikal & kompresi hambatan angin horizontal
            fall_stretch = min(0.18, abs(self._velocity_y) * 0.009)
            drag_squash = min(0.10, abs(self._velocity_x) * 0.005)
            scale_y = max(0.85, 1.0 + fall_stretch - drag_squash * 0.4)
            scale_x = max(0.82, 1.0 / math.sqrt(scale_y))

            self.pet_label.set_ragdoll(self._ragdoll_angle, scale_x, scale_y, anchor="scruff")

        else:
            # 3. KONDISI MENDARAT & MEMBAL ELASTIS (LANDING SQUASH REBOUND)
            squash_acc = -self._ragdoll_squash * 0.32 - self._ragdoll_squash_vel * 0.24
            self._ragdoll_squash_vel += squash_acc
            self._ragdoll_squash += self._ragdoll_squash_vel

            self._ragdoll_angle *= 0.72

            scale_y = max(0.60, 1.0 - self._ragdoll_squash)
            scale_x = min(1.45, 1.0 + self._ragdoll_squash * 1.25)

            self.pet_label.set_ragdoll(self._ragdoll_angle, scale_x, scale_y, anchor="bottom")

            # Jika osilasi sudah reda, istirahatkan loop ragdoll
            if abs(self._ragdoll_squash) < 0.008 and abs(self._ragdoll_squash_vel) < 0.008 and abs(self._ragdoll_angle) < 0.2:
                self._ragdoll_squash = 0.0
                self._ragdoll_squash_vel = 0.0
                self._ragdoll_angle = 0.0
                self.pet_label.reset_ragdoll()
                self._ragdoll_timer.stop()

    def _after_landing(self):
        if self.current_state == "LANDING":
            if self.is_spotify_dancing:
                self._trigger_random_spotify_dance()
            elif getattr(self, 'is_watching_video', False):
                self._trigger_random_video_watch()
            elif getattr(self, 'is_in_discord_voice', False):
                self._trigger_random_discord_listen()
            else:
                self.set_state("IDLE")
                self.cat_audio.play_chirp()
                replies = [
                    "Meow! Mendarat dengan mulus di 4 kaki! 🐾",
                    "Purrr~ Pendaratan sempurna ala kucing akrobat! ✨",
                    "Nyaa! Kucing selalu mendarat dengan selamat, Tuan! 🐱"
                ]
                self.speech_bubble.show_message(random.choice(replies), 3000)
                self._enforce_topmost()

    # --- CELETUKAN SPONTAN & ANIMASI OTOMATIS BERKALA ---
    def _trigger_spontaneous_cute_animation(self):
        """Memicu aksi dan animasi unik Mimi secara otomatis (joget, makan popcorn, minum boba, atau pakai headset)."""
        if not self.is_safe_for_notifications():
            return
        if self.is_spotify_dancing or getattr(self, 'is_watching_video', False) or getattr(self, 'is_in_discord_voice', False):
            return

        actions = [
            # Tarian & Joget
            ("DANCE", "Meow! Lagu ceria terngiang di kepalaku! *joget riang berirama* 💃🎶"),
            ("DANCE_DISCO", "Disco time! Tunjuk cakar ke atas! Saturday night fever di desktop Tuan! 🕺✨"),
            ("DANCE_ROCK", "Headbang mantap! Yeahhh rock on! Semangat terus ya Tuan! 🎸⚡"),
            # Bioskop & Popcorn / Minuman
            ("POPCORN", "Nyam nyam! Ngemil popcorn mentega hangat dulu biar rileks! 🍿😸"),
            ("WATCH_DRINK", "Slurp! Minum soda dingin segar menemani kerja keras Tuan! 🥤✨"),
            ("WATCH_GLASSES", "Keren banget kacamata 3D retro ini! Semuanya terasa timbul keluar layar! 🕶️🎬"),
            # Menyimak & Headset
            ("LISTEN_HEADSET", "Headset gaming Mimi pasang! Audio jernih siap memantau notifikasi Tuan! 🎧🐾"),
            ("LISTEN_NOD", "*Angguk-angguk*... Mimi selalu fokus menyimak dan menemani Tuan! 💭✨"),
            ("LISTEN", "Ssshh... Mimi duduk tenang menikmati kedamaian desktop Tuan! 🤫🐾")
        ]
        chosen_anim, msg = random.choice(actions)
        self.preview_animation(chosen_anim, msg)

    def _on_spontaneous_thought(self):
        # KRUSIAL: Notifikasi dan celetukan HANYA boleh muncul saat mode diam/normal dan tidak sedang disentuh/mengetik
        if not self.is_safe_for_notifications():
            return

        roll = random.random()
        if roll < 0.28:
            # 🎭 Animasi imut otomatis berkala (Joget, Popcorn, Minum, Headset, dsb)
            self._trigger_spontaneous_cute_animation()
        elif roll < 0.58:
            self.set_state("STRETCH")
            thought = self.ai_handler.get_spontaneous_thought()
            self.say_message(thought)
            QTimer.singleShot(3500, lambda: self.set_state("IDLE") if self.current_state == "STRETCH" else None)
        elif roll < 0.85:
            thought = self.ai_handler.get_spontaneous_thought()
            self.say_message(thought)

    # --- LOGIKA JALAN-JALAN MANDIRI ---
    def _maybe_wander(self):
        # Periksa jika ada notifikasi WhatsApp yang sempat tertunda saat pengguna mengetik
        if hasattr(self, '_pending_wa_notification') and self._pending_wa_notification and self.is_safe_for_notifications():
            sender, count = self._pending_wa_notification
            self._deliver_whatsapp_notification(sender, count)
            return

        if not self.auto_wander_enabled or self._is_dragging or self._fall_timer.isActive():
            return
        if self.active_game_window is not None and self.active_game_window.isVisible():
            return
        if getattr(self, 'is_in_discord_voice', False):
            return
        if self.current_state not in ["IDLE", "IDLE_LEFT"]:
            return

        roll = random.random()
        if roll < 0.40:
            screen = QApplication.primaryScreen().geometry()
            target_x = random.randint(40, screen.width() - self.width() - 40)
            if abs(target_x - self.x()) < 40:
                return

            self._target_x = target_x
            self.set_state("WALK_RIGHT" if self._target_x > self.x() else "WALK_LEFT")
            self._step_timer.start()
        elif roll < 0.58:
            # 🎭 Aksi animasi imut otomatis berkala
            self._trigger_spontaneous_cute_animation()
        elif roll < 0.78:
            self.set_state("SNIFF")
            QTimer.singleShot(2500, lambda: self.set_state("IDLE") if self.current_state == "SNIFF" else None)
        elif roll < 0.92:
            self.set_state("STRETCH")
            QTimer.singleShot(2800, lambda: self.set_state("IDLE") if self.current_state == "STRETCH" else None)

    def _on_walk_step(self):
        if self._is_dragging or self._fall_timer.isActive() or self.current_state not in ["WALK_LEFT", "WALK_RIGHT", "RUN_LEFT", "RUN_RIGHT"]:
            self._step_timer.stop()
            self._step_timer.setInterval(30)
            return

        current_x = self.x()
        dist = self._target_x - current_x
        is_sprint = self.current_state in ["RUN_LEFT", "RUN_RIGHT"]
        speed = 8 if is_sprint else 2

        if abs(dist) <= speed + 1:
            self.move(self._target_x, self.y())
            self._step_timer.stop()
            self._step_timer.setInterval(30)
            if self.speech_bubble.isVisible():
                self.speech_bubble.update_position()

            if is_sprint:
                self.set_state("HAPPY")
                self.cat_audio.play_purr()
                QTimer.singleShot(1800, lambda: self.set_state("IDLE") if self.current_state == "HAPPY" else None)
            elif random.random() < 0.5:
                self.set_state("SNIFF")
                QTimer.singleShot(2200, lambda: self.set_state("IDLE") if self.current_state == "SNIFF" else None)
            else:
                self.set_state("IDLE")
        else:
            step = speed if dist > 0 else -speed
            self.move(current_x + step, self.y())
            if self.speech_bubble.isVisible():
                self.speech_bubble.update_position()

    def stop_wandering(self):
        if self._step_timer.isActive():
            self._step_timer.stop()

    # --- STATE & ANIMASI ---
    def set_state(self, state: str):
        self.current_state = state
        self._inactivity_seconds = 0

        gif_map = {
            "IDLE": "cat_idle.gif",
            "IDLE_LEFT": "cat_idle_left.gif",
            "LOOK_LEFT": "cat_look_left.gif",
            "LOOK_RIGHT": "cat_look_right.gif",
            "LISTEN": "cat_listen.gif",
            "LISTEN_HEADSET": "cat_listen_headset.gif",
            "LISTEN_NOD": "cat_listen_nod.gif",
            "TALKING": "cat_talk.gif",
            "THINKING": "cat_think.gif",
            "SLEEP": "cat_sleep.gif",
            "HAPPY": "cat_happy.gif",
            "WALK_RIGHT": "cat_walk_right.gif",
            "WALK_LEFT": "cat_walk_left.gif",
            "SNIFF": "cat_sniff.gif",
            "PICKED": "cat_picked.gif",
            "LANDING": "cat_landing.gif",
            "STRETCH": "cat_stretch.gif",
            "DANCE": "cat_dance.gif",
            "DANCE_DISCO": "cat_dance_disco.gif",
            "DANCE_ROCK": "cat_dance_rock.gif",
            "RUN_LEFT": "cat_run_left.gif",
            "RUN_RIGHT": "cat_run_right.gif",
            "JUMP": "cat_jump.gif",
            "POUNCE": "cat_pounce.gif",
            "BYE": "cat_bye.gif",
            "POPCORN": "cat_popcorn.gif",
            "WATCH_DRINK": "cat_watch_drink.gif",
            "WATCH_GLASSES": "cat_watch_glasses.gif"
        }

        filename = gif_map.get(state, "cat_idle.gif")
        gif_path = os.path.join(self.assets_dir, filename)

        if os.path.exists(gif_path):
            if self.movie:
                self.movie.stop()
            self.movie = QMovie(gif_path)
            self.movie.setScaledSize(QSize(128, 128))
            self.pet_label.setMovie(self.movie)
            self.movie.start()

    def _trigger_random_spotify_dance(self):
        """Memilih animasi joget Spotify secara acak & anti-nabrak."""
        candidates = [d for d in DANCE_STATES if d != self.current_state] or DANCE_STATES
        chosen = random.choice(candidates)
        self.set_state(chosen)
        self._last_dance_switch_time = time.time()
        self._next_dance_duration = random.uniform(6.0, 10.5)

    def _trigger_random_video_watch(self):
        """Memilih animasi menonton bioskop/YouTube secara acak & anti-nabrak."""
        candidates = [w for w in WATCH_STATES if w != self.current_state] or WATCH_STATES
        chosen = random.choice(candidates)
        self.set_state(chosen)
        self._last_watch_switch_time = time.time()
        self._next_watch_duration = random.uniform(7.0, 12.5)

    def _trigger_random_discord_listen(self):
        """Memilih animasi menyimak Discord secara acak & anti-nabrak."""
        candidates = [l for l in LISTEN_STATES if l != self.current_state] or LISTEN_STATES
        chosen = random.choice(candidates)
        self.set_state(chosen)
        self._last_listen_switch_time = time.time()
        self._next_listen_duration = random.uniform(8.0, 14.5)

    def _check_inactivity(self):
        active_states = [
            "SLEEP", "THINKING", "TALKING", "WALK_LEFT", "WALK_RIGHT",
            "PICKED", "LANDING", "RUN_LEFT", "RUN_RIGHT",
            "JUMP", "POUNCE", "BYE"
        ] + DANCE_STATES + WATCH_STATES + LISTEN_STATES
        if self.current_state not in active_states:
            # Jika pengguna sedang mengetik atau dialog input aktif, jangan biarkan tertidur
            if hasattr(self, 'speech_bubble') and self.speech_bubble.is_input_active():
                self._inactivity_seconds = 0
                return

            self._inactivity_seconds += 1
            if self._inactivity_seconds >= 85:
                # Jika Spotify sedang memutar musik, sedang berburu, di voice channel Discord, atau sedang nobar video, jangan biarkan tertidur
                if self.is_spotify_dancing or self.is_hunting or getattr(self, 'is_in_discord_voice', False) or getattr(self, 'is_watching_video', False):
                    self._inactivity_seconds = 0
                    return
                self.stop_wandering()
                self.set_state("SLEEP")
                if hasattr(self, 'discord_rpc'):
                    self.discord_rpc.set_sleep_status()
                self.speech_bubble.show_message(f"Zzz... *{self.pet_name} tidur melingkar damai*", 3500)

    # --- PENGAWAL NOTIFIKASI & MODE DIAM/NORMAL MIMI ---
    def is_safe_for_notifications(self) -> bool:
        """
        Mengecek apakah Mimi berada dalam mode diam/normal yang aman
        untuk menampilkan notifikasi spontan tanpa membatalkan atau mengganggu pengguna.
        Notifikasi HANYA diizinkan saat mode diam atau normal saat Mimi tidak disentuh.
        """
        if self._is_dragging or self._fall_timer.isActive() or self._ragdoll_timer.isActive():
            return False
        if self.current_state not in ["IDLE", "IDLE_LEFT"]:
            return False
        if hasattr(self, 'speech_bubble') and self.speech_bubble.is_input_active():
            return False
        if hasattr(self, 'active_game_window') and self.active_game_window is not None and self.active_game_window.isVisible():
            return False
        if getattr(self, 'is_hunting', False):
            return False
        if getattr(self, 'is_watching_video', False):
            return False
        return True

    def _on_whatsapp_message(self, sender: str, count: int):
        """Menerima sinyal notifikasi pesan baru WhatsApp dari Google Chrome."""
        if self.is_safe_for_notifications():
            self._deliver_whatsapp_notification(sender, count)
        else:
            # Tunda notifikasi jika pengguna sedang mengetik perintah / berinteraksi
            self._pending_wa_notification = (sender, count)

    def _deliver_whatsapp_notification(self, sender: str, count: int):
        self._pending_wa_notification = None
        self.stop_wandering()
        self._inactivity_seconds = 0
        self.set_state("SNIFF")
        self.cat_audio.play_chirp()

        if sender and sender not in ["Kontak WhatsApp", ""]:
            msg = f"Meow! 🟢 Ada pesan WhatsApp baru masuk di Google Chrome dari **{sender}**! 💬🐾"
        else:
            msg = f"Meow! 🟢 Ada {count} pesan WhatsApp baru masuk di Google Chrome, Tuan! 💬🐾"

        self.speech_bubble.show_message(msg, duration_ms=7500, persistent=False, force=False)
        QTimer.singleShot(2500, lambda: self.set_state("IDLE") if self.current_state == "SNIFF" else None)

    # --- KOMUNIKASI & SUARA MEONG ---
    def say_message(self, text: str, force: bool = False):
        if hasattr(self, 'speech_bubble') and self.speech_bubble.is_input_active() and not force:
            return
        self.stop_wandering()
        self._inactivity_seconds = 0
        if self.current_state == "SLEEP":
            self.set_state("IDLE")

        self.cat_audio.play_talk()
        self.speech_bubble.show_message(text, force=force)

    def show_ai_answer(self, text: str):
        """Menampilkan jawaban atas pertanyaan: jendela tetap terbuka selamanya sampai dikonfirmasi tutup dengan tanda silang."""
        self.stop_wandering()
        self._inactivity_seconds = 0
        if self.current_state in ["SLEEP", "THINKING"]:
            self.set_state("IDLE")

        self.cat_audio.play_talk()
        self.speech_bubble.show_ai_answer(text)

    def _on_audio_start_safe(self):
        if self.current_state not in ["PICKED", "LANDING"]:
            self.set_state("TALKING")

    def _on_audio_finish_safe(self):
        if self.current_state == "TALKING":
            self.set_state("IDLE")

    def show_input(self):
        self.stop_wandering()
        self._inactivity_seconds = 0
        if self.current_state == "SLEEP":
            self.set_state("IDLE")
        self.speech_bubble.show_input()

    def setup_game_positioning(self, game_window):
        """
        Memposisikan jendela game di area tengah layar yang nyaman,
        dan menjaga Mimi tetap berdiri di bawah di lantai desktop (floor_y).
        Mimi tidak dipaksa melayang di samping jendela game.
        """
        self.active_game_window = game_window
        self.stop_wandering()

        screen = QApplication.primaryScreen().availableGeometry()
        gw = game_window.width()
        gh = game_window.height()
        mw = self.width()   # 128
        mh = self.height()  # 128
        margin = 16

        # Posisikan jendela game di tengah layar horizontal & vertikal yang nyaman
        gx = max(margin, (screen.width() - gw) // 2)
        gy = max(screen.top() + margin, (screen.height() - gh) // 2 - 25)

        # Mimi TETAP berdiri di bawah di lantai desktop (floor_y)
        floor_y = self._get_floor_y()
        mimi_y = floor_y

        # Pertahankan posisi x Mimi di lantai desktop (default: pojok kanan bawah yang aman)
        cur_x = self.x()
        mimi_x = cur_x
        # Pastikan Mimi tidak tertutup badan game_window
        if (gx - 10) <= mimi_x <= (gx + gw + 10) and gy + gh > floor_y:
            # Jika ada tumpang tindih dengan bagian bawah jendela game, geser Mimi ke kanan atau kiri jendela game
            if (screen.width() - (gx + gw)) >= mw + margin:
                mimi_x = gx + gw + margin
            else:
                mimi_x = max(margin, gx - mw - margin)

        # Batasi agar Mimi tetap di dalam batas layar
        mimi_x = max(margin, min(mimi_x, screen.width() - mw - margin))

        game_window.move(gx, gy)
        self.move(mimi_x, mimi_y)
        self.set_state("IDLE")

        game_window.show()
        game_window.raise_()
        game_window.activateWindow()

        # Kunci: Mimi dinaikkan ke paling depan
        self.raise_()
        if hasattr(self, 'speech_bubble'):
            self.speech_bubble.update_position()

    def on_game_closed(self, game_window):
        """Dipanggil ketika jendela game ditutup."""
        if self.active_game_window == game_window:
            self.active_game_window = None
            if self.chess_window == game_window: self.chess_window = None
            if self.tetris_window == game_window: self.tetris_window = None
            if self.snake_window == game_window: self.snake_window = None
            if self.sudoku_window == game_window: self.sudoku_window = None
            if self.snakes_ladders_window == game_window: self.snakes_ladders_window = None
            if self.battleship_window == game_window: self.battleship_window = None
            self.raise_()
            self.say_message(f"Meow! Permainan selesai. Mimi siap menemani aktivitas Tuan lagi! 🐾✨")

    def open_chess_game(self, difficulty: str = "Normal"):
        """Membuka jendela catur interaktif bersama Mimi."""
        self.stop_wandering()
        self._inactivity_seconds = 0
        if self.current_state == "SLEEP":
            self.set_state("IDLE")

        if hasattr(self, 'discord_rpc'):
            self.discord_rpc.set_game_status(f"Catur ({difficulty})")

        if self.chess_window is None or not self.chess_window.isVisible():
            try:
                from src.ui.chess_window import MimiChessWindow
            except ImportError:
                from ui.chess_window import MimiChessWindow
            self.chess_window = MimiChessWindow(
                pet_parent=self,
                pet_name=self.pet_name,
                default_difficulty=difficulty
            )
            self.setup_game_positioning(self.chess_window)
        else:
            if hasattr(self.chess_window, "_start_new_game"):
                self.chess_window._start_new_game(difficulty)
            self.setup_game_positioning(self.chess_window)

    def open_tetris_game(self):
        """Membuka game Tetris Mini bersama Mimi."""
        self.stop_wandering()
        self._inactivity_seconds = 0
        if self.current_state == "SLEEP":
            self.set_state("IDLE")

        if hasattr(self, 'discord_rpc'):
            self.discord_rpc.set_game_status("Tetris Balok")

        if self.tetris_window is None or not self.tetris_window.isVisible():
            try:
                from src.ui.tetris_window import MimiTetrisWindow
            except ImportError:
                from ui.tetris_window import MimiTetrisWindow
            self.tetris_window = MimiTetrisWindow(pet_parent=self, pet_name=self.pet_name)
            self.setup_game_positioning(self.tetris_window)
        else:
            self.setup_game_positioning(self.tetris_window)

    def open_snake_game(self):
        """Membuka game Snake (Ular Tangkap Ikan) bersama Mimi."""
        self.stop_wandering()
        self._inactivity_seconds = 0
        if self.current_state == "SLEEP":
            self.set_state("IDLE")

        if hasattr(self, 'discord_rpc'):
            self.discord_rpc.set_game_status("Snake Tangkap Ikan")

        if self.snake_window is None or not self.snake_window.isVisible():
            try:
                from src.ui.snake_window import MimiSnakeWindow
            except ImportError:
                from ui.snake_window import MimiSnakeWindow
            self.snake_window = MimiSnakeWindow(pet_parent=self, pet_name=self.pet_name)
            self.setup_game_positioning(self.snake_window)
        else:
            self.setup_game_positioning(self.snake_window)

    def open_sudoku_game(self, difficulty: str = "Sedang"):
        """Membuka game Sudoku interaktif bersama Mimi."""
        self.stop_wandering()
        self._inactivity_seconds = 0
        if self.current_state == "SLEEP":
            self.set_state("IDLE")

        if hasattr(self, 'discord_rpc'):
            self.discord_rpc.set_game_status(f"Sudoku ({difficulty})")

        if self.sudoku_window is None or not self.sudoku_window.isVisible():
            try:
                from src.ui.sudoku_window import MimiSudokuWindow
            except ImportError:
                from ui.sudoku_window import MimiSudokuWindow
            self.sudoku_window = MimiSudokuWindow(
                pet_parent=self,
                pet_name=self.pet_name,
                default_difficulty=difficulty
            )
            self.setup_game_positioning(self.sudoku_window)
        else:
            if hasattr(self.sudoku_window, "_start_new_game"):
                self.sudoku_window._start_new_game(difficulty)
            self.setup_game_positioning(self.sudoku_window)

    def open_ular_tangga_game(self):
        """Membuka game Ular Tangga bersama Mimi."""
        self.stop_wandering()
        self._inactivity_seconds = 0
        if self.current_state == "SLEEP":
            self.set_state("IDLE")

        if hasattr(self, 'discord_rpc'):
            self.discord_rpc.set_game_status("Ular Tangga")

        if self.snakes_ladders_window is None or not self.snakes_ladders_window.isVisible():
            try:
                from src.ui.snakes_ladders_window import MimiSnakesLaddersWindow
            except ImportError:
                from ui.snakes_ladders_window import MimiSnakesLaddersWindow
            self.snakes_ladders_window = MimiSnakesLaddersWindow(
                pet_parent=self,
                pet_name=self.pet_name
            )
            self.setup_game_positioning(self.snakes_ladders_window)
        else:
            self.setup_game_positioning(self.snakes_ladders_window)

    def open_battleship_game(self):
        """Membuka game Battleship (Kapal Perang) bersama Mimi."""
        self.stop_wandering()
        self._inactivity_seconds = 0
        if self.current_state == "SLEEP":
            self.set_state("IDLE")

        if hasattr(self, 'discord_rpc'):
            self.discord_rpc.set_game_status("Battleship Armada")

        if self.battleship_window is None or not self.battleship_window.isVisible():
            try:
                from src.ui.battleship_window import MimiBattleshipWindow
            except ImportError:
                from ui.battleship_window import MimiBattleshipWindow
            self.battleship_window = MimiBattleshipWindow(
                pet_parent=self,
                pet_name=self.pet_name
            )
            self.setup_game_positioning(self.battleship_window)
        else:
            self.setup_game_positioning(self.battleship_window)

    def _toggle_cursor_chase(self):
        """Mengaktifkan / menonaktifkan mode Mimi mengejar kursor mouse di layar."""
        self.cursor_chase_mode = not self.cursor_chase_mode
        self.stop_wandering()
        if self.cursor_chase_mode:
            self.say_message("Meow! Mode Kejar Kursor AKTIF! Gerakkan mouse Tuan, Mimi akan coba mengejarnya! 🐾🏃‍♂️")
        else:
            self.set_state("IDLE")
            self.say_message("Meow! Mode Kejar Kursor NONAKTIF. Mimi santai kembali di tempat! 🐱✨")

    def _track_cursor_interaction(self):
        """Memantau posisi kursor mouse global untuk interaksi kejar kursor."""
        if self._is_dragging or self._fall_timer.isActive():
            return

        if self.cursor_chase_mode:
            cursor_pos = QCursor.pos()
            screen = QApplication.primaryScreen().geometry()
            target_x = max(20, min(cursor_pos.x() - self.width() // 2, screen.width() - self.width() - 20))
            dist_x = target_x - self.x()

            if abs(dist_x) > 35:
                self._target_x = target_x
                new_state = "WALK_RIGHT" if dist_x > 0 else "WALK_LEFT"
                if self.current_state != new_state:
                    self.set_state(new_state)
                if not self._step_timer.isActive():
                    self._step_timer.start()
            else:
                if self.current_state in ["WALK_LEFT", "WALK_RIGHT"]:
                    self._step_timer.stop()
                    self.set_state("SNIFF")
                    self.cat_audio.play_chirp()
                    QTimer.singleShot(2000, lambda: self.set_state("IDLE") if self.current_state == "SNIFF" else None)

    # --- PEMANTAUAN & INTERAKSI APLIKASI AKTIF (WINDOWS FOREGROUND) ---
    def _check_active_application(self):
        """
        Memantau posisi dan status aplikasi yang sedang dibuka di Windows.
        - Jika diminimize, diclose, atau desktop: TIDAK BERINTERAKSI.
        - Menyesuaikan tatapan / orientasi Mimi ke arah aplikasi tersebut (kiri/kanan/sniff).
        - Menyiapkan interaksi kontekstual dan pertanyaan random.
        """
        if not self.app_observer_enabled:
            return
        if self.active_game_window is not None and self.active_game_window.isVisible():
            return
        if self._is_dragging or self._fall_timer.isActive() or self.cursor_chase_mode:
            return
        if self.current_state == "SLEEP":
            return

        app_info = window_observer.get_foreground_app_info(ignore_pids=[os.getpid()])

        # JIKA MINIMIZE, DITUTUP, ATAU DESKTOP: SEKETIKA BATALKAN & JANGAN BERINTERAKSI!
        if not app_info or app_info.get("is_minimized"):
            if getattr(self, 'is_watching_video', False):
                self.is_watching_video = False
                if self.current_state in WATCH_STATES:
                    self.set_state("IDLE")
            if self._pending_app_timer.isActive():
                self._pending_app_timer.stop()
            self._pending_app_info = None
            self._last_active_hwnd = None
            return

        # Rekam aktivitas aplikasi ke Hermes Evolution Engine
        if hasattr(self, 'hermes_engine'):
            self.hermes_engine.record_app_opened(app_info.get("app_name", ""))

        # 0. DETEKSI MODE NONTON VIDEO & BIOSKOP MINI (YouTube di Browser atau Video Player Offline)
        is_video = app_info.get("is_video", False)
        now = time.time()
        if is_video:
            if hasattr(self, 'hermes_engine'):
                self.hermes_engine.record_video_session(app_info.get("title", ""))

            if not getattr(self, 'is_watching_video', False):
                self.is_watching_video = True
                self.stop_wandering()
                self._trigger_random_video_watch()
                self.cat_audio.play_purr()
                vtype = "YouTube" if app_info.get("video_type") == "youtube" else "video offline"
                video_msgs = [
                    f"Wah, Tuan lagi mutar {vtype} nih! Mimi langsung ambil ember popcorn lezat! Nyam nyam yuk tonton bareng! 🍿🎬🐾",
                    f"Waktunya bioskop mini di desktop! Mimi siapkan minuman dingin segar & popcorn hangat! Meoww~ Nobar ya Tuan! 🥤🎬✨",
                    f"Kacamata bioskop 3D siap terpasang! Meoww~ Seru banget videonya Tuan! Nobar bareng Mimi yuk! 🕶️🍿👀🐾"
                ]
                self.speech_bubble.show_message(random.choice(video_msgs), 5500)
            else:
                if self.current_state in WATCH_STATES:
                    if now - self._last_watch_switch_time >= self._next_watch_duration:
                        candidates = [w for w in WATCH_STATES if w != self.current_state] or WATCH_STATES
                        new_watch = random.choice(candidates)
                        self.set_state(new_watch)
                        self._last_watch_switch_time = now
                        self._next_watch_duration = random.uniform(7.0, 13.0)
                elif self.current_state not in ["TALK", "THINKING", "PICKED", "LANDING"] and not self._is_dragging and not self._fall_timer.isActive():
                    self._trigger_random_video_watch()
        else:
            if getattr(self, 'is_watching_video', False):
                self.is_watching_video = False
                if self.current_state in WATCH_STATES:
                    self.set_state("IDLE")
                    self.cat_audio.play_talk()
                    self.speech_bubble.show_message("Nyam! Videonya seru banget ya Tuan! Mimi senang nobar bareng Tuan! 🍿🎬✨", 5000)

        hwnd = app_info["hwnd"]
        now = time.time()

        # 1. SPATIAL AWARENESS: Mimi menatap ke arah jendela aplikasi yang aktif TANPA gerak kaki (bebas jalan di tempat)
        win_cx = app_info["center_x"]
        mimi_cx = self.x() + self.width() // 2
        dx = win_cx - mimi_cx

        # Jika sedang di Discord Voice, jangan ubah orientasi agar Mimi tetap tenang menyimak
        if getattr(self, 'is_in_discord_voice', False):
            return

        # Jika Mimi sedang IDLE, sesuaikan arah tatapan Mimi tanpa menggerakkan kaki
        if self.current_state in ["IDLE", "IDLE_LEFT"] and not self._step_timer.isActive():
            if dx < -110:
                # Aplikasi berada di sisi kiri layar Mimi -> menoleh santai ke kiri
                if self.current_state != "LOOK_LEFT":
                    self.set_state("LOOK_LEFT")
                    QTimer.singleShot(2500, lambda: self.set_state("IDLE_LEFT") if self.current_state == "LOOK_LEFT" else None)
            elif dx > 110:
                # Aplikasi berada di sisi kanan layar Mimi -> menoleh santai ke kanan
                if self.current_state != "LOOK_RIGHT":
                    self.set_state("LOOK_RIGHT")
                    QTimer.singleShot(2500, lambda: self.set_state("IDLE") if self.current_state == "LOOK_RIGHT" else None)
            elif abs(dx) <= 110 and random.random() < 0.25:
                # Tepat di area Mimi -> Mengendus penasaran ke atas
                self.set_state("SNIFF")
                QTimer.singleShot(1800, lambda: self.set_state("IDLE") if self.current_state == "SNIFF" else None)

        # 2. CEK PERPINDAHAN APLIKASI ATAU JUDUL DOKUMEN BARU
        if hwnd != self._last_active_hwnd or (app_info["title"] and app_info["title"] != self._last_active_title):
            self._last_active_hwnd = hwnd
            self._last_active_title = app_info["title"]
            self._app_focus_start_time = now
            self._pending_app_info = app_info

            # Beri jeda wajar (3.0 detik) agar pengguna nyaman dan tidak kaget
            self._pending_app_timer.start(3000)
            return

        # 3. INTERAKSI PERIODIK JIKA FOKUS LAMA DI APLIKASI (setiap 85 detik sekali)
        if now - self._last_app_interact_time > 85.0 and (now - self._app_focus_start_time) > 40.0:
            if self.is_safe_for_notifications() and not self.speech_bubble.isVisible():
                self._trigger_app_interaction(app_info)

    def _trigger_pending_app_interaction(self):
        """Memicu interaksi atau pertanyaan random setelah jeda perpindahan aplikasi."""
        if not self._pending_app_info or not self.app_observer_enabled:
            return

        # KRUSIAL: Jangan pernah memicu interaksi jika Mimi sedang tidak aman atau input sedang terbuka
        if not self.is_safe_for_notifications():
            self._pending_app_info = None
            return

        app_info = self._pending_app_info
        self._pending_app_info = None

        # CEK ULANG KEAMANAN: Jika jendela diminimize atau ditutup saat timer berjalan, JANGAN BERINTERAKSI!
        hwnd = app_info.get("hwnd")
        if not hwnd or window_observer.is_window_minimized(hwnd) or not window_observer.is_window_valid_and_visible(hwnd):
            return

        # Pastikan jendela tersebut masih menjadi jendela foreground yang aktif
        cur_hwnd = window_observer.user32.GetForegroundWindow()
        if cur_hwnd != hwnd:
            return

        # Jangan mengganggu jika balon obrolan sedang dipakai
        if self.speech_bubble.isVisible():
            return

        # Jaga cooldown minimal 25 detik antar celetukan aplikasi
        now = time.time()
        if now - self._last_app_interact_time < 25.0:
            return

        self._trigger_app_interaction(app_info)

    def _trigger_app_interaction(self, app_info: dict):
        """Mengeksekusi celetukan dan pertanyaan random untuk aplikasi yang aktif."""
        if not self.is_safe_for_notifications():
            return

        hwnd = app_info.get("hwnd")
        if not hwnd or window_observer.is_window_minimized(hwnd) or not window_observer.is_window_valid_and_visible(hwnd):
            return

        interaction = window_observer.get_random_app_interaction(app_info)
        self._last_app_interact_time = time.time()

        # Update Discord Rich Presence jika aplikasi aktif adalah Discord
        if "parsed_discord" in interaction and hasattr(self, 'discord_rpc'):
            pd = interaction["parsed_discord"]
            target = pd.get("target", "")
            channel = pd.get("channel", "")
            info_str = f"#{channel} ({target})" if channel and target else target
            self.discord_rpc.set_discord_browse_status(info_str)

        anim = interaction.get("anim", "TALK")
        sound_type = interaction.get("sound", "talk")

        self.set_state(anim)
        if sound_type == "purr":
            self.cat_audio.play_purr()
        elif sound_type == "chirp":
            self.cat_audio.play_chirp()
        else:
            self.cat_audio.play_talk()

        self.speech_bubble.show_message(interaction["message"], 6500)
        QTimer.singleShot(3200, lambda: self.set_state("IDLE") if self.current_state == anim else None)

    def _toggle_app_observer(self):
        """Mengaktifkan / menonaktifkan pemantauan aplikasi aktif."""
        self.app_observer_enabled = not self.app_observer_enabled
        if self.app_observer_enabled:
            self.say_message("Meow! Penglihatan aplikasi AKTIF! Mimi akan memperhatikan dan menatap aplikasi apa saja yang Tuan buka! 👁️🐾✨")
        else:
            if self._pending_app_timer.isActive():
                self._pending_app_timer.stop()
            self._pending_app_info = None
            self._last_active_hwnd = None
            self.say_message("Meow! Penglihatan aplikasi NONAKTIF. Mimi santai di pojok layar dan tidak akan mengomentari aplikasimu! 🐱✨")

    def _check_spotify_music(self):
        """Memantau pemutaran musik di Spotify: Mimi joget riang secara acak & anti-nabrak jika ada lagu berputar."""
        if not self.spotify_enabled:
            return
        if self.active_game_window is not None and self.active_game_window.isVisible():
            return

        try:
            status = spotify_observer.get_spotify_playback()
        except Exception:
            return

        is_playing = status.get("is_playing", False)
        track = status.get("track", "")

        if is_playing:
            self.is_spotify_dancing = True
            self._inactivity_seconds = 0
            now = time.time()

            # Jika lagu baru terdeteksi
            if track and track != self._last_spotify_track:
                self._last_spotify_track = track
                # Ganti gaya tari secara acak untuk menyambut lagu baru
                if self.current_state in DANCE_STATES or self.current_state in ["IDLE", "SNIFF", "STRETCH", "IDLE_LEFT"]:
                    self.stop_wandering()
                    self._trigger_random_spotify_dance()

                # Tampilkan celetukan interaktif singkat hanya jika balon tidak sedang dipakai baca
                if not self.speech_bubble.isVisible() and (now - self._last_spotify_dance_toast > 20.0):
                    self._last_spotify_dance_toast = now
                    self.cat_audio.play_purr()
                    self.speech_bubble.show_message(
                        f"🎶 Asyik! Spotify lagi memutar: **{track}**! Mimi ikut joget ya Tuan! 💃🐾",
                        duration_ms=4500,
                        persistent=False
                    )

            # Jika sedang aktif joget, cek apakah waktunya rotasi gaya tari secara acak & anti-nabrak
            if self.current_state in DANCE_STATES:
                if now - self._last_dance_switch_time >= self._next_dance_duration:
                    candidates = [d for d in DANCE_STATES if d != self.current_state] or DANCE_STATES
                    new_dance = random.choice(candidates)
                    self.set_state(new_dance)
                    self._last_dance_switch_time = now
                    self._next_dance_duration = random.uniform(6.0, 10.5)
            elif self.current_state in ["IDLE", "SNIFF", "STRETCH", "IDLE_LEFT"] and not self._is_dragging and not self._fall_timer.isActive() and not self.cursor_chase_mode:
                self.stop_wandering()
                self._trigger_random_spotify_dance()
        else:
            # Lagu dijeda / dihentikan / Spotify ditutup
            if self.is_spotify_dancing:
                self.is_spotify_dancing = False
                self._last_spotify_track = ""
                if self.current_state in DANCE_STATES:
                    self.set_state("IDLE")

    def _toggle_spotify_dance(self):
        """Mengaktifkan / menonaktifkan fitur joget saat Spotify memutar lagu."""
        self.spotify_enabled = not self.spotify_enabled
        if self.spotify_enabled:
            self.say_message("Meow! Joget musik Spotify AKTIF! Mimi akan otomatis joget dengan 3 variasi tarian acak saat Tuan memutar lagu di Spotify! 💃🕺🎶🐾")
        else:
            self.is_spotify_dancing = False
            if self.current_state in DANCE_STATES:
                self.set_state("IDLE")
            self.say_message("Meow! Joget musik Spotify NONAKTIF. Mimi santai di tempat! 🐱✨")

    # --- PEMANTAUAN VOICE CHANNEL DISCORD (DUDUK DIAM & MENYIMAK) ---
    def _check_discord_voice(self):
        """
        Memantau status apakah Tuan sedang terhubung ke Voice Channel Discord:
        - Jika masuk Voice: Mimi otomatis menyimak dengan 3 variasi animasi acak (headset gaming, angguk-angguk, atau tenang).
        - Menghentikan jalan-jalan mandiri agar tidak mondar-mandir mengganggu konsentrasi.
        - Merotasi gaya menyimak secara acak & anti-nabrak tanpa me-reset mendadak.
        - Jika keluar Voice: Mimi meregangkan badan dan menyapa riang.
        """
        if self._is_dragging or self._fall_timer.isActive():
            return

        in_voice, channel_hint = False, ""
        try:
            if discord_observer:
                in_voice, channel_hint = discord_observer.check_discord_voice_active()
        except Exception:
            in_voice = False

        now = time.time()
        if in_voice and not self.is_in_discord_voice:
            # Pengguna baru saja masuk ke Voice Channel!
            self.is_in_discord_voice = True
            self.stop_wandering()
            self._trigger_random_discord_listen()
            if hasattr(self, 'discord_rpc'):
                self.discord_rpc.set_voice_status(True, channel_hint)

            voice_replies = [
                "Ssshh... Mimi pasang headset dan duduk manis menyimak obrolan Tuan ya~ 🎧🐾",
                "Mimi pasang telinga baik-baik... Suara obrolannya seru! Mimi simak dengan tenang ya Tuan~ 🤫✨",
                "Purrr~ Mimi duduk santai di sini menemani sesi voice Tuan! 🐾🎧"
            ]
            self.speech_bubble.show_message(random.choice(voice_replies), 4500)

        elif not in_voice and self.is_in_discord_voice:
            # Pengguna baru saja keluar dari Voice Channel!
            self.is_in_discord_voice = False
            if hasattr(self, 'discord_rpc'):
                self.discord_rpc.set_voice_status(False)
            if self.current_state in LISTEN_STATES:
                self.set_state("STRETCH")
                QTimer.singleShot(2200, lambda: self.set_state("IDLE") if self.current_state == "STRETCH" else None)
                self.speech_bubble.show_message("Meow~ Sesi voice-nya sudah selesai ya Tuan? Seru banget suaranya, Mimi senang ikut menyimak! 🐾✨", 4500)

        elif in_voice and self.is_in_discord_voice:
            # Tetap jaga pose menyimak dan rotasi acak & anti-nabrak selama di voice channel
            if self.current_state in LISTEN_STATES:
                if now - self._last_listen_switch_time >= self._next_listen_duration:
                    candidates = [l for l in LISTEN_STATES if l != self.current_state] or LISTEN_STATES
                    new_listen = random.choice(candidates)
                    self.set_state(new_listen)
                    self._last_listen_switch_time = now
                    self._next_listen_duration = random.uniform(8.0, 15.0)
            elif self.current_state in ["IDLE", "IDLE_LEFT"] and not self._is_dragging and not self._fall_timer.isActive():
                self._trigger_random_discord_listen()

    # --- INTERAKSI BERBURU MANGSA (TIKUS & LALAT) & AKSI DINAMIS ---
    def start_hunting(self, prey_type: str = "mouse"):
        """Mimi mulai memburu mangsa mini (tikus atau lalat) di layar desktop."""
        if self._is_dragging or self._fall_timer.isActive():
            return
        if self.current_state in ["THINKING", "TALKING", "BYE"]:
            return

        self.stop_wandering()
        self.is_hunting = True
        self._inactivity_seconds = 0
        if self.current_state == "SLEEP":
            self.set_state("IDLE")

        if self.prey_widget:
            self.prey_widget.hide()
            self.prey_widget.deleteLater()
            self.prey_widget = None

        self.prey_widget = PreyWidget(prey_type=prey_type)
        screen_geo = QApplication.primaryScreen().geometry()
        screen_w = screen_geo.width()

        offset = 260 if self.x() < screen_w // 2 else -260
        spawn_x = max(60, min(screen_w - 90, self.x() + offset))
        self.prey_widget.spawn(start_x=spawn_x)

        # FASE 1: STALK (MENGENDAP-ENDAP DENGAN BUTT WIGGLE)
        self.set_state("POUNCE")
        self.cat_audio.play_chirp()
        label_prey = "tikus" if prey_type == "mouse" else "lalat"
        self.speech_bubble.show_message(
            f"*{self.pet_name} mengendap-endap melihat ada {label_prey} lincah!* 🐾👀",
            duration_ms=2500,
            persistent=False
        )

        QTimer.singleShot(1400, self._start_hunt_chase)

    def _start_hunt_chase(self):
        if not self.is_hunting or not self.prey_widget or not self.prey_widget.isVisible():
            self.is_hunting = False
            self.set_state("IDLE")
            return

        self.prey_widget.flee_from(self.x(), self.y())
        self._hunt_step_timer.start()

    def _on_hunt_tick(self):
        if not self.is_hunting or not self.prey_widget or not self.prey_widget.isVisible():
            self._hunt_step_timer.stop()
            self.is_hunting = False
            self.set_state("IDLE")
            return

        mimi_cx = self.x() + self.width() // 2
        prey_pos = self.prey_widget.get_center_pos()
        prey_x = prey_pos.x()
        dist_x = prey_x - mimi_cx

        if dist_x > 0:
            if self.current_state != "RUN_RIGHT":
                self.set_state("RUN_RIGHT")
        else:
            if self.current_state != "RUN_LEFT":
                self.set_state("RUN_LEFT")

        run_speed = 9
        if abs(dist_x) <= 85:
            # FASE 3: LOMPAT TERKAM!
            self._hunt_step_timer.stop()
            self._execute_pounce_attack()
        else:
            step = run_speed if dist_x > 0 else -run_speed
            self.move(self.x() + step, self.y())
            if self.speech_bubble.isVisible():
                self.speech_bubble.update_position()

    def _execute_pounce_attack(self):
        """Melompat menerkam mangsa di titik akhir."""
        self.set_state("JUMP")
        self.cat_audio.play_talk()

        init_y = self.y()
        self.move(self.x() + (25 if self.current_state == "RUN_RIGHT" else -25), init_y - 25)

        def land_and_resolve():
            self.move(self.x(), init_y)
            if random.random() < 0.82:
                if self.prey_widget:
                    self.prey_widget.caught()
                self.set_state("HAPPY")
                self.cat_audio.play_purr()
                self.speech_bubble.show_message(
                    "HAP!! 🐾✨ Cakar sakti Mimi berhasil menerkam mangsa!",
                    duration_ms=3500,
                    persistent=False
                )
            else:
                if self.prey_widget:
                    self.prey_widget.escape()
                self.set_state("SNIFF")
                self.cat_audio.play_chirp()
                self.speech_bubble.show_message(
                    "Meoww! Cepat sekali kaburnya! Lain kali pasti kena cakar Mimi! 😼💨",
                    duration_ms=3500,
                    persistent=False
                )

            self.is_hunting = False
            QTimer.singleShot(3200, lambda: self.set_state("IDLE") if self.current_state in ["HAPPY", "SNIFF"] else None)

        QTimer.singleShot(350, land_and_resolve)

    def _maybe_spontaneous_play(self):
        """Mimi secara berkala dan acak bermain sendiri: berburu tikus, menyergap lalat, sprint lari kencang, atau melompat gembira."""
        # Jadwalkan interval berikutnya secara acak antara 45 s.d 80 detik
        next_interval = random.randint(45000, 80000)
        self.spontaneous_play_timer.setInterval(next_interval)

        # Cek kondisi agar Mimi hanya beraksi saat mode diam/normal dan aman (tidak disentuh / mengetik)
        if not self.is_safe_for_notifications():
            return
        if self.cursor_chase_mode or self.is_spotify_dancing or self._step_timer.isActive():
            return

        if not self.speech_bubble.isVisible():
            action_choice = random.choice(["mouse", "fly", "sprint", "jump"])
            screen_w = QApplication.primaryScreen().geometry().width()
            if action_choice == "mouse":
                self.start_hunting("mouse")
            elif action_choice == "fly":
                self.start_hunting("fly")
            elif action_choice == "sprint":
                direction = "right" if self.x() < screen_w // 2 else "left"
                self.action_sprint(direction)
            elif action_choice == "jump":
                self.action_high_jump()

    def action_sprint(self, direction="right"):
        """Mimi berlari kencang menyeberang desktop."""
        if self._is_dragging or self._fall_timer.isActive() or self.is_hunting:
            return
        self.stop_wandering()
        self._inactivity_seconds = 0
        state = "RUN_RIGHT" if direction == "right" else "RUN_LEFT"
        self.set_state(state)
        self.cat_audio.play_talk()
        self.speech_bubble.show_message("Wuuush! 🏃💨 Mimi sprint zoomies!", duration_ms=2000, persistent=False)

        screen_w = QApplication.primaryScreen().geometry().width()
        target_x = min(screen_w - 140, self.x() + 350) if direction == "right" else max(40, self.x() - 350)
        self._target_x = target_x
        self._step_timer.setInterval(20)
        self._step_timer.start()

    def action_high_jump(self):
        """Mimi melompat tinggi gembira."""
        if self._is_dragging or self._fall_timer.isActive() or self.is_hunting:
            return
        self.stop_wandering()
        self._inactivity_seconds = 0
        self.set_state("JUMP")
        self.cat_audio.play_talk()
        self.speech_bubble.show_message("Huuup! 🦘✨ Melompat gembira!", duration_ms=2000, persistent=False)
        init_y = self.y()
        self.move(self.x(), init_y - 45)
        QTimer.singleShot(350, lambda: self.move(self.x(), init_y))
        QTimer.singleShot(500, lambda: self.set_state("HAPPY"))
        QTimer.singleShot(2200, lambda: self.set_state("IDLE") if self.current_state == "HAPPY" else None)

    def handle_user_prompt(self, prompt: str):
        self.stop_wandering()
        self._inactivity_seconds = 0

        # Cek perintah langsung untuk game & kursor & spotify & hunting
        low = prompt.lower().strip()
        if any(w in low for w in ["main catur", "ayo catur", "buka catur", "bermain catur", "lawan catur", "chess"]):
            diff = "Normal"
            if any(w in low for w in ["sulit", "hard", "master", "jago", "ahli"]):
                diff = "Sulit"
            elif any(w in low for w in ["mudah", "easy", "santai", "gampang", "pemula"]):
                diff = "Mudah"
            self.open_chess_game(diff)
            self.say_message(f"Meow! Mimi sudah siapkan papan catur di mode {diff}! Ayo uji kemampuan strategi, Tuan! 🐾♟️")
            return
        elif any(w in low for w in ["tetris", "main tetris", "buka tetris", "game tetris"]):
            self.open_tetris_game()
            self.say_message("Meow! Game Tetris sudah Mimi siapkan! Susun baloknya yang rapi ya Tuan! 🧱🐾")
            return
        elif any(w in low for w in ["ular tangga", "main ular tangga", "buka ular tangga", "game ular tangga", "snakes and ladders"]):
            self.open_ular_tangga_game()
            self.say_message("Meow! Papan Ular Tangga siap! Ayo berlomba mencapai petak 100 bersama Mimi! 🎲🐾")
            return
        elif any(w in low for w in ["snake", "main snake", "buka snake", "game ular", "main ular"]):
            self.open_snake_game()
            self.say_message("Meow! Game Snake siap! Bantu ular kucing tangkap ikan 🐟 sebanyak-banyaknya ya Tuan! 🐾")
            return
        elif any(w in low for w in ["sudoku", "main sudoku", "buka sudoku", "game sudoku"]):
            diff = "Sedang"
            if any(w in low for w in ["sulit", "hard", "master"]):
                diff = "Sulit"
            elif any(w in low for w in ["mudah", "easy", "gampang"]):
                diff = "Mudah"
            self.open_sudoku_game(diff)
            self.say_message(f"Meow! Mimi sudah siapkan teka-teki Sudoku mode {diff}! Selamat mengasah logika, Tuan! 🐾🧩")
            return
        elif any(w in low for w in ["battleship", "main battleship", "buka battleship", "game battleship", "kapal perang", "perang kapal"]):
            self.open_battleship_game()
            self.say_message("Meow! Armada Battleship siap tempur! Tenggelamkan semua armada Mimi ya Tuan! 🚢⚓💥")
            return
        elif any(w in low for w in ["kejar kursor", "ikuti kursor", "kejar mouse", "ikuti mouse", "tangkap kursor"]):
            self._toggle_cursor_chase()
            return
        elif any(w in low for w in ["pantau aplikasi", "lihat aplikasi", "interaksi aplikasi", "amati aplikasi"]):
            self._toggle_app_observer()
            return
        elif any(w in low for w in ["joget spotify", "joget musik", "goyang spotify", "dansa spotify", "spotify joget"]):
            self._toggle_spotify_dance()
            return
        elif any(w in low for w in ["kejar tikus", "tangkap tikus", "buru tikus", "ada tikus"]):
            self.start_hunting("mouse")
            return
        elif any(w in low for w in ["kejar lalat", "tangkap lalat", "buru lalat", "ada lalat"]):
            self.start_hunting("fly")
            return
        elif any(w in low for w in ["lari", "berlari", "sprint", "ayo lari"]):
            self.action_sprint("right" if self.x() < 500 else "left")
            return
        elif any(w in low for w in ["lompat", "melompat", "jump", "ayo lompat"]):
            self.action_high_jump()
            return
        elif any(w in low for w in ["menerkam", "terkam", "pounce", "sergap"]):
            self.start_hunting("mouse")
            return

        self.set_state("THINKING")
        self.speech_bubble.show_message(f"🤔 *{self.pet_name} sedang berpikir...*", 14000)

        self.ai_handler.ask(
            prompt=prompt,
            on_thinking=lambda: self.set_state("THINKING") if self.current_state != "PICKED" else None,
            on_searching=lambda status_msg: self.speech_bubble.show_message(f"🔍 *{status_msg}*", 14000),
            on_response=self._on_ai_response,
            on_error=self._on_ai_error
        )

    def _on_ai_response(self, reply: str):
        if reply.startswith("__ACTION_CHESS__:"):
            diff = reply.split(":", 1)[1].strip() or "Normal"
            self.open_chess_game(diff)
            self.say_message(f"Meow! Papan catur mode {diff} sudah siap! Silakan melangkah duluan ya Tuan! 🐾♟️")
            return
        elif reply == "__ACTION_TETRIS__":
            self.open_tetris_game()
            self.say_message("Meow! Game Tetris dibuka! Selamat menyusun balok, Tuan! 🧱🐾")
            return
        elif reply == "__ACTION_SNAKE__":
            self.open_snake_game()
            self.say_message("Meow! Game Snake dibuka! Tangkap ikan sebanyak-banyaknya ya Tuan! 🐍🐟🐾")
            return
        elif reply.startswith("__ACTION_SUDOKU__"):
            parts = reply.split(":", 1)
            diff = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "Sedang"
            self.open_sudoku_game(diff)
            self.say_message(f"Meow! Teka-teki Sudoku mode {diff} dibuka! Selamat bermain, Tuan! 🐾🧩")
            return
        elif reply == "__ACTION_ULAR_TANGGA__":
            self.open_ular_tangga_game()
            self.say_message("Meow! Papan Ular Tangga dibuka! Siap-siap melempar dadu ya Tuan! 🎲🐾")
            return
        elif reply == "__ACTION_BATTLESHIP__":
            self.open_battleship_game()
            self.say_message("Meow! Game Battleship dibuka! Atur formasimu dan luncurkan torpedo! 🚢💥")
            return
        elif reply == "__ACTION_CHASE_CURSOR__":
            self._toggle_cursor_chase()
            return
        elif reply == "__ACTION_TOGGLE_APP_OBSERVER__":
            self._toggle_app_observer()
            return
        elif reply == "__ACTION_TOGGLE_SPOTIFY_DANCE__":
            self._toggle_spotify_dance()
            return
        elif reply.startswith("__ACTION_ANIMATION__:"):
            parts = reply.split(":", 2)
            state = parts[1] if len(parts) > 1 else "DANCE"
            toast = parts[2] if len(parts) > 2 else ""
            self.preview_animation(state, toast)
            return
        self.show_ai_answer(reply)

    def _on_ai_error(self, err: str):
        fallback = f"Meow! Terjadi kendala: {err}. Mimi tetap di sini ya Tuan!"
        self.show_ai_answer(fallback)

    # --- MOUSE EVENTS & INTERAKSI KURSOR ---
    def enterEvent(self, event):
        """Saat kursor mouse masuk ke tubuh Mimi."""
        super().enterEvent(event)
        self._pet_stroke_distance = 0
        self._last_hover_pos = QCursor.pos()

        if self.current_state == "SLEEP":
            self.set_state("STRETCH")
            self.cat_audio.play_chirp()
            self.speech_bubble.show_message(f"Meow! Mimi terbangun karena kursor Tuan menyapa! 🐾✨", 3500)
            QTimer.singleShot(2400, lambda: self.set_state("IDLE") if self.current_state == "STRETCH" else None)
        elif self.current_state == "IDLE":
            self.set_state("SNIFF")
            self.cat_audio.play_chirp()
            QTimer.singleShot(1800, lambda: self.set_state("IDLE") if self.current_state == "SNIFF" else None)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._pet_stroke_distance = 0

    def mouseMoveEvent(self, event):
        if self._is_dragging and (event.buttons() & Qt.LeftButton):
            cur_pos = event.globalPos()
            now = time.time()
            if self._last_drag_pos is not None:
                dt = max(0.008, now - self._last_drag_time)
                instant_vx = (cur_pos.x() - self._last_drag_pos.x()) / (dt * 60.0)
                instant_vy = (cur_pos.y() - self._last_drag_pos.y()) / (dt * 60.0)
                # Smoothing filter kecepatan gerak seretan kursor
                self._drag_velocity_x = self._drag_velocity_x * 0.55 + instant_vx * 0.45
                self._drag_velocity_y = self._drag_velocity_y * 0.55 + instant_vy * 0.45

            self._last_drag_pos = cur_pos
            self._last_drag_time = now

            self.move(cur_pos - self._drag_pos)
            if self.speech_bubble.isVisible():
                self.speech_bubble.update_position()
            event.accept()
        else:
            # Deteksi Elus-elus Kucing via Kursor Mouse (Petting)
            cur_pos = event.globalPos()
            delta = (cur_pos - self._last_hover_pos).manhattanLength()
            self._last_hover_pos = cur_pos
            if delta > 3:
                self._pet_stroke_distance += delta
                if self._pet_stroke_distance > 130:
                    self._pet_stroke_distance = 0
                    now = time.time()
                    if now - self._last_pet_time > 4.0:
                        self._last_pet_time = now
                        self._on_petted_by_cursor()
            super().mouseMoveEvent(event)

    def _on_petted_by_cursor(self):
        """Respons bahagia saat tubuh Mimi dielus-elus bolak-balik dengan kursor mouse."""
        self.stop_wandering()
        self._inactivity_seconds = 0
        self.set_state("HAPPY")
        self.cat_audio.play_purr()
        replies = [
            "Purrrrr~ Enak sekali dielus kursor Tuan! Mimi suka! 🥰✨🐾",
            "Nyaaa~ Geli-geli manja! Usap Mimi terus Tuan! 💕🐾",
            "Purrr~ Mendengkur bahagia saat dielus kursor Tuan! Sayang Tuan! 🥰🐱",
            "Meoww! Kursor Tuan lembut sekali! Mimi merasa disayang~ 💖🐾"
        ]
        self.speech_bubble.show_message(random.choice(replies), 4500)
        QTimer.singleShot(3500, lambda: self.set_state("IDLE") if self.current_state == "HAPPY" else None)

    def mousePressEvent(self, event):
        self._inactivity_seconds = 0
        if hasattr(self, '_pending_app_timer') and self._pending_app_timer.isActive():
            self._pending_app_timer.stop()
            self._pending_app_info = None

        if event.button() == Qt.LeftButton:
            self.stop_wandering()
            if self._fall_timer.isActive():
                self._fall_timer.stop()

            self._is_dragging = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self._last_drag_pos = event.globalPos()
            self._last_drag_time = time.time()
            self._drag_velocity_x = 0.0
            self._drag_velocity_y = 0.0
            self._velocity_x = 0.0
            self._velocity_y = 0.0

            self.pet_label.setCursor(Qt.ClosedHandCursor)
            self._inactivity_seconds = 0

            # Jalankan fisika ragdoll saat diangkat
            self._ragdoll_timer.start()

            # Putar suara meong kaget & ubah animasi
            self.cat_audio.play_picked()
            self.set_state("PICKED")
            event.accept()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.pet_label.setCursor(Qt.OpenHandCursor)

            # Pewarisan momentum lemparan tangan (Toss Physics)
            self._velocity_x = max(-26.0, min(self._drag_velocity_x * 0.75, 26.0))
            self._velocity_y = max(-24.0, min(self._drag_velocity_y * 0.75, 24.0))

            floor_y = self._get_floor_y()
            if self.y() < floor_y - 20 or abs(self._velocity_y) > 4.0 or abs(self._velocity_x) > 4.0:
                self.speech_bubble.hide_bubble()
                self._fall_timer.start()
                self._ragdoll_timer.start()
            else:
                self.move(self.x(), floor_y)
                self._velocity_x = 0.0
                self._velocity_y = 0.0
                self._ragdoll_timer.start()
                self.set_state("IDLE")
            self._enforce_topmost()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.show_input()
            event.accept()

    # --- CONTEXT MENU LENGKAP & PUSAT MEMORI ---
    def _show_context_menu(self, global_pos):
        self.stop_wandering()
        self._inactivity_seconds = 0
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFDF9; color: #2D2424;
                border: 1.5px solid #D8C3A5; border-radius: 9px;
                padding: 5px; font-family: 'Segoe UI', sans-serif; font-size: 11px;
            }
            QMenu::item { padding: 5px 20px 5px 10px; border-radius: 5px; }
            QMenu::item:selected { background-color: #F8E1D4; color: #8E3B20; }
            QMenu::separator { height: 1px; background: #E8D8C8; margin: 4px 5px; }
        """)

        # PUSAT MEMORI & TRAINING DATA
        action_memory = QAction("🧠 Latih Data & Memori AI", self)
        action_memory.triggered.connect(self._show_memory_dialog)
        menu.addAction(action_memory)

        action_hermes = QAction("🧬 Evolusi Hermes Agent Mimi", self)
        action_hermes.triggered.connect(self._open_hermes_window)
        menu.addAction(action_hermes)

        # SUBMENU 1: KONTROL SISTEM & CMD
        menu_system = menu.addMenu("⚡ Kontrol Sistem & CMD")
        menu_system.setStyleSheet(menu.styleSheet())

        act_sys_cmd = QAction("💻 Buka Command Prompt (CMD)", self)
        act_sys_cmd.triggered.connect(lambda: self.say_message(desktop_actions.open_cmd_terminal()))
        menu_system.addAction(act_sys_cmd)

        act_sys_timer = QAction("⏱️ Set Timer Shutdown Komputer...", self)
        act_sys_timer.triggered.connect(self._action_prompt_shutdown_timer)
        menu_system.addAction(act_sys_timer)

        act_sys_cancel = QAction("❌ Batalkan Timer Shutdown", self)
        act_sys_cancel.triggered.connect(lambda: self.say_message(desktop_actions.cancel_shutdown()))
        menu_system.addAction(act_sys_cancel)

        act_sys_sleep = QAction("💤 Tidurkan Komputer (Sleep)", self)
        act_sys_sleep.triggered.connect(lambda: self.say_message(desktop_actions.sleep_computer(0)))
        menu_system.addAction(act_sys_sleep)

        act_sys_lock = QAction("🔒 Kunci Layar (Lock Screen)", self)
        act_sys_lock.triggered.connect(lambda: self.say_message(desktop_actions.lock_computer()))
        menu_system.addAction(act_sys_lock)

        # BROWSER & PENCARIAN OTOMATIS (Langsung tanpa pilihan berbelit)
        act_auto_browser = QAction("🌐 Buka Browser / Cari Otomatis...", self)
        act_auto_browser.triggered.connect(self._action_prompt_auto_browser)
        menu.addAction(act_auto_browser)

        # SUBMENU YOUTUBE: JELAJAH, CARI & PUTAR VIDEO
        menu_youtube = menu.addMenu("🎬 YouTube")
        menu_youtube.setStyleSheet(menu.styleSheet())

        act_yt_explore = QAction("🌐 Jelajah YouTube (Beranda / Trending)", self)
        act_yt_explore.triggered.connect(lambda: self.say_message(desktop_actions.explore_youtube()))
        menu_youtube.addAction(act_yt_explore)

        act_yt_search = QAction("🔍 Cari Video di YouTube (Search)...", self)
        act_yt_search.triggered.connect(self._action_prompt_youtube_search)
        menu_youtube.addAction(act_yt_search)

        act_yt_play = QAction("▶️ Putar Video YouTube Langsung...", self)
        act_yt_play.triggered.connect(self._action_prompt_youtube_play)
        menu_youtube.addAction(act_yt_play)

        # AKSI CEPAT DESKTOP LAINNYA
        action_note = QAction("📝 Buka Buku Catatan (Notepad)", self)
        action_note.triggered.connect(lambda: self.say_message(desktop_actions.open_notes()))
        menu.addAction(action_note)

        # SUBMENU 3: MINI GAMES (CATUR, TETRIS, SNAKE)
        menu_games = menu.addMenu("🎮 Game Seru bersama Mimi")
        menu_games.setStyleSheet(menu.styleSheet())

        # Catur
        menu_chess = menu_games.addMenu("♟️ Bermain Catur (Chess)")
        menu_chess.setStyleSheet(menu.styleSheet())
        act_ch_easy = QAction("🟢 Mode Mudah (Anak Kucing)", self)
        act_ch_easy.triggered.connect(lambda: self.open_chess_game("Mudah"))
        menu_chess.addAction(act_ch_easy)

        act_ch_norm = QAction("🟡 Mode Normal (Kucing Cerdik)", self)
        act_ch_norm.triggered.connect(lambda: self.open_chess_game("Normal"))
        menu_chess.addAction(act_ch_norm)

        act_ch_hard = QAction("🔴 Mode Sulit (Kucing Master)", self)
        act_ch_hard.triggered.connect(lambda: self.open_chess_game("Sulit"))
        menu_chess.addAction(act_ch_hard)

        # Tetris
        act_tetris = QAction("🧱 Bermain Tetris (Balok)", self)
        act_tetris.triggered.connect(self.open_tetris_game)
        menu_games.addAction(act_tetris)

        # Snake
        act_snake = QAction("🐍 Bermain Snake (Tangkap Ikan)", self)
        act_snake.triggered.connect(self.open_snake_game)
        menu_games.addAction(act_snake)

        # Sudoku
        menu_sudoku = menu_games.addMenu("🧩 Bermain Sudoku (Angka)")
        menu_sudoku.setStyleSheet(menu.styleSheet())
        act_su_easy = QAction("🟢 Mode Mudah (~38 Clue)", self)
        act_su_easy.triggered.connect(lambda: self.open_sudoku_game("Mudah"))
        menu_sudoku.addAction(act_su_easy)
        act_su_norm = QAction("🟡 Mode Sedang (~30 Clue)", self)
        act_su_norm.triggered.connect(lambda: self.open_sudoku_game("Sedang"))
        menu_sudoku.addAction(act_su_norm)
        act_su_hard = QAction("🔴 Mode Sulit (~24 Clue)", self)
        act_su_hard.triggered.connect(lambda: self.open_sudoku_game("Sulit"))
        menu_sudoku.addAction(act_su_hard)

        # Ular Tangga
        act_snakes = QAction("🎲 Bermain Ular Tangga", self)
        act_snakes.triggered.connect(self.open_ular_tangga_game)
        menu_games.addAction(act_snakes)

        # Battleship
        act_battleship = QAction("🚢 Bermain Battleship (Kapal)", self)
        act_battleship.triggered.connect(self.open_battleship_game)
        menu_games.addAction(act_battleship)


        action_workspace = QAction("🚀 Buka Workspace Antigravity / Folder", self)
        action_workspace.triggered.connect(lambda: self.say_message(desktop_actions.open_antigravity()))
        menu.addAction(action_workspace)
        menu.addSeparator()

        action_pet = QAction(f"🐟 Beri Makan Ikan / 🐾 Elus {self.pet_name}", self)
        action_pet.triggered.connect(self._action_pet_cat)
        menu.addAction(action_pet)

        action_talk = QAction("💬 Tanya / Beri Perintah", self)
        action_talk.triggered.connect(self.show_input)
        menu.addAction(action_talk)

        menu.addSeparator()

        action_api = QAction("🔑 Atur Gemini API Key", self)
        action_api.triggered.connect(self._action_configure_api_key)
        menu.addAction(action_api)

        status_text = self.ai_handler.get_mode_status()
        action_status = QAction(status_text, self)
        action_status.setEnabled(False)
        menu.addAction(action_status)

        menu.addSeparator()

        wander_label = "🛑 Diam di Tempat" if self.auto_wander_enabled else "🚶 Aktifkan Jalan-Jalan"
        action_wander = QAction(wander_label, self)
        action_wander.triggered.connect(self._toggle_wander)
        menu.addAction(action_wander)

        chase_label = "🐾 Matikan Kejar Kursor" if self.cursor_chase_mode else "🐾 Aktifkan Kejar Kursor"
        action_chase = QAction(chase_label, self)
        action_chase.triggered.connect(self._toggle_cursor_chase)
        menu.addAction(action_chase)

        mute_label = "🔊 Unmute Meong" if self.cat_audio.is_muted() else "🔇 Mute Meong"
        action_mute = QAction(mute_label, self)
        action_mute.triggered.connect(self._toggle_mute)
        menu.addAction(action_mute)

        sleep_label = "☀️ Bangun" if self.current_state == "SLEEP" else "💤 Tidur"
        action_sleep = QAction(sleep_label, self)
        action_sleep.triggered.connect(self._toggle_sleep)
        menu.addAction(action_sleep)

        menu.addSeparator()

        is_auto = autostart.is_autostart_enabled()
        auto_label = "🚀 Aktif Otomatis saat Windows Menyala: [ON]" if is_auto else "🚀 Aktif Otomatis saat Windows Menyala: [OFF]"
        action_autostart = QAction(auto_label, self)
        action_autostart.triggered.connect(self._toggle_autostart)
        menu.addAction(action_autostart)

        menu.addSeparator()

        action_exit = QAction("❌ Keluar (Exit)", self)
        action_exit.triggered.connect(self._exit_app)
        menu.addAction(action_exit)

        menu.exec_(global_pos)

    def _show_memory_dialog(self):
        self.stop_wandering()
        dlg = MemoryDialog(self, on_memory_updated=self.say_message)
        dlg.exec_()

    def preview_animation(self, state: str, toast: str = ""):
        """Memperagakan animasi tertentu untuk demonstrasi/preview pengguna."""
        self.stop_wandering()
        self.set_state(state)
        self.cat_audio.play_purr()
        if toast:
            self.speech_bubble.show_message(toast, duration_ms=4500)
        # Kembalikan ke IDLE setelah 6.5 detik jika tidak ada interaksi lain
        QTimer.singleShot(6500, lambda: self.set_state("IDLE") if self.current_state == state else None)

    def _action_prompt_shutdown_timer(self):
        self.stop_wandering()
        minutes, ok = QInputDialog.getInt(
            self,
            "Timer Shutdown Komputer",
            "Berapa menit lagi komputer ingin dimatikan?",
            30, 1, 1440, 1
        )
        if ok and minutes > 0:
            res = desktop_actions.shutdown_computer(minutes * 60)
            self.say_message(res)

    def _action_prompt_auto_browser(self):
        self.stop_wandering()
        query, ok = QInputDialog.getText(
            self,
            "🌐 Browser & Pencarian Otomatis",
            "Ketik kueri pencarian, gambar, saham, atau link web:\n(Kosongkan atau tekan OK langsung untuk membuka browser)",
            QLineEdit.Normal,
            ""
        )
        if ok:
            if not query.strip():
                res = desktop_actions.open_browser()
            else:
                res = desktop_actions.smart_browser_search(query.strip())
            self.say_message(res)

    def _action_prompt_youtube_search(self):
        self.stop_wandering()
        query, ok = QInputDialog.getText(
            self,
            "🔍 Cari Video di YouTube",
            "Ketik judul video atau topik yang ingin dicari di YouTube:\n(Misal: tutorial python pemula, podcast seru)",
            QLineEdit.Normal,
            ""
        )
        if ok and query.strip():
            res = desktop_actions.search_youtube(query.strip())
            self.say_message(res)

    def _action_prompt_youtube_play(self):
        self.stop_wandering()
        query, ok = QInputDialog.getText(
            self,
            "▶️ Putar Video YouTube Langsung",
            "Ketik judul lagu atau video yang ingin langsung diputar:\n(Misal: Laskar Pelangi Nidji, Coldplay Yellow)",
            QLineEdit.Normal,
            ""
        )
        if ok and query.strip():
            res = desktop_actions.play_youtube(query.strip())
            self.say_message(res)

    def _action_prompt_google_search(self):
        return self._action_prompt_auto_browser()

    def _action_prompt_image_search(self):
        self.stop_wandering()
        query, ok = QInputDialog.getText(
            self,
            "Pencarian Gambar Google Images",
            "Ketik gambar apa yang ingin dicari:\n(Misal: lamborghini)",
            QLineEdit.Normal,
            "lamborghini"
        )
        if ok and query.strip():
            res = desktop_actions.browser_search(query.strip(), is_image=True)
            self.say_message(res)

    def _action_pet_cat(self):
        self.stop_wandering()
        self.set_state("HAPPY")
        self.cat_audio.play_happy()
        reaction = self.ai_handler.get_pet_reaction()
        self.speech_bubble.show_message(reaction)
        QTimer.singleShot(4000, lambda: self.set_state("IDLE") if self.current_state == "HAPPY" else None)

    def _action_configure_api_key(self):
        self.stop_wandering()
        current_key = self.ai_handler.api_key if "your_gemini_api_key" not in self.ai_handler.api_key else ""
        new_key, ok = QInputDialog.getText(
            self,
            "Pengaturan Google Gemini API Key",
            "Masukkan Google Gemini API Key Anda:\n(Dapatkan gratis di https://aistudio.google.com/)",
            QLineEdit.Normal,
            current_key
        )
        if ok and new_key.strip():
            api_val = new_key.strip()
            self.ai_handler.update_config(api_val, self.ai_handler.model_name, self.pet_name)

            env_path = os.path.join(os.path.dirname(__file__), ".env")
            try:
                env_content = ""
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    updated = False
                    new_lines = []
                    for line in lines:
                        if line.startswith("GEMINI_API_KEY="):
                            new_lines.append(f"GEMINI_API_KEY={api_val}\n")
                            updated = True
                        else:
                            new_lines.append(line)
                    if not updated:
                        new_lines.append(f"GEMINI_API_KEY={api_val}\n")
                    env_content = "".join(new_lines)
                else:
                    env_content = f"GEMINI_API_KEY={api_val}\nGEMINI_MODEL=gemini-flash-latest\nPET_NAME={self.pet_name}\nTTS_ENABLED=true\nTTS_RATE=175\n"

                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(env_content)

                self.say_message("Meow! Keren sekali Tuan! API Key berhasil diperbarui!")
            except Exception as e:
                self.say_message(f"API Key terpasang di memori, tapi gagal menulis file: {e}")

    def _toggle_wander(self):
        self.auto_wander_enabled = not self.auto_wander_enabled
        if not self.auto_wander_enabled:
            self.stop_wandering()
            if self.current_state in ["WALK_LEFT", "WALK_RIGHT", "SNIFF"]:
                self.set_state("IDLE")
            self.speech_bubble.show_message("Meow! Aku duduk tenang di sini menemani Tuan.", 2500)
        else:
            self.speech_bubble.show_message("Nyaa~ Asyik! Aku mulai jalan-jalan lagi di layarmu!", 2500)

    def _toggle_mute(self):
        is_enabled = self.cat_audio.toggle_mute()
        status = "Suara meong diaktifkan! 🐱" if is_enabled else "Suara meong dibisukan (Mute) 🔇"
        self.speech_bubble.show_message(status, 2500)

    def _toggle_sleep(self):
        self.stop_wandering()
        if self.current_state == "SLEEP":
            self.set_state("IDLE")
            self.say_message("Meow! Aku sudah bangun dan segar kembali, Tuan!")
        else:
            self.set_state("SLEEP")
            self.speech_bubble.show_message("Zzz... Selamat istirahat juga ya Tuan.", 3000)

    def _toggle_autostart(self):
        if autostart.is_autostart_enabled():
            ok, msg = autostart.disable_autostart()
        else:
            ok, msg = autostart.enable_autostart()

        if hasattr(self, 'act_tray_auto') and self.act_tray_auto:
            is_auto = autostart.is_autostart_enabled()
            self.act_tray_auto.setText("🚀 Aktif Otomatis saat Windows Menyala: [ON]" if is_auto else "🚀 Aktif Otomatis saat Windows Menyala: [OFF]")

        self.say_message(msg)

    def showEvent(self, event):
        super().showEvent(event)
        self._enforce_topmost()
        if not self._intro_played:
            self._intro_played = True
            QTimer.singleShot(150, self.play_intro_spawn)

    def play_intro_spawn(self):
        """Animasi keren dan lucu saat Mimi pertama kali aktif/muncul di layar."""
        target_floor_y = self._get_floor_y()

        # Mulai meluncur dari atas (~180px di atas posisi lantai)
        start_y = max(40, target_floor_y - 180)
        self.move(self.x(), start_y)
        self.set_state("JUMP")

        self._spawn_step = 0
        self._spawn_timer = QTimer(self)
        self._spawn_timer.setInterval(22)

        def on_spawn_tick():
            self._spawn_step += 1
            cur_y = self.y()
            if cur_y < target_floor_y - 10:
                speed = min(18, 6 + self._spawn_step * 2)
                self.move(self.x(), min(target_floor_y, cur_y + speed))
            else:
                self.move(self.x(), target_floor_y)
                self._spawn_timer.stop()
                self.set_state("LANDING")
                self.cat_audio.play_chirp()
                self._enforce_topmost()

                hour = datetime.datetime.now().hour
                if 5 <= hour < 12:
                    sapaan = "Selamat pagi Tuan!"
                elif 12 <= hour < 17:
                    sapaan = "Selamat siang Tuan!"
                elif 17 <= hour < 21:
                    sapaan = "Selamat sore Tuan!"
                else:
                    sapaan = "Selamat malam Tuan!"

                QTimer.singleShot(350, lambda: self.speech_bubble.show_message(
                    f"Meow! {sapaan} Mimi sudah siap aktif dan menemani Tuan hari ini! 🌟🐾✨",
                    duration_ms=4500,
                    persistent=False
                ))
                # Jika Spotify, Video YouTube, atau Discord Voice sudah aktif, langsung lanjutkan mode tersebut!
                if self.is_spotify_dancing:
                    QTimer.singleShot(1800, lambda: self._trigger_random_spotify_dance() if self.current_state == "LANDING" else None)
                elif getattr(self, 'is_watching_video', False):
                    QTimer.singleShot(1800, lambda: self._trigger_random_video_watch() if self.current_state == "LANDING" else None)
                elif getattr(self, 'is_in_discord_voice', False):
                    QTimer.singleShot(1800, lambda: self._trigger_random_discord_listen() if self.current_state == "LANDING" else None)
                else:
                    QTimer.singleShot(1800, lambda: self.set_state("IDLE") if self.current_state == "LANDING" else None)

        self._spawn_timer.timeout.connect(on_spawn_tick)
        self._spawn_timer.start()

    def _exit_app(self):
        self.stop_wandering()
        reply = QMessageBox.question(
            self,
            "Konfirmasi Keluar",
            f"Apakah Tuan yakin ingin membiarkan {self.pet_name} tidur dan menutup aplikasi?\n\n"
            f"(Mimi selalu siap aktif menjaga layar desktop Tuan lho! 🐾)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.play_exit_animation()

    def _open_hermes_window(self):
        """Membuka jendela GUI Pusat Evolusi & Pembelajaran Mandiri Hermes Agent."""
        self.stop_wandering()
        if not self.hermes_window:
            self.hermes_window = HermesStatusWindow(self.hermes_engine, self)
        self.hermes_window.refresh_data()
        self.hermes_window.show()
        self.hermes_window.raise_()
        self.hermes_window.activateWindow()

    def _on_hermes_leveled_up(self, data):
        """
        Level naik secara otomatis dan hening di latar belakang tanpa notifikasi/balon dialog yang mengganggu.
        Mimi belajar dan berevolusi mandiri seperti manusia yang terus mengamati.
        """
        # Perbarui jendela status jika sedang dibuka pengguna
        if hasattr(self, 'hermes_window') and self.hermes_window and self.hermes_window.isVisible():
            self.hermes_window.refresh_data()

    def _on_hermes_spontaneous_insight(self, insight_text):
        """Celetukan spontan dari perenungan mandiri Mimi hanya saat santai/idle dan tidak sedang nonton video."""
        # KRUSIAL: Notifikasi filsafat hanya boleh muncul saat mode diam/normal dan tidak disentuh
        if not self.is_safe_for_notifications():
            return
        if self.speech_bubble.isVisible():
            return

        self.set_state("THINKING")
        self.cat_audio.play_chirp()
        self.speech_bubble.show_message(
            f"Meow! *merenung sejenak ala filsuf kucing* 💡\n\n{insight_text}",
            duration_ms=6500,
            persistent=False
        )
        QTimer.singleShot(3500, lambda: self.set_state("IDLE") if self.current_state == "THINKING" else None)

    def play_exit_animation(self):
        """
        Animasi perpisahan manis sebelum aplikasi keluar:
        - Mimi menyapa ramah pamit masuk ke portal dimensi.
        - Portal dimensi kosmik terbuka berpendar di bawah kaki Mimi.
        - Mimi melangkah dan terhisap masuk secara sinematik ke dalam pusaran portal.
        - Portal menutup menjadi kilatan bintang lalu lenyap.
        """
        if hasattr(self, 'whatsapp_thread') and self.whatsapp_thread:
            try:
                self.whatsapp_thread.stop()
            except Exception:
                pass

        if self._fall_timer.isActive():
            self._fall_timer.stop()
        if self._step_timer.isActive():
            self._step_timer.stop()
        if hasattr(self, '_hunt_step_timer') and self._hunt_step_timer.isActive():
            self._hunt_step_timer.stop()
        if hasattr(self, 'wander_timer') and self.wander_timer.isActive():
            self.wander_timer.stop()
        if hasattr(self, 'spontaneous_play_timer') and self.spontaneous_play_timer.isActive():
            self.spontaneous_play_timer.stop()
        if hasattr(self, 'discord_voice_timer') and self.discord_voice_timer.isActive():
            self.discord_voice_timer.stop()
        if hasattr(self, 'discord_rpc'):
            self.discord_rpc.close()
        if hasattr(self, 'app_observer_timer') and self.app_observer_timer.isActive():
            self.app_observer_timer.stop()
        if hasattr(self, 'hermes_engine') and hasattr(self.hermes_engine, 'cycle_timer'):
            self.hermes_engine.cycle_timer.stop()
        if self.prey_widget:
            self.prey_widget.hide()

        # 1. Mimi melambaikan cakar dan menyapa pamit
        self.set_state("BYE")
        self.cat_audio.play_purr()
        prof = cat_memory.load_memory().get("user_profile", {})
        tuan_sapa = prof.get("nickname") or "Tuan"
        self.speech_bubble.show_message(
            f"Sampai nanti {tuan_sapa}! Mimi pamit masuk ke dalam portal dimensi dulu yaa~ Meoww! 👋🌌✨",
            duration_ms=4000,
            persistent=False
        )

        # 2. Buka Portal Dimensi Kosmik & jalankan adegan tersedot masuk
        def on_portal_finished():
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()
            self.speech_bubble.close()
            self.cat_audio.close()
            QApplication.quit()

        self._portal_overlay = DimensionalPortalOverlay(self, on_finished=on_portal_finished)
        # Beri jeda 350ms agar pengguna sempat membaca sapaan lalu portal terbuka
        QTimer.singleShot(350, self._portal_overlay.start_animation)


DogPetWindow = CatPetWindow
