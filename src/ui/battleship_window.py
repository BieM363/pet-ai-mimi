import os
import sys
import random
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPolygonF, QRadialGradient, QLinearGradient
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QApplication
)

SHIPS_CONFIG = [
    {"name": "Kapal Induk", "size": 5, "icon": "🚢", "type": "carrier", "color": "#2C3E50", "border": "#4A6572", "accent": "#F1C40F"},
    {"name": "Kapal Tempur", "size": 4, "icon": "🛳️", "type": "battleship", "color": "#34495E", "border": "#5D6D7E", "accent": "#E74C3C"},
    {"name": "Penjelajah", "size": 3, "icon": "🛥️", "type": "cruiser", "color": "#2E4053", "border": "#5499C7", "accent": "#3498DB"},
    {"name": "Kapal Selam", "size": 3, "icon": "🐬", "type": "submarine", "color": "#117864", "border": "#16A085", "accent": "#1ABC9C"},
    {"name": "Kapal Patroli", "size": 2, "icon": "⛵", "type": "patrol", "color": "#7E5109", "border": "#D35400", "accent": "#F39C12"}
]


def place_ships_randomly():
    """Menempatkan 5 kapal secara acak pada grid 10x10 tanpa tumpang tindih."""
    grid = [[None for _ in range(10)] for _ in range(10)]
    placed_ships = []

    for ship_info in SHIPS_CONFIG:
        size = ship_info["size"]
        name = ship_info["name"]
        placed = False
        attempts = 0

        while not placed and attempts < 400:
            attempts += 1
            horiz = random.choice([True, False])
            if horiz:
                r = random.randint(0, 9)
                c = random.randint(0, 10 - size)
                coords = [(r, c + i) for i in range(size)]
            else:
                r = random.randint(0, 10 - size)
                c = random.randint(0, 9)
                coords = [(r + i, c) for i in range(size)]

            # Cek apakah koordinat kosong
            if all(grid[cr][cc] is None for cr, cc in coords):
                ship_obj = {
                    "name": name,
                    "size": size,
                    "icon": ship_info["icon"],
                    "type": ship_info["type"],
                    "color": ship_info["color"],
                    "border": ship_info["border"],
                    "accent": ship_info["accent"],
                    "coords": coords,
                    "hits": set()
                }
                for cr, cc in coords:
                    grid[cr][cc] = ship_obj
                placed_ships.append(ship_obj)
                placed = True

    return grid, placed_ships


