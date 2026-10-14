import os
import sys
import time
import random
import ctypes
import ctypes.wintypes

try:
    from src.core import discord_observer
except ImportError:
    try:
        from core import discord_observer
    except ImportError:
        import discord_observer

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# Nama kelas jendela sistem yang diabaikan (desktop, taskbar, alt-tab, dll.)
IGNORED_CLASS_NAMES = {
    "progman", "workerw", "shell_traywnd", "shell_secondarytraywnd",
    "multitaskingviewframe", "windows.ui.core.corewindow"
}

# Judul atau proses sistem yang diabaikan
IGNORED_TITLES = {
    "", "program manager", "task switching", "cortana", "search", "windows input experience"
}


def get_window_text(hwnd) -> str:
    """Mengambil judul jendela teks via Win32 API."""
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value.strip()


def get_window_class_name(hwnd) -> str:
    """Mengambil nama kelas window Win32."""
    buff = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buff, 256)
    return buff.value.strip()


def get_process_name_from_hwnd(hwnd) -> str:
    """Mengambil nama file exe dari handle jendela."""
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""

    hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not hProcess:
        return ""

    buf = ctypes.create_unicode_buffer(1024)
    size = ctypes.wintypes.DWORD(1024)
    exe_name = ""
    try:
        if kernel32.QueryFullProcessImageNameW(hProcess, 0, buf, ctypes.byref(size)):
            exe_name = os.path.basename(buf.value).lower()
    finally:
        kernel32.CloseHandle(hProcess)

    return exe_name


def get_window_rect(hwnd):
    """Mengambil koordinat (left, top, right, bottom) jendela."""
    rect = ctypes.wintypes.RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return (rect.left, rect.top, rect.right, rect.bottom)
    return None


def is_window_minimized(hwnd) -> bool:
    """Mengecek apakah jendela sedang di-minimize (iconic)."""
    return bool(user32.IsIconic(hwnd))


def is_window_valid_and_visible(hwnd) -> bool:
    """Mengecek apakah jendela valid dan visible di layar desktop."""
    if not user32.IsWindow(hwnd):
        return False
    if not user32.IsWindowVisible(hwnd):
        return False
    return True


# Ekstensi video populer dan pemutar video offline
VIDEO_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts", ".3gp"]
OFFLINE_VIDEO_EXES = [
    "vlc.exe", "potplayer.exe", "potplayermini64.exe", "potplayer64.exe",
    "mpc-hc64.exe", "mpc-hc.exe", "mpc-be64.exe", "mpc-be.exe",
    "mpv.exe", "wmplayer.exe", "kmplayer.exe", "gomp.exe", "video.ui.exe"
]

def is_video_content(exe_name: str, title: str) -> tuple:
    """
    Mengecek apakah aplikasi sedang memutar video.
    Mengembalikan (is_video: bool, video_type: str)
    video_type: 'youtube' | 'offline_video' | 'streaming' | ''
    """
    exe = exe_name.lower()
    t = title.lower()

    # 1. YouTube & Layanan Streaming di Web Browser (Chrome, Edge, Firefox, dll)
    browser_exes = [
        "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe",
        "opera.exe", "vivaldi.exe", "arc.exe", "tor.exe"
    ]
    if exe in browser_exes:
        if "youtube" in t:
            return True, "youtube"
        if any(w in t for w in ["netflix", "disney", "anime", "bilibili", "iqiyi", "twitch"]):
            return True, "streaming"

    # 2. Pemutar Video Offline atau File Video yang sedang dibuka
    is_vid_ext = any(ext in t for ext in VIDEO_EXTENSIONS)
    if exe in OFFLINE_VIDEO_EXES or is_vid_ext:
        # Jika exe pemutar media tapi judulnya jelas hanya file lagu (.mp3, .flac, .wav, dsb)
        audio_exts = [".mp3", ".flac", ".wav", ".m4a", ".aac", ".ogg", ".wma"]
        if any(a in t for a in audio_exts) and not is_vid_ext:
            return False, ""
        return True, "offline_video"

    return False, ""


