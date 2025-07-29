from telegram import Bot, InputFile
from telegram.error import TelegramError
import logging
from typing import Union, Optional, BinaryIO
import os
import asyncio

class telegram_admin_notifier:
    def __init__(self, bot_token: str, admin_chat_id: Union[str, int]):
        """
        Асинхронный класс для отправки сообщений и файлов администратору в Telegram.
        
        :param bot_token: Токен бота (получить у @BotFather)
        :param admin_chat_id: ID чата администратора (узнать у @userinfobot)
        """
        self.bot = Bot(token=bot_token)
        self.admin_chat_id = admin_chat_id
        self.logger = logging.getLogger(__name__)

    async def send_message(self, text: str, parse_mode: Optional[str] = None) -> bool:
        """
        Асинхронно отправляет текстовое сообщение.
        
        :param text: Текст сообщения
        :param parse_mode: "MarkdownV2", "HTML" или None
        :return: True, если успешно, иначе False
        """
        try:
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=text,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            self.logger.error(f"Ошибка при отправке сообщения: {e}")
            return False

    async def send_file(
        self,
        file_path: str,
        caption: Optional[str] = None,
        file_type: str = "document",
        timeout: int = 600
    ) -> bool:
        """
        Асинхронно отправляет файл.
        
        :param file_path: Путь к файлу
        :param caption: Подпись к файлу
        :param file_type: "document", "photo", "audio", "video"
        :param timeout: Таймаут отправки в секундах (по умолчанию 30)
        :return: True, если успешно, иначе False
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Файл не найден: {file_path}")
            return False
        
        try:
            with open(file_path, 'rb') as file:
                input_file = InputFile(file)
                
                if file_type == "photo":
                    await self.bot.send_photo(
                        chat_id=self.admin_chat_id,
                        photo=input_file,
                        caption=caption,
                        write_timeout=timeout
                    )
                elif file_type == "audio":
                    await self.bot.send_audio(
                        chat_id=self.admin_chat_id,
                        audio=input_file,
                        caption=caption,
                        write_timeout=timeout
                    )
                elif file_type == "video":
                    await self.bot.send_video(
                        chat_id=self.admin_chat_id,
                        video=input_file,
                        caption=caption,
                        write_timeout=timeout
                    )
                else:  # document (по умолчанию)
                    await self.bot.send_document(
                        chat_id=self.admin_chat_id,
                        document=input_file,
                        caption=caption,
                        write_timeout=timeout
                    )
            return True
        except (TelegramError, IOError) as e:
            self.logger.error(f"Ошибка при отправке файла: {e}")
            return False