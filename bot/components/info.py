"""Информационные команды: ссылки на соцсети и т.п. (данные берутся из bot_settings)."""
from __future__ import annotations

from twitchio.ext import commands

from bot import config
from bot.components.base import BaseComponent, reply_chunks


class InfoComponent(BaseComponent):
    async def _info(self, ctx: commands.Context, key: str) -> None:
        msg = config.INFO_MESSAGES.get(key, {}).get(ctx.broadcaster.name)
        if msg:
            await ctx.reply(msg)

    @commands.command(name="тг", aliases=["телеграм", "телега", "telegram", "tg"])
    async def telegram(self, ctx: commands.Context) -> None:
        await self._info(ctx, "telegrams")

    @commands.command(name="вконтакте", aliases=["вк", "vk", "vkontakte"])
    async def vkontakte(self, ctx: commands.Context) -> None:
        await self._info(ctx, "vks")

    @commands.command(name="бусти", aliases=["boosty", "кошка"])
    async def boosty(self, ctx: commands.Context) -> None:
        await self._info(ctx, "boostys")

    @commands.command(name="донат", aliases=["donat", "пожертвование"])
    async def donat(self, ctx: commands.Context) -> None:
        await self._info(ctx, "donats")

    @commands.command(name="мем", aliases=["меме", "meme"])
    async def meme(self, ctx: commands.Context) -> None:
        await self._info(ctx, "memes")

    @commands.command(name="стим", aliases=["steam", "игры"])
    async def steam(self, ctx: commands.Context) -> None:
        await self._info(ctx, "steams")

    @commands.command(name="записи", aliases=["vods"])
    async def vods(self, ctx: commands.Context) -> None:
        await self._info(ctx, "vods")

    @commands.command(name="смайлы", aliases=["7tv", "smiles", "emoji", "смайлики", "эмоуты"])
    async def special_smiles(self, ctx: commands.Context) -> None:
        if ctx.broadcaster.name in config.ALLOW_URL:
            await ctx.reply("Чтобы видеть и посылать крутые смайлы в чате устанавливайте расширение "
                            "для браузера по ссылке: https://7tv.app/")

    @commands.command(name="help", aliases=["commands", "команды", "помощь", "бот"])
    async def help_bot(self, ctx: commands.Context) -> None:
        names = sorted({cmd.name for cmd in self.bot.commands.values()})
        text = (f"@{ctx.chatter.name} Доступные команды: {', '.join(names)}" if names
                else f"@{ctx.chatter.name} У меня нет команд PoroSad")
        await reply_chunks(ctx, text)
