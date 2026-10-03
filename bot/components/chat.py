"""Реакции на обычные (не командные) сообщения + логирование чата в БД."""
from __future__ import annotations

import random

import twitchio
from twitchio.ext import commands

from bot import config
from bot.components.base import BaseComponent, whitelisted
from bot.data.some_data import byes, custom_copypast_cmd, hellos
from bot.text_utils import first_token


class ChatComponent(BaseComponent):
    @commands.Component.listener()
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        if payload.source_broadcaster is not None:  # дубликат из shared chat
            return
        bot = self.bot
        broadcaster = payload.broadcaster
        # Логируем все сообщения, включая сообщения самого бота (как и раньше)
        await bot.db.log_message(payload.text, int(payload.chatter.id), payload.chatter.display_name,
                                 int(broadcaster.id), broadcaster.name)
        if payload.chatter.id == bot.bot_id or payload.text.startswith(config.PREFIX):
            return

        text = payload.text
        word = first_token(text)

        if word in custom_copypast_cmd and broadcaster.name in config.ALLOW_FLOOD:
            await bot.say(broadcaster, word)
        elif word in hellos:
            await bot.say(broadcaster, random.choice(hellos), reply_to=payload.id)
        elif word in byes:
            await bot.say(broadcaster, random.choice(byes), reply_to=payload.id)
        elif f"@{bot.bot_login}" in text.lower():
            reply = await bot.db.random_message_of_ogey_or_streamer(int(broadcaster.id))
            await bot.say(broadcaster, reply or "Сообщений пока нет", reply_to=payload.id)
        elif payload.chatter.name == "moobot":
            await bot.say(broadcaster, "Мубот соси", reply_to=payload.id)

    # ---- включение/отключение команд в канале ----
    @commands.command(name="отбой")
    @whitelisted()
    async def sleep(self, ctx: commands.Context) -> None:
        self.bot.muted_channels.add(ctx.broadcaster.name)
        await ctx.reply("Я спать ppSleep")

    @commands.command(name="подъём")
    @whitelisted()
    async def wake(self, ctx: commands.Context) -> None:
        if ctx.broadcaster.name in self.bot.muted_channels:
            self.bot.muted_channels.discard(ctx.broadcaster.name)
            await ctx.reply("Я проснулся AYAYASleepy")
        else:
            await ctx.reply("Я и не спал roflanTanec")
