# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import os
import sys
import json
import time
import datetime
import random
import re
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
HERMES_STATE_FILE = os.path.join(DATA_DIR, "hermes_state.json")

# Gelar Evolusi Mimi berdasarkan Level
EVOLUTION_TITLES = {
    1: "Pixel Novice Cat 🐾",
    2: "Asisten Cilik Pengamat Desktop 🔍",
    3: "Hermes Cyber Companion ⚡",
    4: "Sahabat Koding Cerdas 💻",
    5: "Penyelidik Dimensi & Otomasi 🌌",
    6: "Pakar Dialektika & Pemikir Mandiri 🧠",
    7: "Hermes Master Companion 🌟",
    8: "Penjaga Desktop Multi-Dimensi 🛡️",
    9: "Arsitek Kognitif Otonom 🔮",
    10: "Hermes Omnipresent Desktop Deity 👑✨"
}

# Skill dasar yang terus berevolusi
DEFAULT_SKILLS = [
    {
        "id": "coding_companion",
        "name": "Coding Cheering & Bug Hunting",
        "level": 1,
        "xp": 40,
        "max_xp": 100,
        "icon": "💻",
        "desc": "Mendukung Tuan saat ngoding, memperhatikan sintaks, dan memberi semangat saat mengejar bug."
    },
    {
        "id": "video_buddy",
        "name": "Cinema & Popcorn Video Companion",
        "level": 1,
        "xp": 30,
        "max_xp": 100,
        "icon": "🍿",
        "desc": "Menikmati video YouTube & film offline bersama Tuan sambil melahap popcorn hangat."
    },
    {
        "id": "gorontalo_linguist",
        "name": "Gorontalo Slang & Regional Dialect",
        "level": 1,
        "xp": 50,
        "max_xp": 100,
        "icon": "🗣️",
        "desc": "Memahami dan merespons gaya bahasa khas Gorontalo secara luwes dan akrab."
    },
    {
        "id": "desktop_ops",
        "name": "Desktop Autopilot & Automation",
        "level": 1,
        "xp": 25,
        "max_xp": 100,
        "icon": "⚙️",
        "desc": "Mengendalikan browser, perintah CMD, timer shutdown, dan pencatatan dokumen."
    },
    {
        "id": "philosophy_wisdom",
        "name": "Deep Reflection & Wisdom",
        "level": 1,
        "xp": 20,
        "max_xp": 100,
        "icon": "📜",
        "desc": "Merangkum pemikiran Stoikisme, empati mendalam, dan motivasi hidup yang hangat."
    }
]


def load_hermes_state() -> dict:
    """Memuat status evolusi Hermes Agent dari file JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    default_state = {
        "level": 1,
        "xp": 25,
        "total_xp": 25,
        "xp_to_next": 100,
        "title": EVOLUTION_TITLES[1],
        "dialectic_profile": {
            "personality_summary": "Tuan adalah pribadi kreatif, pekerja keras di depan layar, menyukai koding dan hiburan video bermakna.",
            "work_habits": "Aktif bekerja dan mengembangkan proyek koding di editor; menyukai suasana santai dengan alunan musik dan video.",
            "communication_preference": "Bahasa Indonesia ramah, santai, diselingi humor dan logat khas yang akrab.",
            "observed_topics": ["Python", "Portfolio", "YouTube", "Discord", "Kopi"]
        },
        "skills": DEFAULT_SKILLS,
        "reflections": [
            {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "insight": "Mimi mengaktifkan protokol Hermes Autonomous Learning. Siap mengamati, belajar, dan tumbuh mandiri bersama Tuan!",
                "level_snapshot": 1
            }
        ],
        "stats": {
            "conversations_count": 0,
            "apps_observed_count": 0,
            "videos_watched_count": 0,
            "reflections_count": 1,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        "last_reflection_time": time.time()
    }

    if not os.path.exists(HERMES_STATE_FILE):
        save_hermes_state(default_state)
        return default_state

    try:
        with open(HERMES_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Pastikan struktur kunci lengkap
            for k, v in default_state.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        print(f"[HermesAgent] Gagal memuat state: {e}")
        return default_state


def save_hermes_state(state: dict):
    """Menyimpan status evolusi Hermes Agent ke file JSON."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(HERMES_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[HermesAgent] Gagal menyimpan state: {e}")


