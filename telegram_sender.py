import os
import tempfile
import shutil
import json
from datetime import datetime
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import requests
import torch

# Jika environment punya ffmpeg-python atau imageio, bisa dipakai
# Di sini kita pakai cara paling sederhana → simpan frame dulu → ffmpeg via subprocess
import subprocess

class TelegramSender:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "video": ("VIDEO",),               # <- video tensor dari ComfyUI
                "chat_id": ("STRING", {"default": "", "multiline": False}),
                "bot_token": ("STRING", {"default": "", "multiline": False}),
                
                "enable_video": ("BOOLEAN", {"default": False}),
                "enable_image": ("BOOLEAN", {"default": True}),
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
                
                # Opsional: bisa ditambah kalau mau kontrol video quality
                "video_crf": ("INT", {"default": 23, "min": 0, "max": 51, "step": 1}),   # H.264 CRF (23 ≈ bagus & ukuran sedang)
            },
            "hidden": {"prompt": "PROMPT"},
        }

    RETURN_TYPES = ("STRING",)
    OUTPUT_NODE = True
    FUNCTION = "send_to_telegram"
    CATEGORY = "tools"

    def send_to_telegram(
        self, 
        images, 
        video,                      # tensor video
        chat_id, 
        bot_token, 
        enable_video,
        enable_image, 
        enable_text, 
        text,
        bold, 
        code, 
        disable_notification, 
        protect_content, 
        image_format,
        png_compress_level, 
        jpeg_quality, 
        webp_lossless, 
        webp_quality,
        video_crf,
        prompt
    ):
        if not (enable_video or enable_image or enable_text):
            return ["Nothing to send (all features disabled)"]

        temp_dir = tempfile.mkdtemp()
        cur_date = datetime.now().strftime('%d-%m-%Y-%H-%M-%S')
        counter = 0

        # ────────────────────────────────────────
        # 1. Prepare caption / text
        # ────────────────────────────────────────
        formatted_text = text
        if enable_text:
            if bold:
                formatted_text = f"**{formatted_text}**"
            if code:
                formatted_text = f"```{formatted_text}```"
        else:
            formatted_text = ""

        # ────────────────────────────────────────
        # 2. Kirim VIDEO jika di-enable
        # ────────────────────────────────────────
        if enable_video and video is not None and len(video) > 0:
            try:
                # Video tensor biasanya: [batch, frames, H, W, C]
                if video.dim() == 5:
                    video = video[0]  # ambil batch pertama

                frames = []
                for frame in video:
                    array = np.clip(255.0 * frame.cpu().numpy(), 0, 255).astype(np.uint8)
                    frames.append(Image.fromarray(array))

                # Simpan sementara sebagai sequence gambar
                frame_paths = []
                for i, img in enumerate(frames):
                    frame_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
                    img.save(frame_path)
                    frame_paths.append(frame_path)

                video_path = os.path.join(temp_dir, f"video_{cur_date}.mp4")

                # Pakai ffmpeg untuk encode (harus ada ffmpeg di sistem)
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-framerate", "24",                    # ← sesuaikan fps sesuai kebutuhan
                    "-i", os.path.join(temp_dir, "frame_%06d.png"),
                    "-c:v", "libx264",
                    "-crf", str(video_crf),
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    video_path
                ]

                subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

                # Kirim ke Telegram
                with open(video_path, "rb") as f:
                    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
                    data = {
                        "chat_id": chat_id,
                        "caption": formatted_text,
                        "parse_mode": "Markdown",
                        "disable_notification": disable_notification,
                        "protect_content": protect_content,
                        "supports_streaming": True,
                    }
                    files = {"video": (os.path.basename(video_path), f, "video/mp4")}
                    response = requests.post(url, data=data, files=files)
                    response.raise_for_status()

                counter += 1

            except Exception as e:
                print(f"Error sending video: {str(e)}")
                # lanjut saja ke image/text (tidak raise)

        # ────────────────────────────────────────
        # 3. Kirim IMAGE jika di-enable
        # ────────────────────────────────────────
        if enable_image and images is not None:
            for image in images:
                try:
                    array = np.clip(255.0 * image.cpu().numpy(), 0, 255).astype(np.uint8)
                    img = Image.fromarray(array)

                    file_name = f"ComfyUI_{cur_date}_{counter}.{image_format.lower()}"
                    file_path = os.path.join(temp_dir, file_name)

                    img_params = {
                        "PNG": {"compress_level": png_compress_level},
                        "JPEG": {"quality": jpeg_quality, "optimize": True},
                        "WebP": {"lossless": webp_lossless, "quality": webp_quality},
                        "GIF": {},
                        "TIFF": {},
                    }

                    save_kwargs = img_params.get(image_format, {})
                    img.save(file_path, **save_kwargs)

                    with open(file_path, "rb") as f:
                        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                        data = {
                            "chat_id": chat_id,
                            "caption": formatted_text if counter == 0 else "",  # caption hanya di foto pertama
                            "parse_mode": "Markdown",
                            "disable_notification": disable_notification,
                            "protect_content": protect_content,
                        }
                        files = {"photo": f}
                        response = requests.post(url, data=data, files=files)
                        response.raise_for_status()

                    counter += 1

                except Exception as e:
                    print(f"Error sending image: {str(e)}")

        # ────────────────────────────────────────
        # 4. Kirim TEXT saja (jika tidak ada media)
        # ────────────────────────────────────────
        if enable_text and counter == 0:
            try:
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
            except Exception as e:
                print(f"Error sending text: {str(e)}")

        shutil.rmtree(temp_dir, ignore_errors=True)

        return [f"Telegram message sent successfully ({counter} media sent)"]