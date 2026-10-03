"""Единая точка доступа к настройкам из bot_settings.py (не в git).

Отсутствующие необязательные настройки получают значения по умолчанию,
поэтому старый bot_settings.py продолжит работать после обновления.
"""
from __future__ import annotations

import bot_settings as _s

# --- Twitch (TwitchIO 3: нужен client_id/secret и id аккаунтов, а не только токен) ---
CLIENT_ID: str = _s.CLIENT_ID
CLIENT_SECRET: str = _s.CLIENT_SECRET
BOT_ID: str = str(_s.BOT_ID)  # числовой id аккаунта бота
OWNER_ID: str | None = str(getattr(_s, "OWNER_ID", "")) or None
ACCESS_TOKEN: str = getattr(_s, "ACCESS_TOKEN", "")
REFRESH_TOKEN: str = getattr(_s, "REFRESH_TOKEN", "")

PREFIX: str = getattr(_s, "PREFIX", "!")
INITIAL_CHANNELS: list[str] = [c.lower() for c in _s.INITIAL_CHANNELS]
ALLOW_URL: set[str] = set(getattr(_s, "ALLOW_URL", []))
ALLOW_FLOOD: set[str] = set(getattr(_s, "ALLOW_FLOOD", []))
OGEY_OF_DAY_CHANNELS: list[str] = [c.lower() for c in getattr(_s, "OGEY_OF_DAY_CHANNELS", [])]
WHITE_LIST: set[str] = {n.lower() for n in getattr(_s, "white_list", [])}

# --- БД ---
DB_HOST: str = _s.DB_HOST
DB_PORT: int = _s.DB_PORT
DB_NAME: str = _s.DB_NAME
DB_USER: str = _s.DB_USER
DB_PASSWORD: str = _s.DB_PASSWORD

# --- Внешние сервисы ---
TELEGRAM_BOT_TOKEN: str = getattr(_s, "TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID: int = getattr(_s, "TELEGRAM_ADMIN_CHAT_ID", 0)
OPENWEATHER_API_KEY: str = getattr(_s, "OPENWEATHER_API_KEY", "")
OPENROUTER_API_KEY: str = getattr(_s, "OPENROUTER_API_KEY", "")
OPENROUTER_MODEL: str = getattr(_s, "OPENROUTER_MODEL", "openai/gpt-oss-120b:free")

# --- Информационные команды: {имя_команды: {канал: сообщение}} ---
INFO_MESSAGES: dict[str, dict[str, str]] = {
    name: getattr(_s, name, {})
    for name in ("telegrams", "vks", "boostys", "donats", "memes", "steams", "vods")
}
