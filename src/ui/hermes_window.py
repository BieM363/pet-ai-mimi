# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import os
import sys
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QBrush, QLinearGradient
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QScrollArea, QWidget, QFrame, QTabWidget,
    QMessageBox
)

try:
    from src.core import hermes_agent
except ImportError:
    from core import hermes_agent


class HermesStatusWindow(QDialog):
    """
    Jendela Visual Pusat Evolusi & Pembelajaran Mandiri Hermes Agent untuk Mimi:
    - Menampilkan Level Evolusi, Progress Bar XP, dan Gelar Mimi.
    - Menampilkan Model Dialektis Pengguna (Honcho/Hermes dialectic profile).
    - Menampilkan Pohon Keterampilan Otonom (Skills Tree).
    - Menampilkan Riwayat Jurnal Perenungan Mandiri (Reflection Chronicles).
    - Dilengkapi tombol untuk memicu siklus refleksi instan.
    """
    def __init__(self, evolution_engine, parent=None):
        super().__init__(parent)
        self.evolution_engine = evolution_engine

        self.setWindowTitle("🧬 Mimi Hermes Agent — Pusat Evolusi & Pembelajaran Mandiri")
        self.resize(680, 620)
        self.setMinimumSize(600, 520)

        # Style sheet dark modern bergaya futuristic cyber-companion
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #e6edf3;
                font-family: 'Segoe UI', sans-serif;
            }
            QFrame#card {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 12px;
            }
            QFrame#card_highlight {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a162b, stop:1 #111a2e);
                border: 1.5px solid #8a2be2;
                border-radius: 12px;
                padding: 14px;
            }
            QLabel {
                color: #e6edf3;
            }
            QProgressBar {
                border: 1px solid #30363d;
                border-radius: 6px;
                background-color: #21262d;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                height: 18px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f5d4, stop:1 #9b5de5);
                border-radius: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #30363d;
                background-color: #161b22;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #21262d;
                color: #8b949e;
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #161b22;
                color: #00f5d4;
                border-bottom: 2px solid #00f5d4;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QPushButton {
                background-color: #21262d;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: bold;
                font-size: 11.5px;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
            }
            QPushButton#primary_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9b5de5, stop:1 #00f5d4);
                color: #0d1117;
                border: none;
                font-weight: bold;
            }
            QPushButton#primary_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #af72f5, stop:1 #33f7dc);
            }
        """)

        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # 1. HEADER UTAMA
        header_layout = QHBoxLayout()
        icon_lbl = QLabel("🧬")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 26))
        header_layout.addWidget(icon_lbl)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)
        h_title = QLabel("Mimi Hermes Agent — Autonomous Evolution")
        h_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        h_title.setStyleSheet("color: #00f5d4;")
        title_vbox.addWidget(h_title)

        h_sub = QLabel("Arsitektur Pembelajaran & Perenungan Mandiri Berkelanjutan (Inspired by Nous Research Hermes)")
        h_sub.setFont(QFont("Segoe UI", 9))
        h_sub.setStyleSheet("color: #8b949e;")
        title_vbox.addWidget(h_sub)
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # 2. STATUS CARD (LEVEL & XP PROGRESS)
        self.status_card = QFrame()
        self.status_card.setObjectName("card_highlight")
        card_vbox = QVBoxLayout(self.status_card)
        card_vbox.setSpacing(8)

        # Baris Level & Gelar
        level_row = QHBoxLayout()
        self.level_badge = QLabel("LEVEL 1")
        self.level_badge.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.level_badge.setStyleSheet("""
            background: #9b5de5; color: #ffffff;
            border-radius: 6px; padding: 3px 8px;
        """)
        level_row.addWidget(self.level_badge)

        self.title_label = QLabel("Pixel Novice Cat 🐾")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.title_label.setStyleSheet("color: #fee440;")
        level_row.addWidget(self.title_label)
        level_row.addStretch()

        self.xp_text_lbl = QLabel("XP: 25 / 100")
        self.xp_text_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.xp_text_lbl.setStyleSheet("color: #00f5d4;")
        level_row.addWidget(self.xp_text_lbl)
        card_vbox.addLayout(level_row)

        # Progress Bar XP
        self.xp_bar = QProgressBar()
        self.xp_bar.setRange(0, 100)
        self.xp_bar.setValue(25)
        card_vbox.addWidget(self.xp_bar)

        # Mini Stats Badges
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.stat_reflections = QLabel("🧠 Refleksi: 0")
        self.stat_videos = QLabel("🍿 Video Ditonton: 0")
        self.stat_apps = QLabel("👁️ Pengamatan: 0")
        for s in [self.stat_reflections, self.stat_videos, self.stat_apps]:
            s.setStyleSheet("color: #8b949e; font-size: 10px; font-weight: bold;")
            stats_row.addWidget(s)
        stats_row.addStretch()
        card_vbox.addLayout(stats_row)

        main_layout.addWidget(self.status_card)

        # 3. TABS KONTEN UTAMA
        self.tabs = QTabWidget()

        # Tab A: Model Dialektis Pengguna (Honcho/Hermes User Model)
        self.tab_dialectic = QWidget()
        self._init_dialectic_tab()
        self.tabs.addTab(self.tab_dialectic, "🧠 Model Dialektis Tuan")

        # Tab B: Pohon Keterampilan (Skills Tree)
        self.tab_skills = QWidget()
        self._init_skills_tab()
        self.tabs.addTab(self.tab_skills, "⚡ Pohon Keterampilan (Skills)")

        # Tab C: Jurnal Perenungan Mandiri (Reflection Chronicles)
        self.tab_reflections = QWidget()
        self._init_reflections_tab()
        self.tabs.addTab(self.tab_reflections, "📜 Jurnal Refleksi Mandiri")

        main_layout.addWidget(self.tabs)

        # 4. ACTION BAR (BOTTOM BUTTONS)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        self.btn_reflect_now = QPushButton("⚡ Refleksi Mandiri Sekarang", self)
        self.btn_reflect_now.setObjectName("primary_btn")
        self.btn_reflect_now.setCursor(Qt.PointingHandCursor)
        self.btn_reflect_now.clicked.connect(self._on_click_reflect_now)
        action_layout.addWidget(self.btn_reflect_now)

        self.btn_refresh = QPushButton("🔄 Segarkan Data", self)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_data)
        action_layout.addWidget(self.btn_refresh)

        action_layout.addStretch()

        self.btn_close = QPushButton("Tutup", self)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.accept)
        action_layout.addWidget(self.btn_close)

        main_layout.addLayout(action_layout)

    def _init_dialectic_tab(self):
        vbox = QVBoxLayout(self.tab_dialectic)
        vbox.setContentsMargins(14, 14, 14, 14)
        vbox.setSpacing(10)

        info_lbl = QLabel("Model dialektis adalah representasi pemahaman mendalam yang dibangun Mimi secara bertahap mengenai kebiasaan, ritme kerja, dan preferensi Tuan lintas waktu.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #8b949e; font-size: 10.5px; font-style: italic;")
        vbox.addWidget(info_lbl)

        # Kartu-kartu dialektis
        self.lbl_personality = self._create_dialectic_field(vbox, "🎭 Profil & Karakteristik:", "")
        self.lbl_habits = self._create_dialectic_field(vbox, "⏱️ Kebiasaan & Ritme Kerja:", "")
        self.lbl_comm = self._create_dialectic_field(vbox, "💬 Gaya Komunikasi Disukai:", "")
        self.lbl_topics = self._create_dialectic_field(vbox, "🌟 Minat & Topik Utama:", "")

        vbox.addStretch()

    def _create_dialectic_field(self, parent_layout, label_title, default_val):
        frame = QFrame()
        frame.setObjectName("card")
        f_vbox = QVBoxLayout(frame)
        f_vbox.setContentsMargins(10, 8, 10, 8)
        f_vbox.setSpacing(4)

        t_lbl = QLabel(label_title)
        t_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        t_lbl.setStyleSheet("color: #00f5d4;")
        f_vbox.addWidget(t_lbl)

        val_lbl = QLabel(default_val)
        val_lbl.setFont(QFont("Segoe UI", 10))
        val_lbl.setWordWrap(True)
        val_lbl.setStyleSheet("color: #c9d1d9;")
        f_vbox.addWidget(val_lbl)

        parent_layout.addWidget(frame)
        return val_lbl

    def _init_skills_tab(self):
        vbox = QVBoxLayout(self.tab_skills)
        vbox.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.skills_container = QWidget()
        self.skills_layout = QVBoxLayout(self.skills_container)
        self.skills_layout.setSpacing(8)
        scroll.setWidget(self.skills_container)

        vbox.addWidget(scroll)

    def _init_reflections_tab(self):
        vbox = QVBoxLayout(self.tab_reflections)
        vbox.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.reflections_container = QWidget()
        self.reflections_layout = QVBoxLayout(self.reflections_container)
        self.reflections_layout.setSpacing(8)
        scroll.setWidget(self.reflections_container)

        vbox.addWidget(scroll)

    def refresh_data(self):
        """Memuat ulang seluruh data dari hermes_state.json ke antarmuka visual."""
        state = hermes_agent.load_hermes_state()

        # Update Status Card
        level = state.get("level", 1)
        xp = state.get("xp", 0)
        needed = state.get("xp_to_next", 100)
        title = state.get("title", hermes_agent.EVOLUTION_TITLES.get(level, f"Level {level}"))

        self.level_badge.setText(f"LEVEL {level}")
        self.title_label.setText(title)
        self.xp_text_lbl.setText(f"XP: {xp} / {needed}")

        pct = int(min(100, (xp / max(1, needed)) * 100))
        self.xp_bar.setValue(pct)

        stats = state.get("stats", {})
        self.stat_reflections.setText(f"🧠 Refleksi: {stats.get('reflections_count', 0)}")
        self.stat_videos.setText(f"🍿 Video Ditonton: {stats.get('videos_watched_count', 0)}")
        self.stat_apps.setText(f"👁️ Pengamatan: {stats.get('apps_observed_count', len(getattr(self.evolution_engine, 'recent_apps', [])))}")

        # Update Dialectic Profile
        dp = state.get("dialectic_profile", {})
        self.lbl_personality.setText(dp.get("personality_summary", "Sedang mengamati pola interaksi Tuan..."))
        self.lbl_habits.setText(dp.get("work_habits", "Sedang memetakan jam produktivitas dan aplikasi favorit..."))
        self.lbl_comm.setText(dp.get("communication_preference", "Bahasa Indonesia santai dan akrab."))
        topics = dp.get("observed_topics", [])
        self.lbl_topics.setText(", ".join(topics) if topics else "Koding, Hiburan Video, Obrolan Santai")

        # Update Skills Tree
        while self.skills_layout.count():
            item = self.skills_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for sk in state.get("skills", []):
            card = QFrame()
            card.setObjectName("card")
            c_vbox = QVBoxLayout(card)
            c_vbox.setContentsMargins(10, 8, 10, 8)
            c_vbox.setSpacing(4)

            top_row = QHBoxLayout()
            icon_s = QLabel(sk.get("icon", "✨"))
            icon_s.setFont(QFont("Segoe UI Emoji", 14))
            top_row.addWidget(icon_s)

            name_lbl = QLabel(sk.get("name", "Skill"))
            name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            name_lbl.setStyleSheet("color: #ffffff;")
            top_row.addWidget(name_lbl)
            top_row.addStretch()

            sk_lvl = sk.get("level", 1)
            lvl_lbl = QLabel(f"Mastery Lv. {sk_lvl} " + ("★" * min(5, sk_lvl)))
            lvl_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
            lvl_lbl.setStyleSheet("color: #fee440;")
            top_row.addWidget(lvl_lbl)
            c_vbox.addLayout(top_row)

            desc_lbl = QLabel(sk.get("desc", ""))
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("color: #8b949e; font-size: 9.5px;")
            c_vbox.addWidget(desc_lbl)

            # Mini Progress bar skill
            sk_xp = sk.get("xp", 0)
            sk_max = sk.get("max_xp", 100)
            sk_bar = QProgressBar()
            sk_bar.setFixedHeight(10)
            sk_bar.setRange(0, sk_max)
            sk_bar.setValue(sk_xp)
            sk_bar.setTextVisible(False)
            c_vbox.addWidget(sk_bar)

            self.skills_layout.addWidget(card)

        self.skills_layout.addStretch()

        # Update Reflection Chronicles
        while self.reflections_layout.count():
            item = self.reflections_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        reflections = state.get("reflections", [])
        if not reflections:
            empty_lbl = QLabel("Belum ada perenungan mandiri yang tersimpan.")
            empty_lbl.setStyleSheet("color: #8b949e; font-style: italic; padding: 20px;")
            self.reflections_layout.addWidget(empty_lbl)
        else:
            for ref in reflections:
                rcard = QFrame()
                rcard.setObjectName("card")
                r_vbox = QVBoxLayout(rcard)
                r_vbox.setContentsMargins(10, 8, 10, 8)
                r_vbox.setSpacing(4)

                r_head = QHBoxLayout()
                t_stamp = QLabel(ref.get("timestamp", ""))
                t_stamp.setStyleSheet("color: #8b949e; font-size: 9.5px;")
                r_head.addWidget(t_stamp)
                r_head.addStretch()

                lvl_snap = ref.get("level_snapshot", 1)
                snap_lbl = QLabel(f"Level {lvl_snap}")
                snap_lbl.setStyleSheet("color: #00f5d4; font-size: 9.5px; font-weight: bold;")
                r_head.addWidget(snap_lbl)
                r_vbox.addLayout(r_head)

                insight_lbl = QLabel(ref.get("insight", ""))
                insight_lbl.setWordWrap(True)
                insight_lbl.setStyleSheet("color: #e6edf3; font-size: 10px;")
                r_vbox.addWidget(insight_lbl)

                self.reflections_layout.addWidget(rcard)

        self.reflections_layout.addStretch()

    def _on_click_reflect_now(self):
        """Memicu proses perenungan mandiri seketika."""
        self.btn_reflect_now.setEnabled(False)
        self.btn_reflect_now.setText("⏳ Sedang Merenung & Belajar...")

        def _on_reflection_done(res):
            self.btn_reflect_now.setEnabled(True)
            self.btn_reflect_now.setText("⚡ Refleksi Mandiri Sekarang")
            self.refresh_data()

            insight = res.get("insight", "")
            leveled = res.get("leveled_up", False)
            new_lvl = res.get("new_level", 1)

            if leveled:
                QMessageBox.information(
                    self,
                    "Evolusi Hermes Naik Level! 🌟",
                    f"Meoww! Mimi berhasil berevolusi ke **LEVEL {new_lvl}**!\n\n"
                    f"Gelar Baru: **{res.get('title')}**\n\n"
                    f"Catatan Refleksi:\n\"{insight}\""
                )
            else:
                QMessageBox.information(
                    self,
                    "Refleksi Mandiri Selesai 🧠",
                    f"Mimi telah selesai merenung dan memperoleh wawasan baru (+{res.get('xp_gain', 35)} XP):\n\n"
                    f"\"{insight}\""
                )

        self.evolution_engine.trigger_reflection_cycle(on_done_callback=_on_reflection_done)