class BattleshipGridWidget(QWidget):
    """
    Widget visual grid laut (10x10):
    - Digunakan untuk Papan Laut Pemain & Radar Musuh Mimi.
    - Menampilkan ilustrasi kapal nyata dengan lambung utuh, turet, runway, dan tanda visual jelas.
    - Mendukung kontrol penataan penuh dengan mouse: hover preview, klik-angkat, klik-taruh, rotasi via klik kanan/wheel/R.
    """
    cell_clicked = pyqtSignal(int, int)
    fleet_changed = pyqtSignal()

    def __init__(self, is_enemy_radar=False, parent=None):
        super().__init__(parent)
        self.is_enemy_radar = is_enemy_radar
        self.cell_size = 27
        self.offset_x = 24
        self.offset_y = 24
        self.total_size = self.offset_x + self.cell_size * 10
        self.setFixedSize(self.total_size + 4, self.total_size + 4)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor if is_enemy_radar else Qt.PointingHandCursor)

        self.grid = [[None for _ in range(10)] for _ in range(10)]
        self.ships = []
        self.shots = {}  # (r, c): 'hit' atau 'miss'
        self.is_interactive = is_enemy_radar

        # State Pengaturan Kapal (Placement Mode)
        self.is_placement_mode = not is_enemy_radar
        self.active_ship_idx = None       # Index kapal yang sedang dipegang kursor mouse
        self.active_orientation = "H"     # "H" (Horizontal) atau "V" (Vertikal)
        self.hover_cell = None            # (r, c) saat kursor mouse bergerak

    def set_fleet(self, grid, ships):
        self.grid = grid
        self.ships = ships
        self.shots.clear()
        self.active_ship_idx = None
        self.hover_cell = None
        self.update()
        self.fleet_changed.emit()

    def select_ship_to_place(self, idx: int):
        """Memilih kapal untuk ditaruh di papan."""
        if not self.is_placement_mode or idx < 0 or idx >= len(self.ships):
            return
        target_ship = self.ships[idx]
        # Jika kapal sudah ada di papan, angkat sementara
        if target_ship["coords"]:
            for r, c in target_ship["coords"]:
                if 0 <= r < 10 and 0 <= c < 10 and self.grid[r][c] == target_ship:
                    self.grid[r][c] = None
            # Tentukan orientasi aslinya
            if len(target_ship["coords"]) > 1:
                r0, c0 = target_ship["coords"][0]
                r1, c1 = target_ship["coords"][1]
                self.active_orientation = "H" if r0 == r1 else "V"
            target_ship["coords"] = []

        self.active_ship_idx = idx
        self.update()
        self.fleet_changed.emit()

    def toggle_orientation(self):
        """Memutar orientasi kapal yang sedang dipegang (Horizontal <-> Vertikal)."""
        self.active_orientation = "V" if self.active_orientation == "H" else "H"
        self.update()

    def clear_all_ships(self):
        """Mengosongkan semua kapal dari papan untuk ditata ulang dari nol."""
        if not self.is_placement_mode:
            return
        self.grid = [[None for _ in range(10)] for _ in range(10)]
        for s in self.ships:
            s["coords"] = []
            s["hits"].clear()
        self.active_ship_idx = None
        self.update()
        self.fleet_changed.emit()

    def is_all_ships_placed(self):
        """Mengecek apakah seluruh 5 kapal telah ditempatkan pada papan."""
        if len(self.ships) < 5:
            return False
        return all(len(s.get("coords", [])) == s["size"] for s in self.ships)

    def _get_placement_coords(self, r: int, c: int, size: int, orientation: str):
        if orientation == "H":
            return [(r, c + i) for i in range(size)]
        else:
            return [(r + i, c) for i in range(size)]

    def _can_place_ship(self, coords, exclude_ship=None):
        for r, c in coords:
            if not (0 <= r < 10 and 0 <= c < 10):
                return False
            cell_val = self.grid[r][c]
            if cell_val is not None and cell_val != exclude_ship:
                return False
        return True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        cs = self.cell_size
        ox = self.offset_x
        oy = self.offset_y

        # 1. Gambar Label Kolom (A - J) & Baris (1 - 10)
        font_hdr = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font_hdr)
        painter.setPen(QColor(138, 114, 100))

        cols_label = "ABCDEFGHIJ"
        for c in range(10):
            rx = ox + c * cs
            painter.drawText(QRect(rx, 0, cs, oy), Qt.AlignCenter, cols_label[c])

        for r in range(10):
            ry = oy + r * cs
            painter.drawText(QRect(0, ry, ox, cs), Qt.AlignCenter, str(r + 1))

        # 2. Gambar Sel Laut (10x10)
        sea_bg = QColor(30, 43, 56) if self.is_enemy_radar else QColor(36, 68, 98)
        grid_line = QColor(44, 62, 80) if self.is_enemy_radar else QColor(50, 88, 126)

        for r in range(10):
            for c in range(10):
                rx = ox + c * cs
                ry = oy + r * cs
                cell_rect = QRect(rx, ry, cs, cs)

                # Efek air laut bergradasi halus
                painter.fillRect(cell_rect, sea_bg)
                painter.setPen(QPen(grid_line, 1))
                painter.drawRect(cell_rect)

        # 3. Tampilkan Ilustrasi Kapal Nyata pada Papan Pemain
        if not self.is_enemy_radar:
            for s_idx, ship in enumerate(self.ships):
                coords = ship.get("coords", [])
                if not coords or len(coords) != ship["size"]:
                    continue
                # Jangan gambar jika kapal ini sedang diangkat mouse
                if self.is_placement_mode and self.active_ship_idx == s_idx:
                    continue
                self._draw_ship_hull(painter, ship)

        # 4. Gambar Status Tembakan (Hit / Miss)
        for (r, c), st in self.shots.items():
            rx = ox + c * cs
            ry = oy + r * cs
            cell_rect = QRect(rx, ry, cs, cs)

            if st == "hit":
                # Efek ledakan api menyala
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(231, 76, 60, 200)))
                painter.drawRoundedRect(cell_rect.adjusted(1, 1, -1, -1), 4, 4)
                painter.setBrush(QBrush(QColor(243, 156, 18)))
                painter.drawEllipse(QPoint(rx + cs // 2, ry + cs // 2), 9, 9)
                painter.setFont(QFont("Segoe UI Emoji", 10))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(cell_rect, Qt.AlignCenter, "💥")
            elif st == "miss":
                # Percikan air meleset
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(133, 193, 233, 160)))
                painter.drawEllipse(QPoint(rx + cs // 2, ry + cs // 2), 5, 5)
                painter.setPen(QPen(QColor(255, 255, 255, 140), 1))
                painter.drawEllipse(QPoint(rx + cs // 2, ry + cs // 2), 8, 8)

        # 5. Siluet Kapal Musuh yang Karam di Radar Mimi
        if self.is_enemy_radar:
            for ship in self.ships:
                if len(ship["hits"]) == ship["size"]:
                    self._draw_ship_hull(painter, ship, is_sunk=True)

        # 6. Ghost Preview saat Menata Kapal dengan Mouse
        if self.is_placement_mode and self.active_ship_idx is not None and self.hover_cell is not None:
            hr, hc = self.hover_cell
            active_ship = self.ships[self.active_ship_idx]
            cand_coords = self._get_placement_coords(hr, hc, active_ship["size"], self.active_orientation)
            is_valid = self._can_place_ship(cand_coords, exclude_ship=active_ship)

            # Gambar visual ghost ship preview
            self._draw_ghost_preview(painter, active_ship, cand_coords, is_valid)

    def _draw_ship_hull(self, painter: QPainter, ship: dict, is_sunk: bool = False):
        """Menggambar kapal asli utuh dengan bow runcing, turet senjata, runway, dan detail nyata."""
        coords = sorted(ship["coords"])
        if not coords:
            return

        cs = self.cell_size
        ox = self.offset_x
        oy = self.offset_y

        is_horiz = (len(coords) > 1 and coords[0][0] == coords[1][0]) or (len(coords) == 1)

        min_r = min(r for r, _ in coords)
        max_r = max(r for r, _ in coords)
        min_c = min(c for _, c in coords)
        max_c = max(c for _, c in coords)

        x = ox + min_c * cs + 2
        y = oy + min_r * cs + 2
        w = (max_c - min_c + 1) * cs - 4
        h = (max_r - min_r + 1) * cs - 4
        ship_rect = QRect(x, y, w, h)

        painter.save()

        # Bayangan Lambung di Air (Water Ripple / Hull Shadow)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(15, 30, 45, 120)))
        painter.drawRoundedRect(ship_rect.adjusted(1, 2, 1, 3), 6, 6)

        # Warna Lambung Utama
        base_color = QColor(ship.get("color", "#2C3E50"))
        border_color = QColor(ship.get("border", "#4A6572"))
        accent_color = QColor(ship.get("accent", "#F1C40F"))

        if is_sunk:
            base_color = QColor(25, 20, 25, 200)
            border_color = QColor(192, 57, 43, 200)

        # Gradasi Baja Lambung Kapal
        grad = QLinearGradient(x, y, x + (w if not is_horiz else 0), y + (h if is_horiz else 0))
        grad.setColorAt(0.0, base_color.lighter(125))
        grad.setColorAt(0.5, base_color)
        grad.setColorAt(1.0, base_color.darker(130))

        painter.setPen(QPen(border_color, 1.6))
        painter.setBrush(QBrush(grad))

        # Bentuk Lambung Ramping (Pointed Bow & Flat Stern)
        radius = 8
        painter.drawRoundedRect(ship_rect, radius, radius)

        # Garis Sekat Antar Kompartemen / Kotak Sel Grid
        painter.setPen(QPen(border_color.lighter(130), 1, Qt.DotLine))
        if is_horiz:
            for i in range(1, ship["size"]):
                sep_x = x + i * cs - 2
                painter.drawLine(sep_x, y + 2, sep_x, y + h - 2)
        else:
            for i in range(1, ship["size"]):
                sep_y = y + i * cs - 2
                painter.drawLine(x + 2, sep_y, x + w - 2, sep_y)

        # Detail Khusus Tiap Jenis Kapal Nyata
        stype = ship.get("type", "patrol")
        if not is_sunk:
            if stype == "carrier":
                # Kapal Induk: Runway Landasan Pacu Garis Kuning Putus-putus & Jet Tempur
                painter.setPen(QPen(accent_color, 1.5, Qt.DashLine))
                if is_horiz:
                    mid_y = y + h // 2
                    painter.drawLine(x + 10, mid_y, x + w - 12, mid_y)
                else:
                    mid_x = x + w // 2
                    painter.drawLine(mid_x, y + 10, mid_x, y + h - 12)

                # Menara Kontrol Pulau & Simbol Pesawat
                painter.setFont(QFont("Segoe UI Emoji", 8))
                painter.setPen(QColor(255, 255, 255, 230))
                painter.drawText(ship_rect, Qt.AlignCenter, "✈")

            elif stype == "battleship":
                # Kapal Tempur: Turet Meriam Ganda (Double Gun Turrets) & Jangkar Haluan
                painter.setPen(QPen(QColor(20, 20, 20), 1.5))
                painter.setBrush(QBrush(accent_color))

                turret_radius = 4
                if is_horiz:
                    # Dua turet meriam di kiri & kanan
                    t1_x = x + cs // 2
                    t2_x = x + w - cs // 2
                    cy = y + h // 2
                    painter.drawEllipse(QPoint(t1_x, cy), turret_radius, turret_radius)
                    painter.drawEllipse(QPoint(t2_x, cy), turret_radius, turret_radius)
                else:
                    cx = x + w // 2
                    t1_y = y + cs // 2
                    t2_y = y + h - cs // 2
                    painter.drawEllipse(QPoint(cx, t1_y), turret_radius, turret_radius)
                    painter.drawEllipse(QPoint(cx, t2_y), turret_radius, turret_radius)

                painter.setFont(QFont("Segoe UI Emoji", 8))
                painter.setPen(QColor(255, 255, 255, 220))
                painter.drawText(ship_rect, Qt.AlignCenter, "⚓")

            elif stype == "cruiser":
                # Penjelajah: Tabung Rudal & Radar Cepat
                painter.setFont(QFont("Segoe UI Emoji", 8))
                painter.setPen(QColor(255, 255, 255, 220))
                painter.drawText(ship_rect, Qt.AlignCenter, "🛥️")

            elif stype == "submarine":
                # Kapal Selam: Menara Periskop & Baling-baling
                painter.setFont(QFont("Segoe UI Emoji", 8))
                painter.setPen(QColor(255, 255, 255, 220))
                painter.drawText(ship_rect, Qt.AlignCenter, "🔭")

            elif stype == "patrol":
                # Kapal Patroli: Moncong Cepat Ramping
                painter.setFont(QFont("Segoe UI Emoji", 8))
                painter.setPen(QColor(255, 255, 255, 220))
                painter.drawText(ship_rect, Qt.AlignCenter, "⛵")

        else:
            # Tanda Karam / Hancur
            painter.setFont(QFont("Segoe UI Emoji", 10))
            painter.setPen(QColor(231, 76, 60))
            painter.drawText(ship_rect, Qt.AlignCenter, "💀")

        painter.restore()

    def _draw_ghost_preview(self, painter: QPainter, ship: dict, coords: list, is_valid: bool):
        """Menggambar bayangan kapal (ghost preview) yang mengikuti mouse saat penataan."""
        cs = self.cell_size
        ox = self.offset_x
        oy = self.offset_y

        fill_color = QColor(46, 204, 113, 110) if is_valid else QColor(231, 76, 60, 110)
        border_color = QColor(46, 204, 113, 240) if is_valid else QColor(231, 76, 60, 240)

        painter.save()
        for r, c in coords:
            if 0 <= r < 10 and 0 <= c < 10:
                rx = ox + c * cs
                ry = oy + r * cs
                cell_rect = QRect(rx, ry, cs, cs)
                painter.setPen(QPen(border_color, 1.8, Qt.DashLine if not is_valid else Qt.SolidLine))
                painter.setBrush(QBrush(fill_color))
                painter.drawRoundedRect(cell_rect.adjusted(2, 2, -2, -2), 5, 5)

        # Indikator Status Taruh di Sel Pertama
        if coords:
            fr, fc = coords[0]
            if 0 <= fr < 10 and 0 <= fc < 10:
                fx = ox + fc * cs
                fy = oy + fr * cs
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                painter.setPen(QColor(255, 255, 255))
                symbol = "✅" if is_valid else "❌"
                painter.drawText(QRect(fx, fy, cs, cs), Qt.AlignCenter, symbol)

        painter.restore()

    def mouseMoveEvent(self, event):
        mx = event.x() - self.offset_x
        my = event.y() - self.offset_y
        cs = self.cell_size

        if 0 <= mx < cs * 10 and 0 <= my < cs * 10:
            c = int(mx // cs)
            r = int(my // cs)
            if self.hover_cell != (r, c):
                self.hover_cell = (r, c)
                self.update()
        else:
            if self.hover_cell is not None:
                self.hover_cell = None
                self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self.hover_cell is not None:
            self.hover_cell = None
            self.update()
        super().leaveEvent(event)

    def wheelEvent(self, event):
        """Putar orientasi kapal dengan scroll mouse saat penataan kapal."""
        if self.is_placement_mode and self.active_ship_idx is not None:
            self.toggle_orientation()
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        """Putar orientasi kapal dengan tombol R pada keyboard."""
        if self.is_placement_mode and event.key() == Qt.Key_R:
            self.toggle_orientation()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        mx = event.x() - self.offset_x
        my = event.y() - self.offset_y
        cs = self.cell_size

        if mx < 0 or my < 0 or mx >= cs * 10 or my >= cs * 10:
            return

        c = int(mx // cs)
        r = int(my // cs)

        # 1. Mode Penataan Kapal (Sebelum Pertempuran Dimulai)
        if self.is_placement_mode:
            # Klik Kanan -> Putar Orientasi Seketika
            if event.button() == Qt.RightButton:
                self.toggle_orientation()
                event.accept()
                return

            # Klik Kiri -> Taruh Kapal atau Angkat Kapal yang Ada di Laut
            if event.button() == Qt.LeftButton:
                if self.active_ship_idx is not None:
                    # Sedang memegang kapal -> Coba taruh di koordinat ini
                    active_ship = self.ships[self.active_ship_idx]
                    cand_coords = self._get_placement_coords(r, c, active_ship["size"], self.active_orientation)

                    if self._can_place_ship(cand_coords, exclude_ship=active_ship):
                        # Taruh kapal secara sah
                        active_ship["coords"] = cand_coords
                        for cr, cc in cand_coords:
                            self.grid[cr][cc] = active_ship
                        self.active_ship_idx = None
                        self.update()
                        self.fleet_changed.emit()
                        event.accept()
                        return
                    else:
                        # Gagal taruh karena terhalang/keluar batas -> getarkan atau abaikan
                        event.accept()
                        return
                else:
                    # Tidak sedang memegang kapal -> Cek apakah mengklik kapal yang sudah ada di laut untuk diangkat
                    clicked_ship = self.grid[r][c]
                    if clicked_ship is not None and clicked_ship in self.ships:
                        idx = self.ships.index(clicked_ship)
                        self.select_ship_to_place(idx)
                        event.accept()
                        return

        # 2. Mode Radar Tembak Musuh (Saat Pertempuran Aktif)
        if self.is_interactive and event.button() == Qt.LeftButton:
            self.cell_clicked.emit(r, c)
            event.accept()


class MimiBattleshipWindow(QDialog):
    """
    Jendela Game Kapal Perang Laut (Battleship):
    - Pertempuran Armada Tuan vs Armada Kucing Mimi AI.
    - Ilustrasi kapal nyata dan jelas (Kapal Induk, Kapal Tempur, Penjelajah, Kapal Selam, Kapal Patroli).
    - Mode Penataan Kapal Interaktif: Klik & angkat, putar (R / Klik Kanan), dok armada kapal.
    - AI Mimi Cerdas dengan mode pelacakan (Hunt-and-Target).
    - Suara meong, ledakan kapal, dan celetukan seru.
    """
    def __init__(self, pet_parent=None, pet_name="Mimi"):
        super().__init__(None, Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.pet_parent = pet_parent
        self.pet_name = pet_name

        self.setWindowTitle(f"🚢 Perang Kapal Battleship bersama {self.pet_name}")
        self.setFixedSize(880, 595)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFDF9;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # Game State
        self.is_battle_started = False
        self.is_game_over = False
        self.player_turn = True

        # AI Mimi State (Hunt-and-Target)
        self.mimi_target_queue = []
        self.mimi_hits_history = set()

        # Statistik
        self.player_shots_count = 0
        self.player_hits_count = 0

        self.ship_dock_buttons = []

        self._init_ui()
        self._setup_new_fleets()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(16)

        # SISI KIRI & TENGAH: PAPAN LAUT TUAN & RADAR MIMI
        boards_layout = QVBoxLayout()
        boards_layout.setSpacing(8)

        grids_row = QHBoxLayout()
        grids_row.setSpacing(14)

        # 1. Papan Laut Pemain
        box_player = QVBoxLayout()
        box_player.setSpacing(4)
        lbl_p = QLabel("⚓ Laut Armada Tuan (Atur Kapalmu di Sini)", self)
        lbl_p.setStyleSheet("font-weight: bold; font-size: 11px; color: #2C3E50;")
        box_player.addWidget(lbl_p)

        self.grid_player = BattleshipGridWidget(is_enemy_radar=False, parent=self)
        self.grid_player.fleet_changed.connect(self._on_fleet_changed)
        box_player.addWidget(self.grid_player)
        grids_row.addLayout(box_player)

        # 2. Radar Serang Musuh (Mimi)
        box_enemy = QVBoxLayout()
        box_enemy.setSpacing(4)
        lbl_e = QLabel(f"🎯 Radar Tembak Armada {self.pet_name}", self)
        lbl_e.setStyleSheet("font-weight: bold; font-size: 11px; color: #C0392B;")
        box_enemy.addWidget(lbl_e)

        self.grid_enemy = BattleshipGridWidget(is_enemy_radar=True, parent=self)
        self.grid_enemy.cell_clicked.connect(self._on_player_shoot)
        box_enemy.addWidget(self.grid_enemy)
        grids_row.addLayout(box_enemy)

        boards_layout.addLayout(grids_row)

        # 3. DOK ARMADA KAPAL & KONTROL PENATAAN MOUSE (Bawah Grid)
        self.dock_frame = QFrame(self)
        self.dock_frame.setStyleSheet("""
            QFrame {
                background: #F8F4EE;
                border: 1px solid #E2D7C9;
                border-radius: 8px;
                padding: 4px 6px;
            }
        """)
        dock_layout = QVBoxLayout(self.dock_frame)
        dock_layout.setContentsMargins(6, 4, 6, 4)
        dock_layout.setSpacing(4)

        # Baris Petunjuk Navigasi Mouse
        self.lbl_dock_guide = QLabel(
            "🖱️ <b>Navigasi Mouse:</b> Klik kapal di laut untuk memindahkan • <b>Klik Kanan / Tombol 'R'</b> untuk memutar (Horizontal ↔ Vertikal)",
            self.dock_frame
        )
        self.lbl_dock_guide.setStyleSheet("font-size: 9.5px; color: #7B6858;")
        dock_layout.addWidget(self.lbl_dock_guide)

        # Baris Tombol 5 Kapal
        ship_btns_row = QHBoxLayout()
        ship_btns_row.setSpacing(6)

        self.ship_dock_buttons = []
        for idx, sinfo in enumerate(SHIPS_CONFIG):
            btn = QPushButton(f"{sinfo['icon']} {sinfo['name']} ({sinfo['size']})", self.dock_frame)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: #FFFFFF; color: #2C3E50;
                    font-size: 9.5px; font-weight: bold;
                    border: 1.2px solid #D8C3A5; border-radius: 5px; padding: 4px 6px;
                }
                QPushButton:hover { background: #FDEED9; border-color: #E07A5F; }
            """)
            btn.clicked.connect(lambda checked, i=idx: self._on_dock_ship_clicked(i))
            ship_btns_row.addWidget(btn)
            self.ship_dock_buttons.append(btn)

        dock_layout.addLayout(ship_btns_row)
        boards_layout.addWidget(self.dock_frame)

        main_layout.addLayout(boards_layout)

        # SISI KANAN: KARTU MIMI, STATS, & KONTROL AKSI
        side_layout = QVBoxLayout()
        side_layout.setSpacing(8)

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
        lbl_name = QLabel(f"Laksamana {self.pet_name}", mimi_card)
        lbl_name.setStyleSheet("font-size: 11px; font-weight: bold; color: #D35400;")
        self.lbl_sub = QLabel("Komandan Armada Kucing 🐾", mimi_card)
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
                font-size: 10px;
                color: #2D2424;
                line-height: 130%;
            }
        """)
        self.chat_bubble.setText(f"Meow! Armada laut Mimi sudah siaga! Atur letak kapal Tuan dengan mouse lalu klik 'Mulai Pertempuran'! 🚢🐾")
        m_layout.addWidget(self.chat_bubble)
        side_layout.addWidget(mimi_card)

        # Kartu Status Kapal Tersisa
        stats_card = QFrame(self)
        stats_card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #EADDCF;
                border-radius: 10px;
                padding: 8px 10px;
            }
        """)
        s_layout = QVBoxLayout(stats_card)
        s_layout.setSpacing(5)

        self.lbl_player_ships = QLabel("🛡️ Sisa Kapal Tuan: 5 / 5", stats_card)
        self.lbl_player_ships.setStyleSheet("font-size: 11px; font-weight: bold; color: #2980B9;")
        s_layout.addWidget(self.lbl_player_ships)

        self.lbl_enemy_ships = QLabel(f"🎯 Sisa Kapal Mimi: 5 / 5", stats_card)
        self.lbl_enemy_ships.setStyleSheet("font-size: 11px; font-weight: bold; color: #C0392B;")
        s_layout.addWidget(self.lbl_enemy_ships)

        self.lbl_accuracy = QLabel("🎯 Akurasi Tembak: 0%", stats_card)
        self.lbl_accuracy.setStyleSheet("font-size: 10px; color: #5D6D7E;")
        s_layout.addWidget(self.lbl_accuracy)

        side_layout.addWidget(stats_card)

        # Tombol-tombol Pengaturan Formasi
        self.btn_rotate = QPushButton("🔄 Putar Arah Kapal (R)", self)
        self.btn_rotate.setCursor(Qt.PointingHandCursor)
        self.btn_rotate.setStyleSheet("""
            QPushButton {
                background: #EDF2F7; color: #2D3748;
                font-size: 10.5px; font-weight: bold;
                border: 1px solid #CBD5E0; border-radius: 6px; padding: 6px;
            }
            QPushButton:hover { background: #E2E8F0; }
        """)
        self.btn_rotate.clicked.connect(self._on_btn_rotate_clicked)
        side_layout.addWidget(self.btn_rotate)

        btns_row = QHBoxLayout()
        btns_row.setSpacing(6)

        self.btn_randomize = QPushButton("🎲 Acak Formasi", self)
        self.btn_randomize.setCursor(Qt.PointingHandCursor)
        self.btn_randomize.setStyleSheet("""
            QPushButton {
                background: #F4F1EA; color: #6D594F;
                font-size: 10.5px; font-weight: bold;
                border: 1px solid #D8C3A5; border-radius: 6px; padding: 6px;
            }
            QPushButton:hover { background: #EADDCF; }
        """)
        self.btn_randomize.clicked.connect(self._setup_new_fleets)
        btns_row.addWidget(self.btn_randomize)

        self.btn_clear = QPushButton("🗑️ Tata Ulang", self)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background: #FDEDEC; color: #C0392B;
                font-size: 10.5px; font-weight: bold;
                border: 1px solid #F5B7B1; border-radius: 6px; padding: 6px;
            }
            QPushButton:hover { background: #FADBD8; }
        """)
        self.btn_clear.clicked.connect(self._clear_player_fleet)
        btns_row.addWidget(self.btn_clear)
        side_layout.addLayout(btns_row)

        # Tombol Mulai Pertempuran
        self.btn_start = QPushButton("⚔️ Mulai Pertempuran Laut!", self)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: #E07A5F; color: white;
                font-weight: bold; font-size: 11px;
                border: none; border-radius: 6px; padding: 9px;
            }
            QPushButton:hover { background: #C74A27; }
            QPushButton:disabled { background: #BDC3C7; color: #7F8C8D; }
        """)
        self.btn_start.clicked.connect(self._start_battle)
        side_layout.addWidget(self.btn_start)

        side_layout.addStretch()
        main_layout.addLayout(side_layout)

    def _on_btn_rotate_clicked(self):
        """Memutar orientasi kapal yang sedang dipegang kursor."""
        self.grid_player.toggle_orientation()
        cur_ori = "Vertikal ↕" if self.grid_player.active_orientation == "V" else "Horizontal ↔"
        self.btn_rotate.setText(f"🔄 Putar Arah: {cur_ori} (R)")

    def _on_dock_ship_clicked(self, idx: int):
        """Memilih kapal dari dok armada untuk ditaruh di papan."""
        if self.is_battle_started:
            return
        self.grid_player.select_ship_to_place(idx)
        ship_name = SHIPS_CONFIG[idx]["name"]
        self.chat_bubble.setText(f"Tuan sedang memegang <b>{ship_name}</b>! Arahkan kursor ke papan laut dan klik untuk menaruhnya! ⚓")
        if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
            self.pet_parent.cat_audio.play_chirp()

    def _clear_player_fleet(self):
        """Mengosongkan semua kapal dari papan pemain."""
        if self.is_battle_started:
            return
        self.grid_player.clear_all_ships()
        self.chat_bubble.setText("Papan laut dikosongkan! Silakan klik kapal di dok bawah dan taruh satu per satu di posisi favorit Tuan! 🐾")

    def _on_fleet_changed(self):
        """Update tampilan dok armada dan status tombol mulai."""
        all_placed = self.grid_player.is_all_ships_placed()
        self.btn_start.setEnabled(all_placed and not self.is_battle_started)

        # Update indikator tombol di dok
        for idx, btn in enumerate(self.ship_dock_buttons):
            if idx < len(self.grid_player.ships):
                s = self.grid_player.ships[idx]
                is_placed = len(s.get("coords", [])) == s["size"]
                is_active = (self.grid_player.active_ship_idx == idx)

                if is_active:
                    btn.setStyleSheet("""
                        QPushButton {
                            background: #FDEBD0; color: #D35400;
                            font-size: 9.5px; font-weight: bold;
                            border: 2px solid #E67E22; border-radius: 5px; padding: 4px 6px;
                        }
                    """)
                    btn.setText(f"🖐️ {s['name']} (Pegang)")
                elif is_placed:
                    btn.setStyleSheet("""
                        QPushButton {
                            background: #EAFAF1; color: #27AE60;
                            font-size: 9.5px; font-weight: bold;
                            border: 1.2px solid #A9DFBF; border-radius: 5px; padding: 4px 6px;
                        }
                        QPushButton:hover { background: #D5F5E3; }
                    """)
                    btn.setText(f"⚓ {s['name']} ({s['size']})")
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            background: #FDEDEC; color: #C0392B;
                            font-size: 9.5px; font-weight: bold;
                            border: 1.2px solid #F5B7B1; border-radius: 5px; padding: 4px 6px;
                        }
                        QPushButton:hover { background: #FADBD8; }
                    """)
                    btn.setText(f"➕ {s['name']} ({s['size']})")

    def _setup_new_fleets(self):
        p_grid, p_ships = place_ships_randomly()
        self.grid_player.set_fleet(p_grid, p_ships)
        self.grid_player.is_placement_mode = True

        e_grid, e_ships = place_ships_randomly()
        self.grid_enemy.set_fleet(e_grid, e_ships)

        self.is_battle_started = False
        self.is_game_over = False
        self.grid_enemy.is_interactive = False
        self.btn_start.setEnabled(True)
        self.btn_randomize.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_rotate.setEnabled(True)
        self.dock_frame.setEnabled(True)

        self.mimi_target_queue.clear()
        self.mimi_hits_history.clear()
        self.player_shots_count = 0
        self.player_hits_count = 0

        self.lbl_player_ships.setText("🛡️ Sisa Kapal Tuan: 5 / 5")
        self.lbl_enemy_ships.setText(f"🎯 Sisa Kapal Mimi: 5 / 5")
        self.lbl_accuracy.setText("🎯 Akurasi Tembak: 0%")

        self.lbl_avatar.setText("🐱")
        self.chat_bubble.setText("Meow! Formasi armada baru siap! Tuan bisa menggeser kapal dengan mouse atau klik 'Mulai Pertempuran'! ⚓🐾")
        self._on_fleet_changed()

    def _start_battle(self):
        if not self.grid_player.is_all_ships_placed():
            QMessageBox.warning(self, "Armada Belum Siap", "Harap taruh seluruh 5 kapal di papan laut sebelum memulai pertempuran!")
            return

        self.is_battle_started = True
        self.grid_player.is_placement_mode = False
        self.grid_player.active_ship_idx = None
        self.grid_player.update()

        self.grid_enemy.is_interactive = True
        self.btn_start.setEnabled(False)
        self.btn_randomize.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_rotate.setEnabled(False)
        self.dock_frame.setEnabled(False)
        self.player_turn = True

        self.lbl_avatar.setText("😼")
        self.chat_bubble.setText("🚨 PERTEMPURAN LAUT DIMULAI! Silakan pilih kotak di Radar Kanan untuk menembak kapal Mimi duluan! 💥")
        if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
            self.pet_parent.cat_audio.play_talk()

    def _on_player_shoot(self, r: int, c: int):
        if not self.is_battle_started or self.is_game_over or not self.player_turn:
            return

        if (r, c) in self.grid_enemy.shots:
            return  # Sudah pernah ditembak

        self.player_shots_count += 1
        target_ship = self.grid_enemy.grid[r][c]

        if target_ship is not None:
            # Tembakan Kena!
            self.grid_enemy.shots[(r, c)] = "hit"
            target_ship["hits"].add((r, c))
            self.player_hits_count += 1
            self.grid_enemy.update()

            if len(target_ship["hits"]) == target_ship["size"]:
                # Kapal Tenggelam
                self.lbl_avatar.setText("🙀")
                self.chat_bubble.setText(f"KABOOM! 💥 {target_ship['name']} Mimi karam ke dasar laut! Tembakan hebat, Tuan! 💀")
                if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                    self.pet_parent.cat_audio.play_hiss()
            else:
                self.lbl_avatar.setText("🙀")
                self.chat_bubble.setText(f"Duaarr! 💥 Torpedo Tuan mengenai kapal Mimi di ({chr(65+c)}{r+1})! Meoww!")
                if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                    self.pet_parent.cat_audio.play_chirp()
        else:
            # Tembakan Meleset
            self.grid_enemy.shots[(r, c)] = "miss"
            self.grid_enemy.update()
            self.lbl_avatar.setText("😸")
            self.chat_bubble.setText(f"Byuurr! 💦 Torpedo Tuan meleset jatuh ke laut kosong di ({chr(65+c)}{r+1})!")
            if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                self.pet_parent.cat_audio.play_talk()

        # Update stats
        self._update_fleet_status()

        # Cek Kemenangan Pemain
        if self._check_all_sunk(self.grid_enemy.ships):
            self._handle_game_over(winner="player")
            return

        # Giliran Mimi
        self.player_turn = False
        self.grid_enemy.is_interactive = False
        QTimer.singleShot(1100, self._mimi_ai_turn)

    def _mimi_ai_turn(self):
        if not self.isVisible() or self.is_game_over:
            return

        # Algoritma Berburu AI Mimi (Hunt-and-Target)
        shot_coord = None

        # 1. Cek antrean target di sekitar tembakan yang kena
        while self.mimi_target_queue:
            cand = self.mimi_target_queue.pop(0)
            if cand not in self.grid_player.shots:
                shot_coord = cand
                break

        # 2. Jika antrean kosong, tembak petak acak yang belum pernah ditembak
        if shot_coord is None:
            unshot = []
            for r in range(10):
                for c in range(10):
                    if (r, c) not in self.grid_player.shots:
                        unshot.append((r, c))
            if unshot:
                shot_coord = random.choice(unshot)

        if shot_coord is None:
            return

        mr, mc = shot_coord
        target_ship = self.grid_player.grid[mr][mc]

        if target_ship is not None:
            # Mimi Kena Kapal Pemain
            self.grid_player.shots[(mr, mc)] = "hit"
            target_ship["hits"].add((mr, mc))
            self.mimi_hits_history.add((mr, mc))
            self.grid_player.update()

            # Tambahkan sel tetangga (Atas, Bawah, Kiri, Kanan) ke antrean bidikan Mimi
            neighbors = [(mr - 1, mc), (mr + 1, mc), (mr, mc - 1), (mr, mc + 1)]
            for nr, nc in neighbors:
                if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) not in self.grid_player.shots:
                    if (nr, nc) not in self.mimi_target_queue:
                        self.mimi_target_queue.append((nr, nc))

            if len(target_ship["hits"]) == target_ship["size"]:
                self.lbl_avatar.setText("😸")
                self.chat_bubble.setText(f"Horeee! Mimi berhasil menenggelamkan {target_ship['name']} Tuan! 🐾🚢💥")
                if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                    self.pet_parent.cat_audio.play_purr()
            else:
                self.lbl_avatar.setText("😼")
                self.chat_bubble.setText(f"Duaarr! Torpedo Mimi mengenai kapal Tuan di ({chr(65+mc)}{mr+1})! Kena sasaran! 🐾")
                if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                    self.pet_parent.cat_audio.play_chirp()
        else:
            # Mimi Meleset
            self.grid_player.shots[(mr, mc)] = "miss"
            self.grid_player.update()
            self.lbl_avatar.setText("🐱")
            self.chat_bubble.setText(f"Yah, torpedo Mimi meleset di ({chr(65+mc)}{mr+1})! Giliran Tuan lagi meow! 🐾")

        self._update_fleet_status()

        # Cek Kemenangan Mimi
        if self._check_all_sunk(self.grid_player.ships):
            self._handle_game_over(winner="mimi")
            return

        # Kembalikan giliran ke pemain
        self.player_turn = True
        self.grid_enemy.is_interactive = True

    def _update_fleet_status(self):
        p_alive = sum(1 for s in self.grid_player.ships if len(s["hits"]) < s["size"])
        e_alive = sum(1 for s in self.grid_enemy.ships if len(s["hits"]) < s["size"])

        self.lbl_player_ships.setText(f"🛡️ Sisa Kapal Tuan: {p_alive} / 5")
        self.lbl_enemy_ships.setText(f"🎯 Sisa Kapal Mimi: {e_alive} / 5")

        acc = int((self.player_hits_count / max(1, self.player_shots_count)) * 100)
        self.lbl_accuracy.setText(f"🎯 Akurasi Tembak: {acc}% ({self.player_hits_count}/{self.player_shots_count})")

    def _check_all_sunk(self, ships):
        return all(len(s["hits"]) == s["size"] for s in ships)

    def _handle_game_over(self, winner: str):
        self.is_game_over = True
        self.grid_enemy.is_interactive = False

        if winner == "player":
            self.lbl_avatar.setText("😻")
            self.chat_bubble.setText("🏆 KEMENANGAN MUTLAK! Semua armada Mimi telah karam! Tuan adalah Penguasa Lautan sejati! 🎉🚢")
            if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                self.pet_parent.cat_audio.play_chirp()
        else:
            self.lbl_avatar.setText("😸")
            self.chat_bubble.setText("Nyahaha! Mimi berhasil mengalahkan armada Tuan! Pertempuran laut yang sangat epik! 🐾⚓")
            if self.pet_parent and hasattr(self.pet_parent, "cat_audio"):
                self.pet_parent.cat_audio.play_purr()

    def closeEvent(self, event):
        self.is_game_over = True
        if self.pet_parent and hasattr(self.pet_parent, "on_game_closed"):
            self.pet_parent.on_game_closed(self)
        super().closeEvent(event)
