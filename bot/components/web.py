"""Команды, ходящие во внешние сервисы: погода, курс, время, анекдоты, факты, гороскоп."""
from __future__ import annotations

import logging

import aiohttp
from twitchio.ext import commands

from bot.components.base import BaseComponent, chat_cooldown, reply_chunks
from bot.services import ai, http_scrapers as web

log = logging.getLogger(__name__)
_WIND = ["С", "ССВ", "СВ", "ВСВ", "В", "ВЮВ", "ЮВ", "ЮЮВ", "Ю", "ЮЮЗ", "ЮЗ", "ЗЮЗ", "З", "ЗСЗ", "СЗ", "ССЗ"]


class WebComponent(BaseComponent):
    @property
    def session(self) -> aiohttp.ClientSession:
        return self.bot.session  # type: ignore[return-value]

    @chat_cooldown(30)
    @commands.command(name="день")
    async def today(self, ctx: commands.Context) -> None:
        try:
            await ctx.reply(await web.today_holiday(self.session))
        except Exception:
            log.exception("holiday")
            await ctx.reply("Не удалось узнать, какой сегодня праздник PoroSad")

    @chat_cooldown(30, commands.BucketType.chatter)
    @commands.command(name="погода", aliases=["weather"])
    async def weather(self, ctx: commands.Context, *, city: str) -> None:
        try:
            status, data = await web.weather(self.session, city)
        except (aiohttp.ClientError, TimeoutError):
            await ctx.reply("Не удалось выполнить запрос погоды PoroSad")
            return
        if status == 404:
            await ctx.reply(f'Город "{city}" не найден PoroSad')
        elif status != 200:
            await ctx.reply(f"Ошибка получения данных о погоде (код: {status}) PoroSad")
        else:
            try:
                temp = data["main"]["temp"]
                smile = "Coldge" if temp <= 0 else "hell" if temp > 29 else "peepoPls"
                wind = _WIND[round(data["wind"].get("deg", 0) / 22.5) % 16]
                await ctx.reply(f'В {data["name"]} на данный момент {temp:.1f}°C. '
                                f'{data["weather"][0]["description"].capitalize()}. '
                                f'Ветер {wind} {data["wind"]["speed"]:.1f} м/с. {smile}')
            except (KeyError, IndexError):
                await ctx.reply("Ошибка обработки данных погоды PoroSad")

    @chat_cooldown(60)
    @commands.command(name="время", aliases=["time"])
    async def time(self, ctx: commands.Context, *, city: str) -> None:
        result = await web.current_time_in_city(self.session, city)
        await ctx.reply(f"В {city} сейчас {result} MadgeTime" if result
                        else "Не удалось узнать время в указанном месте PoroSad")

    @chat_cooldown(30)
    @commands.command(name="курс")
    async def kurs(self, ctx: commands.Context) -> None:
        try:
            await ctx.reply(f"1 USD = {await web.usd_rub(self.session):.2f} RUB GAGAGA")
        except Exception:
            log.exception("kurs")
            await ctx.reply("Не удалось получить курс доллара PoroSad")

    @chat_cooldown(60)
    @commands.command(name="анек", aliases=["кринж"])
    async def anek(self, ctx: commands.Context, *, topic: str | None = None) -> None:
        try:
            text = await (ai.joke(self.session, topic) if topic else web.random_anek(self.session))
            await reply_chunks(ctx, f'Зацените прикол: "{text}". Классно, да?')
        except Exception as e:
            log.exception("anek")
            await ctx.reply(f"Нейросеть умерла: {e} FeelsBadMan" if topic else "Анекдот не нашёлся FeelsBadMan")

    @chat_cooldown(10)
    @commands.command(name="факт", aliases=["fact"])
    async def fact(self, ctx: commands.Context, *, topic: str | None = None) -> None:
        try:
            text = await (ai.absurd_fact(self.session, topic) if topic else web.random_fact(self.session))
            await reply_chunks(ctx, f"{text or 'Факты кончились'} rockFact")
        except Exception as e:
            log.exception("fact")
            await ctx.reply(f"Нейросеть умерла: {e} rockFact" if topic else "Факт не нашёлся rockFact")

    @chat_cooldown(180)
    @commands.command(name="гороскоп", aliases=["prediction"])
    async def prediction(self, ctx: commands.Context, sign: str) -> None:
        try:
            text = await web.horoscope(self.session, sign)
        except Exception:
            log.exception("horoscope")
            text = None
        if text:
            await reply_chunks(ctx, text)
        else:
            await ctx.reply("Не удалось получить гороскоп по вашему запросу PoroSad")
