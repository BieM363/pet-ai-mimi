# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import re
import html

def markdown_to_html(text: str) -> str:
    """
    Mengonversi teks berformat Markdown menjadi HTML bergaya hangat & modern
    yang didukung oleh QLabel / QTextDocument PyQt5.
    
    Fitur:
    - Menghilangkan tanda baca asteris/bintang (*) yang terlihat aneh bagi pengguna.
    - Memberi gaya khusus dan warna terracotta pada ekspresi kucing (*Meow!*, *Purrrr~*, dsb).
    - Memformat teks tebal (**tebal**), miring (*miring*), judul (#), daftar butir (-), dan kutipan.
    - Mengubah perintah catatan ('buka note') menjadi tautan interaktif jika relevan.
    """
    if not text:
        return ""

    # Normalisasi baris baru
    raw_lines = text.strip().split("\n")
    processed_lines = []
    
    in_code_block = False
    code_block_lines = []

    for line in raw_lines:
        # Penanganan Blok Kode (```)
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_block_lines = []
            else:
                in_code_block = False
                code_content = html.escape("\n".join(code_block_lines))
                processed_lines.append(
                    f'<pre style="background: #2D2424; color: #F8E1D4; padding: 6px; border-radius: 5px; font-family: Consolas, monospace; font-size: 10px; margin: 4px 0;">{code_content}</pre>'
                )
            continue
        
        if in_code_block:
            code_block_lines.append(line)
            continue

        # Penanganan Heading Markdown (#, ##, ###)
        h_match = re.match(r'^(#{1,3})\s+(.+)$', line.strip())
        if h_match:
            level = len(h_match.group(1))
            h_text = html.escape(h_match.group(2))
            font_size = "12px" if level == 1 else ("11px" if level == 2 else "10.5px")
            processed_lines.append(
                f'<div style="font-weight: bold; font-size: {font_size}; color: #D35400; margin: 4px 0 2px 0;">{h_text}</div>'
            )
            continue

        # Penanganan Baris Kutipan (> ...)
        if line.strip().startswith(">"):
            q_text = html.escape(line.strip()[1:].strip())
            processed_lines.append(
                f'<div style="border-left: 2.5px solid #E07A5F; padding-left: 6px; margin: 3px 0; color: #7B341E; font-style: italic;">{q_text}</div>'
            )
            continue

        # Penanganan Butir Daftar (- item, * item, • item)
        bullet_match = re.match(r'^[\*\-•]\s+(.+)$', line.strip())
        if bullet_match:
            b_text = _format_inline(bullet_match.group(1))
            processed_lines.append(
                f'<div style="margin-left: 8px; margin-top: 2px;">• {b_text}</div>'
            )
            continue

        # Penanganan Daftar Bernomor (1. item)
        num_match = re.match(r'^(\d+)\.\s+(.+)$', line.strip())
        if num_match:
            num = num_match.group(1)
            n_text = _format_inline(num_match.group(2))
            processed_lines.append(
                f'<div style="margin-left: 8px; margin-top: 2px;"><b>{num}.</b> {n_text}</div>'
            )
            continue

        # Baris kosong = spasi paragraf
        if not line.strip():
            processed_lines.append('<div style="height: 5px;"></div>')
            continue

        # Baris Teks Biasa
        formatted_line = _format_inline(line)
        processed_lines.append(f'<div>{formatted_line}</div>')

    html_result = "".join(processed_lines)
    
    # Bungkus dalam container dengan styling font yang konsisten
    return f'<div style="font-family: \'Segoe UI\', sans-serif; font-size: 11px; line-height: 140%; color: #2D2424;">{html_result}</div>'


