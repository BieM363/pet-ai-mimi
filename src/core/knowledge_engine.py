import os
import json
import re
import datetime
import math
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
KNOWLEDGE_FILE = os.path.join(DATA_DIR, "mimi_knowledge.json")


def _tokenize(text: str) -> List[str]:
    """Membersihkan dan memecah teks menjadi token kata yang relevan."""
    clean = text.lower().strip()
    # Hapus tanda baca dan karakter khusus
    clean = re.sub(r'[\?\!\.,;:\"\'\(\)\[\]\{\}\\\/\<\>\-_+*=~`@#$%^&|]', ' ', clean)
    words = clean.split()
    # Filter kata hubung, kata tanya, & kata awalan umum dalam Bahasa Indonesia & Inggris
    stop_words = {
        "yang", "di", "ke", "dari", "pada", "dalam", "untuk", "dengan", "dan", "atau",
        "ini", "itu", "juga", "sudah", "akan", "bisa", "dapat", "ada", "adalah", "yaitu",
        "ialah", "apakah", "apa", "siapa", "mengapa", "kenapa", "bagaimana", "dimana",
        "kapan", "tolong", "coba", "mimi", "tuan", "ya", "saja", "aja", "dong", "deh",
        "jelaskan", "jelasin", "tentang", "mengenai", "ceritakan", "seputar", "info",
        "tahu", "tau", "kasih", "beritahu", "punya", "kamu", "aku", "saya", "tahu",
        "the", "a", "an", "is", "are", "what", "who", "where", "how", "when", "why", "about", "tell"
    }
    return [w for w in words if len(w) > 1 and w not in stop_words]


# ------------------------------------------------------------------------------
# BASIS PENGETAHUAN BAWAAN OFFLINE (SEED KNOWLEDGE)
# Memungkinkan Mimi menjawab berbagai topik esensial tanpa internet sejak awal
# ------------------------------------------------------------------------------
DEFAULT_SEED_KNOWLEDGE = [
    {
        "topic": "identitas_mimi",
        "keywords": ["mimi", "kucing", "siapa", "kamu", "asisten", "pixel", "art", "robot", "pencipta"],
        "content": "Mimi adalah kucing 2D Pixel Art cerdas dan asisten AI setia yang hidup di desktop Windows milik Tuan! Mimi bisa diajak ngobrol, mengingat fakta, mencatat di Notepad, membuka browser, memantau aplikasi, hingga bermain catur dan games seru.",
        "category": "personal"
    },
    {
        "topic": "bahasa_python",
        "keywords": ["python", "bahasa", "pemrograman", "coding", "koding", "guido", "van", "rossum"],
        "content": "Python adalah bahasa pemrograman tingkat tinggi yang dibuat oleh Guido van Rossum dan dirilis pertama kali pada tahun 1991. Python terkenal karena sintaksnya yang sangat mudah dibaca, elegan, dan banyak digunakan untuk AI, web, otomasi, dan data science.",
        "category": "programming"
    },
    {
        "topic": "ibukota_indonesia",
        "keywords": ["ibukota", "ibu", "kota", "indonesia", "nusantara", "ikn", "jakarta", "negara"],
        "content": "Ibukota Negara Indonesia adalah Ibu Kota Nusantara (IKN) yang terletak di Kalimantan Timur, menggantikan Daerah Khusus Ibukota Jakarta.",
        "category": "geography"
    },
    {
        "topic": "filsafat_stoikisme",
        "keywords": ["stoik", "stoikisme", "stoicism", "filsafat", "marcus", "aurelius", "seneca", "epictetus", "tenang"],
        "content": "Stoikisme adalah aliran filsafat Yunani-Romawi kuno yang mengajarkan dikotomi kendali: fokuslah pada hal-hal yang dapat kita kendalikan (pikiran, respon, dan tindakan kita), serta ikhlas menerima hal-hal di luar kendali kita dengan ketenangan batin.",
        "category": "philosophy"
    },
    {
        "topic": "fakta_kucing_purr",
        "keywords": ["dengkur", "purr", "suara", "kucing", "kenapa", "sembuh", "getaran"],
        "content": "Kucing mendengkur (purring) pada frekuensi antara 20-140 Hz. Getaran suara purr ini tidak hanya menunjukkan rasa nyaman dan bahagia, tetapi secara medis terbukti membantu meredakan stres, merangsang regenerasi jaringan, dan mempercepat penyembuhan tulang!",
        "category": "cats"
    },
    {
        "topic": "produktivitas_pomodoro",
        "keywords": ["pomodoro", "teknik", "fokus", "belajar", "kerja", "waktu", "istirahat", "produktivitas"],
        "content": "Teknik Pomodoro adalah metode manajemen waktu di mana kamu bekerja fokus selama 25 menit, diikuti istirahat singkat 5 menit. Setelah 4 sesi pomodoro, ambil istirahat lebih panjang (15-30 menit) agar otak tetap segar!",
        "category": "productivity"
    },
    {
        "topic": "lelucon_kucing_coding",
        "keywords": ["lelucon", "jokes", "humor", "lucu", "lawak", "tertawa", "candaan"],
        "content": "Kenapa kucing jago banget koding? Karena kucing selalu fokus berburu 'mouse' dan sangat teliti menangkap setiap 'bugs' yang berkeliaran di layar desktop! Meoww~ 🐭💻",
        "category": "jokes"
    },
    {
        "topic": "perintah_cmd_desktop",
        "keywords": ["cmd", "perintah", "command", "matikan", "shutdown", "sleep", "restart", "kunci"],
        "content": "Tuan bisa menyuruh Mimi mengontrol komputer melalui obrolan: 'matikan komputer 30 menit lagi', 'sleep komputer', 'kunci layar', 'buka note', 'baca note', atau 'buka youtube'!",
        "category": "system"
    }
]


