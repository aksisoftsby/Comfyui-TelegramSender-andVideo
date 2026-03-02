import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

OUTPUT_FOLDER = "/root/ComfyUI/output"          # sesuaikan kalau beda
BOT_TOKEN = "ISI_BOT_TOKEN_KAMU"
CHAT_ID = "ISI_CHAT_ID_KAMU"

def send_to_telegram(file_path):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}"
        with open(file_path, "rb") as f:
            files = {"document": (os.path.basename(file_path), f)}
            r = requests.post(
                url + "/sendDocument",
                data={"chat_id": CHAT_ID},
                files=files,
                timeout=25
            )
            print(file_path, "→", r.status_code, r.text[:100])
    except Exception as e:
        print("Gagal kirim:", file_path, str(e))

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory: return
        time.sleep(3)  # kasih napas dulu
        if os.path.exists(event.src_path):
            print("New file:", event.src_path)
            send_to_telegram(event.src_path)

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_FOLDER):
        print(f"Folder tidak ditemukan: {OUTPUT_FOLDER}")
    else:
        observer = Observer()
        observer.schedule(Handler(), OUTPUT_FOLDER, recursive=False)
        observer.start()
        print(f"Memantau: {OUTPUT_FOLDER}")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()