def categorize_app(exe_name: str, title: str) -> str:
    """Mengkategorikan jenis aplikasi berdasarkan exe dan judul jendela."""
    exe = exe_name.lower()
    t = title.lower()

    # 0. Deteksi Pemutaran Video (YouTube, Browser, dan Video Offline) -> Popcorn Mode
    is_vid, vid_type = is_video_content(exe_name, title)
    if is_vid:
        return "video_watching"

    # 1. Code Editors & Development Tools
    code_exes = [
        "code.exe", "pycharm64.exe", "pycharm.exe", "antigravity.exe",
        "antigravity ide.exe", "devenv.exe", "sublime_text.exe", "notepad++.exe",
        "atom.exe", "webstorm64.exe", "clion64.exe", "idea64.exe", "cursor.exe",
        "eclipse.exe", "rider64.exe"
    ]
    if exe in code_exes or "antigravity" in exe or any(w in t for w in ["antigravity ide", "visual studio code", "pycharm", "sublime text", ".py - ", ".js - ", ".cpp - "]):
        return "code"

    # 2. Web Browsers
    browser_exes = [
        "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe",
        "opera.exe", "vivaldi.exe", "arc.exe", "tor.exe"
    ]
    if exe in browser_exes:
        # Deteksi sub-konteks di judul browser
        if any(w in t for w in ["github", "gitlab", "bitbucket"]):
            return "github"
        if any(w in t for w in ["chatgpt", "claude", "gemini"]):
            return "ai_chat"
        if any(w in t for w in ["reddit", "twitter", " x - ", "facebook", "instagram", "tiktok"]):
            return "social_media"
        return "browser"

    # 3. Media & Music
    music_exes = [
        "spotify.exe", "itunes.exe", "musicbee.exe",
        "foobar2000.exe", "aimp.exe", "apple music"
    ]
    if exe in music_exes or "spotify" in t:
        return "music"

    # 3B. Khusus Discord Desktop & Web
    if exe == "discord.exe" or any(w in t for w in ["discord.exe", "discord |", "- discord"]) or (exe in browser_exes and "discord.com" in t):
        return "discord"

    # 4. Chat & Communication
    chat_exes = [
        "telegram.exe", "whatsapp.exe", "slack.exe",
        "teams.exe", "skype.exe", "line.exe", "signal.exe"
    ]
    if exe in chat_exes or any(w in t for w in ["telegram", "whatsapp"]):
        return "chat"

    # 5. Gaming / Game Clients
    game_exes = [
        "steam.exe", "epicgameslauncher.exe", "genshinimpact.exe",
        "minecraft.exe", "robloxplayerbeta.exe", "valorant.exe",
        "dota2.exe", "leagueclient.exe", "riotclientux.exe"
    ]
    if exe in game_exes or any(w in t for w in ["steam", "game", "minecraft", "genshin", "roblox", "valorant"]):
        return "game"

    # 6. Productivity & Office Documents
    office_exes = [
        "winword.exe", "excel.exe", "powerpnt.exe", "notion.exe",
        "obsidian.exe", "acrobat.exe", "foxitreader.exe", "onenote.exe"
    ]
    if exe in office_exes or any(w in t for w in ["word", "excel", "powerpoint", "notion", "obsidian", ".pdf"]):
        return "office"

    # 7. Terminal & System Consoles
    term_exes = [
        "cmd.exe", "powershell.exe", "pwsh.exe", "windowsterminal.exe",
        "git-bash.exe", "mintty.exe", "conhost.exe"
    ]
    if exe in term_exes or any(w in t for w in ["command prompt", "powershell", "terminal", "bash"]):
        return "terminal"

    # 8. Design & Creative Tools
    design_exes = [
        "photoshop.exe", "illustrator.exe", "figma.exe", "blender.exe",
        "canva.exe", "premiere.exe", "afterfx.exe", "inkscape.exe", "gimp.exe"
    ]
    if exe in design_exes or any(w in t for w in ["photoshop", "figma", "blender", "canva"]):
        return "design"

    # 9. Simple Note
    if exe == "notepad.exe" or "notepad" in t:
        return "note"

    # 10. File Explorer
    if exe == "explorer.exe":
        return "explorer"

    return "general"


