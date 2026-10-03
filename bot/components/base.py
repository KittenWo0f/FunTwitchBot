from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from twitchio.ext import commands

from bot import config
from bot.text_utils import split_message

if TYPE_CHECKING:
    from bot.core import TwitchBot


class BaseComponent(commands.Component):
    def __init__(self, bot: "TwitchBot") -> None:
        self.bot = bot


async def reply_chunks(ctx: commands.Context, text: str, delay: float = 2.0) -> None:
    """Отправляет длинный текст несколькими ответами с паузой (антиспам Twitch)."""
    for i, chunk in enumerate(split_message(text)):
        if i:
            await asyncio.sleep(delay)
        await ctx.reply(chunk)


def whitelisted():
    """Guard: команда доступна только пользователям из white_list."""
    return commands.guard(lambda ctx: ctx.chatter.name.lower() in config.WHITE_LIST)


def login_arg(value: str) -> str:
    return value.lstrip("@").lower()


def chat_cooldown(per: int, key: commands.BucketType = commands.BucketType.channel):
    return commands.cooldown(rate=1, per=per, key=key)
