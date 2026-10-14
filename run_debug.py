import sys
import os
import traceback
import time

log_file = r"d:\Ngoding\17. Pet Asisten\run_debug.log"
def log(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    print(msg)

log("Starting debug run...")

try:
    PROJECT_ROOT = r"d:\Ngoding\17. Pet Asisten"
    SRC_DIR = os.path.join(PROJECT_ROOT, "src")
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    from PyQt5.QtCore import Qt, QCoreApplication, QTimer
    from PyQt5.QtWidgets import QApplication

    log("PyQt5 imported")

    from src.core.cat_audio import CatAudioEngine
    from src.core.ai_handler import AIHandler
    from src.ui.pet_window import CatPetWindow

    log("Modules imported")

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Virtual Pixel Cat AI Companion")
    log("QApplication created")

    audio = CatAudioEngine(enabled=True)
    log("Audio engine initialized")

    ai = AIHandler(
        api_key=os.getenv("GEMINI_API_KEY", ""),
        model_name=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        pet_name="Mimi"
    )
    log(f"AI Handler initialized: {ai.get_mode_status()}")

    pet_win = CatPetWindow(ai, audio, "Mimi")
    log(f"CatPetWindow created. Win pos: ({pet_win.x()}, {pet_win.y()})")

    pet_win.show()
    log("pet_win.show() called")

    # Keep alive for 10 seconds to monitor
    def tick():
        log(f"Tick - pos: ({pet_win.x()}, {pet_win.y()}), state: {pet_win.current_state}, visible: {pet_win.isVisible()}")

    t = QTimer()
    t.setInterval(2000)
    t.timeout.connect(tick)
    t.start()

    log("Entering app.exec_()...")
    app.exec_()
    log("app.exec_() exited cleanly")

except Exception as e:
    err = traceback.format_exc()
    log(f"FATAL ERROR:\n{err}")
