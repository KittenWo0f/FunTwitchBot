"""Класс бота на TwitchIO 3.x.

Главные отличия от 2.x:
  * IRC удалён — сообщения чата приходят через EventSub (channel.chat.message), на каждый
    канал нужна подписка (см. setup_hook);
  * нужны client_id/client_secret и числовые id бота/владельца;
  * команды живут в Component'ах; вместо ctx.author / ctx.channel используются
    ctx.chatter / ctx.broadcaster; бакеты кулдаунов — commands.BucketType.
"""
from __future__ import annotations

import asyncio
import logging
import time

import aiohttp
import twitchio
from twitchio import eventsub
from twitchio.ext import commands

from bot import config
from bot.context import BotContext
from bot.db import Database
from bot.messages import USAGE
from bot.services.telegram_notifier import TelegramAdminNotifier

log = logging.getLogger(__name__)
_ONLINE_TTL = 30.0  # сек: кэш статуса стрима, чтобы не дёргать API на каждую команду


class TwitchBot(commands.Bot):
    def __init__(self, db: Database, notifier: TelegramAdminNotifier) -> None:
        super().__init__(
            client_id=config.CLIENT_ID,
            client_secret=config.CLIENT_SECRET,
            bot_id=config.BOT_ID,
            owner_id=config.OWNER_ID,
            prefix=config.PREFIX,
        )
        self.db = db
        self.notifier = notifier
        self.session: aiohttp.ClientSession | None = None
        self.bot_login: str = ""
        self.channels: dict[str, str] = {}        # login -> broadcaster id
        self.muted_channels: set[str] = set()     # каналы, где команды отключены (!отбой)
        self._online_cache: dict[str, tuple[float, bool]] = {}

    # ---------- запуск ----------
    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        await asyncio.to_thread(self.db.connect)

        # Токены: файл .tio.tokens.json содержит самые свежие (после автообновления),
        # поэтому токены из настроек добавляем только при первом запуске.
        if self.bot_id not in self.tokens and config.ACCESS_TOKEN and config.REFRESH_TOKEN:
            await self.add_token(config.ACCESS_TOKEN, config.REFRESH_TOKEN)

        me = (await self.fetch_users(ids=[self.bot_id]))[0]
        self.bot_login = me.name

        users = await self.fetch_users(logins=config.INITIAL_CHANNELS)
        self.channels = {u.name: u.id for u in users}
        for missing in set(config.INITIAL_CHANNELS) - set(self.channels):
            log.warning("Канал %s не найден", missing)

        # Компоненты (импорт здесь — чтобы избежать циклических импортов)
        from bot.components import ALL_COMPONENTS
        for cls in ALL_COMPONENTS:
            await self.add_component(cls(self))

        for user in users:
            await self.subscribe_websocket(
                eventsub.ChatMessageSubscription(broadcaster_user_id=user.id, user_id=self.bot_id))
            log.info("Подписка на чат %s оформлена", user.name)

    async def event_ready(self) -> None:
        log.warning("Бот запущен как %s (id=%s), каналы: %s", self.bot_login, self.bot_id, ", ".join(self.channels))

    async def close(self, **options) -> None:
        if self.session:
            await self.session.close()
        self.db.close()
        await super().close(**options)

    # ---------- обработка сообщений ----------
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        # !отбой: в канале не работают никакие команды, кроме !подъём
        channel = payload.broadcaster.name
        if channel in self.muted_channels and not payload.text.startswith(f"{config.PREFIX}подъём"):
            return
        await super().event_message(payload)  # пропускает свои сообщения и вызывает process_commands

    async def event_command_error(self, payload: commands.CommandErrorPayload) -> None:
        ctx, err = payload.context, payload.exception
        if isinstance(err, commands.CommandOnCooldown):
            if not await self.is_stream_online(ctx.broadcaster.id):
                await ctx.reply(f'Команда "{ctx.command.name}" заряжается, ещё {int(err.remaining)} сек.')
            return
        if isinstance(err, (commands.MissingRequiredArgument, commands.BadArgument)):
            usage = USAGE.get(ctx.command.name)
            await ctx.reply(f"Неверный формат! Используй: {config.PREFIX}{usage}" if usage else "Неверный формат команды")
            return
        if isinstance(err, (commands.CommandNotFound, commands.GuardFailure)):
            return
        await super().event_command_error(payload)

    def get_context(self, payload, *, cls=None):
        return super().get_context(payload, cls=cls or BotContext)

    async def say(self, broadcaster: twitchio.PartialUser, text: str, *, reply_to: str | None = None) -> None:
        """Отправка сообщения от имени бота user-токеном (вне команд: рутины, реакции чата)."""
        await broadcaster.send_message(text, sender=self.bot_id, token_for=self.bot_id, reply_to_message_id=reply_to)

    # ---------- общие помощники ----------
    async def is_stream_online(self, broadcaster_id: str) -> bool:
        cached = self._online_cache.get(broadcaster_id)
        if cached and time.monotonic() - cached[0] < _ONLINE_TTL:
            return cached[1]
        streams = await self.fetch_streams(user_ids=[broadcaster_id], type="live")
        online = bool(streams)
        self._online_cache[broadcaster_id] = (time.monotonic(), online)
        return online
