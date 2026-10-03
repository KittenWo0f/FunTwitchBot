"""Интерактивные команды чата: чмок, кусь, донос, ауф, привет, админу."""
from __future__ import annotations

import random

from twitchio.ext import commands

from bot.components.base import BaseComponent, chat_cooldown
from bot.data.some_data import auf_messages
from bot.text_utils import is_valid_args


def _clean(phrase: str) -> str:
    return "".join(c for c in phrase if c.isprintable())


class SocialComponent(BaseComponent):
    async def _random_chatter(self, ctx: commands.Context) -> str | None:
        """Раньше брали ctx.chatters из IRC; в 3.x список зрителей требует отдельного
        scope (moderator:read:chatters), поэтому берём недавних авторов из БД."""
        names = await self.bot.db.last_active_users(int(ctx.broadcaster.id))
        return random.choice(names) if names else None

    async def _targeted(self, ctx: commands.Context, phrase: str | None, *, verb: str, emote: str,
                        self_msg: str, bot_msg: str, empty_msg: str) -> None:
        """Общая логика !чмок и !кусь (работают только когда стрим офлайн)."""
        if await self.bot.is_stream_online(ctx.broadcaster.id):
            return
        me = ctx.chatter.name
        phrase = _clean(phrase) if phrase else ""
        if phrase:
            if not is_valid_args(phrase):
                await ctx.reply("Бана хочешь моего?")
            elif me in phrase.lower():
                await ctx.reply(self_msg.format(me=me))
            elif self.bot.bot_login in phrase.lower():
                await ctx.reply(bot_msg)
            else:
                await ctx.reply(f"@{me} {verb} {phrase} {emote}")
        elif (target := await self._random_chatter(ctx)):
            await ctx.reply(f"@{me} {verb} @{target} {emote}")
        else:
            await ctx.reply(empty_msg)

    @commands.cooldown(rate=1, per=10, key=commands.BucketType.chatter)
    @commands.command(name="чмок")
    async def chmok(self, ctx: commands.Context, *, phrase: str | None = None) -> None:
        await self._targeted(ctx, phrase, verb="чмокнул", emote="😘",
                             self_msg="@{me} боюсь что это нереально. Давай лучше я 😘",
                             bot_msg="И тебе чмок 😘", empty_msg="В этом чате некого чмокнуть PoroSad")

    @commands.cooldown(rate=1, per=10, key=commands.BucketType.chatter)
    @commands.command(name="кусь")
    async def kus(self, ctx: commands.Context, *, phrase: str | None = None) -> None:
        await self._targeted(ctx, phrase, verb="куснул", emote="peepoGiggles",
                             self_msg="@{me} странный ты eeeh", bot_msg="Stare",
                             empty_msg="В этом чате пусто PoroSad")

    @commands.cooldown(rate=1, per=10, key=commands.BucketType.user)
    @commands.command(name="ауф", aliases=["auf"])
    async def auf(self, ctx: commands.Context) -> None:
        await ctx.reply(random.choice(auf_messages))

    @chat_cooldown(7200)
    @commands.command(name="привет", aliases=["hello", "hi"])
    async def hello(self, ctx: commands.Context) -> None:
        if await self.bot.is_stream_online(ctx.broadcaster.id):
            return
        names = await self.bot.db.last_active_users(int(ctx.broadcaster.id))
        if not names:
            await ctx.reply("Я не знаю кто был в чате недавно. Поэтому привет всем KonCha")
            return
        await ctx.reply("Привет, " + " ".join(f"@{n}" for n in names) + " hi")

    @commands.cooldown(rate=1, per=30, key=commands.BucketType.user)
    @commands.command(name="донос")
    async def denunciation(self, ctx: commands.Context, *, phrase: str | None = None) -> None:
        if phrase and not is_valid_args(phrase):
            await ctx.reply("Бана хочешь моего?")
            return
        target = phrase or f"канал @{ctx.broadcaster.name}"
        await self.bot.db.add_denunciation(int(ctx.chatter.id))
        await ctx.reply(f"@{ctx.chatter.name}, донос на {target} был отправлен в соответствующие органы policeBear")

    @commands.cooldown(rate=1, per=10800, key=commands.BucketType.user)
    @commands.command(name="админу")
    async def to_admin(self, ctx: commands.Context, *, text: str) -> None:
        ok = await self.bot.notifier.send_message(f"{ctx.chatter.name} ({ctx.broadcaster.name}): {text}")
        await ctx.reply("Ваше сообщение было отправлено админу NOTED" if ok
                        else "Не удалось отправить ваше сообщение админу NotLikeThis")

    @chat_cooldown(10)
    @commands.command(name="год", aliases=["year", "прогресс"])
    async def year(self, ctx: commands.Context) -> None:
        import calendar
        import datetime as dt
        now = dt.datetime.now()
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        total = (365 + calendar.isleap(now.year)) * 86400
        await ctx.reply(f"@{ctx.chatter.name}, прогресс года: {(now - start).total_seconds() / total * 100:.10f}% catDespair")
