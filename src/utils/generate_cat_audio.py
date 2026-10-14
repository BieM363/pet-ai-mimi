# ==============================================================================
# Mimi Virtual Pixel Cat AI Companion
# Creator / Author: BieM363 (https://github.com/BieM363)
# GitHub Repository: https://github.com/BieM363/pet-ai-mimi
# ==============================================================================
__author__ = "BieM363"
__repository__ = "https://github.com/BieM363/pet-ai-mimi"

import os
import math
import wave
import struct

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOUNDS_DIR = os.path.join(PROJECT_ROOT, "assets", "sounds")

def write_wav(filepath, sample_rate, samples):
    """Menulis list float sample [-1.0, 1.0] ke file WAV 16-bit mono."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with wave.open(filepath, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        data = []
        for s in samples:
            val = int(max(-1.0, min(1.0, s)) * 32767)
            data.append(struct.pack("<h", val))
        wav.writeframes(b"".join(data))
    print(f"[Audio] Berhasil membuat suara kucing: {os.path.basename(filepath)}")

def generate_meow_talk():
    """Suara meong manis santai saat kucing berbicara di balon dialog."""
    sample_rate = 22050
    duration = 0.38
    num_samples = int(duration * sample_rate)
    samples = []
    phase = 0.0

    # Frekuensi meong naik sedikit lalu turun: 520Hz -> 820Hz -> 460Hz
    for i in range(num_samples):
        t = i / num_samples
        if t < 0.30:
            f = 520 + (820 - 520) * (t / 0.30)
        else:
            f = 820 - (820 - 460) * ((t - 0.30) / 0.70)

        # Envelope vokal (serak manis ala kucing)
        env = math.sin(t * math.pi) ** 0.85
        # Modulasi formant
        phase += 2 * math.pi * f / sample_rate
        # Nada dasar + harmonik kucing alami
        s = 0.65 * math.sin(phase) + 0.25 * math.sin(2 * phase) + 0.10 * math.sin(3 * phase)
        samples.append(s * env)

    write_wav(os.path.join(SOUNDS_DIR, "meow_talk.wav"), sample_rate, samples)

def generate_meow_happy():
    """Suara meong gembira bernada tinggi saat dielus atau diberi makan ikan."""
    sample_rate = 22050
    duration = 0.48
    num_samples = int(duration * sample_rate)
    samples = []
    phase = 0.0

    # Frekuensi ceria dengan getaran vibrato: 600Hz -> 960Hz -> 580Hz
    for i in range(num_samples):
        t = i / num_samples
        if t < 0.40:
            base_f = 600 + (960 - 600) * (t / 0.40)
        else:
            base_f = 960 - (960 - 580) * ((t - 0.40) / 0.60)

        # Vibrato halus
        vibrato = math.sin(2 * math.pi * 12 * (i / sample_rate)) * 18
        f = base_f + vibrato

        env = (math.sin(t * math.pi) ** 0.75) * (1.0 + 0.15 * math.sin(2 * math.pi * 6 * t))
        phase += 2 * math.pi * f / sample_rate
        s = 0.60 * math.sin(phase) + 0.30 * math.sin(2 * phase) + 0.10 * math.sin(4 * phase)
        samples.append(s * env)

    write_wav(os.path.join(SOUNDS_DIR, "meow_happy.wav"), sample_rate, samples)

def generate_meow_chirp():
    """Suara meong pendek riang (chirp/squeak) saat mendarat atau bangun tidur."""
    sample_rate = 22050
    duration = 0.22
    num_samples = int(duration * sample_rate)
    samples = []
    phase = 0.0

    # Nada cepat naik lalu turun singkat: 650Hz -> 1020Hz -> 750Hz
    for i in range(num_samples):
        t = i / num_samples
        if t < 0.35:
            f = 650 + (1020 - 650) * (t / 0.35)
        else:
            f = 1020 - (1020 - 750) * ((t - 0.35) / 0.65)

        env = math.sin(t * math.pi) ** 1.1
        phase += 2 * math.pi * f / sample_rate
        s = 0.70 * math.sin(phase) + 0.20 * math.sin(2 * phase) + 0.10 * math.sin(3 * phase)
        samples.append(s * env)

    write_wav(os.path.join(SOUNDS_DIR, "meow_chirp.wav"), sample_rate, samples)

def generate_meow_picked():
    """Suara meong kaget imut saat diangkat dengan kursor."""
    sample_rate = 22050
    duration = 0.32
    num_samples = int(duration * sample_rate)
    samples = []
    phase = 0.0

    # Nada naik penasaran kaget: 480Hz -> 880Hz
    for i in range(num_samples):
        t = i / num_samples
        f = 480 + (880 - 480) * (t ** 0.8)
        env = math.sin(t * math.pi) ** 0.8
        phase += 2 * math.pi * f / sample_rate
        s = 0.65 * math.sin(phase) + 0.25 * math.sin(2 * phase) + 0.10 * math.sin(3 * phase)
        samples.append(s * env)

    write_wav(os.path.join(SOUNDS_DIR, "meow_picked.wav"), sample_rate, samples)

def generate_meow_purr():
    """Suara mendengkur halus (purrr) saat santai."""
    sample_rate = 22050
    duration = 0.65
    num_samples = int(duration * sample_rate)
    samples = []
    phase = 0.0

    # Rhythmic low frequency purr pulse (25 Hz pulse on 110Hz base tone)
    for i in range(num_samples):
        t = i / num_samples
        pulse = (math.sin(2 * math.pi * 24 * t) + 1.0) * 0.5
        base_f = 110 + pulse * 35

        env = math.sin(t * math.pi) ** 0.6
        phase += 2 * math.pi * base_f / sample_rate
        s = (math.sin(phase) + 0.4 * math.sin(2 * phase) + 0.2 * math.sin(3 * phase)) * (0.4 + 0.6 * pulse)
        samples.append(s * env * 0.8)

    write_wav(os.path.join(SOUNDS_DIR, "meow_purr.wav"), sample_rate, samples)

def generate_meow_hiss():
    """Suara desis kaget/peringatan imut kucing saat ada kesalahan atau konflik angka."""
    sample_rate = 22050
    duration = 0.28
    num_samples = int(duration * sample_rate)
    samples = []
    import random
    for i in range(num_samples):
        t = i / num_samples
        env = math.sin(t * math.pi) ** 1.3
        # Campuran desis lembut dan nada frekuensi kucing
        noise = (random.random() * 2.0 - 1.0) * 0.35
        f = 420 + (260 - 420) * t
        phase = 2 * math.pi * f * t
        s = 0.35 * math.sin(phase) + noise
        samples.append(s * env * 0.5)

    write_wav(os.path.join(SOUNDS_DIR, "meow_hiss.wav"), sample_rate, samples)

def generate_all_sounds():
    """Menghasilkan seluruh file audio efek suara kucing."""
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    generate_meow_talk()
    generate_meow_happy()
    generate_meow_chirp()
    generate_meow_picked()
    generate_meow_purr()
    generate_meow_hiss()
    print("[Audio Selesai] Seluruh suara kucing berhasil dibuat!")

if __name__ == "__main__":
    generate_all_sounds()
