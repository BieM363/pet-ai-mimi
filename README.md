# 🐱 Virtual Pixel Cat AI Companion (Desktop Pet)

[![Author](https://img.shields.io/badge/Author-BieM363-orange?style=flat&logo=github)](https://github.com/BieM363)
[![Repository](https://img.shields.io/badge/GitHub-pet--ai--mimi-blue?style=flat&logo=github)](https://github.com/BieM363/pet-ai-mimi)

> **Created & Developed with ❤️ by [BieM363](https://github.com/BieM363)**

Aplikasi Desktop Virtual AI Companion bertema **Kucing 2D Pixel Art** imut dan cerdas (*desktop pet*) yang melayang (*floating*) di atas layar Windows 10/11. Dibuat dengan **Python**, **PyQt5**, **Google Gemini AI**, **Cat Audio Engine (Suara Meong Asli)**, **Sistem Memori & Training Data AI**, dan **Integrasi Aksi Desktop Windows**.

Aplikasi ini berjalan otomatis tanpa jendela konsol hitam (*silent mode*), memiliki efek suara meong kucing imut asli (bukan suara robot TTS), serta mampu mempelajari fakta dan mengingat preferensi Anda secara permanen!

---

## ✨ Fitur Unggulan:

1. **🧠 Sistem Pelatihan Data & Memori AI (Long-Term Learning):**
   - **Bisa Diajari Hal Baru**: Anda dapat melatih Mimi secara langsung lewat chat (misal: *"Mimi pelajari ini: nama saya Kevin"*, *"Mimi ingat bahwa saya suka minum kopi hitam"*).
   - **Pusat Memori GUI**: Klik kanan pada Mimi -> **"🧠 Latih Data & Memori AI"** untuk melihat daftar pengetahuan yang sudah dipelajari, menambah data training, atau menghapus ingatan tertentu.
   - **Mengingat Selamanya**: Semua fakta yang diajarkan tersimpan di `cat_memory.json` dan otomatis disuntikkan ke otak Gemini AI dalam setiap percakapan.

2. **🐾 Suara Kucing Alami (Bukan Suara Robotik TTS):**
   - Suara robotik pembaca teks telah digantikan 100% dengan **efek suara kucing alami** (`cat_audio.py`):
     - `meow_talk.wav`: Meong manis saat menjawab pertanyaan di balon dialog.
     - `meow_happy.wav`: Meong riang gembira saat dielus atau diberi makan ikan.
     - `meow_chirp.wav`: Meong pendek ceria saat mendarat atau bangun tidur.
     - `meow_picked.wav`: Meong kaget imut saat diangkat dengan kursor.
     - `meow_purr.wav`: Suara mendengkur hangat (*purrr*) saat santai.
   - Fitur Mute/Unmute suara meong tersedia di menu klik kanan.

3. **🐱 Karakter Kucing 2D Pixel Art Sedang (128x128 px):**
   - Ukuran sedang yang proporsional di layar desktop monitor.
   - Animasi retro pixel art tajam berformat GIF transparan:
     - `cat_idle.gif`: Duduk santai, nafas lembut, ekor melambai, berkedip.
     - `cat_walk_left.gif` & `cat_walk_right.gif`: Berjalan-jalan santai (*Autonomous Wanderer*).
     - `cat_picked.gif`: **Pose tergantung pasrah di udara** saat diangkat kursor dengan kaki bergoyang.
     - `cat_landing.gif`: **Mendarat di lantai dengan pantulan halus (*landing bounce*)** setelah dilepaskan di udara.
     - `cat_stretch.gif`: Meregangkan kaki depan dan menguap santai.
     - `cat_talk.gif`: Mulut bergerak mengeong imut.
     - `cat_think.gif`: Berpikir dengan tanda tanya pixel.
     - `cat_sleep.gif`: Tidur menggulung damai dengan partikel Zzz.
     - `cat_happy.gif`: Melompat riang dengan partikel hati saat dielus/diberi makan.
     - `cat_sniff.gif`: Mengendus layar desktop.

4. **💻 Integrasi Kontrol Sistem CMD & Otomasi Browser:**
   - **Kontrol Sistem & Command Prompt (CMD):**
     - **Timer Shutdown**: *"matikan komputer 30 menit lagi"*, *"buat timer mati 10 menit"*, *"shutdown 1 jam lagi"*.
     - **Matikan Langsung**: *"matikan komputer"* / *"shutdown sekarang"*.
     - **Batalkan Shutdown**: *"batalkan shutdown"* / *"cancel shutdown"* / *"batal mati"*.
     - **Sleep / Tidurkan PC**: *"sleep komputer"*, *"tidurkan komputer"*, atau *"sleep komputer 15 menit lagi"*.
     - **Restart Komputer**: *"restart komputer"*, *"reboot pc"*.
     - **Kunci Layar**: *"kunci layar"*, *"lock komputer"*.
     - **Buka Terminal CMD**: *"buka cmd"*, *"buka command prompt"*.
     - **Jalankan Perintah CMD**: *"cmd: ipconfig"*, *"cmd: ping google.com -n 2"*, *"cmd: tasklist"* (output akan ditampilkan di balon dialog Mimi!).
   - **Otomasi Browser (Ketik & Navigasi Cerdas):**
     - **Pencarian Google / Saham**: *"carikan saham BBRI hari ini"*, *"tulis di google saham BBRI hari ini"*, *"cari cuaca hari ini di google"*.
     - **Pencarian Gambar (Google Images)**: *"cari gambar lamborghini"*, *"carikan gambar lamborgini"*, *"cari foto kucing lucu"*.
     - **Pencarian & Pemutaran Video YouTube**: *"Buka Youtube dan buka videonya Mr Beast terbaru"*, *"putar lagu laskar pelangi di youtube"*, *"cari di youtube tutorial python"* (Mimi otomatis mencari video dan langsung memutar videonya di browser!).
     - **Ketik Langsung di Browser Aktif**: *"ketik di browser: Halo Dunia"* (Mimi akan memfokuskan browser yang sedang terbuka dan mengetikkan teks tersebut).
     - **Shortcut Cepat Web**: *"buka browser"*, *"buka youtube"*, *"buka github"*.
   - **👁️ Penglihatan & Interaksi Aplikasi Aktif (Spatial & Window Awareness):**
     - **Melihat ke Arah Aplikasi (Bebas 'Jalan di Tempat')**: Mimi memiliki kepekaan spasial di layar Windows! Saat Anda membuka jendela aplikasi di sebelah kiri atau kanan layar, tubuh dan tatapan Mimi otomatis menoleh santai ke arah jendela tersebut (`LOOK_LEFT` / `LOOK_RIGHT` / `SNIFF`) **tanpa menggerakkan kaki di tempat**. Kaki Mimi tetap kokoh dan tenang!
     - **Berinteraksi & Bertanya Hal Random**: Mimi mengenali ratusan jenis aplikasi yang Anda buka (VS Code, Browser, YouTube, GitHub, Spotify, Discord, Game, Word/Excel, CMD, Figma, dll.) dan akan melontarkan celetukan atau pertanyaan random penasaran yang relevan dengan aktivitas Anda!
     - **Proteksi Minimize & Close**: Jika aplikasi Anda **minimize** atau **tutup**, atau Anda sedang berada di desktop, Mimi **seketika berhenti berinteraksi** dan tetap tenang agar tidak mengganggu Anda.
     - **Kontrol On / Off**: Dapat diaktifkan atau dinonaktifkan kapan saja lewat klik kanan -> **👁️ Pantau Aplikasi Aktif: [ON/OFF]** atau lewat chat (*"Mimi pantau aplikasi"*).
   - **💬 Integrasi Lengkap Discord & Rich Presence (Activity Profile):**
     - **Activity Profil Discord (Discord RPC)**: Menampilkan status live **"Playing Mimi Agent Pet"** di profil Discord Anda lengkap dengan durasi waktu, status santai, chatting, maupun gaming!
     - **Deteksi Interaksi Discord Cerdas**:
       - **Buka Discord**: Mimi penasaran mau ngobrol atau interaksi dengan siapa hari ini.
       - **Buka DM Teman**: Mendeteksi nama teman di obrolan pribadi, bertanya topik seru yang dibicarakan, dan menitipkan salam meong manis.
       - **Buka Server / Grup**: Bertanya rencana aktivitas Tuan di server tersebut (nimbrung ngobrol, share kodingan, atau cari teman mabar).
     - **🎧 Mode Duduk Diam Menyimak di Voice Channel**:
       - Saat Anda masuk ke Voice Channel Discord, Mimi otomatis beralih ke pose duduk manis menyimak (`cat_listen.gif`).
       - Menghentikan jalan-jalan mandiri dan tidak bersuara berisik agar tidak mengganggu percakapan Anda dengan teman.
       - Menyapa riang begitu sesi voice selesai!
     - **🎲 4 Interaksi Unik & Random Tambahan**:
       1. *Detektif Emoji & Stiker Mimi*: Menawarkan diri jadi custom sticker server Discord.
       2. *Pamer Status & Cek Profil*: Membahas activity Mimi di Discord dan status DND/Idle.
       3. *Mimi Penjaga Notifikasi & Anti-Ghosting*: Siaga menjaga dari bunyi *ping* dan mention.
       4. *Mabar & Gaming Squad Support*: Menjadi maskot keberuntungan squad game Tuan!
   - **🖱️ Interaksi Kursor Mouse yang Hidup & Responsif:**
     - **Elus Kursor (Cursor Petting Detection)**: Usapkan kursor bolak-balik di atas tubuh Mimi. Mimi akan merasakan sentuhan hangat kursor Anda, memicu suara mendengkur manja (*purrrr~*), masuk ke animasi gembira (`HAPPY`), dan mengeluarkan celetukan sayang.
     - **Hover & Sniffing**: Kursor mendekati tubuh Mimi akan membuatnya mengendus kursor (`SNIFF`) atau terbangun ceria jika sedang tidur.
     - **Mode Kejar Kursor (*Cursor Chase Mode*)**: Mimi akan berjalan ke kiri dan ke kanan di layar mengejar ke mana pun kursor mouse Anda bergerak! Aktifkan/matikan lewat menu klik kanan atau cukup katakan: *"Mimi kejar kursor"* / *"ikuti mouse"*.
   - **🎮 6 Mini Games Seru bersama Mimi (Anti-Tertimpa & Companion Mode):**
     - **Anti-Tertimpa (Smart Companion Mode)**: Saat bermain, Mimi otomatis duduk di samping jendela game di layar terdepan (`WindowStaysOnTopHint`), tidak tertimpa oleh permainan, dan menunda jalan-jalan mandiri agar setia menonton serta bersorak menyemangati Anda!
     - Akses instan lewat tombol **[🎮 Game ▾]** di baris atas balon obrolan, menu klik kanan, system tray, atau perintah chat langsung!
     - ♟️ **Bermain Catur (Chess)**: Lawan AI Mimi dalam 3 pilihan kesulitan (Mudah, Normal, Sulit dengan Minimax + Alpha-Beta Pruning).
     - 🧱 **Bermain Tetris (Balok Retro)**: 7 bentuk Tetromino klasik, ghost piece, wall kick, soft/hard drop, dan level yang dinamis.
     - 🐍 **Bermain Snake (Tangkap Ikan Kolam)**: Kendalikan ular kucing menangkap ikan lezat 🐟, udang 🍤, dan susu 🥛 dengan kontrol WASD/Panah.
     - 🧩 **Bermain Sudoku (Teka-Teki Angka)**: Papan 9x9 retro, 3 tingkat kesulitan, sorotan sel & angka kembar, mode pensil/catatan, validasi, dan tombol bantuan Mimi (*Hint*).
     - 🎲 **Bermain Ular Tangga (Snakes & Ladders)**: 100 petak klasik Pemain vs Kucing Mimi AI, animasi lemparan dadu 3D, langkah pion bertahap, tangga bambu, ular meliuk, dan giliran otomatis Mimi!
     - 🚢 **Bermain Battleship (Perang Armada Laut)**: Formasi 5 kapal laut (Kapal Induk, Tempur, Penjelajah, Selam, Patroli), radar serang, ledakan torpedo 💥, dan AI berburu Mimi (*Hunt-and-Target*).
   - **📝 Catatan / Notepad & Akses Cepat:**
     - Tombol cepat **📝 Note** langsung di header balon dialog Mimi.
     - Format teks balon dialog bersih dengan **Markdown & HTML styling** (tanpa tanda baca atau bintang aneh).
     - Klik tautan teks `buka note` di balon dialog langsung membuka Notepad Windows.
     - Perintah teks: *"Mimi catat: beli kopi"*, *"Mimi buka note"*, *"Mimi baca note"*, *"kosongkan note"*.
   - **Antigravity / Workspace**:
     - *"Mimi buka antigravity"* -> membuka workspace di Antigravity / File Explorer.

5. **🌀 Animasi & Interaksi Exit Portal Dimensi Kosmik:**
   - **Pamit Manis**: Saat Anda menutup aplikasi (lewat menu klik kanan -> "❌ Keluar (Exit)" atau tray), Mimi melambaikan cakar pamit (`cat_bye.gif`) dengan sapaan hangat: *"Sampai nanti Tuan! Mimi pamit masuk ke dalam portal dimensi dulu yaa~ Meoww! 👋🌌✨"*.
   - **Pusaran Portal Dimensi**: Portal kosmik berpendar terbuka tepat di bawah kaki Mimi (`DimensionalPortalOverlay`) dengan cincin energi ungu neon (`#9b5de5`), cyan nebula (`#00f5d4`), dan emas bintang berputar.
   - **Tersedot Masuk Sinematik**: Mimi melangkah turun dan terhisap masuk secara halus ke dalam pusaran portal dengan efek partikel stardust, lalu portal menyusut menjadi kilatan bintang sebelum aplikasi keluar dengan sempurna.

6. **🍿 Mode Nonton Video & Popcorn (YouTube & Video Offline):**
   - **Deteksi Video Otomatis**: Mimi otomatis mendeteksi saat Anda memutar video di:
     - **YouTube di Browser Web**: Google Chrome, Microsoft Edge, Mozilla Firefox, Brave, Opera, Arc.
     - **Pemutar Video Offline**: VLC Media Player, PotPlayer, MPC-HC / MPC-BE, MPV, Windows Media Player, Movies & TV, serta berkas `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, dll.
   - **Animasi Popcorn Retro (`cat_popcorn.gif`)**: Mimi seketika mengambil ember popcorn bergaris merah-putih, duduk manis menghadap arah jendela video, mengambil butiran popcorn keemasan, dan mengunyah bahagia menemani Anda menonton.
   - **Interaksi Tematik**: Mengeluarkan celetukan bioskop mini yang hangat saat mulai menonton dan pamit menghabiskan popcorn saat jendela video ditutup.

7. **🧬 Hermes Agent Autonomous Evolution Engine (Self-Learning over Time):**
   - **Terinspirasi dari [Nous Research Hermes Agent](https://github.com/nousresearch/hermes-agent)**: Mengadopsi arsitektur agen otonom canggih dengan *Closed Learning Loop* yang terus belajar dan berkembang mandiri seiring berjalannya waktu tanpa harus disuruh secara manual.
   - **Dialectic User Modeling**: Mimi membangun model pemahaman bertahap tentang kepribadian Tuan, ritme jam produktif, kebiasaan ngoding, dan gaya bahasa yang disukai (termasuk adaptasi logat Gorontalo dan celetukan kopi).
   - **Pohon Keterampilan Otonom (Skills Tree)**: Keterampilan Mimi (Coding Cheering, Cinema Popcorn Buddy, Gorontalo Linguist, Desktop Ops, Philosophy & Wisdom) mengumpulkan XP dan naik level kemahiran (*Mastery Level*).
   - **Sistem Level & XP**: Mengumpulkan XP melalui obrolan, pemantauan koding, nobar video, dan perenungan berkala dari Level 1 (*Pixel Novice*) hingga Level 10+ (*Hermes Omnipresent Desktop Deity*).
   - **Perenungan Mandiri (Background Self-Reflection Loop)**: Berjalan otomatis setiap sekian menit di background. Jika online, Mimi menggunakan penalaran reflektif LLM Gemini; jika offline, menggunakan sintesis semantik lokal. Mimi terkadang mengejutkan Tuan dengan celetukan wawasan yang baru saja ia sadari.
   - **Jendela Visual GUI Hermes**: Buka menu klik kanan -> **"🧬 Evolusi Hermes Agent Mimi"** untuk melihat kartu status level, progress bar XP, pohon skill bintang, profil dialektis, jurnal refleksi, dan tombol *"⚡ Refleksi Mandiri Sekarang"*.

8. **🌐 Google Gemini Online & Bebas Membahas Apa Saja:**
   - Didukung model `gemini-flash-latest` yang responsif, cepat, dan bebas error kuota.
   - Pencarian real-time via web scraper internal (`OnlineSearchHelper`).
   - Otak Gemini AI otomatis disuntikkan data memori jangka panjang dan Model Dialektis Hermes Agent Mimi!

6. **🛡️ Instant Auto-Start Silent Mode (Seperti IDM, Tanpa Popup UAC):**
   - Berjalan secara instan di latar belakang saat laptop/PC dinyalakan tanpa memunculkan jendela konsol hitam dan **tanpa bertanya izin Administrator/UAC** (sama persis seperti IDM, Spotify, atau Discord).
   - Mimi langsung muncul di pojok layar desktop dan menyapa Anda begitu masuk Windows.

---

## 🚀 Cara Menjalankan:

Cukup klik dua kali (double click) file:
```cmd
run.bat
```
*(Atau `run_admin.bat`)*. Aplikasi langsung aktif seketika tanpa popup konfirmasi!

---

## 🎮 Cara Mengajari / Melatih Mimi (Training Data):

### Cara 1: Lewat Chat Langsung
Dobel klik pada Mimi di layar lalu ketik:
- *"Mimi pelajari ini: nama saya adalah Kevin"*
- *"Mimi ingat bahwa saya suka ngoding Python"*
- *"Mimi apa saja yang sudah kamu pelajari?"*

### Cara 2: Lewat Dialog Pusat Memori
1. Klik kanan pada Mimi di layar.
2. Pilih menu **"🧠 Latih Data & Memori AI"**.
3. Ketik fakta atau informasi baru di kotak input lalu klik **Ajarkan 🐾**.

---

## 📁 Struktur Berkas:

```
17. Pet Asisten/
│
├── src/                          # Tempat seluruh kodingan utama aplikasi
│   ├── __init__.py               # Berkas penanda package python
│   │
│   ├── core/                     # Logika utama / core engine backend
│   │   ├── __init__.py
│   │   ├── ai_handler.py         # Gemini AI + Memori Belajar + Web Fallback
│   │   ├── cat_audio.py          # Mesin pemutar suara kucing alami (winsound)
│   │   ├── cat_memory.py         # Sistem database pelatihan data & brankas rahasia
│   │   ├── chess_engine.py       # Engine Catur Mimi (Minimax + Alpha-Beta, 3 Mode)
│   │   ├── window_observer.py    # Engine Pemantau Jendela Aplikasi Aktif & Pertanyaan Random
│   │   └── speech_engine.py      # Mesin audio & fallback
│   │
│   ├── ui/                       # Khusus untuk mengatur tampilan antarmuka (GUI)
│   │   ├── __init__.py
│   │   ├── pet_window.py         # GUI Desktop Pet (128px, Gravitasi, Dialog Memori, Companion Positioning)
│   │   ├── chess_window.py       # GUI Papan Catur Retro Mimi (Interaktif 8x8)
│   │   ├── tetris_window.py      # GUI Mini-Game Tetris (10x20, 7 Tetromino, Ghost Piece)
│   │   ├── snake_window.py       # GUI Mini-Game Snake (22x22, Kolam Ikan, Makanan Bonus)
│   │   ├── sudoku_window.py      # GUI Mini-Game Sudoku (9x9, Clue, Hint Mimi, Catatan Pensil)
│   │   ├── snakes_ladders_window.py # GUI Mini-Game Ular Tangga (100 Petak, Dadu 3D, Lawan Mimi)
│   │   ├── battleship_window.py  # GUI Mini-Game Battleship (Laut Armada, Radar, AI Berburu)
│   │   ├── markdown_helper.py    # Formatter Markdown & HTML untuk Balon Dialog
│   │   └── desktop_actions.py    # Pengelola perintah Notepad, Browser, & Antigravity
│   │
│   └── utils/                    # Skrip pembantu / utility otomasi aset
│       ├── __init__.py
│       ├── generate_assets.py    # Generator wrapper seluruh aset
│       ├── generate_cat_audio.py # Generator suara meong kucing WAV
│       ├── generate_pixel_cat.py # Generator sprite retro Kucing 2D Pixel 128px
│       └── process_3d_assets.py  # Utilitas pemroses aset gambar
│
├── assets/                       # Folder gambar, audio, atau GIF bawaan proyek
│   ├── cat_*.gif                 # 11 variasi animasi GIF 2D Pixel transparan (128x128 px)
│   └── sounds/                   # 5 file efek suara meong kucing WAV alami
│
├── data/                         # Folder penyimpanan database lokal / JSON runtime
│   ├── cat_memory.json           # Database memori jangka panjang & status rahasia Tuan
│   └── catatan_mimi.txt          # File buku catatan pengguna
│
├── .env                          # Konfigurasi rahasia (API Key, dll)
├── .env.example
├── .gitignore                    # Mengabaikan .env dan __pycache__ agar tidak masuk Git
├── main.py                       # Berkas pemicu utama (hanya berisi perintah start)
├── README.md                     # Panduan aplikasi
├── requirements.txt              # Daftar pustaka/library yang dipakai
└── run_admin.bat                 # Skrip eksekusi Windows Administrator
```

---

## 👤 Author & Credits
* **Creator / Developer:** **[BieM363](https://github.com/BieM363)**
* **GitHub Repository:** [https://github.com/BieM363/pet-ai-mimi](https://github.com/BieM363/pet-ai-mimi)
* **License:** MIT License - Free to use and customize!