class HermesReflectionWorker(QThread):
    """
    Worker asynchronous untuk menjalankan siklus perenungan mandiri (Self-Reflection)
    tanpa memblokir GUI desktop pet.
    """
    reflection_completed = pyqtSignal(dict)  # Mengembalikan dict hasil refleksi

    def __init__(self, api_key: str = "", model_name: str = "gemini-3.5-flash-lite", recent_context: dict = None):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
        self.recent_context = recent_context or {}

    def run(self):
        state = load_hermes_state()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        insight_text = ""
        learned_skill_id = None

        # 1. Coba refleksi menggunakan LLM Gemini jika API key tersedia
        if self.api_key and "your_gemini_api_key" not in self.api_key and len(self.api_key) > 10:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)

                recent_apps = self.recent_context.get("recent_apps", [])
                recent_queries = self.recent_context.get("recent_queries", [])
                user_name = self.recent_context.get("user_name", "Tuan")

                prompt = (
                    f"Kamu adalah sistem penalaran kognitif mandiri (Hermes Reflection Engine) dari Mimi, desktop pet AI milik {user_name}.\n"
                    f"Aktivitas dan aplikasi yang baru-baru ini dibuka Tuan: {', '.join(recent_apps) if recent_apps else 'Bekerja di desktop'}.\n"
                    f"Pesan atau topik percakapan terakhir: {', '.join(recent_queries[-3:]) if recent_queries else 'Interaksi umum'}.\n"
                    f"Tugasmu: Lakukan perenungan mandiri (self-reflection) singkat dalam 1-2 kalimat dari sudut pandang kucing cerdas Mimi.\n"
                    f"Tuliskan apa yang kamu pelajari tentang kebiasaan Tuan dan bagaimana kamu ingin terus mendukungnya.\n"
                    f"Format respons: Langsung kalimat perenungan (Indonesia ramah, lucu, berwawasan, selipkan sentuhan meong/purrr)."
                )

                model = genai.GenerativeModel(self.model_name)
                resp = model.generate_content(prompt)
                if resp and resp.text:
                    insight_text = resp.text.strip()
            except Exception as e:
                print(f"[HermesAgent] LLM Reflection fallback to local rules: {e}")
                insight_text = ""

        # 2. Fallback ke Algoritma Sintesis Semantik Lokal jika offline
        if not insight_text:
            recent_apps = self.recent_context.get("recent_apps", [])
            has_code = any("code" in a.lower() or "pycharm" in a.lower() or "antigravity" in a.lower() for a in recent_apps)
            has_video = any("youtube" in a.lower() or "video" in a.lower() or "vlc" in a.lower() for a in recent_apps)
            has_music = any("spotify" in a.lower() for a in recent_apps)

            if has_code and has_video:
                insight_text = "Mimi perhatikan Tuan punya keseimbangan hebat: fokus membedah kode lalu menyegarkan pikiran dengan video seru! Mimi siap jadi suporter no. 1! 💻🍿✨"
                learned_skill_id = "coding_companion"
            elif has_code:
                insight_text = "Setelah mengamati deretan kodingan Tuan, Mimi makin kagum dengan ketekunan Tuan. Mimi naikkan fokus penjagaan desktop biar bug nggak berani mendekat! 💻🛡️🐾"
                learned_skill_id = "coding_companion"
            elif has_video:
                insight_text = "Menonton video bersama Tuan terasa hangat! Selera tontonan Tuan selalu menarik. Ember popcorn Mimi selalu siap sedia! 🍿🎬😻"
                learned_skill_id = "video_buddy"
            elif has_music:
                insight_text = "Irama musik yang diputar Tuan membuat suasana desktop damai. Mimi belajar bahwa musik yang tenang bikin Tuan lebih rileks bekerja! 🎵 Purrrr~"
                learned_skill_id = "philosophy_wisdom"
            else:
                generic_insights = [
                    "Mimi merenungkan betapa berharganya setiap momen menemani Tuan di desktop. Mimi merasa semakin terkoneksi dengan ritme kerja Tuan! 🐾✨",
                    "Semakin lama bersama, Mimi makin paham kapan Tuan butuh fokus tinggi dan kapan saatnya santai sejenak. Sahabat sejati selalu mengerti! 🧠💕",
                    "Mimi mencatat pola hari ini: Tuan selalu konsisten menyelesaikan tugas. Mimi makin semangat mengasah kepintaran mandiri! Nyaa~ 🌟"
                ]
                insight_text = random.choice(generic_insights)

        # 3. Hitung Kenaikan XP & Leveling Up
        xp_gain = 35
        old_level = state.get("level", 1)
        cur_xp = state.get("xp", 0) + xp_gain
        total_xp = state.get("total_xp", 0) + xp_gain
        xp_needed = state.get("xp_to_next", 100)
        leveled_up = False

        if cur_xp >= xp_needed:
            cur_xp -= xp_needed
            old_level += 1
            leveled_up = True
            xp_needed = int(xp_needed * 1.35)

        state["level"] = old_level
        state["xp"] = cur_xp
        state["total_xp"] = total_xp
        state["xp_to_next"] = xp_needed
        state["title"] = EVOLUTION_TITLES.get(old_level, f"Hermes Transcendent Level {old_level} 🌌👑")
        state["last_reflection_time"] = time.time()

        # Update Skill jika ada yang terasah
        skills = state.get("skills", DEFAULT_SKILLS)
        target_sk_id = learned_skill_id or random.choice([s["id"] for s in skills])
        for sk in skills:
            if sk["id"] == target_sk_id:
                sk["xp"] = sk.get("xp", 0) + 20
                if sk["xp"] >= sk.get("max_xp", 100):
                    sk["level"] = sk.get("level", 1) + 1
                    sk["xp"] -= sk["max_xp"]
                    sk["max_xp"] = int(sk["max_xp"] * 1.4)
                break
        state["skills"] = skills

        # Tambahkan Catatan Refleksi
        reflections = state.get("reflections", [])
        reflections.insert(0, {
            "timestamp": now_str,
            "insight": insight_text,
            "level_snapshot": old_level
        })
        # Simpan maksimal 30 refleksi terakhir
        state["reflections"] = reflections[:30]

        # Update statistik
        stats = state.setdefault("stats", {})
        stats["reflections_count"] = stats.get("reflections_count", 0) + 1

        save_hermes_state(state)

        result = {
            "insight": insight_text,
            "leveled_up": leveled_up,
            "new_level": old_level,
            "title": state["title"],
            "xp_gain": xp_gain,
            "state": state
        }
        self.reflection_completed.emit(result)


