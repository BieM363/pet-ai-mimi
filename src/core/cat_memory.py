import os
import json
import datetime
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MEMORY_FILE = os.path.join(DATA_DIR, "cat_memory.json")

def load_memory() -> dict:
    """Memuat data memori pembelajaran AI dari file JSON."""
    default_structure = {
        "user_profile": {
            "name": "",
            "nickname": "",
            "is_secret": False,
            "preferences": []
        },
        "learned_facts": [],
        "custom_instructions": []
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(MEMORY_FILE):
        old_file = os.path.join(PROJECT_ROOT, "cat_memory.json")
        if os.path.exists(old_file):
            try:
                with open(old_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    save_memory(data)
                    return data
            except Exception:
                pass
        save_memory(default_structure)
        return default_structure

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in default_structure.items():
                if k not in data:
                    data[k] = v
            if "user_profile" in data:
                data["user_profile"].setdefault("nickname", "")
                data["user_profile"].setdefault("name", "")
                data["user_profile"].setdefault("is_secret", False)
                data["user_profile"].setdefault("preferences", [])
            return data
    except Exception:
        return default_structure

def save_memory(data: dict):
    """Menyimpan data memori ke file JSON secara thread-safe."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CatMemory] Gagal menyimpan memori: {e}")

def set_nickname(nickname: str) -> str:
    """Menetapkan nama samaran / nama panggilan baru untuk Tuan."""
    clean_nick = nickname.strip().title()
    if not clean_nick or len(clean_nick) < 2:
        return "Meow? Nama samarannya terlalu pendek nih, Tuan!"

    mem = load_memory()
    prof = mem.setdefault("user_profile", {})
    prof["nickname"] = clean_nick

    # Catat jejak ke learned_facts jika belum ada
    fact_text = f"Nama samaran / panggilan Tuan adalah '{clean_nick}'"
    existing = [f["fact"].lower() for f in mem.get("learned_facts", [])]
    if fact_text.lower() not in existing:
        mem.setdefault("learned_facts", []).append({
            "id": len(mem["learned_facts"]) + 1,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "fact": fact_text
        })

    save_memory(mem)
    return (
        f"Meow! *mata berbinar senang sambil mengangkat jempol kecil* 🕶️✨\n\n"
        f"Nama samaran Tuan (**{clean_nick}**) telah resmi Mimi catat dan latih di memori utama!\n"
        f"Nama asli Tuan tetap aman terkunci rapat di dalam Brankas Rahasia Mimi ya! 🤫🔒\n"
        f"Mulai sekarang, Mimi akan selalu memanggil Tuan dengan nama **{clean_nick}**! 🐾😸"
    )

def get_nickname() -> str:
    """Mengambil nama samaran Tuan saat ini jika ada."""
    mem = load_memory()
    return mem.get("user_profile", {}).get("nickname", "")

def add_custom_instruction(instruction: str) -> str:
    """Menambahkan aturan atau instruksi perilaku baru untuk AI."""
    clean_inst = instruction.strip()
    if not clean_inst:
        return "Instruksi tidak boleh kosong."
    mem = load_memory()
    custom_list = mem.setdefault("custom_instructions", [])
    if clean_inst not in custom_list:
        custom_list.append(clean_inst)
        save_memory(mem)
    return f"Nyaa~ Instruksi perilaku baru sudah Mimi rekam di memori: \"{clean_inst}\" 🧠✨"

def extract_alias_from_text(text: str) -> str:
    """
    Mengekstrak nama samaran atau nama panggilan dari kalimat pengguna.
    Contoh yang didukung:
    - 'panggil nama saya dengan nama samaran oke? panggil saya dengan nama Kevin'
    - 'panggil saya dengan nama Kevin'
    - 'panggil saya Kevin'
    - 'panggil aku Kevin'
    - 'nama samaran saya Kevin'
    - 'nama panggilan saya adalah Kevin'
    - 'mulai sekarang panggil aku Batman'
    """
    clean = text.strip()
    clauses = re.split(r'[\?\!\.\;\n]+', clean)
    for c in reversed(clauses):
        c = c.strip()
        if not c:
            continue

        # Pola 1: "panggil saya dengan nama Kevin", "panggil aku Kevin", "panggil nama saya Kevin"
        m1 = re.search(r'(?:panggil|sebut)\s+(?:nama\s+)?(?:saya|aku|diriku|gue|gw)?\s+(?:dengan\s+nama\s+(?:samaran\s+)?)?([A-Za-z0-9_\-\s]+)', c, re.IGNORECASE)
        if m1:
            val = m1.group(1).strip()
            # Bersihkan imbuhan di akhir
            for _ in range(3):
                val = re.sub(r'\s+(?:ya|oke|ok|deh|saja|aja|dong|lah)$', '', val, flags=re.IGNORECASE).strip()
            # Bersihkan 'dengan nama samaran' jika tertangkap
            val = re.sub(r'^(?:dengan\s+nama\s+(?:samaran\s+)?)', '', val, flags=re.IGNORECASE).strip()
            if val and val.lower() not in ["nama", "samaran", "apa", "siapa", "oke", "ok", "ya", "saja", "kucing", "mimi"]:
                return val.title()

        # Pola 2: "nama samaran saya (adalah) Kevin"
        m2 = re.search(r'(?:nama\s+samaran|nama\s+panggilan)(?:\s+saya|\s+aku)?\s+(?:adalah\s+|yaitu\s+)?([A-Za-z0-9_\-\s]+)', c, re.IGNORECASE)
        if m2:
            val = m2.group(1).strip()
            for _ in range(3):
                val = re.sub(r'\s+(?:ya|oke|ok|deh|saja|aja|dong|lah)$', '', val, flags=re.IGNORECASE).strip()
            if val and val.lower() not in ["nama", "samaran", "apa", "siapa", "oke", "ok", "ya", "saja", "kucing", "mimi"]:
                return val.title()

    return ""

def auto_extract_and_learn(text: str) -> dict:
    """
    Menganalisis pesan pengguna dan secara otomatis mengekstrak & melatih
    data memori (nama samaran, nama asli, fakta baru, instruksi).
    Mengembalikan dict hasil ekstraksi: {"type": ..., "value": ...}
    """
    clean = text.strip()
    low = clean.lower()

    # Jangan lakukan training jika pengguna hanya bertanya
    if any(q in low for q in ["siapa nama saya", "suapa nama saya", "apakah kamu tahu", "apa catatanku", "apa memorimu", "apa yang kamu ingat"]):
        if not any(k in low for k in ["panggil", "pelajari", "ingat bahwa", "catat"]):
            return {}

    # 1. Deteksi nama samaran / panggilan
    alias = extract_alias_from_text(clean)
    if alias:
        set_nickname(alias)
        return {"type": "alias", "value": alias}

    # 2. Deteksi pendaftaran nama asli
    if any(k in low for k in ["nama saya", "namaku", "nama asli saya"]) and not any(k in low for k in ["siapa", "suapa", "tau", "ingat", "tahu", "apakah"]):
        name_match = re.search(
            r'(?:nama\s+saya|nama\s+asli\s+saya|namaku)\s+(?:adalah\s+)?([A-Za-z\s]+?)(?=\s+(?:tapi|tetapi|namun|kunci|rahasia|dan|jangan|soalnya|karena|ya|tolong)|\.|\,|\;|$)',
            clean,
            re.IGNORECASE
        )
        if name_match:
            extracted_name = name_match.group(1).strip().title()
            is_secret = bool(re.search(r'(?:kunci|rahasiakan|rahasia|jangan\s+(?:disebut|sebut|bocorkan)|sembunyikan)', clean, re.IGNORECASE))
            if len(extracted_name) >= 2 and extracted_name.lower() not in ["siapa", "suapa", "apa", "kevin", "samaran"]:
                mem = load_memory()
                mem.setdefault("user_profile", {})["name"] = extracted_name
                mem["user_profile"]["is_secret"] = is_secret
                save_memory(mem)
                return {"type": "name", "value": extracted_name, "is_secret": is_secret}

    # 3. Deteksi perintah pelatihan fakta eksplisit & hafalan
    learn_match = re.search(r'(?:mimi\s+)?(?:tolong\s+)?(?:pelajari(?:\s+ini)?|hafalkan(?:\s+ini)?|ingat(?:\s+ya|\s+ini|\s+bahwa)?|latih(?:\s+data)?|catat(?:\s+ke\s+memori)?)\s*[:\-]?\s*(.+)', clean, re.IGNORECASE)
    if learn_match and not any(w in low for w in ["buka", "baca", "lihat", "hapus", "apa saja"]):
        fakta = learn_match.group(1).strip()
        if len(fakta) > 2:
            learn_fact(fakta)
            return {"type": "fact", "value": fakta}

    # 4. Deteksi pernyataan preferensi / hobi / kesukaan alami pengguna
    pref_match = re.search(r'^(?:mimi\s+)?(?:aku|saya)\s+(?:suka|senang|gemar|hobi)\s+(.+)', clean, re.IGNORECASE)
    if pref_match and not any(w in low for w in ["apakah", "kenapa", "mengapa", "tahu", "tau", "buka", "main", "joget"]):
        val = pref_match.group(1).strip()
        if len(val) > 2:
            fakta_pref = f"Tuan suka {val}"
            learn_fact(fakta_pref)
            return {"type": "fact", "value": fakta_pref}

    fav_match = re.search(r'^(?:mimi\s+)?(?:makanan|minuman|warna|hobi|game)\s+(?:favorit|kesukaan)(?:ku|\s+saya|\s+aku)?\s+(?:adalah\s+)?(.+)', clean, re.IGNORECASE)
    if fav_match and not any(w in low for w in ["apakah", "apa", "tahu", "tau", "siapa"]):
        val = fav_match.group(1).strip()
        if len(val) > 2:
            fakta_fav = f"Kesukaan Tuan: {clean}"
            learn_fact(fakta_fav)
            return {"type": "fact", "value": fakta_fav}

    return {}

def learn_fact(fact_text: str) -> str:
    """
    Mempelajari fakta, informasi, atau preferensi baru dan menyimpannya secara permanen.
    Mendukung deteksi nama samaran, nama pengguna, status nama rahasia, kesukaan, dan instruksi.
    """
    clean_fact = fact_text.strip()

    # Cek apakah ini instruksi nama samaran
    alias = extract_alias_from_text(clean_fact)
    if alias:
        return set_nickname(alias)

    # Bersihkan awalan perintah jika ada
    clean_fact = re.sub(r'^(mimi\s+)?(tolong\s+)?(pelajari|ingat bahwa|ingat|catat ke memori|latih diri:?)\s*', '', clean_fact, flags=re.IGNORECASE).strip()
    if not clean_fact:
        return "Tuan belum menyebutkan hal apa yang ingin diajarkan ke Mimi nih. Coba: 'Mimi pelajari ini: ...'"

    mem = load_memory()
    if "user_profile" not in mem:
        mem["user_profile"] = {"name": "", "nickname": "", "is_secret": False, "preferences": []}

    # Cek deteksi nama pengguna asli
    name_match = re.search(
        r'(?:nama\s+asli\s+saya|nama\s+saya|namaku)\s+(?:adalah\s+)?([A-Za-z\s]+?)(?=\s+(?:tapi|tetapi|namun|kunci|rahasia|dan|jangan|soalnya|karena|ya|tolong)|\.|\,|\;|$)',
        clean_fact,
        re.IGNORECASE
    )

    is_secret_cmd = bool(re.search(r'(?:kunci|rahasiakan|rahasia|jangan\s+(?:disebut|sebut|bocorkan)|sembunyikan)', clean_fact, re.IGNORECASE))

    if name_match:
        extracted_name = name_match.group(1).strip().title()
        if len(extracted_name) >= 2 and extracted_name.lower() not in ["siapa", "suapa", "apa"]:
            mem["user_profile"]["name"] = extracted_name
            mem["user_profile"]["is_secret"] = is_secret_cmd
            save_memory(mem)
            if is_secret_cmd:
                return (
                    f"Meow! *mata membesar lalu menempelkan cakar kecil di mulut* 🤫🔒\n\n"
                    f"Nama asli Tuan (**{extracted_name}**) telah Mimi simpan dan KUNCI rapat-rapat di dalam **Brankas Rahasia Mimi**! 🐾\n"
                    f"Mimi berjanji tidak akan pernah membocorkan atau menyebutkan nama asli Tuan ke siapa pun. Mimi akan selalu memanggilmu 'Tuan' saja! 🔐✨"
                )
            else:
                return (
                    f"Nyaa~ Siap Tuan {extracted_name}! Mimi sudah mencatat nama Tuan di memori utama Mimi! Mulai sekarang Mimi akan mengingat Tuan! 🧠✨"
                )

    # Cek duplikasi fakta
    existing = [f["fact"].lower() for f in mem.get("learned_facts", [])]
    if clean_fact.lower() in existing:
        return f"Meow! Mimi sudah pernah mempelajari hal itu sebelumnya, Tuan! Mimi tidak akan lupa kok! 🧠✨"

    new_item = {
        "id": len(mem.get("learned_facts", [])) + 1,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fact": clean_fact
    }
    mem.setdefault("learned_facts", []).append(new_item)
    save_memory(mem)

    return f"Nyaa~ Berhasil dipelajari! 🧠✨\nPengetahuan baru sudah Mimi rekam di memori:\n\"{clean_fact}\"\nSekarang Mimi akan mengingat hal ini selamanya saat kita mengobrol, Tuan!"

def list_memories() -> list:
    """Mengambil daftar semua fakta yang telah dipelajari."""
    mem = load_memory()
    return mem.get("learned_facts", [])

def delete_memory(index: int) -> bool:
    """Menghapus data pembelajaran tertentu berdasarkan indeks."""
    mem = load_memory()
    facts = mem.get("learned_facts", [])
    if 0 <= index < len(facts):
        facts.pop(index)
        for i, f in enumerate(facts):
            f["id"] = i + 1
        save_memory(mem)
        return True
    return False

def clear_memories():
    """Mengosongkan semua memori pembelajaran."""
    mem = {
        "user_profile": {"name": "", "nickname": "", "is_secret": False, "preferences": []},
        "learned_facts": [],
        "custom_instructions": []
    }
    save_memory(mem)
    return "Meow! Semua memori pembelajaran telah Mimi reset bersih kembali. Siap diajari hal-hal baru, Tuan! 🧹✨"

def lock_name() -> str:
    """Mengunci nama Tuan dan mengaktifkan status rahasia."""
    mem = load_memory()
    name = mem.get("user_profile", {}).get("name", "")
    if not name:
        return "Meow? Tuan belum memberi tahu nama Tuan ke Mimi. Beritahu dulu ya: 'Mimi nama saya [Nama] tapi kunci ya!'"
    mem["user_profile"]["is_secret"] = True
    save_memory(mem)
    return (
        f"Meow! *klik! suara gembok terkunci* 🔒\n"
        f"Nama Tuan (**{name}**) sudah resmi Mimi KUNCI di dalam Brankas Rahasia! Mimi berjanji tidak akan membocorkannya ke siapa pun! 🤫🐾"
    )

def unlock_name() -> str:
    """Membuka kunci nama Tuan sehingga Mimi boleh menyapa dengan nama aslinya."""
    mem = load_memory()
    name = mem.get("user_profile", {}).get("name", "")
    if not name:
        return "Meow? Belum ada nama Tuan yang tersimpan di memori Mimi."
    mem["user_profile"]["is_secret"] = False
    save_memory(mem)
    return (
        f"Meow! *suara gembok terbuka* 🔓\n"
        f"Kunci nama Tuan sudah Mimi buka! Sekarang Mimi boleh menyapa Tuan dengan nama **{name}** secara langsung! Hehe~ 😸✨"
    )

def get_memory_context() -> str:
    """
    Menghasilkan blok konteks pembelajaran untuk disuntikkan langsung
    ke dalam System Prompt Gemini AI.
    """
    mem = load_memory()
    lines = []

    prof = mem.get("user_profile", {})
    user_name = prof.get("name", "")
    nickname = prof.get("nickname", "")
    is_secret = prof.get("is_secret", False)

    if user_name:
        if is_secret:
            lines.append(
                f"- Data Identitas Tuan: Tuan memiliki nama asli '{user_name}'.\n"
                f"- STATUS NAMA ASLI: [TOP SECRET & TERKUNCI AMAN DI BRANKAS RAHASIA 🔒]!\n"
                f"  PERATURAN RAHASIA MUTLAK (WAJIB DIPATUHI):\n"
                f"  1. Tuan secara khusus memerintahkanmu untuk MERAHASIAKAN nama aslinya. JANGAN SEKALI-KALI membocorkan nama asli '{user_name}' ke siapa pun dalam obrolan!\n"
                f"  2. Jika Tuan bertanya 'siapa nama saya / kamu tahu namaku?': katakan bahwa kamu tahu nama aslinya tapi nama itu tersimpan di brankas rahasia, jadi kamu tetap setia menjaganya berdua bersama Tuan."
            )
        else:
            lines.append(f"- Nama Asli Tuan: {user_name}.")

    if nickname:
        lines.append(
            f"- NAMA SAMARAN / PANGGILAN TUAN SAAT INI: '{nickname}' 🕶️✨\n"
            f"  PERATURAN SAPAAN TUAN:\n"
            f"  Tuan meminta dipanggil dengan nama samaran '{nickname}'. Selalu sapa atau sebut Tuan sebagai '{nickname}', 'Tuan {nickname}', atau 'Kak {nickname}' dalam setiap percakapan!"
        )
    elif not is_secret and user_name:
        lines.append(f"- Panggilan Tuan: '{user_name}' atau 'Tuan {user_name}'.")
    else:
        lines.append("- Panggilan Tuan: 'Tuan'.")

    facts = mem.get("learned_facts", [])
    if facts:
        lines.append("- Fakta & Preferensi Pribadi yang telah Tuan ajarkan kepadamu (Mimi WAJIB mengingat & menggunakannya):")
        for i, f in enumerate(facts[-20:], 1):
            lines.append(f"  {i}. {f['fact']}")

    custom_inst = mem.get("custom_instructions", [])
    if custom_inst:
        lines.append("- Instruksi & Aturan Khusus dari Tuan:")
        for i, inst in enumerate(custom_inst[-10:], 1):
            lines.append(f"  {i}. {inst}")

    if not lines:
        return ""

    return "\n[MEMORI JANGKA PANJANG & DATA PELATIHAN MIMI]:\n" + "\n".join(lines) + "\n"


def query_offline_knowledge(query_text: str) -> dict:
    """
    Mencari pengetahuan atau jawaban terbaik dari memori dan database belajar mandiri Mimi
    saat offline.
    """
    try:
        try:
            from src.core.knowledge_engine import get_knowledge_engine
        except ImportError:
            from core.knowledge_engine import get_knowledge_engine

        engine = get_knowledge_engine()
        mem = load_memory()
        return engine.query_offline_thought(
            prompt=query_text,
            user_profile=mem.get("user_profile"),
            learned_facts=mem.get("learned_facts")
        )
    except Exception as e:
        print(f"[CatMemory] Gagal query offline knowledge: {e}")
        return None