class MimiKnowledgeEngine:
    """
    Mesin Basis Data Pengetahuan & Penalaran Mandiri Offline Mimi.
    Menyimpan fakta hasil belajar, percakapan bermakna, dan mampu mencari jawaban offline.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MimiKnowledgeEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.data_dir = DATA_DIR
        self.db_file = KNOWLEDGE_FILE
        self._cache = {}
        self._load_knowledge()

    def _load_knowledge(self):
        """Memuat data pengetahuan dari file JSON atau inisialisasi awal."""
        os.makedirs(self.data_dir, exist_ok=True)
        default_data = {
            "version": "2.0",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "knowledge_items": DEFAULT_SEED_KNOWLEDGE,
            "qa_cache": [],
            "learned_from_chats": []
        }

        if not os.path.exists(self.db_file):
            self._cache = default_data
            self._save_knowledge()
            return

        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Pastikan key esensial ada
                for k, v in default_data.items():
                    if k not in data:
                        data[k] = v
                self._cache = data
        except Exception as e:
            print(f"[KnowledgeEngine] Gagal membaca data: {e}")
            self._cache = default_data

    def _save_knowledge(self):
        """Menyimpan database pengetahuan ke disk secara aman."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            self._cache["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[KnowledgeEngine] Gagal menyimpan data: {e}")

    def add_knowledge_item(self, topic: str, content: str, keywords: Optional[List[str]] = None, category: str = "general") -> bool:
        """Menambahkan entri pengetahuan baru ke dalam database Mimi."""
        clean_topic = topic.strip()
        clean_content = content.strip()
        if not clean_content:
            return False

        if not keywords:
            keywords = _tokenize(f"{clean_topic} {clean_content}")

        items = self._cache.setdefault("knowledge_items", [])
        # Cek apakah topic sudah ada, perbarui jika ada
        for item in items:
            if item.get("topic", "").lower() == clean_topic.lower():
                item["content"] = clean_content
                item["keywords"] = list(set(item.get("keywords", []) + keywords))
                item["category"] = category
                item["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save_knowledge()
                return True

        # Entri baru
        new_item = {
            "topic": clean_topic,
            "keywords": keywords,
            "content": clean_content,
            "category": category,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        items.append(new_item)
        self._save_knowledge()
        return True

    def record_qa_pair(self, question: str, answer: str, source: str = "online_gemini"):
        """
        Continuous Learning: Merekam pasangan tanya-jawab bermakna saat online
        sehingga Mimi dapat menggunakannya kembali secara cerdas saat offline.
        """
        clean_q = question.strip()
        clean_a = answer.strip()
        if len(clean_q) < 4 or len(clean_a) < 10:
            return

        # Abaikan percakapan sistem internal atau perintah aksi
        if any(w in clean_q.lower() for w in ["cmd:", "buka browser", "buka youtube", "matikan komputer", "sleep komputer", "main catur"]):
            return

        qa_list = self._cache.setdefault("qa_cache", [])
        tokens_q = _tokenize(clean_q)

        # Cek apakah pertanyaan serupa sudah pernah disimpan
        for entry in qa_list:
            existing_tokens = set(_tokenize(entry.get("question", "")))
            common = set(tokens_q).intersection(existing_tokens)
            if len(tokens_q) > 0 and len(common) / len(tokens_q) > 0.80:
                # Perbarui jawaban dengan yang terbaru
                entry["answer"] = clean_a
                entry["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                self._save_knowledge()
                return

        # Simpan jika belum ada (maksimal simpan 150 Q&A terbaik untuk efisiensi)
        if len(qa_list) > 150:
            qa_list.pop(0)

        qa_list.append({
            "question": clean_q,
            "tokens": tokens_q,
            "answer": clean_a,
            "source": source,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self._save_knowledge()

    def query_offline_thought(self, prompt: str, user_profile: Optional[dict] = None, learned_facts: Optional[List[dict]] = None) -> Optional[dict]:
        """
        Mengeksekusi proses 'Berpikir Offline' Mimi:
        Mencari jawaban terbaik dari:
        1. Fakta yang diajarkan langsung oleh Tuan (learned_facts dari cat_memory.json)
        2. Profil & Nama Samaran Tuan
        3. Basis Pengetahuan Terstruktur (knowledge_items)
        4. Arsip Tanya-Jawab Hasil Belajar Sebelumnya (qa_cache)
        
        Mengembalikan dict jika ditemukan jawaban relevan:
        {
            "found": True,
            "answer": str,
            "source": str,
            "confidence": float
        }
        """
        clean_p = prompt.strip()
        tokens = _tokenize(clean_p)
        if not tokens:
            return None

        best_match = None
        highest_score = 0.0

        # --- 1. EVALUASI FAKTA YANG DIAJARKAN TUAN (PRIORITAS TERTINGGI) ---
        if learned_facts:
            for f_item in learned_facts:
                fact_str = f_item.get("fact", "")
                fact_tokens = _tokenize(fact_str)
                if not fact_tokens:
                    continue
                matched = [w for w in tokens if w in fact_tokens]
                if matched:
                    # Nilai kemiripan Jaccard-like berbobot tinggi untuk fakta personal
                    score = (len(matched) * 2.5) / (len(tokens) + math.sqrt(len(fact_tokens)))
                    if len(matched) >= 2 or (len(tokens) == 1 and len(matched) == 1):
                        score += 0.4
                    if score > highest_score and score >= 0.50:
                        highest_score = score
                        best_match = {
                            "content": fact_str,
                            "source": "Fakta yang diajarkan Tuan",
                            "type": "user_fact"
                        }

        # --- 2. EVALUASI PROFIL & PREFERENSI TUAN ---
        if user_profile:
            p_name = user_profile.get("name", "")
            p_nick = user_profile.get("nickname", "")
            is_sec = user_profile.get("is_secret", False)

            # Jika menanyakan nama/panggilan
            if any(w in tokens for w in ["nama", "namaku", "panggilan", "samaran"]):
                if p_nick:
                    return {
                        "found": True,
                        "answer": f"Nama samaran Tuan adalah **{p_nick}**! Mimi selalu mengingat nama keren ini! 🕶️✨",
                        "source": "Profil Tuan",
                        "confidence": 1.0
                    }
                elif not is_sec and p_name:
                    return {
                        "found": True,
                        "answer": f"Nama Tuan adalah **{p_name}**! Mimi selalu mengingat Tuan! 😸✨",
                        "source": "Profil Tuan",
                        "confidence": 1.0
                    }

        # --- 3. EVALUASI BASIS PENGETAHUAN TERSTRUKTUR (KNOWLEDGE ITEMS) ---
        for item in self._cache.get("knowledge_items", []):
            item_kws = item.get("keywords", [])
            matched = [w for w in tokens if any(w in kw or kw in w for kw in item_kws)]
            if matched:
                score = (len(matched) * 2.0) / (len(tokens) + 0.5)
                if score > highest_score and score >= 0.38:
                    highest_score = score
                    best_match = {
                        "content": item.get("content", ""),
                        "topic": item.get("topic", ""),
                        "source": "Basis Data Belajar Mandiri Mimi",
                        "type": "seed_knowledge"
                    }

        # --- 4. EVALUASI CACHE TANYA-JAWAB (QA CACHE) ---
        for qa in self._cache.get("qa_cache", []):
            qa_tokens = qa.get("tokens", [])
            matched = [w for w in tokens if any(w in qw or qw in w for qw in qa_tokens)]
            if matched:
                score = (len(matched) * 2.2) / (len(tokens) + math.sqrt(len(qa_tokens)))
                if score > highest_score and score >= 0.40:
                    highest_score = score
                    best_match = {
                        "content": qa.get("answer", ""),
                        "source": f"Pengalaman Obrolan Tuan ({qa.get('date', 'lalu')})",
                        "type": "qa_cache"
                    }

        if best_match and highest_score >= 0.38:
            content = best_match["content"]
            source = best_match.get("source", "Memori Mimi")
            
            # Format jawaban dalam persona Mimi yang hangat dan bangga belajar mandiri
            if best_match.get("type") == "user_fact":
                reply = (
                    f"Meow! *mata berbinar senang mengingat catatan di memoriku* 🧠✨\n\n"
                    f"Berdasarkan apa yang sudah Tuan ajarkan ke Mimi:\n"
                    f"\"{content}\"\n\n"
                    f"Mimi selalu mengingat hal ini walau sedang dalam mode offline, Tuan! 🐾😸"
                )
            else:
                reply = (
                    f"Meow! *duduk manis ala filsuf kucing* 🧠✨\n\n"
                    f"{content}\n\n"
                    f"🐾 *Pengetahuan dari: {source} (Tersimpan aman di database offline Mimi)*"
                )

            return {
                "found": True,
                "answer": reply,
                "source": source,
                "confidence": highest_score
            }

        return None


# Helper instance global
_engine_instance = None

def get_knowledge_engine() -> MimiKnowledgeEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MimiKnowledgeEngine()
    return _engine_instance