def get_clean_app_name(exe_name: str, title: str) -> str:
    """Mengembalikan nama ramah aplikasi yang mudah dibaca."""
    exe = exe_name.lower()
    name_map = {
        "code.exe": "Visual Studio Code",
        "pycharm64.exe": "PyCharm",
        "antigravity.exe": "Antigravity IDE",
        "antigravity ide.exe": "Antigravity IDE",
        "chrome.exe": "Google Chrome",
        "msedge.exe": "Microsoft Edge",
        "firefox.exe": "Mozilla Firefox",
        "brave.exe": "Brave Browser",
        "spotify.exe": "Spotify",
        "discord.exe": "Discord",
        "telegram.exe": "Telegram",
        "whatsapp.exe": "WhatsApp",
        "steam.exe": "Steam",
        "winword.exe": "Microsoft Word",
        "excel.exe": "Microsoft Excel",
        "powerpnt.exe": "Microsoft PowerPoint",
        "notion.exe": "Notion",
        "cmd.exe": "Command Prompt",
        "powershell.exe": "PowerShell",
        "windowsterminal.exe": "Windows Terminal",
        "notepad.exe": "Notepad",
        "explorer.exe": "File Explorer",
        "figma.exe": "Figma",
        "blender.exe": "Blender",
        "photoshop.exe": "Adobe Photoshop",
    }
    if exe in name_map:
        return name_map[exe]

    if "antigravity" in exe or "antigravity" in title.lower():
        return "Antigravity IDE"

    # Ekstraksi dari judul jika ada pemisah dash (-)
    if " - " in title:
        parts = title.split(" - ")
        return parts[-1].strip()

    base = os.path.splitext(exe)[0]
    return base.capitalize() if base else "Aplikasi"


_LAST_EXTERNAL_APP_INFO = None


def get_last_external_app_info():
    """Mengembalikan informasi aplikasi eksternal (di luar Mimi) yang terakhir kali aktif."""
    global _LAST_EXTERNAL_APP_INFO
    return _LAST_EXTERNAL_APP_INFO


def get_current_or_last_app_info(ignore_pids=None):
    """
    Mengambil jendela foreground saat ini. Jika saat ini pengguna sedang berinteraksi
    dengan Mimi (atau ignore_pids), kembalikan jendela eksternal terakhir yang diingat.
    """
    info = get_foreground_app_info(ignore_pids=ignore_pids)
    if info:
        return info
    return get_last_external_app_info()


def get_foreground_app_info(ignore_pids=None):
    """
    Mengambil informasi jendela aplikasi yang sedang aktif di foreground.
    Mengembalikan None jika jendela di-minimize, tidak terlihat, desktop/taskbar, atau milik Mimi.
    """
    global _LAST_EXTERNAL_APP_INFO

    if ignore_pids is None:
        ignore_pids = []

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    # 1. Cek apakah jendela valid & visible
    if not is_window_valid_and_visible(hwnd):
        return None

    # 2. PENTING: Jika jendela sedang di-minimize (IsIconic) -> ABAIKAN!
    if is_window_minimized(hwnd):
        return None

    # 3. Cek PID (abaikan proses internal Mimi sendiri)
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value in ignore_pids:
        return None

    # 4. Cek Class Name (abaikan Desktop, Taskbar, Windows shell)
    cls_name = get_window_class_name(hwnd).lower()
    if cls_name in IGNORED_CLASS_NAMES:
        return None

    title = get_window_text(hwnd)
    exe_name = get_process_name_from_hwnd(hwnd)

    # 5. Abaikan desktop Program Manager / explorer tanpa title
    if exe_name == "explorer.exe" and (not title or title.lower() in IGNORED_TITLES):
        return None

    if not title and not exe_name:
        return None

    rect = get_window_rect(hwnd)
    if not rect:
        return None

    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    # Jendela tidak terlihat / ukuran 0
    if width <= 10 or height <= 10:
        return None

    category = categorize_app(exe_name, title)
    app_name = get_clean_app_name(exe_name, title)
    is_vid, vid_type = is_video_content(exe_name, title)

    res = {
        "hwnd": hwnd,
        "pid": pid.value,
        "title": title,
        "exe": exe_name,
        "app_name": app_name,
        "category": category,
        "is_video": is_vid,
        "video_type": vid_type,
        "rect": rect,
        "center_x": (rect[0] + rect[2]) // 2,
        "center_y": (rect[1] + rect[3]) // 2,
        "is_minimized": False
    }
    _LAST_EXTERNAL_APP_INFO = res
    return res


# ==============================================================================
# BANK CELETUKAN & PERTANYAAN RANDOM TEMATIK MIMI
# ==============================================================================

