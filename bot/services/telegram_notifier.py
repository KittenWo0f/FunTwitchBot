"""Уведомления администратору в Telegram (python-telegram-bot >= 20)."""
from __future__ import annotations

import logging
import os

from telegram import Bot
from telegram.error import TelegramError

log = logging.getLogger(__name__)
_SENDERS = {"photo": ("send_photo", "photo"), "audio": ("send_audio", "audio"),
            "video": ("send_video", "video"), "document": ("send_document", "document")}


class TelegramAdminNotifier:
    def __init__(self, bot_token: str, admin_chat_id: str | int) -> None:
        self._bot = Bot(token=bot_token)
        self._chat_id = admin_chat_id

    async def send_message(self, text: str, parse_mode: str | None = None) -> bool:
        try:
            await self._bot.send_message(chat_id=self._chat_id, text=text, parse_mode=parse_mode)
            return True
        except TelegramError as e:
            log.error("Ошибка отправки сообщения в Telegram: %s", e)
            return False

    async def send_file(self, file_path: str, caption: str | None = None,
                        file_type: str = "document", timeout: int = 600) -> bool:
        if not os.path.exists(file_path):
            log.error("Файл не найден: %s", file_path)
            return False
        method, arg = _SENDERS.get(file_type, _SENDERS["document"])
        try:
            with open(file_path, "rb") as fh:
                await getattr(self._bot, method)(
                    chat_id=self._chat_id, caption=caption, read_timeout=timeout,
                    write_timeout=timeout, connect_timeout=timeout, pool_timeout=timeout, **{arg: fh})
            return True
        except (TelegramError, OSError) as e:
            log.error("Ошибка отправки файла в Telegram: %s", e)
            return False
