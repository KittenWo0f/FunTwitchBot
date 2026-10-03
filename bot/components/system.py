"""Служебные команды и фоновые рутины (Ogey дня, бэкап БД)."""
from __future__ import annotations

import datetime as dt
import logging
from os import path, remove

from twitchio.ext import commands, routines

from bot import config
from bot.components.base import BaseComponent, chat_cooldown, login_arg, whitelisted
from bot.text_utils import plural_ru

log = logging.getLogger(__name__)


def next_daily(hour: int, minute: int = 0) -> dt.datetime:
    """Ближайшее срабатывание «каждый день в hour:minute» (локальное время).
    В TwitchIO 3 параметр time у routine — момент первого запуска, далее раз в сутки."""
    now = dt.datetime.now().astimezone()
    first = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return first if first > now else first + dt.timedelta(days=1)


class SystemComponent(BaseComponent):
    async def component_load(self) -> None:
        self.ogey_of_day_routine.start()
        self.backup_db_routine.start()

    async def component_teardown(self) -> None:
        self.ogey_of_day_routine.cancel()
        self.backup_db_routine.cancel()

    # ---------- рутины ----------
    @routines.routine(time=next_daily(19, 0), wait_first=True)
    async def ogey_of_day_routine(self) -> None:
        for login in config.OGEY_OF_DAY_CHANNELS:
            channel_id = self.bot.channels.get(login)
            if channel_id is None:
                log.warning("Ogey дня: канал %s не подключён", login)
                continue
            broadcaster = self.bot.create_partialuser(channel_id, login)
            try:
                ogey_id = await self.bot.db.random_user_last_hours(int(channel_id), 24)
                if ogey_id is not None and await self.bot.db.set_ogey(int(channel_id), ogey_id):
                    user = (await self.bot.fetch_users(ids=[ogey_id]))[0]
                    text = (f"Ogey дня обновился. Им стал {user.display_name}, "
                            "можно только позавидовать этому чатеру EZ Clap")
                else:
                    text = "Не удалось определить нового Ogey. PoroSad"
                await self.bot.say(broadcaster, text)
            except Exception:  # исключение внутри routine вызывает повторные запуски — не пропускаем его наружу
                log.exception("Ogey дня: ошибка для канала %s", login)

    @routines.routine(time=next_daily(2, 0), wait_first=True)
    async def backup_db_routine(self) -> None:
        backup_path, message = await self.bot.db.backup("db_backups", 9)
        if backup_path:
            await self.bot.notifier.send_file(backup_path)
            if path.exists(backup_path):
                remove(backup_path)
        else:
            await self.bot.notifier.send_message(message)

    # ---------- команды ----------
    @commands.command(name="горячесть", aliases=["температура", "темп", "temp"])
    @whitelisted()
    async def temperature(self, ctx: commands.Context) -> None:
        try:
            from gpiozero import CPUTemperature  # есть только на Raspberry Pi
            await ctx.reply(f"Моя горячесть равна {CPUTemperature().temperature} градусам")
        except Exception:
            await ctx.reply("Датчик температуры недоступен PoroSad")

    @chat_cooldown(60)
    @commands.command(name="последнийстрим", aliases=["laststream"])
    async def last_stream(self, ctx: commands.Context, channel: str | None = None) -> None:
        if channel:
            users = await self.bot.fetch_users(logins=[login_arg(channel)])
            if not users:
                await ctx.reply(f"Не удалось найти канал: {channel} NotLikeThis")
                return
            user_id, name = users[0].id, users[0].name
        else:
            user_id, name = ctx.broadcaster.id, ctx.broadcaster.name
        videos = await self.bot.fetch_videos(user_id=user_id, type="archive", first=1)
        if not videos:
            await ctx.reply(f"У {name} нет недавних стримов или записи не сохраняются NotLikeThis")
            return
        video = videos[0]
        delta = dt.datetime.now(dt.timezone.utc) - video.created_at
        hours, rem = divmod(delta.seconds, 3600)
        minutes = rem // 60
        parts = []
        if delta.days:
            parts.append(f"{delta.days} {plural_ru(delta.days, 'день', 'дня', 'дней')}")
        if delta.days or hours:
            parts.append(f"{hours} {plural_ru(hours, 'час', 'часа', 'часов')}")
        parts.append(f"{minutes} {plural_ru(minutes, 'минуту', 'минуты', 'минут')}")
        await ctx.reply(f'Последний стрим на канале {name} был {", ".join(parts)} назад. '
                        f'Название: "{video.title}" weAreWaiting')