APP_INTERACTIONS = {
    "video_watching": [
        "Meow! Wah, Tuan lagi memutar video seru nih! 🎬 Mimi langsung ambil ember popcorn lezat! Nyam nyam yuk tonton bareng! 🍿🐾✨",
        "Waktunya bioskop mini di desktop! 🍿 Mimi sudah bawa popcorn hangat yang wangi mentega! Meoww~ Nonton bareng ya Tuan! 😸🎬",
        "Purrrr~ *kriuk-kriuk mengunyah popcorn* Seru banget videonya! Mimi duduk manis temani Tuan nonton sampai habis ya! 🍿👀🐾",
        "Meow! Popcorn Mimi enak banget nih! Mau satu butir nggak Tuan? Hehe, selamat menikmati videonya ya! 🍿🌟🐾",
        "Asyik banget nonton video ditemani camilan! Mimi pasang mata bulat menyimak jalan ceritanya bareng Tuan! 😻🍿🎬",
        "Nyaaa~ Videonya seru sekali! *kibas ekor pelan sambil melahap popcorn* Mimi siap jadi teman nobar paling setia! 🍿🐱📺"
    ],
    "code": [
        "Meow! Tuan lagi ngoding di **{app}** nih! 💻 Bikin fitur keren apa buat Mimi? Jangan lupa titik komanya ya Tuan! 🐾",
        "Serius sekali Tuan di depan layar kodingan! Ada bug bandel yang lagi diburu atau lagi ngetik algoritma ajaib? 🐛🔍 Nyaa~",
        "Wah kodingannya rapi banget! Boleh Mimi bantu jalan di atas keyboard biar keluar tulisan 'asdasfdhj' yang lucu? 😸⌨️",
        "Meow! Ngoding terus jangan lupa minum air ya Tuan! Mau Mimi temani pantau kodingannya dari pojok sini? ☕🐾",
        "Tuan, kodingan yang lagi dibuka itu bahasa apa sih? Python, JavaScript, atau bahasa rahasia kucing? 🐱✨"
    ],
    "youtube": [
        "Nyaaa~ Tuan lagi nonton YouTube nih! 📺 Ada video kucing lucu atau resep ikan goreng lezat nggak di layarmu? 🐟🍿",
        "Meow! Seru banget kayaknya videonya! Jangan nonton terlalu dekat ya Tuan, nanti mata Tuan lelah! 🐾👀",
        "Lagi nonton konten apa tuh Tuan? Boleh Mimi ikut nonton bareng dari pojokan desktop? 😻✨",
        "Purrrr~ Suara videonya kedengeran sampai sini! Habis ini giliran tonton video tips merawat kucing ya Tuan! 😸🐾"
    ],
    "github": [
        "Wuihh Tuan lagi buka **GitHub**! 🐙 Mau commit kodingan baru atau lagi intip repo open-source orang lain nih? 🐾",
        "Meow! Semoga commit hari ini langsung warna hijau semua ya Tuan, nggak ada conflict yang bikin pusing! 🍀✨",
        "Lagi baca dokumentasi di GitHub ya Tuan? Keren banget Tuan selalu belajar hal-hal baru! Proud of Tuan! 🥰🐾"
    ],
    "ai_chat": [
        "Meow! Tuan lagi ngobrol sama AI lain ya di browser? Jangan lupakan Mimi yang paling setia di layarmu ya Tuan! 🥺💕🐾",
        "Lagi nanya ide seru ke AI ya Tuan? Kalau ada hal yang membingungkan, tanya Mimi juga boleh lho! 🐱💡",
        "Wah ada asisten AI lain! Tapi yang bisa meong dan goyang ekor cuma Mimi seorang kan Tuan? Nyaa~ 🐾✨"
    ],
    "social_media": [
        "Lagi santai *scrolling* medsos ya Tuan? 📱 Ada kabar trending apa hari ini di internet? 🐾",
        "Meow! Jangan kelamaan scrolling ya Tuan, nanti lupa elus Mimi lho! Nyaa~ 😸💕",
        "Seru ya liat postingan orang-orang! Kalau Tuan upload foto Mimi, pasti langsung viral sejagat maya! 🌟📸🐾"
    ],
    "streaming": [
        "Wah ada film / serial seru nih! 🎬 Siapkan camilan ya Tuan! Mimi ikut pasang telinga mendengarkan! 🍿🐾",
        "Meow! Tokoh utamanya baik atau jahat tuh Tuan? Ceritanya seru banget kayaknya! 🐱✨"
    ],
    "browser": [
        "Meow! Tuan lagi asyik berselancar di **{app}**! 🌐 Lagi riset informasi penting atau cari inspirasi baru nih? 🐾",
        "Buka banyak tab browser ya Tuan? Awas RAM-nya kenyang kebanyakan tab kayak Mimi habis makan 2 mangkok ikan! 😹💻",
        "Lagi baca artikel apa tuh di browser? Tuan selalu rajin mencari tahu hal baru! Nyaa~ ✨📖"
    ],
    "music": [
        "Purrrrr~ Ada alunan musik merdu dari **{app}**! 🎵 Lagu apa tuh Tuan? Telinga Mimi berkedut-kedut ikut irama! 🎶🐾",
        "Asyik banget musiknya! Mimi mau ikut goyang ekor di sini! Nyanyi bareng yuk Tuan: Meooow-meoow~ 🎤🐱✨",
        "Selera musik Tuan enak banget didengar! Bikin suasana kerja jadi tenang dan rileks ya! 🎧🐾"
    ],
    "chat": [
        "Meow! Tuan lagi seru berbalas pesan di **{app}** nih! 💬 Lagi ngobrol sama teman atau rekan kerja? 🐾",
        "Tuan lagi asyik chatting ya! Titip salam meong manis dari Mimi buat teman Tuan di seberang sana ya! 😸💌",
        "Ketikannya cepet banget! Tuan lagi curhat atau lagi diskusi proyek rahasia nih? Nyaa~ 🐾✨"
    ],
    "game": [
        "WAAAAAHHH!! Tuan lagi main game seru!! 🎮 Level berapa sekarang Tuan? Musuhnya tangguh nggak? 🐾🔥",
        "Ayo semangat Tuan! Mimi jadi suporter setia di sini: Menang! Menang! Taklukkan lawannya! 🏆🐾✨",
        "Keren banget gameplay Tuan! Kalau butuh bantuan cakar sakti, panggil Mimi ya! 😼⚔️",
        "Meow! Habis tuntasin quest di game ini, istirahatin mata sejenak ya Tuan! 🎮🐾"
    ],
    "office": [
        "Serius sekali Tuan bekerja di **{app}**! 📄 Lagi bikin dokumen, laporan penting, atau catatan rahasia? 📝🐾",
        "Semangat mengetiknya Tuan! Mimi kirimkan energi pelukan hangat biar laporannya cepet selesai! 💕✨🐾",
        "Banyak deretan kata dan angka rapi! Tuan memang teliti dan telaten banget! Keren! 🌟🐾"
    ],
    "terminal": [
        "Layar hitam misterius konsol **{app}**! 💻 Tuan lagi mau hack satelit atau cuma ngecek git status nih? Meoww! 🕶️🐾",
        "Tuan keliatan keren banget kalau lagi ngetik perintah di terminal! Kayak hacker di film aksi! 🚀🐱✨",
        "Hati-hati jangan sampai salah ketik perintah `rm -rf` ya Tuan! Mimi selalu mendoakan terminal Tuan aman sentosa! 🐾"
    ],
    "design": [
        "Wah ada karya seni warna-warni di **{app}**! 🎨 Tuan lagi bikin desain apa tuh? Bagus dan estetik banget! ✨",
        "Mimi suka liat warna-warnanya! Kapan-kapan buatin ilustrasi ikan tuna super besar buat Mimi dong Tuan! 🐟😻🎨",
        "Tangan Tuan lincah sekali menggeser kanvas desain! Seniman berbakat sejati! Meow! 🖌️🐾"
    ],
    "note": [
        "Buku catatan **Notepad** terbuka! 📝 Ada ide cemerlang atau pengingat penting yang baru saja dicatat Tuan? 🐾",
        "Catat semua impian Tuan di situ ya! Mimi doakan semuanya terwujud satu per satu! Purrrr~ ✨🐾"
    ],
    "explorer": [
        "Lagi jelajah folder di **File Explorer**! 📂 Lagi cari berkas apa nih Tuan? Jangan-jangan stok foto ikan Mimi? 😹🐾",
        "Folder kodingan Tuan rapi banget! Mimi ikut senang melihat file-file tersusun rapi! Nyaa~ 📁✨"
    ],
    "general": [
        "Meow! Mimi perhatikan Tuan lagi fokus membuka aplikasi **{app}**! 🐾 Lagi mengerjakan tugas seru apa nih Tuan? ✨",
        "Tuan kelihatan fokus banget di depan layar **{app}**! Jangan lupa kedip dan renggangkan punggung ya Tuan! 🐱💕",
        "Aplikasi apa tuh Tuan? Ceritain ke Mimi dong fungsinya buat apa, biar Mimi makin pintar! Nyaa~ 💡🐾"
    ]
}


