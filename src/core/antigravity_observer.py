import os
import sys
import re
import ast
import json
import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PARENT_PROJECTS_DIR = os.path.dirname(PROJECT_ROOT)  # Biasanya D:\Ngoding

# Folder-folder yang diabaikan saat scanning proyek
IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".idea", ".vscode", "dist", "build", "env"
}


def clean_title_segment(seg: str) -> tuple:
    """
    Membersihkan penanda unsaved changes (bullet ● atau *) dan whitespace.
    Mengembalikan (cleaned_string, is_dirty)
    """
    s = seg.strip()
    is_dirty = False
    if s.startswith("●") or s.startswith("*"):
        is_dirty = True
        s = s.lstrip("●* \t").strip()
    if s.endswith("*"):
        is_dirty = True
        s = s.rstrip("* \t").strip()
    return s, is_dirty


def parse_antigravity_title(title: str) -> dict:
    """
    Menganalisis judul jendela Antigravity IDE untuk mengekstrak:
    - Nama proyek
    - Nama file aktif
    - Status file unsaved (dirty)
    
    Contoh judul yang didukung:
    - "17. Pet Asisten - Antigravity IDE - hermes_agent.py"
    - "17. Pet Asisten - Antigravity IDE - ● hermes_agent.py"
    - "hermes_agent.py - 17. Pet Asisten - Antigravity IDE"
    - "● hermes_agent.py - 17. Pet Asisten - Antigravity IDE"
    - "17. Pet Asisten - Antigravity IDE"
    - "Antigravity IDE"
    """
    if not title:
        return {"is_antigravity": False, "project_name": "", "file_name": "", "is_dirty": False, "raw_title": ""}

    t_clean = title.strip()
    is_antigravity = "antigravity" in t_clean.lower()
    if not is_antigravity:
        return {"is_antigravity": False, "project_name": "", "file_name": "", "is_dirty": False, "raw_title": t_clean}

    parts = [p.strip() for p in t_clean.split(" - ")]
    project_name = ""
    file_name = ""
    is_dirty = False

    # Cari posisi segmen Antigravity IDE
    ag_idx = -1
    for i, p in enumerate(parts):
        if "antigravity" in p.lower():
            ag_idx = i
            break

    if ag_idx != -1:
        if len(parts) == 3:
            # Pola 1: [Project] - [Antigravity IDE] - [File]
            if ag_idx == 1:
                p_seg, _ = clean_title_segment(parts[0])
                f_seg, dirty = clean_title_segment(parts[2])
                project_name = p_seg
                file_name = f_seg
                is_dirty = dirty
            # Pola 2: [File] - [Project] - [Antigravity IDE]
            elif ag_idx == 2:
                f_seg, dirty = clean_title_segment(parts[0])
                p_seg, _ = clean_title_segment(parts[1])
                file_name = f_seg
                project_name = p_seg
                is_dirty = dirty
        elif len(parts) == 2:
            # Pola: [Project] - [Antigravity IDE] atau [File] - [Antigravity IDE]
            other_part, dirty = clean_title_segment(parts[0] if ag_idx == 1 else parts[1])
            is_dirty = dirty
            if "." in other_part and not any(other_part.lower().endswith(ext) for ext in [".exe"]):
                file_name = other_part
            else:
                project_name = other_part
        elif len(parts) >= 4:
            # Judul kompleks dengan breadcrumbs atau workspace path
            first_seg, _ = clean_title_segment(parts[0])
            last_seg, dirty = clean_title_segment(parts[-1])
            is_dirty = dirty
            if "." in last_seg:
                file_name = last_seg
                project_name = first_seg
            elif "." in first_seg:
                file_name = first_seg
                project_name = last_seg

    return {
        "is_antigravity": True,
        "project_name": project_name,
        "file_name": file_name,
        "is_dirty": is_dirty,
        "raw_title": t_clean
    }


