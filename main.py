import logging
from logging.handlers import RotatingFileHandler
from bot import twitch_bot
import sys

# Настройка логгера
logger = logging.getLogger()  # Получаем корневой логгер
logger.setLevel(logging.WARNING)  # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Создаём RotatingFileHandler
handler = RotatingFileHandler(
    'logs/bot.log',  # Имя файла
    maxBytes=1024 * 1024 * 10,  # Максимальный размер файла (10 МБ)
    backupCount=5,  # Количество сохраняемых старых файлов
    encoding='utf-8',
    mode='a'  # Режим записи ('a' — добавление)
)

# Формат сообщений
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(handler)

# Перенаправление stdout и stderr в логгер
class LoggerWriter:
    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message.strip():  # Игнорируем пустые строки
            self.level(message)

    def flush(self):
        pass

sys.stdout = LoggerWriter(logging.info)
sys.stderr = LoggerWriter(logging.error)
logging.critical(f'\n\n========================== Start bot ==========================\n LogLevel: {logging.getLevelName(logger.level)}\n')

try:
    bot = twitch_bot('twitch_bot')
    bot.run()
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)  # Логируем ошибку с traceback
    sys.exit(1)