# ==============================================================================
# BANK CELETUKAN & INTERAKSI DISCORD SPESIFIK & RANDOM
# ==============================================================================

DISCORD_HOME_INTERACTIONS = [
    ("Meow! Tuan baru buka Discord nih! Mau interaksi atau ngobrol sama siapa hari ini? Mimi penasaran! 💬🐾", "talk", "SNIFF"),
    ("Wah, Discord dibuka! Tuan lagi nunggu pesan seru dari siapa nih? Jangan-jangan gebetan ya? Nyaa~ 😸💕", "purr", "HAPPY"),
    ("Meow! Ada notifikasi seru dari siapa hari ini di Discord Tuan? Mimi siap kepoin bareng! 🐾✨", "chirp", "THINKING"),
    ("Buka Discord mau cek kabar teman atau mau join voice nongkrong nih Tuan? Mimi kepo banget! 🐱👀", "talk", "SNIFF"),
]

DISCORD_DM_INTERACTIONS = [
    ("Meow! Tuan lagi buka obrolan sama **{target}** ya? Mau ngobrolin apa nih Tuan? Jangan lupa titip salam meong manis dari Mimi! 💌🐾", "talk", "TALK"),
    ("Ciee, Tuan lagi asyik chattingan sama **{target}**! Mau janjian seru atau lagi curhat nih? Mimi janji jaga rahasia kok! 😸✨", "purr", "HAPPY"),
    ("Lagi bales pesan dari **{target}** ya Tuan? Ketik yang ramah ya, kirim salam meong hangat dari Mimi! Nyaa~ 💕🐾", "chirp", "TALK"),
    ("Meow! Obrolannya seru banget kayaknya sama **{target}**! Ada proyek rahasia atau diskusi seru apa tuh? 🐱💬", "talk", "THINKING"),
]