def resolve_project_dir(project_name: str) -> str:
    """
    Menemukan path direktori fisik proyek di disk secara aman (hanya pencarian path).
    """
    # 1. Cek apakah proyek saat ini (17. Pet Asisten) cocok
    current_basename = os.path.basename(PROJECT_ROOT)
    if not project_name:
        return PROJECT_ROOT

    p_low = project_name.lower().strip()
    if p_low in current_basename.lower() or current_basename.lower() in p_low:
        return PROJECT_ROOT

    # 2. Cek direktori induk (D:\Ngoding)
    if os.path.isdir(PARENT_PROJECTS_DIR):
        try:
            for entry in os.listdir(PARENT_PROJECTS_DIR):
                full = os.path.join(PARENT_PROJECTS_DIR, entry)
                if os.path.isdir(full):
                    if entry.lower() == p_low or p_low in entry.lower():
                        return full
        except Exception:
            pass

    # Fallback default ke PROJECT_ROOT jika ada kecocokan Pet
    if "pet" in p_low or "asisten" in p_low:
        return PROJECT_ROOT

    return ""


def find_file_in_project(project_dir: str, file_name: str) -> str:
    """
    Mencari lokasi absolut file di dalam struktur folder proyek (Read-Only scan).
    """
    if not project_dir or not os.path.isdir(project_dir) or not file_name:
        return ""

    target = file_name.lower().strip()
    for root, dirs, files in os.walk(project_dir):
        # Saring direktori yang diabaikan
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
        for f in files:
            if f.lower() == target:
                return os.path.join(root, f)

    return ""


def inspect_file_readonly(file_path: str) -> dict:
    """
    Membaca file secara murni READ-ONLY dan menganalisis integritas sintaksis / error.
    TIDAK ADA FUNGSI MENULIS / MENGEDIT.
    """
    if not file_path or not os.path.isfile(file_path):
        return {"exists": False, "error": "File tidak ditemukan di disk."}

    try:
        size = os.path.getsize(file_path)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        lines = content.splitlines()
        line_count = len(lines)
        ext = os.path.splitext(file_path)[1].lower()

        syntax_info = {"valid": True, "details": "Sintaks valid."}

        # Analisis Sintaksis Khusus Python (AST Parser In-Memory)
        if ext == ".py":
            try:
                ast.parse(content, filename=file_path)
                syntax_info = {
                    "valid": True,
                    "error_type": None,
                    "details": "Sintaks Python valid tanpa SyntaxError atau IndentationError."
                }
            except SyntaxError as se:
                syntax_info = {
                    "valid": False,
                    "error_type": "SyntaxError",
                    "line": se.lineno,
                    "offset": se.offset,
                    "details": f"SyntaxError di baris {se.lineno}: {se.msg} (Cuplikan: '{se.text.strip() if se.text else ''}')"
                }
            except IndentationError as ie:
                syntax_info = {
                    "valid": False,
                    "error_type": "IndentationError",
                    "line": ie.lineno,
                    "details": f"IndentationError di baris {ie.lineno}: {ie.msg}"
                }
            except Exception as ex:
                syntax_info = {
                    "valid": False,
                    "error_type": "ParseError",
                    "details": f"Gagal parsing kode: {ex}"
                }

        # Analisis Sintaksis Khusus JSON
        elif ext == ".json":
            try:
                json.loads(content)
                syntax_info = {"valid": True, "details": "Struktur format JSON valid."}
            except json.JSONDecodeError as je:
                syntax_info = {
                    "valid": False,
                    "error_type": "JSONDecodeError",
                    "line": je.lineno,
                    "details": f"JSON Error di baris {je.lineno}: {je.msg}"
                }

        # Potongan cuplikan isi file yang representatif (maksimal 45 baris awal)
        preview_lines = lines[:45]
        preview_text = "\n".join(preview_lines)
        if len(lines) > 45:
            preview_text += f"\n... [{len(lines) - 45} baris kode lainnya]"

        return {
            "exists": True,
            "path": file_path,
            "filename": os.path.basename(file_path),
            "size_bytes": size,
            "line_count": line_count,
            "syntax": syntax_info,
            "preview": preview_text
        }
    except Exception as e:
        return {"exists": False, "error": f"Tidak dapat membaca file: {e}"}


def get_project_file_tree_readonly(project_dir: str, max_items: int = 30) -> list:
    """
    Mengambil daftar file proyek secara ringkas (Read-Only).
    """
    if not project_dir or not os.path.isdir(project_dir):
        return []

    items = []
    try:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for f in sorted(files):
                if f.startswith(".") or f.endswith((".pyc", ".pyd", ".png", ".jpg", ".gif", ".ico", ".wav")):
                    continue
                rel = os.path.relpath(os.path.join(root, f), project_dir)
                items.append(rel.replace("\\", "/"))
                if len(items) >= max_items:
                    return items
    except Exception:
        pass
    return items


