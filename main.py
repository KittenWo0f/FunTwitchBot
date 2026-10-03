import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import twitchio

from bot import config
from bot.core import TwitchBot
from bot.db import Database
from bot.services.telegram_notifier import TelegramAdminNotifier


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    file_handler = RotatingFileHandler("logs/bot.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    root.addHandler(file_handler)
    sys.excepthook = lambda *a: logging.critical("Необработанное исключение", exc_info=a)


def main() -> None:
    setup_logging()
    logging.critical("=== Start bot ===")
    db = Database(config.DB_HOST, config.DB_PORT, config.DB_NAME, config.DB_USER, config.DB_PASSWORD)
    notifier = TelegramAdminNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_ADMIN_CHAT_ID)
    bot = TwitchBot(db, notifier)
    # with_adapter=False: не поднимаем локальный OAuth-сервер (бот работает на headless RPi,
    # токены берутся из bot_settings.py и дальше автоматически обновляются/сохраняются)
    bot.run(with_adapter=False)


if __name__ == "__main__":
    main()