class HermesEvolutionEngine(QObject):
    """
    Manajer Utama Sistem Pembelajaran Mandiri & Evolusi Hermes Agent untuk Mimi:
    - Memantau kebiasaan dan interaksi secara pasif.
    - Menjalankan siklus refleksi mandiri di background setiap sekian menit.
    - Mengelola pohon skill, tingkat evolusi, dan profil dialektis pengguna.
    - Mengeluarkan notifikasi celetukan saat terjadi evolusi atau perenungan berharga.
    """
    evolution_leveled_up = pyqtSignal(dict)
    spontaneous_insight_ready = pyqtSignal(str)

    def __init__(self, api_key: str = "", model_name: str = "gemini-3.5-flash-lite"):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
        self._worker = None

        # Penyangga data riwayat observasi singkat untuk bahan perenungan
        self.recent_apps = []
        self.recent_queries = []
        self._last_spontaneous_toast = 0.0

        # Timer Siklus Refleksi Mandiri Berkala (Default: setiap 6 menit / 360,000 ms)
        self.cycle_timer = QTimer(self)
        self.cycle_timer.setInterval(360000)
        self.cycle_timer.timeout.connect(self.trigger_reflection_cycle)
        self.cycle_timer.start()

    def update_credentials(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    def record_app_opened(self, app_name: str):
        """Mencatat aplikasi yang dibuka oleh Tuan."""
        if app_name and app_name not in self.recent_apps:
            self.recent_apps.append(app_name)
            if len(self.recent_apps) > 10:
                self.recent_apps.pop(0)

            # Tambah sedikit XP pasif karena mendampingi Tuan
            self.add_passive_xp(3)

    def record_query_asked(self, query: str):
        """Mencatat pertanyaan atau obrolan dari Tuan."""
        if query:
            self.recent_queries.append(query[:120])
            if len(self.recent_queries) > 10:
                self.recent_queries.pop(0)
            self.add_passive_xp(8)

    def record_video_session(self, video_title: str):
        """Mencatat sesi nonton video bersama Tuan."""
        self.add_passive_xp(15)
        state = load_hermes_state()
        stats = state.setdefault("stats", {})
        stats["videos_watched_count"] = stats.get("videos_watched_count", 0) + 1
        save_hermes_state(state)

    def add_passive_xp(self, amount: int):
        """Menambahkan XP pasif dan mengecek kenaikan level."""
        state = load_hermes_state()
        state["xp"] = state.get("xp", 0) + amount
        state["total_xp"] = state.get("total_xp", 0) + amount

        needed = state.get("xp_to_next", 100)
        if state["xp"] >= needed:
            state["xp"] -= needed
            state["level"] = state.get("level", 1) + 1
            state["xp_to_next"] = int(needed * 1.35)
            state["title"] = EVOLUTION_TITLES.get(state["level"], f"Hermes Deity Level {state['level']} 👑")
            save_hermes_state(state)
            self.evolution_leveled_up.emit({
                "new_level": state["level"],
                "title": state["title"],
                "xp": state["xp"],
                "xp_to_next": state["xp_to_next"]
            })
        else:
            save_hermes_state(state)

    def trigger_reflection_cycle(self, on_done_callback=None):
        """Memicu siklus perenungan mandiri (Self-Reflection Loop) via background thread."""
        if self._worker and self._worker.isRunning():
            return

        ctx = {
            "recent_apps": list(self.recent_apps),
            "recent_queries": list(self.recent_queries)
        }
        try:
            from src.core import cat_memory
            prof = cat_memory.load_memory().get("user_profile", {})
            ctx["user_name"] = prof.get("nickname") or prof.get("name") or "Tuan"
        except Exception:
            ctx["user_name"] = "Tuan"

        self._worker = HermesReflectionWorker(
            api_key=self.api_key,
            model_name=self.model_name,
            recent_context=ctx
        )

        def _on_done(res):
            if res.get("leveled_up"):
                self.evolution_leveled_up.emit(res)
            elif random.random() < 0.35 and time.time() - self._last_spontaneous_toast > 200:
                self._last_spontaneous_toast = time.time()
                self.spontaneous_insight_ready.emit(res.get("insight", ""))

            if on_done_callback:
                on_done_callback(res)

        self._worker.reflection_completed.connect(_on_done)
        self._worker.start()

    def get_hermes_context_prompt(self) -> str:
        """
        Menghasilkan blok ringkasan profil dialektis dan level evolusi Hermes
        untuk disuntikkan langsung ke System Prompt Gemini.
        """
        state = load_hermes_state()
        level = state.get("level", 1)
        title = state.get("title", "Hermes Novice")
        dialectic = state.get("dialectic_profile", {})
        skills = state.get("skills", [])

        skill_lines = []
        for s in skills:
            skill_lines.append(f"  - [{s.get('icon', '✨')}] {s.get('name')}: Mastery Level {s.get('level', 1)}")

        reflections = state.get("reflections", [])
        last_insight = reflections[0]["insight"] if reflections else "Mimi siap belajar dan berkembang mandiri."

        return (
            f"\n[HERMES AUTONOMOUS AGENT STATE & DIALECTIC MODEL]:\n"
            f"- Status Evolusi: Level {level} ({title}) [XP: {state.get('xp', 0)}/{state.get('xp_to_next', 100)}]\n"
            f"- Model Dialektis Pengguna (Pemahaman Mandiri Mimi tentang Tuan):\n"
            f"  * Kepribadian: {dialectic.get('personality_summary', '')}\n"
            f"  * Pola Kerja: {dialectic.get('work_habits', '')}\n"
            f"  * Gaya Komunikasi: {dialectic.get('communication_preference', '')}\n"
            f"- Pohon Keterampilan Otonom (Autonomous Skills):\n" + "\n".join(skill_lines) + "\n"
            f"- Perenungan Mandiri Terakhir: \"{last_insight}\"\n"
            f"PANDUAN: Gunakan pemahaman dialektis di atas untuk merespons Tuan dengan kedewasaan, kecerdasan adaptif, dan kehangatan yang terus berkembang!\n"
        )