def get_antigravity_status(app_info: dict = None) -> dict:
    """
    Mengumpulkan seluruh status observasi Antigravity IDE saat ini:
    - Status aktif / terakhir
    - Project aktif
    - File aktif
    - Hasil inspeksi sintaks kode (Read-Only)
    - Pohon file proyek
    """
    try:
        from src.core import window_observer
    except ImportError:
        try:
            from core import window_observer
        except ImportError:
            import window_observer

    if not app_info:
        app_info = window_observer.get_current_or_last_app_info() or {}

    title = app_info.get("title", "")
    exe = app_info.get("exe", "").lower()
    app_name = app_info.get("app_name", "")

    is_ag = "antigravity" in exe or "antigravity" in title.lower() or "antigravity" in app_name.lower()

    if not is_ag:
        # Coba cek apakah ada window Antigravity IDE di riwayat jendela terakhir
        last_ext = window_observer.get_last_external_app_info()
        if last_ext and ("antigravity" in last_ext.get("exe", "").lower() or "antigravity" in last_ext.get("title", "").lower()):
            app_info = last_ext
            title = app_info.get("title", "")
            is_ag = True

    if not is_ag:
        return {
            "is_open": False,
            "message": "Antigravity IDE saat ini sedang tidak berada di jendela aktif utama."
        }

    parsed = parse_antigravity_title(title)
    proj_name = parsed.get("project_name") or "17. Pet Asisten"
    file_name = parsed.get("file_name", "")
    is_dirty = parsed.get("is_dirty", False)

    proj_dir = resolve_project_dir(proj_name)
    file_path = ""
    file_inspect = {}

    if proj_dir and file_name:
        file_path = find_file_in_project(proj_dir, file_name)
        if file_path:
            file_inspect = inspect_file_readonly(file_path)

    file_tree = get_project_file_tree_readonly(proj_dir) if proj_dir else []

    return {
        "is_open": True,
        "raw_title": title,
        "project_name": proj_name,
        "project_dir": proj_dir,
        "active_file_name": file_name,
        "active_file_path": file_path,
        "is_dirty": is_dirty,
        "file_inspection": file_inspect,
        "project_files": file_tree
    }


def get_antigravity_context_for_prompt() -> str:
    """
    Menghasilkan blok teks status Antigravity IDE (Read-Only) yang komprehensif
    untuk disuntikkan ke System Prompt Gemini.
    """
    status = get_antigravity_status()
    if not status.get("is_open"):
        return ""

    lines = [
        "\n[STATUS ANTIGRAVITY IDE SAAT INI (AKSES INSPEKSI MELIHAT / READ-ONLY AKTIF)]:",
        f"- Status Jendela: Tuan sedang aktif membuka dan mengerjakan proyek di Antigravity IDE!",
        f"- Judul Jendela: \"{status.get('raw_title', '')}\"",
        f"- Proyek yang Sedang Dikerjakan: '{status.get('project_name')}' (Lokasi: {status.get('project_dir') or 'Workspace Lokal'})"
    ]

    active_file = status.get("active_file_name")
    if active_file:
        dirty_str = " (Ada perubahan belum disimpan/unsaved ●)" if status.get("is_dirty") else ""
        lines.append(f"- File yang Sedang Dibuka di Tab Editor: '{active_file}'{dirty_str}")

        insp = status.get("file_inspection", {})
        if insp.get("exists"):
            lines.append(f"- Path File: {insp.get('path')}")
            lines.append(f"- Ukuran & Panjang: {insp.get('line_count')} baris kode ({insp.get('size_bytes')} bytes)")
            syn = insp.get("syntax", {})
            if syn.get("valid"):
                lines.append(f"- Status Sintaksis: VALID (✅ Tidak ada syntax error yang terdeteksi)")
            else:
                lines.append(f"- Status Sintaksis: ADA KESALAHAN! (❌ {syn.get('details')})")

            if insp.get("preview"):
                lines.append("- Cuplikan Kode File yang Sedang Dibuka:")
                lines.append("```")
                lines.append(insp.get("preview"))
                lines.append("```")
    else:
        lines.append("- File yang Sedang Dibuka: Sedang fokus di terminal / konsol / navigasi folder proyek.")

    files = status.get("project_files", [])
    if files:
        lines.append(f"- Daftar File dalam Proyek '{status.get('project_name')}': {', '.join(files[:18])}")

    lines.append(
        "- PERATURAN AKSES & ANTI-HALUSINASI:\n"
        "  1. Kamu memiliki izin penuh MELIHAT (Read-Only) seluruh project, kode, file, dan error di Antigravity IDE.\n"
        "  2. Kamu TIDAK MEMILIKI HAK untuk mengubah, mengedit, ataupun membuat file kode (hanya melihat, menganalisis, dan melaporkan error).\n"
        "  3. Jika Tuan bertanya apa yang sedang dikerjakan, file apa yang sedang dibuka, atau mengecek error kodingan: KAMU WAJIB MERUJUK SECARA PERSIS pada data nyata di atas!\n"
        "  4. JANGAN PERNAH menebak atau berhalusinasi dengan proyek lama (seperti portofolio vercel) saat data di atas jelas menunjukkan Tuan sedang membuka file Antigravity IDE!"
    )

    return "\n".join(lines) + "\n"


