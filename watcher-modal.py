import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ======================
# CONFIG
# ======================

OUTPUT_FOLDER = "/root/ComfyUI/output"
BOT_TOKEN = "ISI_BOT_TOKEN_KAMU"
CHAT_ID = "ISI_CHAT_ID_KAMU"

# ======================
# TELEGRAM SEND FUNCTION
# ======================

def send_to_telegram(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}"

    with open(file_path, "rb") as f:

        if ext in [".jpg", ".jpeg", ".png", ".webp"]:
            endpoint = "/sendPhoto"
            files = {"photo": f}

        elif ext in [".mp4", ".mov", ".mkv"]:
            endpoint = "/sendDocument"   # atau sendVideo kalau mau streaming
            files = {"document": f}

        else:
            endpoint = "/sendDocument"
            files = {"document": f}

        response = requests.post(
            url + endpoint,
            data={"chat_id": CHAT_ID},
            files=files
        )

        print("Sent:", file_path, response.status_code)


# ======================
# WATCHDOG HANDLER
# ======================

class ComfyOutputHandler(FileSystemEventHandler):

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path

        # Tunggu file selesai ditulis
        time.sleep(2)

        if os.path.exists(file_path):
            print("New file detected:", file_path)
            send_to_telegram(file_path)


# ======================
# START WATCHER
# ======================

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(ComfyOutputHandler(), OUTPUT_FOLDER, recursive=False)
    observer.start()

    print("Watching folder:", OUTPUT_FOLDER)

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()