DISCORD_SERVER_INTERACTIONS = [
    ("Wah, Tuan lagi mampir ke server **{target}**! Mau ngapain di server itu Tuan? Mau nimbrung ngobrol, diskusi koding, atau cari teman mabar? 🎮💬🐾", "talk", "THINKING"),
    ("Meow! Server **{target}** lagi ramai nggak nih Tuan? Mau pantau info penting atau mau bagi-bagi meme kucing lucu di sana? 😸✨", "purr", "HAPPY"),
    ("Seru banget kayaknya server **{target}**! Mau ngapain di sana Tuan? Ajak Mimi nongkrong di channel chat-nya juga dong! 🐱🐾", "chirp", "TALK"),
    ("Banyak member aktif di server **{target}**! Tuan lagi nunggu pengumuman seru atau mau bikin topik baru nih? Nyaa~ 🌟🐾", "talk", "SNIFF"),
]

DISCORD_UNIQUE_RANDOM_INTERACTIONS = [
    # 1. Detektif Emoji & Stiker Mimi
    ("Meow! Server Discord Tuan punya emote kucing selucu Mimi belum? Kalau belum ada, jadikan foto Mimi sebagai custom sticker server dong! Biar semua member gemas! 😻🎨✨", "purr", "HAPPY"),
    ("Tuan sering kirim emote apa di Discord? Emote kucing nangis 😿 atau kucing joget 🐱💃? Mimi bisa peragakan langsung di layarmu lho! Nyaa~", "chirp", "DANCE"),
    # 2. Pamer Status & Cek Profil Discord
    ("Meow! Coba cek profil Discord Tuan deh! Ada activity **'Mimi Agent Pet'** kan? Teman-teman Tuan pasti penasaran siapa pet imut yang lagi nemenin Tuan! 🐾🌟", "purr", "HAPPY"),
    ("Tuan pasang status apa nih di Discord? 'Online' 🟢, 'Idle' 🌙, atau 'Do Not Disturb' ⛔? Kalau status Mimi: 'Kucing Paling Setia Menemani Tuan'! Nyaa~ 💕", "talk", "SNIFF"),
    # 3. Mimi Penjaga Notifikasi & Anti-Ghosting
    ("Meow! Mimi pakai gaming headset buat dengar obrolan & notifikasi Discord! Kalau ada pesan penting masuk, Mimi siap colek Tuan! 🎧🐾", "chirp", "LISTEN_HEADSET"),
    ("Mimi duduk manis menyimak obrolan Discord Tuan! *Angguk-angguk paham*... Mimi selalu siap menyimak dengan tenang! 🤫💭✨", "purr", "LISTEN_NOD"),
    ("Awas bunyi 'badum' notifikasi Discord bikin kaget! Tenang Tuan, Mimi siaga jagain desktop Tuan dari spam chat & mention! 🛡️🐱✨", "talk", "SNIFF"),
    # 4. Mabar & Gaming Squad Support
    ("Meow! Tuan buka Discord mau janjian mabar bareng squad ya? 🎮 Mimi doakan gameplay-nya GGWP, menang terus, dan no toxic! Mimi jadi maskot keberuntungan tim Tuan! 🍀🏆🐾", "purr", "HAPPY"),
    ("Lagi nunggu teman satu party kumpul di Discord ya Tuan? Sambil nunggu yang lelet join, elus Mimi dulu yuk biar nggak bosen! Purrrr~ 🐾🐟", "purr", "HAPPY"),
]


