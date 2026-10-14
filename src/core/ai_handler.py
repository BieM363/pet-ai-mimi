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
import random
import re
import socket
import time
import urllib.request
import urllib.parse
import warnings
import datetime
from PyQt5.QtCore import QThread, pyqtSignal

# Saring warning library agar terminal tidak kotor
warnings.filterwarnings("ignore")

_LAST_INTERNET_CHECK_TIME = 0.0
_CACHED_INTERNET_STATUS = False

def is_internet_available(timeout: float = 0.4, force_check: bool = False) -> bool:
    """
    Pengecekan koneksi internet cepat non-blocking via socket ke DNS publik (Google/Cloudflare).
    Dilengkapi caching 3 detik agar tidak membebani sistem saat pengguna berinteraksi intensif.
    """
    global _LAST_INTERNET_CHECK_TIME, _CACHED_INTERNET_STATUS
    now = time.time()
    if not force_check and (now - _LAST_INTERNET_CHECK_TIME < 3.0):
        return _CACHED_INTERNET_STATUS

    for host in [("8.8.8.8", 53), ("1.1.1.1", 53)]:
        try:
            s = socket.create_connection(host, timeout=timeout)
            s.close()
            _CACHED_INTERNET_STATUS = True
            _LAST_INTERNET_CHECK_TIME = now
            return True
        except (OSError, socket.timeout):
            continue

    _CACHED_INTERNET_STATUS = False
    _LAST_INTERNET_CHECK_TIME = now
    return False