def _format_inline(text: str) -> str:
    """
    Memformat elemen inline markdown:
    - Tebal-Miring (***teks***)
    - Tebal (**teks**)
    - Miring / Aksi Kucing (*Meow!*, *telinga berkedut*, dsb)
    - Inline Code (`kode`)
    - Markdown Link [teks](url)
    - Auto-link 'buka note'
    """
    # 1. Lindungi kode inline terlebih dahulu
    placeholders = {}
    
    def repl_code(m):
        key = f"__CODE_{len(placeholders)}__"
        code_escaped = html.escape(m.group(1))
        placeholders[key] = (
            f'<span style="background-color: #F4EBE1; color: #8E3B20; padding: 1px 4px; '
            f'border-radius: 3px; font-family: Consolas, monospace; font-size: 10px;">{code_escaped}</span>'
        )
        return key

    text = re.sub(r'`([^`]+)`', repl_code, text)

    # 2. Lindungi Markdown Link: [nama](url)
    def repl_link(m):
        key = f"__LINK_{len(placeholders)}__"
        label = html.escape(m.group(1))
        target = m.group(2).strip()
        placeholders[key] = f'<a href="{target}" style="color: #D35400; font-weight: bold; text-decoration: underline;">{label}</a>'
        return key

    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', repl_link, text)

    # 3. Escape HTML karakter umum di teks sisa
    text = html.escape(text)

    # 4. Tebal & Miring: ***teks***
    def repl_bold_italic(m):
        content = m.group(1)
        return f'<b style="color: #BA4A00; font-style: italic;">{content}</b>'
    text = re.sub(r'\*\*\*([^\*]+)\*\*\*', repl_bold_italic, text)

    # 5. Tebal: **teks** atau __teks__
    def repl_bold(m):
        content = m.group(1)
        return f'<b style="color: #1A1414; font-weight: 600;">{content}</b>'
    text = re.sub(r'\*\*([^\*]+)\*\*', repl_bold, text)
    text = re.sub(r'__([^_]+)__', repl_bold, text)

    # 6. Miring / Aksi Suara Kucing: *teks* atau _teks_
    # Beri warna terracotta hangat elegan pada kata ekspresi kucing
    def repl_italic(m):
        content = m.group(1).strip()
        # Jika ekspresi suara kucing (Meow, Purr, dsb), buat lebih menonjol dan manis
        if re.search(r'\b(meow|purr|nyaa|mrrp|he+he+)\b', content, re.IGNORECASE):
            return f'<span style="color: #D35400; font-style: italic; font-weight: bold;">{content}</span>'
        # Aksi/gestur kucing (*telinga berkedut*, *mengibaskan ekor*, dsb)
        return f'<span style="color: #B95D36; font-style: italic;">{content}</span>'

    text = re.sub(r'\*([^\*]+)\*', repl_italic, text)
    text = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', repl_italic, text)

    # 7. Bersihkan sisa tanda bintang liar yang mungkin tidak sengaja tertulis
    text = text.replace("*", "")

    # 8. Otomatis buat 'buka note', 'main tetris', 'main snake' menjadi link interaktif jika belum dalam link
    def repl_note_action(m):
        matched = m.group(0)
        return f'<a href="action:open_notes" style="color: #D35400; font-weight: bold; text-decoration: underline;">{matched} 📝</a>'

    text = re.sub(r'(?i)\b(buka note|buka notepad|buka catatan)\b', repl_note_action, text)

    def repl_tetris_action(m):
        matched = m.group(0)
        return f'<a href="action:play_tetris" style="color: #D35400; font-weight: bold; text-decoration: underline;">{matched} 🧱</a>'

    text = re.sub(r'(?i)\b(main tetris|buka tetris|game tetris)\b', repl_tetris_action, text)

    def repl_snake_action(m):
        matched = m.group(0)
        return f'<a href="action:play_snake" style="color: #D35400; font-weight: bold; text-decoration: underline;">{matched} 🐍</a>'

    text = re.sub(r'(?i)\b(main snake|buka snake|game snake|main ular)\b', repl_snake_action, text)

    # 9. Kembalikan placeholder kode dan link
    for k, v in placeholders.items():
        text = text.replace(k, v)

    return text


def clean_text_for_speech(text: str) -> str:
    """
    Membersihkan markdown, tanda baca aneh (*, #, `, dsb) untuk pembacaan suara TTS (pyttsx3).
    - Mempertahankan teks tebal (**tebal**) tanpa bintangnya.
    - Mempertahankan suara ekspresi kucing (*Meow!*, *Purrrr~*, *Nyaa!*).
    - Menghilangkan deskripsi gestur panjang yang ada di dalam tanda kurung/bintang (*mengibaskan ekor pelan*).
    - Menghapus emoji yang bisa menyebabkan SAPI TTS membaca tanda aneh atau terhenti.
    """
    if not text:
        return ""

    # Hapus URL
    clean = re.sub(r'https?://\S+', '', text)
    # Hapus tag HTML jika ada
    clean = re.sub(r'<[^>]+>', '', clean)

    # 1. Pertahankan kata yang di-bold (**kata**) dengan menghapus bintangnya terlebih dahulu
    clean = re.sub(r'\*\*\*([^\*]+)\*\*\*', r'\1', clean)
    clean = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean)
    clean = re.sub(r'__([^_]+)__', r'\1', clean)

    # 2. Filter tanda bintang tunggal (*ekspresi*)
    def filter_cat_expressions(match):
        content = match.group(1).strip()
        low = content.lower()
        # Jika ekspresi suara kucing pendek, tetap ucapkan
        cat_sounds = ['meow!', 'meow', 'purrrr~', 'purrrr', 'purr~', 'purr', 'nyaa!', 'nyaa', 'nya', 'mrrp', 'hehe']
        for cs in cat_sounds:
            if cs in low or low in cs:
                return content
        # Jika aksi/gestur panjang (*telinga berkedut penasaran*, *kibas ekor*), hilangkan dari suara
        return ""

    clean = re.sub(r'\*([^*]+)\*', filter_cat_expressions, clean)
    clean = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', filter_cat_expressions, clean)

    # Hapus tanda markdown lain: #, `, ~, _, [link](url)
    clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
    clean = re.sub(r'[#`~><\*\^\$]', ' ', clean)

    # Bersihkan simbol/emoji umum yang sering dibaca aneh oleh Windows TTS
    clean = re.sub(r'[^\x00-\x7F\u00A0-\u024F\u1E00-\u1EFF\s\.,!\?:;\-\'\"]+', ' ', clean)

    # Normalisasi spasi dan tanda baca
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