def analyze_active_code_for_chat() -> str:
    """
    Fungsi cerdas untuk menjawab langsung pertanyaan pengguna seputar:
    - Apa yang sedang saya buka di Antigravity?
    - Coba cek kodinganku / ada error gak?
    - Kodinganku benar atau salah?
    """
    status = get_antigravity_status()
    if not status.get("is_open"):
        return "Meow? Saat ini Mimi belum mendeteksi jendela Antigravity IDE yang sedang aktif di layar Tuan. Coba buka atau klik jendela Antigravity IDE Tuan ya! 🐾💻"

    proj = status.get("project_name", "Proyek Tuan")
    file_name = status.get("active_file_name", "")
    insp = status.get("file_inspection", {})

    if not file_name:
        return (
            f"Meow! *duduk manis dan mengamati layar Antigravity IDE* 💻👀\n\n"
            f"Tuan sedang membuka proyek **{proj}**! "
            f"Saat ini Tuan tampaknya sedang di tampilan utama atau terminal. Coba buka salah satu file kodingan biar mata pixel Mimi bisa langsung bedah kodenya! Nyaa~ 🐾"
        )

    if not insp.get("exists"):
        return (
            f"Meow! Mimi melihat Tuan sedang mengerjakan proyek **{proj}** pada file **{file_name}**! 💻✨\n"
            f"Namun Mimi belum bisa menemukan path file fisiknya di disk untuk dibaca. Pastikan foldernya sudah tersimpan ya, Tuan! 🐾"
        )

    line_count = insp.get("line_count", 0)
    syn = insp.get("syntax", {})

    if syn.get("valid"):
        return (
            f"Meow! *pasang kacamata koding dan periksa teliti* 👓💻🐾\n\n"
            f"Tuan sedang mengerjakan proyek **{proj}** pada file **`{file_name}`** ({line_count} baris kode).\n\n"
            f"✅ **Hasil Pengecekan Sintaksis Mimi (Read-Only):**\n"
            f"Kodingan Tuan bersih dan valid! Tidak ada *SyntaxError* ataupun *IndentationError* yang terdeteksi. "
            f"Logika strukturnya rapi! Keren banget, pertahankan Tuan! Mau Mimi bantu cek fungsi atau logika bagian tertentu? *purrr~* 🐾✨"
        )
    else:
        err_detail = syn.get("details", "Ada kesalahan sintaks.")
        err_line = syn.get("line", "?")
        return (
            f"Meow! *telinga berdiri tegak dan cakar menunjuk layar* ⚠️🐾💻\n\n"
            f"Mimi menemukan sesuatu di proyek **{proj}**, file **`{file_name}`**!\n\n"
            f"❌ **Deteksi Error Sintaksis:**\n"
            f"• **Posisi:** Baris {err_line}\n"
            f"• **Keterangan:** {err_detail}\n\n"
            f"Coba periksa kembali baris kode tersebut ya Tuan, jangan sampai ada titik dua `:`, tanda kurung yang belum tertutup, atau spasi indentasi yang melompat! Mimi setia mengawasi dari pojok sini! 🐱🔍"
        )
