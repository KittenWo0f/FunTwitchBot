# Бестолковый твич чат-бот
На [TwitchIO 3](https://twitchio.dev) для Raspberry Pi.

## Запуск
```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp bot_settings.py.sample bot_settings.py   # заполнить
python main.py
```

## Структура
```
main.py                     точка входа, логирование
bot/core.py                 TwitchBot: подписки EventSub, токены, обработка ошибок
bot/config.py               настройки из bot_settings.py (+значения по умолчанию)
bot/text_utils.py           чистые функции: склонения, разбиение сообщений, валидация
bot/messages.py             подсказки по формату команд
bot/db/repository.py        PostgreSQL (пул соединений, async-фасад)
bot/services/               внешние API: сайты, погода, OpenRouter, Telegram
bot/components/             команды по темам (chat, info, web, stats, games, social, system)
bot/data/                   тексты и списки (some_data, roll_data, regex_tests)
```

## Что нужно для работы TwitchIO 3
* Приложение на dev.twitch.tv: `CLIENT_ID`, `CLIENT_SECRET`; числовые `BOT_ID`, `OWNER_ID`.
* Токен бота со scope `user:read:chat user:write:chat user:bot`.
* Права модератора НЕ обязательны, пока бот работает с пользовательским токеном (user access token) со scope выше.
  Модератор или `channel:bot` от стримера нужны только при app access token (например, при переходе на Conduits/AutoBot), см. документацию Twitch (chat/irc-migration).

## TODO
- Описание БД (см. схему в проекте)
- Тесты на text_utils и SQL-запросы
