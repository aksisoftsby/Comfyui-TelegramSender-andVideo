from .telegram_sender import TelegramSender
from .telegram_sender_video import TelegramSenderVideo

NODE_CLASS_MAPPINGS = {
    "TelegramSender": TelegramSender,
    "TelegramSenderVideo": TelegramSenderVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TelegramSender": "Telegram Sender",
    "TelegramSenderVideo": "Telegram Sender Video",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
