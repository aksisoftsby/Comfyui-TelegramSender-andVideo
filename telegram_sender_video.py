import requests
import os
from io import BytesIO

# Tambahkan import ini kalau belum (biasanya sudah ada di ComfyUI context)
try:
    from comfy_api.latest._input_impl.video_types import VideoFromFile
except ImportError:
    VideoFromFile = None  # fallback kalau belum support

class TelegramSenderVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("VIDEO",),
                "chat_id": ("STRING", {"default": ""}),
                "bot_token": ("STRING", {"default": ""}),
            },
            "optional": {
                "caption": ("STRING", {"default": "", "multiline": True}),
                "supports_streaming": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "send_video"
    CATEGORY = "tools"
    OUTPUT_NODE = True

    def send_video(self, video, chat_id, bot_token, caption="", supports_streaming=True):
        if not bot_token or not chat_id:
            return ("❌ bot_token atau chat_id kosong",)

        try:
            # --- Handle berbagai tipe VIDEO input ---
            if isinstance(video, str):  # plain path (legacy/old workflow)
                if not os.path.isfile(video):
                    return (f"❌ File tidak ditemukan: {video}",)
                video_file = open(video, "rb")
                filesize_mb = os.path.getsize(video) / (1024**2)

            elif VideoFromFile and isinstance(video, VideoFromFile):  # ComfyUI modern VideoFromFile
                video_file = video  # VideoFromFile sendiri file-like (punya .read(), dll)
                # Coba cek ukuran kalau bisa (tidak semua support len/seek)
                try:
                    video_file.seek(0, os.SEEK_END)
                    filesize_mb = video_file.tell() / (1024**2)
                    video_file.seek(0)
                except:
                    filesize_mb = "?"  # tidak bisa cek size

            elif isinstance(video, BytesIO):  # kalau suatu saat bytes langsung
                video_file = video
                filesize_mb = len(video.getvalue()) / (1024**2)

            else:
                return (f"❌ Tipe video tidak didukung: {type(video).__name__}",)

            # Cek size (kalau bisa)
            if filesize_mb != "?" and filesize_mb > 50:
                if hasattr(video_file, 'close'):
                    video_file.close()
                return (f"❌ Video terlalu besar ({filesize_mb:.1f} MB) – Telegram bot max 50 MB.",)

            url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
            files = {"video": video_file}  # VideoFromFile bisa langsung dipakai di requests.files
            data = {
                "chat_id": chat_id,
                "supports_streaming": str(supports_streaming).lower(),
            }
            if caption:
                data["caption"] = caption[:1024]

            # Kirim request (timeout lebih panjang biar aman)
            r = requests.post(url, data=data, files=files, timeout=120)

            if r.status_code == 200:
                resp = r.json()
                if resp.get("ok"):
                    msg = f"✅ Terkirim (msg_id: {resp['result']['message_id']})"
                    if filesize_mb != "?":
                        msg += f" | size: {filesize_mb:.1f} MB"
                    return (msg,)
                else:
                    return (f"❌ Telegram API error: {resp.get('description')}",)
            else:
                return (f"❌ HTTP {r.status_code}: {r.text[:300]}",)

        except Exception as e:
            return (f"❌ Error: {str(e)}",)

        finally:
            # Close hanya kalau punya method close DAN bukan VideoFromFile (karena VF manage sendiri)
            if hasattr(video_file, 'close') and not (VideoFromFile and isinstance(video_file, VideoFromFile)):
                video_file.close()