class TelegramSenderVideo:

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "video": ("VIDEO",),
                "chat_id": ("STRING", {"default": ""}),
                "bot_token": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_video"
    CATEGORY = "tools"

    def send_video(self, video, chat_id, bot_token):

        video_path = video  # biasanya sudah berupa path file

        with open(video_path, "rb") as f:
            url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
            files = {"video": f}
            data = {"chat_id": chat_id}
            requests.post(url, data=data, files=files)

        return ()