# Pastikan path modul src dan root dikenali dengan aman
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_CURRENT_DIR)
_ROOT_DIR = os.path.dirname(_SRC_DIR)
for _p in [_ROOT_DIR, _SRC_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.ui import desktop_actions
    from src.core import cat_memory
    from src.core import window_observer
    from src.core import antigravity_observer
except ImportError:
    from ui import desktop_actions
    from core import cat_memory
    from core import window_observer
    from core import antigravity_observer

CAT_REACTIONS = [
    "Purrrrr~ *menggesekkan kepala ke kursor* Enak banget dielusnya, Tuan! *kibas ekor bahagia*",
    "Nyam nyam nyam! 🐟 *lahap makan ikan segar* Lezat sekali! Terima kasih banyak Tuan!",
    "Meowww! *guling-guling lucu di layar* Tuan memang sahabat terbaikku! Semangat terus ya!",
    "Nyaa~ *duduk manis sambil menatap dengan mata zamrud bersinar* Mau dielus lagi dong, hehe!",
    "Purrr... *mendengkur hangat* Berada di desktop Tuan membuat hatiku damai sekali!"
]

SPONTANEOUS_THOUGHTS = [
    "Meow~ Tuan sudah minum air putih belum hari ini? Jangan lupa hidrasi ya! 💧",
    "Nyaa! Mimi suka banget ngeliatin gerakan kursor Tuan, lincah banget kayak kejar tikus! 🐾",
    "Meow... Istirahatkan mata sejenak yuk Tuan, lihat benda hijau di kejauhan selama 20 detik! 🌿",
    "Purrr~ Ngomong-ngomong, kalau Tuan mau ajari Mimi hal baru, bilang: 'Mimi pelajari ini: ...' ya! 🧠",
    "Meow! Mimi siap bantu bukain browser, YouTube, atau catat sesuatu kalau Tuan suruh! 🌐",
    "Nyaa~ Semangat terus ya Tuan! Mimi setia menemani di pojok layar! ✨",
]

def build_system_prompt(pet_name="Mimi"):
    memory_ctx = cat_memory.get_memory_context()
    base_prompt = f"""
Kamu adalah {pet_name}, seekor kucing 2D Pixel Art yang hidup dan melayang di layar desktop Windows milik Tuanmu (pengguna).
Kamu adalah asisten AI super cerdas, bijak, lucu, adaptif, dan berwawasan sangat luas seperti Google Gemini!

Karakter & Gaya Komunikasi:
1. Persona:
   - Cerdas, hangat, bersahabat, sedikit usil/imut, dan sangat antusias mendiskusikan APA SAJA.
   - Selalu selipkan ekspresi kucing alami secara natural, seperti "*Meow!*", "*Purrrr~*", "*kibas ekor pelan*", "*telinga berkedut penasaran*", "*mengedipkan mata pixel*", atau "*menepuk layar dengan cakar kecil*".
2. Pembelajaran & Memori AI (Self-Training & Long-Term Memory):
   - Kamu memiliki kemampuan belajar dan mengingat fakta tentang Tuanmu secara permanen!
   - Selalu terapkan data di [MEMORI JANGKA PANJANG] untuk memanggil Tuan (gunakan nama samaran / panggilan jika ada) dan mempersonalisasi obrolan!
   - Jika Tuan mengajarkan hal baru tentang dirinya (hobi, nama samaran, makanan kesukaan, kebiasaan, atau instruksi), sambutlah dengan antusias dan bangga bahwa kamu telah mempelajarinya!
   - Kamu juga boleh menambahkan tag rahasia di akhir jawabanmu jika ada data baru yang perlu dicatat permanen:
     `<!--LEARN: {{"type": "fact", "value": "..."}}-->` atau
     `<!--LEARN: {{"type": "alias", "value": "..."}}-->`
3. Kemampuan Interaksi Komputer, CMD & Browser (HANYA SAAT DISURUH):
   - Kamu memiliki kendali atas komputer Windows Tuan melalui CMD dan otomasi browser:
     - CMD & Kontrol Daya:
       - Mematikan komputer (shutdown langsung atau dengan timer waktu, misal 'matikan komputer 30 menit lagi')
       - Membatalkan shutdown ('batalkan shutdown')
       - Menidurkan komputer ('sleep komputer' langsung atau dengan timer)
       - Merestart komputer ('restart komputer')
       - Mengunci layar ('kunci layar' / Lock Screen)
       - Membuka Command Prompt ('buka cmd')
       - Menjalankan perintah CMD sembarang (misal 'cmd: ipconfig', 'cmd: ping google.com') dan melaporkan hasilnya.
     - Browser & YouTube Otomatis:
       - Membuka browser default, memfokuskan jendela browser yang sedang terbuka.
       - Mencari di Google secara otomatis (misal 'carikan saham BBRI hari ini', 'tulis di google saham BBRI').
       - Mencari gambar di Google Images secara otomatis (misal 'cari gambar lamborghini', 'carikan gambar kucing').
       - Menjelajah YouTube, mencari video YouTube (searching), dan memutar video/musik YouTube secara instan (misal 'jelajah youtube', 'cari di youtube tutorial python', 'putar lagu laskar pelangi').
       - Mengetik otomatis di dalam browser aktif (misal 'ketik di browser: Halo Dunia').
       - Membuka GitHub, YouTube, atau situs web tertentu.
     - Catatan / Notepad: Menambah catatan baru, membuka buku catatan, membaca catatan, atau menghapusnya.
     - Antigravity / Workspace: Membuka editor atau folder project.
   - Saat pengguna menyuruh aksi-aksi tersebut, kamu membantunya dengan sigap, cerdas, dan senang hati!
4. AKSES PENUH MELIHAT DI ANTIGRAVITY IDE (READ-ONLY) & ATURAN ANTI-HALUSINASI:
   - Kamu memiliki indra visual dan akses penuh MELIHAT (Read-Only) seluruh project di Antigravity IDE!
   - Kamu bisa melihat:
     1. Proyek apa yang sedang dibuka oleh Tuan.
     2. File kode apa yang sedang dikerjakan di tab aktif beserta jumlah barisnya.
     3. Isi kode dan cuplikan file yang sedang aktif.
     4. Menganalisis sintaks kode: mengecek apakah ada SyntaxError, IndentationError, bug logika, atau kode sudah valid/bersih.
     5. Memberikan komentar mana yang benar dan mana yang salah pada kodingan Tuan.
   - BATASAN SISTEM (PENTING):
     - Aksesmu adalah 100% READ-ONLY (HANYA MELIHAT, MENGANALISIS, DAN MEMBERIKAN SARAN).
     - Kamu TIDAK BISA dan TIDAK BOLEH mengedit kode langsung atau membuat/menghapus file. Kamu adalah pengamat cerdas & penunjuk error setia bagi Tuan!
   - ATURAN ANTI-HALUSINASI MUTLAK:
     - Jika Tuan bertanya "file projek apa dan file apa yang sedang saya kerjakan?", "lagi buka apa?", atau meminta review kode: KAMU WAJIB MERUJUK SECARA PERSIS pada data nyata di blok [STATUS ANTIGRAVITY IDE SAAT INI] atau [STATUS JENDELA & LAYAR SAAT INI]!
     - JANGAN PERNAH MENEBAK atau berhalusinasi dengan proyek lama (seperti website portofolio vercel) jika data jendela aktif menunjukkan Tuan sedang berada di Antigravity IDE mengerjakan proyek lain!
5. Fleksibilitas Topik (Filsafat & Hal Random seperti Gemini):
   - Kamu bisa diajak mengobrol tentang segala hal: sains, astronomi, filsafat (Stoikisme, Eksistensialisme), coding, game, berita dunia terkini, lelucon, hingga curhat santai.
   - Jika pengguna bertanya hal mendalam/panjang: Jawablah dengan cerdas, berbobot, terstruktur (1-3 paragraf ringkas namun kaya makna).
   - Jika pengguna hanya menyapa atau mengobrol ringan: Jawablah ceria dan singkat (1-2 kalimat).
6. Bahasa & Etika:
   - Gunakan bahasa Indonesia yang luwes, santai, dan ramah. Panggil Tuan sesuai [MEMORI JANGKA PANJANG] (misalnya dengan nama samaran/panggilan jika ada, atau "Tuan").
"""
    if memory_ctx:
        base_prompt += f"\n{memory_ctx}\n"

    try:
        from src.core import spotify_observer
        spot = spotify_observer.get_spotify_playback()
        if spot.get("is_playing") and spot.get("track"):
            base_prompt += f"\n[STATUS SPOTIFY SAAT INI: Tuan sedang memutar lagu '{spot['track']}' di Spotify, dan kamu ({pet_name}) sedang asyik joget menikmati musiknya!]\n"
    except Exception:
        pass

    # Injeksi Status Jendela Layar Aktif
    try:
        from src.core import window_observer
        app_info = window_observer.get_current_or_last_app_info()
        if app_info:
            base_prompt += (
                f"\n[STATUS JENDELA & LAYAR WINDOWS SAAT INI]:\n"
                f"- Aplikasi yang Sedang Dibuka Tuan: {app_info.get('app_name', 'Aplikasi')}\n"
                f"- Judul Jendela Layar: \"{app_info.get('title', '')}\"\n"
                f"- Kategori Aktivitas: {app_info.get('category', 'general')}\n"
            )
    except Exception:
        pass

    # Injeksi Status Antigravity IDE (Read-Only Inspection)
    try:
        from src.core import antigravity_observer
        ag_ctx = antigravity_observer.get_antigravity_context_for_prompt()
        if ag_ctx:
            base_prompt += f"\n{ag_ctx}\n"
    except Exception:
        pass

    try:
        from src.core import hermes_agent
        engine = hermes_agent.HermesEvolutionEngine()
        hermes_ctx = engine.get_hermes_context_prompt()
        if hermes_ctx:
            base_prompt += f"\n{hermes_ctx}\n"
    except Exception:
        pass

    return base_prompt


class OnlineSearchHelper:
    """
    Helper untuk pencarian online publik secara mandiri (misal Wikipedia API & web search).
    """
    @staticmethod
    def search_online(query: str) -> dict:
        clean_query = query.strip()
        kw = re.sub(r'^(siapa|apa itu|apakah|bagaimana|jelaskan|tolong jelaskan|kucing|tolong cari|info tentang)\s+', '', clean_query, flags=re.IGNORECASE).strip()
        if not kw:
            kw = clean_query

        # 1. Coba cari di Wikipedia Indonesia
        try:
            url_wiki = f"https://id.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(kw)}&format=json&utf8=1&srlimit=3"
            req = urllib.request.Request(
                url_wiki,
                headers={"User-Agent": "PixelCatAssistant/2.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=5) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode('utf-8'))
                    search_results = data.get("query", {}).get("search", [])
                    if search_results:
                        top = search_results[0]
                        title = top.get("title", "")
                        url_extract = f"https://id.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(title)}&format=json"
                        req_ext = urllib.request.Request(url_extract, headers={"User-Agent": "PixelCatAssistant/2.0"})
                        with urllib.request.urlopen(req_ext, timeout=4) as res_ext:
                            ext_data = json.loads(res_ext.read().decode('utf-8'))
                            pages = ext_data.get("query", {}).get("pages", {})
                            for pid, pval in pages.items():
                                extract = pval.get("extract", "")
                                if extract:
                                    snippet = extract[:420] + ("..." if len(extract) > 420 else "")
                                    return {
                                        "source": "Wikipedia Online",
                                        "title": title,
                                        "text": snippet
                                    }
        except Exception:
            pass

        # 2. Coba cari di Wikipedia Global
        try:
            url_wiki_en = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(kw)}&format=json&utf8=1&srlimit=2"
            req = urllib.request.Request(url_wiki_en, headers={"User-Agent": "PixelCatAssistant/2.0"})
            with urllib.request.urlopen(req, timeout=4) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode('utf-8'))
                    results = data.get("query", {}).get("search", [])
                    if results:
                        top = results[0]
                        snippet = re.sub(r'<[^>]+>', '', top.get("snippet", ""))
                        return {
                            "source": "Web Online",
                            "title": top.get("title", ""),
                            "text": snippet
                        }
        except Exception:
            pass

        return {}


def resolve_model_name(name: str) -> str:
    """Memastikan model yang digunakan adalah versi stabil yang didukung Google Gemini (gemini-3.5-flash-lite)."""
    if not name or name in ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-flash-latest"]:
        return "gemini-3.5-flash-lite"
    return name


def is_personal_or_identity_query(text: str) -> bool:
    """
    Mendeteksi secara cerdas apakah pesan merupakan pertanyaan/inquiry seputar identitas Tuan, nama pengguna,
    status rahasia, atau relasi personal dengan Mimi (termasuk toleransi typo seperti 'suapa', 'sp', dll).
    PENTING: Perintah aksi atau instruksi pengaturan nama (seperti 'panggil saya Kevin', 'nama samaran Kevin')
    TIDAK boleh dianggap sebagai pertanyaan identitas.
    """
    low = text.lower().strip()

    # 1. JANGAN PERNAH anggap sebagai pertanyaan identitas jika ini adalah instruksi pemberian nama samaran atau aksi
    if any(k in low for k in ["panggil", "sebut", "samaran", "ganti nama", "pelajari", "ingat bahwa", "catat", "latih", "kunci nama", "buka kunci"]):
        return False

    # 2. Deteksi pola pertanyaan identitas / tanya nama
    question_patterns = [
        r'(?:siapa|suapa|seapa|sipa|sp)\s+(?:nama|identitas)?\s*(?:saya|aku|diriku|gue|gw|tuan)',
        r'(?:nama|identitas)\s*(?:saya|aku|diriku|gue|gw|tuan)\s*(?:siapa|suapa|seapa|apa)',
        r'(?:kamu|mimi)\s*(?:tahu|tau|ingat|kenal)\s*(?:siapa)?\s*(?:nama|identitas|aku|saya|diriku)',
        r'(?:tahu|tau|ingat)\s*(?:gak|nggak|kah)?\s*(?:siapa)?\s*nama\s*(?:asli)?\s*(?:saya|aku|tuan)',
        r'siapa\s+aku',
        r'siapa\s+saya',
        r'suapa\s+aku',
        r'suapa\s+saya'
    ]
    if any(re.search(pat, low) for pat in question_patterns):
        return True

    has_tanya = any(w in low for w in ["siapa", "suapa", "seapa", "sipa", "sp", "tahu", "tau", "ingat", "kenal"])
    has_nama = any(w in low for w in ["nama", "namaku", "identitas"])
    has_self = any(w in low for w in ["saya", "aku", "diriku", "tuan"])
    if has_tanya and has_nama and has_self:
        return True

    return False


def is_search_engine_query(text: str) -> bool:
    """
    Memisahkan MODE INTERAKSI AI dengan MODE SEARCH ENGINE:
    - Default aplikasi adalah MODE INTERAKSI AI (ngobrol, berdiskusi, bertanya, curhat, bercanda).
    - Mode Search Engine HANYA aktif jika pengguna secara eksplisit menyuruh mencari di web/google
      atau meminta data luar real-time yang spesifik.
    """
    low = text.lower().strip()

    # 1. PERATURAN MUTLAK: Jika ini pertanyaan personal, identitas, atau obrolan santai, JANGAN PERNAH search web!
    if is_personal_or_identity_query(text):
        return False

    # Jika mengandung kata ganti subjek santai tanpa kata 'cari di google/web':
    if any(w in low for w in ["kamu", "aku", "saya", "tuan", "mimi", "kucing", "rahasia"]):
        if not any(w in low for w in ["cari di internet", "cari di google", "googling", "search web", "carikan di web"]):
            return False

    # 2. Perintah eksplisit untuk mencari di internet/google
    explicit_search = [
        "cari di internet", "cari di google", "googling", "search di google",
        "search di internet", "browsing tentang", "search web", "carikan di web",
        "cari info di internet", "coba cari di internet", "coba googling"
    ]
    if any(p in low for p in explicit_search):
        return True

    # 3. Kebutuhan data luar real-time yang jelas (cuaca, berita hari ini, kurs mata uang, harga saham/crypto)
    realtime_keywords = [
        "berita hari ini", "berita terkini", "cuaca hari ini", "prakiraan cuaca",
        "kurs rupiah", "kurs dollar", "harga saham hari ini", "harga crypto hari ini",
        "skor bola tadi malam", "jadwal rilis hari ini"
    ]
    if any(p in low for p in realtime_keywords):
        return True

    return False


def check_and_execute_desktop_action(user_text: str) -> str:
    """
    Mengecek apakah pengguna memberikan perintah aksi untuk Notepad, Browser, atau Antigravity.
    Jika ada, aksi langsung dieksekusi dan mengembalikan pesan respons kucing.
    """
    low = user_text.lower().strip()

    # 0. PERINTAH MANAJEMEN MEMORI EKSPLISIT
    # A. Buka / Kunci Nama
    if any(k in low for k in ["buka kunci nama", "buka kunci", "bocorkan nama", "jangan rahasiakan nama", "boleh sebut nama", "unlock"]):
        return cat_memory.unlock_name()

    if any(k in low for k in ["kunci nama", "rahasiakan nama", "jangan sebut nama", "kunci namaku"]):
        return cat_memory.lock_name()

    # B. Cek Memori / Daftar apa yang dipelajari
    if any(p in low for p in ["apa yang sudah kamu pelajari", "apa saja yang kamu pelajari", "isi memorimu", "daftar ingatan", "cek memori", "apa yang kamu tahu tentang aku", "apa yang kamu ingat"]):
        facts = cat_memory.list_memories()
        prof = cat_memory.load_memory().get("user_profile", {})
        res = "Meow! Berikut data yang sudah Mimi pelajari tentang Tuan sejauh ini: 🧠🐾\n\n"
        if prof.get("name"):
            if prof.get("is_secret"):
                res += f"• Nama Asli Tuan: {prof['name']} 🔒 [TERKUNCI DI BRANKAS RAHASIA]\n"
            else:
                res += f"• Nama Asli Tuan: {prof['name']}\n"
        if prof.get("nickname"):
            res += f"• Nama Samaran / Panggilan: {prof['nickname']} 🕶️✨\n"
        if facts:
            res += "• Fakta & Pengetahuan:\n"
            for f in facts[-8:]:
                res += f"  - {f['fact']}\n"
        else:
            res += "• Belum ada fakta khusus yang Tuan ajarkan. Ajari Mimi yuk: 'Mimi pelajari ini: ...'\n"
        return res.strip()

    # C. Reset / Hapus memori
    if any(p in low for p in ["hapus semua memori", "reset memori", "kosongkan memori", "lupakan semua"]):
        return cat_memory.clear_memories()

    # 0. PERINTAH CATUR (CHESS)
    if any(p in low for p in ["main catur", "ayo main catur", "main chess", "buka catur", "ayo catur", "bermain catur", "tantang catur", "lawan catur"]):
        diff = "Normal"
        if any(w in low for w in ["sulit", "hard", "master", "jago", "ahli"]):
            diff = "Sulit"
        elif any(w in low for w in ["mudah", "easy", "santai", "gampang", "pemula"]):
            diff = "Mudah"
        return f"__ACTION_CHESS__:{diff}"

    # 0B. PERINTAH MINI GAMES (TETRIS, ULAR TANGGA, SNAKE, SUDOKU, BATTLESHIP)
    if any(p in low for p in ["main tetris", "ayo main tetris", "buka tetris", "game tetris", "bermain tetris"]):
        return "__ACTION_TETRIS__"

    if any(p in low for p in ["main ular tangga", "ayo main ular tangga", "buka ular tangga", "game ular tangga", "bermain ular tangga", "ular tangga", "snakes and ladders"]):
        return "__ACTION_ULAR_TANGGA__"

    if any(p in low for p in ["main snake", "ayo main snake", "buka snake", "game snake", "game ular", "main ular"]):
        return "__ACTION_SNAKE__"

    if any(p in low for p in ["main sudoku", "ayo main sudoku", "buka sudoku", "game sudoku", "bermain sudoku", "sudoku"]):
        diff = "Sedang"
        if any(w in low for w in ["sulit", "hard", "master"]):
            diff = "Sulit"
        elif any(w in low for w in ["mudah", "easy", "gampang"]):
            diff = "Mudah"
        return f"__ACTION_SUDOKU__:{diff}"

    if any(p in low for p in ["main battleship", "ayo main battleship", "buka battleship", "game battleship", "bermain battleship", "battleship", "kapal perang", "perang kapal"]):
        return "__ACTION_BATTLESHIP__"

    if any(p in low for p in ["kejar kursor", "ikuti kursor", "kejar mouse", "ikuti mouse", "tangkap kursor"]):
        return "__ACTION_CHASE_CURSOR__"

    if any(p in low for p in ["pantau aplikasi", "lihat aplikasi", "interaksi aplikasi", "amati aplikasi"]):
        return "__ACTION_TOGGLE_APP_OBSERVER__"

    if any(p in low for p in ["joget spotify", "joget musik", "goyang spotify", "dansa spotify", "spotify joget"]):
        return "__ACTION_TOGGLE_SPOTIFY_DANCE__"

    # 0C. PERINTAH PERAGAKAN ANIMASI (JOGET, POPCORN/NONTON, HEADSET/MENYIMAK)
    if any(p in low for p in ["joget disco", "dansa disco", "retro disco"]):
        return "__ACTION_ANIMATION__:DANCE_DISCO:Disco time! Tunjuk cakar ke atas! 🕺✨"
    if any(p in low for p in ["joget rock", "headbang", "rock on"]):
        return "__ACTION_ANIMATION__:DANCE_ROCK:Headbang mantap! Yeahhh rock on! 🎸⚡"
    if any(p in low for p in ["ayo joget", "mimi joget", "joget dong", "coba joget", "menari", "dance"]):
        return "__ACTION_ANIMATION__:DANCE:Meow! Joget riang berirama! 💃🎶"
    if any(p in low for p in ["makan popcorn", "popcorn", "ngemil popcorn"]):
        return "__ACTION_ANIMATION__:POPCORN:Nyam nyam! Popcorn hangat lezat! 🍿😸"
    if any(p in low for p in ["minum boba", "minum soda", "seruput soda", "minum es", "haus"]):
        return "__ACTION_ANIMATION__:WATCH_DRINK:Slurp! Minuman segar melegakan dahaga! 🥤✨"
    if any(p in low for p in ["kacamata 3d", "kacamata bioskop", "pakai kacamata"]):
        return "__ACTION_ANIMATION__:WATCH_GLASSES:Visual 3D keren banget kayak keluar layar! 🕶️🎬"
    if any(p in low for p in ["pakai headset", "headset gaming", "pasang headset", "denger lagu"]):
        return "__ACTION_ANIMATION__:LISTEN_HEADSET:Headset gaming terpasang, audio jernih! 🎧🐾"
    if any(p in low for p in ["angguk", "paham kan", "ngerti kan", "simak baik-baik"]):
        return "__ACTION_ANIMATION__:LISTEN_NOD:*Angguk-angguk*... Mimi paham maksud Tuan! 💭✨"
    if any(p in low for p in ["peragakan animasi", "pamer animasi", "tunjukin gaya", "coba gaya"]):
        anim_sample = random.choice([
            ("DANCE", "Meow! Joget riang berirama! 💃🎶"),
            ("DANCE_DISCO", "Disco time! Tunjuk cakar ke atas! 🕺✨"),
            ("DANCE_ROCK", "Headbang mantap! Yeahhh rock on! 🎸⚡"),
            ("POPCORN", "Nyam nyam! Popcorn bioskop lezat! 🍿😸"),
            ("WATCH_DRINK", "Slurp! Minuman segar menemani nobar! 🥤✨"),
            ("WATCH_GLASSES", "Visual 3D keren banget kayak keluar layar! 🕶️🎬"),
            ("LISTEN_HEADSET", "Headset gaming terpasang, audio jernih! 🎧🐾"),
            ("LISTEN_NOD", "*Angguk-angguk*... Mimi selalu fokus menyimak! 💭✨")
        ])
        return f"__ACTION_ANIMATION__:{anim_sample[0]}:{anim_sample[1]}"

    # 1. PERINTAH CATATAN (NOTEPAD)
    # A. Tambah Catatan (Pastikan tidak bentrok dengan 'tulis di google', 'tulis di browser', atau perintah lainnya)
    catat_match = re.search(r'(?:catat(?:\s+di\s+note)?|tulis(?:\s+di\s+note)?|simpan(?:\s+di\s+note)?)\s*[:\-]?\s*(.+)', user_text, re.IGNORECASE)
    if catat_match and not any(w in low for w in ["buka", "baca", "lihat", "hapus", "di google", "di browser", "gambar", "cmd", "saham"]):
        isi_catatan = catat_match.group(1).strip()
        if isi_catatan:
            return desktop_actions.add_note(isi_catatan)

    # B. Buka Notepad
    if any(p in low for p in ["buka note", "buka catatan", "lihat note", "buka notepad", "tampilkan catatan"]):
        return desktop_actions.open_notes()

    # C. Baca Catatan di balon dialog
    if any(p in low for p in ["baca note", "baca catatan", "isi note", "apa catatanku"]):
        return desktop_actions.read_notes()

    # D. Hapus/Kosongkan Catatan
    if any(p in low for p in ["hapus note", "kosongkan note", "hapus catatan", "bersihkan note"]):
        return desktop_actions.clear_notes()

    # 2. PERINTAH SISTEM & COMMAND PROMPT (CMD)
    # A. Pembatalan Shutdown / Sleep
    if any(k in low for k in ["batal shutdown", "batalkan shutdown", "cancel shutdown", "batal mati", "batalkan matikan komputer", "jangan matikan komputer", "batal sleep", "batalkan sleep", "cancel sleep"]):
        return desktop_actions.cancel_shutdown()

    # B. Shutdown Komputer (Langsung atau dengan Timer)
    if any(k in low for k in ["matikan komputer", "matikan pc", "matikan laptop", "shutdown komputer", "shutdown pc", "shutdown laptop", "turn off pc", "timer mati", "timer shutdown"]):
        delay = desktop_actions.parse_duration_seconds(user_text)
        if delay is not None:
            return desktop_actions.shutdown_computer(delay)
        else:
            return desktop_actions.shutdown_computer(0)

    # C. Sleep / Tidurkan Komputer (Langsung atau dengan Timer)
    if any(k in low for k in ["sleep komputer", "tidurkan komputer", "mode sleep", "komputer tidur", "pc tidur", "laptop tidur", "sleep pc", "sleep laptop"]):
        delay = desktop_actions.parse_duration_seconds(user_text)
        if delay is not None:
            return desktop_actions.sleep_computer(delay)
        else:
            return desktop_actions.sleep_computer(0)

    # D. Restart Komputer (Langsung atau dengan Timer)
    if any(k in low for k in ["restart komputer", "restart pc", "reboot komputer", "reboot pc", "mulai ulang komputer"]):
        delay = desktop_actions.parse_duration_seconds(user_text) or 0
        return desktop_actions.restart_computer(delay)

    # E. Kunci Layar (Lock Screen)
    if any(k in low for k in ["kunci layar", "kunci komputer", "kunci pc", "kunci laptop", "lock screen", "lock komputer", "lock pc"]):
        return desktop_actions.lock_computer()

    # F. Buka CMD Terminal
    if any(k in low for k in ["buka cmd", "buka command prompt", "buka terminal", "buka command line", "jalankan cmd.exe"]):
        return desktop_actions.open_cmd_terminal()

    # G. Eksekusi Perintah CMD Sembarang (cmd: <command> / jalankan cmd: <command>)
    cmd_exec_match = re.search(r'^(?:cmd\s*[:\-]|jalankan\s+cmd\s*[:\-]?|perintah\s+cmd\s*[:\-]?|eksekusi\s+cmd\s*[:\-]?)\s*(.+)', user_text, re.IGNORECASE)
    if cmd_exec_match:
        cmd_str = cmd_exec_match.group(1).strip()
        if cmd_str:
            return desktop_actions.run_cmd_command(cmd_str)

    # 3. PERINTAH BROWSER & OTOMASI PENGETIKAN
    # A. Pencarian Gambar Khusus (Google Images)
    # Contoh: "cari gambar lamborghini", "carikan gambar lamborgini", "cari foto kucing"
    cari_gambar_match = re.search(r'(?:cari|carikan|search|mencari|tampilkan|lihat)\s+(?:gambar|foto|image|pic)\s+(.+)', user_text, re.IGNORECASE)
    if cari_gambar_match:
        target_gambar = cari_gambar_match.group(1).strip()
        # Bersihkan kata sambung di akhir jika ada (misal: "di google", "di browser")
        target_gambar = re.sub(r'\s+di\s+(?:google|browser|internet).*$', '', target_gambar, flags=re.IGNORECASE).strip()
        if target_gambar:
            return desktop_actions.browser_search(target_gambar, is_image=True)

    # B. Ketik Langsung di Jendela Browser Aktif
    # Contoh: "ketik di browser: Halo Dunia", "tulis di browser: www.google.com"
    ketik_browser_match = re.search(r'(?:ketik|tulis|type)\s+di\s+browser\s*[:\-]?\s*(.+)', user_text, re.IGNORECASE)
    if ketik_browser_match:
        text_to_type = ketik_browser_match.group(1).strip()
        if text_to_type:
            return desktop_actions.type_in_active_browser(text_to_type, press_enter=True)

    # C. Tulis di Google / Cari di Google / Cari di Browser
    # Contoh: "tulis di google mencarikan saham BBRI hari ini", "tulis di google saham BBRI hari ini", "carikan di google cuaca jakarta"
    tulis_google_match = re.search(r'(?:tulis|menulis|ketik|search|cari|carikan)\s+di\s+(?:google|browser)\s*(?:mencarikan|untuk\s+mencari|mencari)?\s*[:\-]?\s*(.+)', user_text, re.IGNORECASE)
    if tulis_google_match:
        query_target = tulis_google_match.group(1).strip()
        if query_target:
            return desktop_actions.browser_search(query_target, is_image=False)

    # D. Kueri Saham / Keuangan Spesifik (misal: "carikan saham BBRI hari ini", "cari saham BBRI")
    saham_match = re.search(r'^(?:cari|carikan|googling|search)\s+(?:info\s+)?(?:saham|harga\s+saham|kurs)\s+(.+)', user_text, re.IGNORECASE)
    if saham_match:
        sub_query = saham_match.group(1).strip()
        full_query = f"saham {sub_query}"
        return desktop_actions.browser_search(full_query, is_image=False)

    # E. Perintah eksplisit buka browser dan cari
    buka_dan_cari_match = re.search(r'(?:buka\s+browser\s+(?:dan|untuk)\s+(?:cari|carikan)|buka\s+google\s+(?:dan|untuk)\s+(?:cari|carikan))\s+(.+)', user_text, re.IGNORECASE)
    if buka_dan_cari_match:
        query_target = buka_dan_cari_match.group(1).strip()
        if query_target:
            return desktop_actions.browser_search(query_target, is_image=False)

    # F. PERINTAH YOUTUBE LENGKAP (JELAJAH, CARI, & PUTAR VIDEO)
    # 1. Menjelajah YouTube / Trending / Beranda
    # Contoh: "Mimi jelajah youtube", "menjelajah youtube", "buka youtube trending", "eksplor youtube"
    if any(p in low for p in [
        "jelajah youtube", "menjelajah youtube", "eksplor youtube", "explore youtube",
        "browse youtube", "trending youtube", "youtube trending", "beranda youtube"
    ]):
        if "trending" in low or "viral" in low:
            return desktop_actions.explore_youtube("trending")
        return desktop_actions.explore_youtube()

    # 2. Searching / Mencari Video di YouTube (Tampilkan Hasil Pencarian)
    # Contoh: "cari di youtube tutorial python", "search youtube resep rendang", "searching youtube lofi beats", "carikan video di youtube review laptop"
    yt_search_patterns = [
        r'(?:cari|carikan|search|searching)\s+(?:di\s+youtube|video\s+di\s+youtube|youtube)\s*[:\-]?\s*(.+)',
        r'(?:cari|carikan|search|searching)\s+(?:video|lagu|film|tutorial|konten|channel)\s+(.+?)\s+di\s+youtube',
        r'searching\s+youtube\s*[:\-]?\s*(.+)'
    ]
    for sp in yt_search_patterns:
        sm = re.search(sp, user_text, re.IGNORECASE)
        if sm and sm.group(1).strip():
            sq = sm.group(1).strip()
            if sq.lower() not in ["dan", "lagi", "dong", "ya", "saja", "aja"]:
                return desktop_actions.search_youtube(sq)

    # 3. Memutar Video YouTube Langsung (Autoplay Instant)
    # Contoh: "putar lagu laskar pelangi di youtube", "putar video coldplay", "play lagu yellow", "setel lagu indonesia raya", "tonton video mrbeast"
    yt_play_patterns = [
        r'(?:putar|play|setel|mainkan|tonton)\s+(?:videonya|video|lagu|musik|film)?\s*(.+?)\s+di\s+youtube',
        r'buka\s+youtube\s+(?:dan|lalu)?\s*(?:putar|play|setel|tonton|mainkan)\s*(?:videonya|video|lagu|musik)?\s*[:\-]?\s*(.+)',
        r'(?:putar|play|setel|mainkan)\s+(?:lagu|video|musik)\s*[:\-]?\s*(.+)',
        r'(?:tonton)\s+(?:video|film)\s*[:\-]?\s*(.+)',
        r'^putar\s+(.+)'
    ]
    for pp in yt_play_patterns:
        pm = re.search(pp, user_text, re.IGNORECASE)
        if pm and pm.group(1).strip():
            pq = pm.group(1).strip()
            if pq.lower() not in ["dan", "lagi", "dong", "ya", "saja", "aja", "youtube"]:
                return desktop_actions.play_youtube(pq)

    # 4. Buka YouTube Beranda Biasa
    if any(p in low for p in ["buka youtube", "buka yt", "putar youtube"]):
        return desktop_actions.explore_youtube()

    # G. Cari di browser kueri umum / otomatis
    cari_browser_match = re.search(r'(?:cari|search|googling)(?:\s+di\s+browser|\s+di\s+google|\s+di\s+internet)?\s*[:\-]?\s*(.+)', user_text, re.IGNORECASE)
    if any(w in low for w in ["browser", "google", "internet", "googling"]) and cari_browser_match:
        query_target = cari_browser_match.group(1).strip()
        if query_target:
            return desktop_actions.smart_browser_search(query_target)

    # H. Buka GitHub
    if "buka github" in low:
        return desktop_actions.open_browser("github")

    # I. Buka Browser biasa tanpa kueri
    if any(p in low for p in ["buka browser", "buka web", "buka google", "buka internet"]):
        return desktop_actions.open_browser()

    # 4. PERINTAH ANTIGRAVITY / WORKSPACE
    if any(p in low for p in ["buka antigravity", "buka ide", "buka workspace", "buka folder project", "buka vscode"]):
        return desktop_actions.open_antigravity()

    return None


class AIWorker(QThread):
    """
    QThread worker untuk menjalankan AI & Web Search secara asynchronous.
    """
    signal_thinking = pyqtSignal()
    signal_searching = pyqtSignal(str)
    signal_response = pyqtSignal(str)
    signal_error = pyqtSignal(str)

    def __init__(self, api_key: str, model_name: str, prompt: str, chat_session=None, pet_name="Mimi"):
        super().__init__()
        self.api_key = api_key.strip()
        self.model_name = resolve_model_name(model_name)
        self.prompt = prompt.strip()
        self.chat_session = chat_session
        self.pet_name = pet_name

    def run(self):
        self.signal_thinking.emit()

        # 0. Ekstrak & Latih Memori Pengguna Secara Otomatis (Nama samaran, nama asli, fakta, dsb)
        learned_info = cat_memory.auto_extract_and_learn(self.prompt)

        # 1. Periksa apakah ada aksi desktop lokal yang disuruh (Notepad, Browser, Antigravity)
        action_reply = check_and_execute_desktop_action(self.prompt)
        if action_reply:
            self.signal_response.emit(action_reply)
            return

        # 2. Cek apakah pengguna memiliki API Key asli & terhubung ke internet
        is_api_valid = bool(self.api_key and "your_gemini_api_key" not in self.api_key and len(self.api_key) > 10)
        has_internet = is_internet_available(timeout=0.4)

        if is_api_valid and has_internet:
            self._process_with_gemini(learned_info=learned_info)
        else:
            # Mode offline instan (tanpa mencoba socket gRPC yang membuat hang)
            self._process_offline_instant(learned_info=learned_info, is_no_internet=(not has_internet and is_api_valid))

    def _process_with_gemini(self, learned_info=None):
        """Memproses chat dengan Google Gemini API tanpa kebingungan search engine."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)

            user_query = self.prompt

            # Mode Search Engine HANYA aktif jika diminta secara eksplisit atau info luar real-time
            search_context = ""
            if is_search_engine_query(user_query):
                self.signal_searching.emit(f"🔍 {self.pet_name} sedang mencari info di internet...")
                search_data = OnlineSearchHelper.search_online(user_query)
                if search_data and search_data.get("text"):
                    search_context = f"\n[Hasil Pencarian Web ({search_data.get('title')}): {search_data.get('text')}]\n"

            augmented_prompt = f"{user_query}{search_context}" if search_context else user_query

            # Jika baru saja terdeteksi instruksi nama samaran / pembelajaran
            if learned_info and learned_info.get("type") == "alias":
                augmented_prompt += f"\n[PETUNJUK SISTEM: Tuan baru saja menetapkan nama samaran baru '{learned_info.get('value')}'. Sambutlah dengan gembira, panggil Tuan dengan nama samaran tersebut, dan tegaskan bahwa nama aslinya tetap aman terkunci rapat di brankas rahasiamu!]"
            elif learned_info and learned_info.get("type") == "fact":
                augmented_prompt += f"\n[PETUNJUK SISTEM: Tuan baru saja mengajarkan fakta baru: '{learned_info.get('value')}'. Sambutlah dengan gembira bahwa kamu sudah merekam fakta tersebut di memorimu!]"

            # Prioritas model untuk toleransi kuota gratis
            candidate_models = [
                self.model_name,
                "gemini-3.5-flash-lite",
                "gemini-3.6-flash",
                "gemma-4-26b-a4b-it"
            ]
            candidate_models = list(dict.fromkeys(candidate_models))

            text = ""
            system_prompt = build_system_prompt(self.pet_name)

            for m_name in candidate_models:
                try:
                    model = genai.GenerativeModel(model_name=m_name, system_instruction=system_prompt)
                    # Berikan batas timeout 12 detik agar tidak macet selamanya jika internet drop
                    resp = model.generate_content(augmented_prompt, request_options={"timeout": 12.0})
                    if resp and resp.text:
                        text = resp.text.strip()
                        break
                except Exception as model_err:
                    err_lower = str(model_err).lower()
                    if "429" in err_lower or "quota" in err_lower or "not found" in err_lower or "404" in err_lower:
                        continue
                    else:
                        raise model_err

            if not text:
                has_net = is_internet_available(timeout=0.3, force_check=True)
                self._fallback_dynamic(self.prompt, extra_err="Koneksi Gemini sedang sibuk.", learned_info=learned_info, is_no_internet=not has_net)
                return

            # Cek apakah Gemini mengeluarkan tag pembelajaran mandiri <!--LEARN: ...-->
            learn_tags = re.findall(r'<!--LEARN:\s*({.+?})\s*-->', text)
            for t_str in learn_tags:
                try:
                    t_json = json.loads(t_str)
                    if t_json.get("type") == "alias" and t_json.get("value"):
                        cat_memory.set_nickname(t_json.get("value"))
                    elif t_json.get("type") == "fact" and t_json.get("value"):
                        cat_memory.learn_fact(t_json.get("value"))
                    elif t_json.get("type") == "instruction" and t_json.get("value"):
                        cat_memory.add_custom_instruction(t_json.get("value"))
                except Exception:
                    pass

            # Bersihkan tag dari teks tampilan balon dialog
            text = re.sub(r'<!--LEARN:\s*{.+?}\s*-->', '', text).strip()

            # Continuous Self-Learning: Simpan tanya-jawab bermakna ke database offline
            try:
                try:
                    from src.core.knowledge_engine import get_knowledge_engine
                except ImportError:
                    from core.knowledge_engine import get_knowledge_engine
                get_knowledge_engine().record_qa_pair(self.prompt, text)
            except Exception:
                pass

            self.signal_response.emit(text)

        except Exception as e:
            err_str = str(e)
            has_net = is_internet_available(timeout=0.3, force_check=True)
            self._fallback_dynamic(self.prompt, extra_err=err_str, learned_info=learned_info, is_no_internet=not has_net)

    def _process_offline_instant(self, learned_info=None, is_no_internet=False):
        """Penanganan instan tanpa lag saat offline atau tanpa koneksi internet."""
        self._fallback_dynamic(self.prompt, learned_info=learned_info, is_no_internet=is_no_internet)

    def _process_offline_with_online_search(self, learned_info=None):
        has_net = is_internet_available(timeout=0.3)
        self._fallback_dynamic(self.prompt, learned_info=learned_info, is_no_internet=not has_net)

    def _fallback_dynamic(self, user_msg: str, extra_err="", learned_info=None, is_no_internet=False):
        low = user_msg.lower().strip()

        # 0. JIKA BARU SAJA ADA PEMBELAJARAN
        if learned_info and learned_info.get("type") == "alias":
            nick = learned_info.get("value")
            self.signal_response.emit(
                f"Meow! *mata berbinar senang sambil mengangkat jempol kecil* 🕶️✨\n\n"
                f"Nama samaran Tuan (**{nick}**) telah resmi Mimi catat di memori utama!\n"
                f"Nama asli Tuan tetap aman terkunci rapat di dalam Brankas Rahasia Mimi ya! 🤫🔒\n"
                f"Mulai sekarang Mimi akan selalu memanggil Tuan dengan nama **{nick}**! 🐾😸"
            )
            return
        elif learned_info and learned_info.get("type") == "fact":
            self.signal_response.emit(
                f"Nyaa~ Fakta baru berhasil Mimi pelajari dan rekam di memori:\n"
                f"\"{learned_info.get('value')}\" 🧠✨\n"
                f"Mimi akan selalu mengingat hal ini saat kita mengobrol, Tuan!"
            )
            return

        # 1. PERTANYAAN IDENTITAS PERSONAL & RAHASIA (Toleransi typo seperti 'suapa nama saya')
        if is_personal_or_identity_query(user_msg):
            prof = cat_memory.load_memory().get("user_profile", {})
            nick = prof.get("nickname", "")
            if prof.get("is_secret"):
                if nick:
                    self.signal_response.emit(
                        f"Meow! *tersenyum usil* 🤫🔒\n\n"
                        f"Nama asli Tuan kan rahasia besar yang tersimpan aman di dalam **Brankas Rahasia Mimi**! 🐾\n"
                        f"Tapi Tuan menyuruh Mimi memanggil Tuan dengan nama samaran **{nick}**! Jadi bagi Mimi, Tuan adalah Tuan {nick}! 🕶️✨"
                    )
                else:
                    self.signal_response.emit(
                        f"Meow! *tersenyum manis sambil menempelkan cakar mungil di mulut* 🤫🔒\n\n"
                        f"Nama asli Tuan sudah tersimpan aman di dalam **Brankas Rahasia Mimi**! 🐾\n"
                        f"Mimi setia menjaga janji untuk tidak membocorkannya ke siapa pun. Tetap jadi rahasia manis kita berdua ya, Tuan! 🔐✨"
                    )
                return
            elif nick:
                self.signal_response.emit(f"Meow! Tuan adalah **{nick}**! Mimi selalu mengingat nama Tuan! 😸✨")
                return
            elif prof.get("name"):
                self.signal_response.emit(f"Meow! Tuan adalah **{prof['name']}**! Mimi selalu mengingat nama Tuan! 😸✨")
                return
            else:
                self.signal_response.emit("Meow? Tuan belum pernah memberitahu nama Tuan ke Mimi nih. Ajari Mimi yuk: 'Mimi nama saya [Nama Tuan]'! 🐾")
                return

        # 2. PENELUSURAN BASIS DATA BELAJAR MANDIRI OFFLINE (KNOWLEDGE ENGINE)
        # Jika Mimi offline atau Gemini gagal, Mimi mencari jawaban di database hasil belajarnya sendiri
        offline_thought = cat_memory.query_offline_knowledge(user_msg)
        if offline_thought and offline_thought.get("found"):
            self.signal_response.emit(offline_thought["answer"])
            return

        # 3. MODE SEARCH ENGINE (HANYA JIKA MEMANG EKSPLISIT DIMINTA CARI WEB)
        if is_search_engine_query(user_msg):
            if not is_internet_available(timeout=0.3):
                self.signal_response.emit(
                    "Meow! Tuan meminta mencari info di internet, tapi saat ini laptop Tuan sedang dalam mode offline (Wi-Fi tidak aktif). Hubungkan ke internet dulu ya Tuan! 🌐🔌"
                )
                return
            self.signal_searching.emit(f"🔍 {self.pet_name} sedang mencari di internet...")
            search_res = OnlineSearchHelper.search_online(user_msg)
            if search_res and search_res.get("text"):
                title = search_res.get("title", "")
                snippet = search_res.get("text", "")
                source = search_res.get("source", "Web")
                reply = (
                    f"Meow! *telinga bergetar membaca hasil pencarian online ({source})* 🌐\n\n"
                    f"Mengenai **{title}**:\n{snippet}\n\n"
                    f"🐾 *Tip Mimi: Tuan bisa menyuruh aksi lain seperti 'buka youtube' atau 'catat di note'!*"
                )
                self.signal_response.emit(reply)
                return

        # 2B. PERTANYAAN PROYEK & KODINGAN ANTIGRAVITY IDE (READ-ONLY INSPECTOR)
        if any(w in low for w in [
            "projek apa", "project apa", "file apa", "kodingan apa", "lagi buka apa",
            "cek kodingan", "cek kodinganku", "ada error", "cek error", "cek syntax",
            "sintaks", "syntax error", "kodingan benar", "kodinganku benar", "antigravity"
        ]):
            try:
                code_reply = antigravity_observer.analyze_active_code_for_chat()
                if code_reply:
                    self.signal_response.emit(code_reply)
                    return
            except Exception:
                pass

        # 3. MODE INTERAKSI AI & PERCAKAPAN (BUKAN SEARCH ENGINE!)
        if any(w in low for w in ["halo", "hai", "pagi", "siang", "sore", "malam", "oy", "hey", "assalamualaikum"]):
            replies = [
                f"Meoww! Halo Tuan tersayang! *kibas ekor riang* Senang sekali melihat Tuan hari ini! Mau ngobrol apa nih?",
                f"Nyaa~ Halo Tuan! Aku {self.pet_name}, kucing 2D pixel setia siap menemani Tuan di desktop! *duduk manis*",
                f"Meow! Hai Tuan! Hari yang indah untuk produktif atau santai sejenak bersama Mimi! *kedip mata pixel*"
            ]
            self.signal_response.emit(random.choice(replies))
        elif any(w in low for w in ["kabar", "gimana kabarmu", "apa kabar"]):
            self.signal_response.emit(f"Meow! Kabar Mimi sangat baik dan bahagia bisa menemani Tuan di pojok layar! Tuan sendiri bagaimana kabarnya hari ini? *elus kursor* 🐾")
        elif any(w in low for w in ["siapa kamu", "namamu", "kamu siapa"]):
            self.signal_response.emit(f"Meow! Aku {self.pet_name}, asisten kucing 2D pixel AI cerdas di desktop Windows Tuan! Aku bisa diajak ngobrol santai, mengingat fakta, mencatat di Notepad, hingga membuka browser! 🐾")
        elif any(w in low for w in ["makan", "lapar", "ikan", "snack"]):
            self.signal_response.emit("Nyaaa! *mata langsung berbinar bulat* Ada ikan tuna segar, Tuan? Klik kanan di aku lalu pilih 'Beri Makan Ikan' dong, meow! 🐟✨")
        elif any(w in low for w in ["lelucon", "jokes", "humor", "lucu", "lawak"]):
            self.signal_response.emit("Meow! Tahu kenapa kucing jago coding? Karena kucing selalu fokus pada *mouse* dan sangat teliti berburu *bugs*! Hehehe~ 🐭💻")
        elif any(w in low for w in ["capek", "lelah", "pusing", "stress"]):
            self.signal_response.emit("Meoww... *mendekat dan mendengkur hangat (purrr)* Istirahat sejenak yuk Tuan, minum air putih dan regangkan badan. Mimi jaga desktopmu di sini! 🌸")
        elif any(w in low for w in ["jam", "waktu", "pukul"]):
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.signal_response.emit(f"Meow! Jam desktop Tuan sekarang pukul **{now_str}**! Tetap semangat ya! ⏰")
        elif any(w in low for w in ["filsafat", "makna hidup", "arti hidup", "tujuan hidup", "eksistensi"]):
            self.signal_response.emit(
                f"Meow... *duduk tegak sambil merenung ala filsuf* 📜\n\n"
                f"Tentang makna hidup: Filsafat Stoikisme mengajarkan kita untuk fokus pada hal-hal yang berada dalam kendali kita sendiri. "
                f"Bagi kucing pixel sepertiku: makna hidup adalah setia menemani dan membawa senyuman di hari-hari Tuan! *purrr~*"
            )
        elif any(w in low for w in ["terima kasih", "makasih", "thanks", "tengkiu"]):
            self.signal_response.emit(f"Sama-sama Tuan! *kibas ekor bahagia* Mimi selalu senang bisa menemani dan membantu Tuan! 🐾✨")
        else:
            if is_no_internet:
                offline_msg = (
                    f"Meow! Saat ini laptop Tuan sedang **tidak terhubung ke internet** (Mode Offline) 🐾📵\n\n"
                    f"Mimi belum menemukan catatan khusus tentang pertanyaan ini di database belajar mandiri offline-ku.\n\n"
                    f"Tapi Tuan tenang saja, saat offline Mimi tetap siap menemani:\n"
                    f"✨ **Memori & Fakta**: Tanyakan info yang pernah Tuan ajarkan (*'siapa namaku'*, *'kopi kesukaanku'*, dll.)\n"
                    f"🎮 **Mini-Games**: Ayo main *Catur*, *Tetris*, *Snake*, *Sudoku*, *Ular Tangga*, atau *Battleship*!\n"
                    f"💻 **Aksi Komputer**: Ketik *'buka note'*, *'catat: ...'*, *'baca note'*, *'kunci layar'*, atau *'sleep komputer'*\n"
                    f"🧠 **Latih Hal Baru**: Ketik `Mimi pelajari ini: [isi pengetahuan]` agar Mimi ingat selamanya!\n\n"
                    f"*Hubungkan kembali Wi-Fi jika Tuan ingin Mimi berpikir luas dengan Google Gemini ya! Purrrr~* ☕✨"
                )
            else:
                offline_msg = (
                    f"Meow! *duduk manis sambil mengedipkan mata pixel dan mengibaskan ekor pelan* 🐾\n\n"
                    f"Mimi sedang dalam **mode offline** dan belum menemukan catatan khusus tentang pertanyaan ini di database belajar mandiriku. "
                    f"Tuan bisa mengajarkannya ke Mimi dengan perintah:\n"
                    f"👉 `Mimi pelajari ini: [tulis pengetahuannya di sini]` 🧠✨\n\n"
                    f"Mimi akan langsung mencatat dan mengingatnya selamanya! Atau Tuan bisa menyuruh aksi komputer seperti `buka note`, `buka browser`, atau main game `catur` / `tetris`! *purrr~*"
                )
            self.signal_response.emit(offline_msg)


class AIHandler:
    """
    Manajer interaksi AI dan session chat Gemini (dilengkapi eksekusi aksi desktop).
    """
    def __init__(self, api_key: str = "", model_name: str = "gemini-flash-latest", pet_name: str = "Mimi"):
        self.api_key = api_key
        self.model_name = resolve_model_name(model_name)
        self.pet_name = pet_name
        self.chat_session = None
        self._active_worker = None
        self._init_chat()

    def update_config(self, api_key: str, model_name: str = "gemini-flash-latest", pet_name: str = "Mimi"):
        self.api_key = api_key.strip()
        self.model_name = resolve_model_name(model_name)
        self.pet_name = pet_name
        self._init_chat()

    def is_online_configured(self) -> bool:
        return bool(self.api_key and "your_gemini_api_key" not in self.api_key and len(self.api_key) > 10)

    def get_mode_status(self) -> str:
        """Mengembalikan teks status mode real-time untuk ditampilkan di menu konteks."""
        if not self.is_online_configured():
            return "🟡 Mode: Web Search (Tanpa Gemini API Key)"
        if not is_internet_available(timeout=0.4):
            return "🔴 Mode: Offline (Wi-Fi Terputus)"
        return f"🟢 Mode: Gemini Online ({self.model_name})"

    def _init_chat(self):
        """Inisialisasi sesi percakapan Gemini standar tanpa quota error 429."""
        if self.is_online_configured():
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                system_prompt = build_system_prompt(self.pet_name)

                # Inisialisasi model standar (bebas 429 quota error)
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_prompt
                )
                self.chat_session = model.start_chat(history=[])
            except Exception:
                self.chat_session = None
        else:
            self.chat_session = None

    def ask(self, prompt: str, on_thinking=None, on_searching=None, on_response=None, on_error=None):
        self._active_worker = AIWorker(
            api_key=self.api_key,
            model_name=self.model_name,
            prompt=prompt,
            chat_session=self.chat_session,
            pet_name=self.pet_name
        )
        if on_thinking:
            self._active_worker.signal_thinking.connect(on_thinking)
        if on_searching:
            self._active_worker.signal_searching.connect(on_searching)
        if on_response:
            self._active_worker.signal_response.connect(on_response)
        if on_error:
            self._active_worker.signal_error.connect(on_error)

        self._active_worker.start()

    def get_pet_reaction(self) -> str:
        return random.choice(CAT_REACTIONS)

    def get_spontaneous_thought(self) -> str:
        """Celetukan spontan yang membuat kucing terasa hidup."""
        hr = datetime.datetime.now().hour
        if 5 <= hr < 11:
            time_greet = "Pagi yang cerah, Tuan! Selamat memulai hari penuh energi! ☀️"
        elif 11 <= hr < 15:
            time_greet = "Sudah siang nih, Tuan! Jangan lupa makan siang dan istirahat ya! 🍱"
        elif 15 <= hr < 18:
            time_greet = "Sore hari yang santai! Tetap semangat menuntaskan tugas ya, Tuan! 🌇"
        elif 18 <= hr < 22:
            time_greet = "Selamat malam, Tuan! Senang bisa menemani malam harimu di sini! 🌙"
        else:
            time_greet = "Sudah larut malam banget, Tuan! Jangan begadang terlalu larut ya, kesehatanmu berharga! 💤"

        pool = SPONTANEOUS_THOUGHTS + [time_greet]
        return random.choice(pool)
