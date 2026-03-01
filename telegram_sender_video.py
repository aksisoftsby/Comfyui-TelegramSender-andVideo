import requests
import os

class TelegramSenderVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("VIDEO",),               # path str atau bytes
                "chat_id": ("STRING", {"default": ""}),
                "bot_token": ("STRING", {"default": ""}),
            },
            "optional": {
                "caption": ("STRING", {"default": "", "multiline": True}),
                "supports_streaming": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)               # mengembalikan status pesan
    RETURN_NAMES = ("status",)
    FUNCTION = "send_video"
    CATEGORY = "tools"
    OUTPUT_NODE = True

    def send_video(self, video, chat_id, bot_token, caption="", supports_streaming=True):
        if not bot_token or not chat_id:
            return ("❌ bot_token atau chat_id kosong",)

        # Handle video input
        if isinstance(video, str):           # path
            if not os.path.isfile(video):
                return (f"❌ File tidak ditemukan: {video}",)
            video_file = open(video, "rb")
            filesize_mb = os.path.getsize(video) / (1024 * 1024)
        else:
            # kalau suatu saat upstream kirim bytes
            from io import BytesIO
            video_file = BytesIO(video) if isinstance(video, bytes) else video
            filesize_mb = len(video) / (1024 * 1024) if isinstance(video, bytes) else "?"

        if filesize_mb != "?" and filesize_mb > 50:
            # video_file.close()
            return (f"❌ Video terlalu besar ({filesize_mb:.1f} MB). Telegram bot batas 50 MB.",)

        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
            files = {"video": video_file}
            data = {
                "chat_id": chat_id,
                "supports_streaming": str(supports_streaming).lower(),
            }
            if caption:
                data["caption"] = caption[:1024]  # Telegram batas caption 1024 char

            with video_file:  # auto close
                r = requests.post(url, data=data, files=files, timeout=90)

            if r.status_code == 200:
                resp = r.json()
                if resp.get("ok"):
                    return (f"✅ Video terkirim (message_id: {resp['result']['message_id']})",)
                else:
                    return (f"❌ Telegram error: {resp.get('description')}",)
            else:
                return (f"❌ HTTP {r.status_code}: {r.text[:200]}",)

        except requests.Timeout:
            return ("❌ Timeout – video terlalu besar / koneksi lambat",)
        except Exception as e:
            return (f"❌ Exception: {str(e)}",)
        finally:
            if 'video_file' in locals() and not video_file.closed:
                video_file.close()