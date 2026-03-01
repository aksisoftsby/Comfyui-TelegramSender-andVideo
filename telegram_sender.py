import os
import tempfile
import shutil
import json
from datetime import datetime
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import requests

class TelegramSender:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "video": ("VIDEO",),  # ✅ TAMBAH VIDEO REQUIRED
                "chat_id": ("STRING", {"default": "", "multiline": False}),
                "bot_token": ("STRING", {"default": "", "multiline": False}),
                "enable_image": ("BOOLEAN", {"default": True}),
                "enable_video": ("BOOLEAN", {"default": False}),  # ✅ Toggle video
                "enable_text": ("BOOLEAN", {"default": False}),
                "text": ("STRING", {"default": "", "multiline": True}),
                "bold": ("BOOLEAN", {"default": False}),
                "code": ("BOOLEAN", {"default": False}),
                "disable_notification": ("BOOLEAN", {"default": False}),
                "protect_content": ("BOOLEAN", {"default": False}),
                "image_format": (["PNG", "JPEG", "WebP", "GIF", "TIFF"], {"default": "PNG"}),
                "png_compress_level": ("INT", {"default": 4, "min": 0, "max": 9, "step": 1}),
                "jpeg_quality": ("INT", {"default": 90, "min": 1, "max": 100, "step": 1}),
                "webp_lossless": ("BOOLEAN", {"default": False}),
                "webp_quality": ("INT", {"default": 90, "min": 1, "max": 100, "step": 1}),
            },
            "hidden": {"prompt": "PROMPT"},
        }

    RETURN_TYPES = ("STRING",)
    OUTPUT_NODE = True
    FUNCTION = "send_to_telegram"
    CATEGORY = "tools"

    def send_to_telegram(
        self, images, video, chat_id, bot_token,
        enable_image, enable_video, enable_text, text,
        bold, code, disable_notification, protect_content,
        image_format, png_compress_level, jpeg_quality,
        webp_lossless, webp_quality, prompt
    ):

        temp_dir = tempfile.mkdtemp()
        counter = 0
        cur_date = datetime.now().strftime('%d-%m-%Y-%H-%M-%S')

        # Format text
        if enable_text:
            formatted_text = text
            if bold:
                formatted_text = f"**{formatted_text}**"
            if code:
                formatted_text = f"```{text}```"
        else:
            formatted_text = ""

        # =====================
        # SEND IMAGE
        # =====================
        if enable_image:
            for image in images:
                array = np.clip(255.0 * image.cpu().numpy(), 0, 255).astype(np.uint8)
                img = Image.fromarray(array)

                metadata = PngInfo()
                metadata.add_text("prompt", json.dumps(prompt))

                file_name = f"ComfyUI_{cur_date}_{counter}.{image_format.lower()}"
                file_path = os.path.join(temp_dir, file_name)

                img_params = {
                    "PNG": {"compress_level": png_compress_level},
                    "JPEG": {"quality": jpeg_quality},
                    "WebP": {"lossless": webp_lossless, "quality": webp_quality},
                    "GIF": {},
                    "TIFF": {},
                }

                img.save(file_path, **img_params.get(image_format, {}))

                with open(file_path, "rb") as f:
                    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                    data = {
                        "chat_id": chat_id,
                        "caption": formatted_text,
                        "parse_mode": "Markdown",
                        "disable_notification": disable_notification,
                        "protect_content": protect_content,
                    }
                    files = {"photo": f}
                    response = requests.post(url, data=data, files=files)
                    response.raise_for_status()

                counter += 1

        # =====================
        # SEND VIDEO → sendDocument
        # =====================
        
        if enable_video and video is not None:

            # Kalau list ambil pertama
            if isinstance(video, list):
                video = video[0]

            # Ambil path dari object VideoFromFile
            if hasattr(video, "filename"):
                video_path = video.filename
            elif hasattr(video, "file"):
                video_path = video.file
            else:
                raise Exception("VIDEO input tidak memiliki attribute filename/file")

            with open(video_path, "rb") as f:
                url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                data = {
                    "chat_id": chat_id,
                    "caption": formatted_text,
                    "parse_mode": "Markdown",
                    "disable_notification": disable_notification,
                    "protect_content": protect_content,
                }
                files = {"document": f}
                response = requests.post(url, data=data, files=files)
                response.raise_for_status()

        # =====================
        # SEND TEXT ONLY
        # =====================
        if enable_text and not enable_image and not enable_video:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": formatted_text,
                "parse_mode": "Markdown",
                "disable_notification": disable_notification,
                "protect_content": protect_content,
            }
            response = requests.post(url, data=data)
            response.raise_for_status()

        shutil.rmtree(temp_dir)

        return ["Telegram message sent successfully"]