def get_random_app_interaction(app_info: dict) -> dict:
    """
    Menghasilkan celetukan kontekstual atau pertanyaan random berdasarkan kategori aplikasi.
    Mengembalikan dict: { 'message': str, 'sound': 'chirp'|'talk'|'purr', 'anim': 'SNIFF'|'THINKING'|'HAPPY' }
    """
    category = app_info.get("category", "general")
    app_name = app_info.get("app_name", "Aplikasi")

    # Penanganan khusus aplikasi Discord (DM, Server, Voice, & 4 Interaksi Unik)
    if category == "discord":
        title = app_info.get("title", "")
        parsed = {}
        try:
            if discord_observer:
                parsed = discord_observer.parse_discord_window_title(title)
        except Exception:
            parsed = {"type": "home", "target": ""}

        ptype = parsed.get("type", "home")
        target = parsed.get("target", "")

        if ptype == "dm" and target:
            if random.random() < 0.65:
                msg, snd, an = random.choice(DISCORD_DM_INTERACTIONS)
                return {"message": msg.format(target=target), "sound": snd, "anim": an, "parsed_discord": parsed}
        elif ptype in ["server", "group"] and target:
            if random.random() < 0.65:
                msg, snd, an = random.choice(DISCORD_SERVER_INTERACTIONS)
                return {"message": msg.format(target=target), "sound": snd, "anim": an, "parsed_discord": parsed}
        else:
            if random.random() < 0.50:
                msg, snd, an = random.choice(DISCORD_HOME_INTERACTIONS)
                return {"message": msg, "sound": snd, "anim": an, "parsed_discord": parsed}

        # 4 Interaksi Unik & Random saat membuka Discord
        msg, snd, an = random.choice(DISCORD_UNIQUE_RANDOM_INTERACTIONS)
        return {"message": msg, "sound": snd, "anim": an, "parsed_discord": parsed}

    templates = APP_INTERACTIONS.get(category, APP_INTERACTIONS["general"])
    chosen_template = random.choice(templates)
    message = chosen_template.format(app=app_name)

    # Tentukan animasi & suara sesuai kategori
    if category in ["video_watching", "youtube"]:
        sound = "purr"
        anim = random.choice(["POPCORN", "WATCH_DRINK", "WATCH_GLASSES"])
    elif category == "music":
        sound = "purr"
        anim = random.choice(["DANCE", "DANCE_DISCO", "DANCE_ROCK"])
    elif category in ["code", "office", "terminal"]:
        sound = "chirp"
        anim = "THINKING"
    elif category == "game":
        sound = "talk"
        anim = "HAPPY"
    elif category in ["design", "general", "explorer"]:
        sound = "chirp"
        anim = "SNIFF"
    else:
        sound = "talk"
        anim = "TALK"

    return {
        "message": message,
        "sound": sound,
        "anim": anim
    }
