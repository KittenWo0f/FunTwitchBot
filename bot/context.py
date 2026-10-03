"""Context, который всегда отправляет сообщения от имени бота (его user-токеном).

В TwitchIO 3 PartialUser.send_message без token_for использует app-токен, а для него
Twitch требует права модератора / scope channel:bot у стримера (ошибка 401).
С пользовательским токеном бота (user:write:chat) это не требуется.
"""
from __future__ import annotations

from twitchio.ext import commands


class BotContext(commands.Context):
    async def send(self, content: str, *, me: bool = False):
        text = (f"/me {content}" if me else content).strip()
        return await self.channel.send_message(sender=self.bot.bot_id, message=text, token_for=self.bot.bot_id)

    async def reply(self, content: str, *, me: bool = False):
        text = (f"/me {content}" if me else content).strip()
        return await self.channel.send_message(sender=self.bot.bot_id, message=text, token_for=self.bot.bot_id,
                                               reply_to_message_id=self._payload.id)
