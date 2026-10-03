"""Статистика чата из БД."""
from __future__ import annotations

from twitchio.ext import commands

from bot.components.base import BaseComponent, chat_cooldown, login_arg
from bot.text_utils import fmt_num, plural_ru

_MONTH_HOURS_MIN = 1.0


def _hours_since_month_start() -> float:
    import datetime as dt
    now = dt.datetime.now()
    return max((now - now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 3600,
               _MONTH_HOURS_MIN)


class StatsComponent(BaseComponent):
    # ----- топы -----
    async def _top(self, ctx: commands.Context, rows, title: str, tail: str, empty: str, fmt=fmt_num) -> None:
        if not rows:
            await ctx.reply(empty)
            return
        body = ", ".join(f"{name} ({fmt(cnt)})" for name, cnt in rows)
        await ctx.reply(f"{title}: {body} {tail}")

    @chat_cooldown(600)
    @commands.command(name="топ", aliases=["top"])
    async def top(self, ctx: commands.Context) -> None:
        rows = await self.bot.db.top_users_month(int(ctx.broadcaster.id))
        await self._top(ctx, rows, "Топ месяца по сообщениям", "PogChamp", "Не найдены сообщения для топа NotLikeThis")

    @commands.cooldown(rate=1, per=30, key=commands.BucketType.chatter)
    @commands.command(name="ogeyofday", aliases=["огейдня", "ogeyoftheday"])
    async def ogey_of_day(self, ctx: commands.Context) -> None:
        from bot import config
        if ctx.broadcaster.name not in config.OGEY_OF_DAY_CHANNELS:
            return
        name = await self.bot.db.current_ogey(int(ctx.broadcaster.id))
        await ctx.reply(f"Ogey дня сегодня {name}, можно только позавидовать этому чатеру EZ Clap" if name
                        else "Ogey дня не определен PoroSad")

    @chat_cooldown(600)
    @commands.command(name="ogeysofmonth", aliases=["огеимесяца", "ogeysofthemonth"])
    async def ogeys_of_month(self, ctx: commands.Context) -> None:
        rows = await self.bot.db.top_ogeys_month(int(ctx.broadcaster.id))
        await self._top(ctx, rows, "Топ Ogey месяца", "KappaPride", "Не найдены сообщения для топа огеев NotLikeThis")

    @chat_cooldown(600)
    @commands.command(name="topogeys", aliases=["топогеев"])
    async def top_ogeys(self, ctx: commands.Context) -> None:
        rows = await self.bot.db.top_ogeys_all(int(ctx.broadcaster.id))
        await self._top(ctx, rows, "Топ Ogey за всё время", "KappaPride", "Не найдены сообщения для топа огеев NotLikeThis")

    @commands.cooldown(rate=1, per=300, key=commands.BucketType.user)
    @commands.command(name="топдоносчиков")
    async def top_denunciations(self, ctx: commands.Context) -> None:
        rows = await self.bot.db.top_denunciations()
        await self._top(ctx, rows, "Топ доносчиков", "POLICE", "Не найдены сообщения для топа доносчиков NotLikeThis",
                        fmt=lambda n: f"{n:,}")

    # ----- счётчики -----
    @commands.cooldown(rate=1, per=30, key=commands.BucketType.user)
    @commands.command(name="скольконасрал")
    async def how_much(self, ctx: commands.Context, target: str | None = None) -> None:
        if await self.bot.is_stream_online(ctx.broadcaster.id):
            return
        name = login_arg(target) if target else ctx.chatter.name
        count = await self.bot.db.user_month_count(int(ctx.broadcaster.id), name)
        if not count:
            await ctx.reply("Не удалось подсчитать сообщения запрошенного пользователя NotLikeThis.")
            return
        word = plural_ru(count, "сообщение", "сообщения", "сообщений")
        await ctx.reply(f"В этом месяце {name} написал в чате {fmt_num(count)} {word}, "
                        f"скорость: {count / _hours_since_month_start():.2f} с/ч PogChamp")

    @chat_cooldown(300)
    @commands.command(name="всегонасрано")
    async def total(self, ctx: commands.Context) -> None:
        count = await self.bot.db.channel_month_count(int(ctx.broadcaster.id))
        await ctx.reply(f"В этом месяце в чате насрали {count:,} сообщений SHTO" if count
                        else "Не удалось подсчитать количество написанных сообщений NotLikeThis")

    @chat_cooldown(60)
    @commands.command(name="маления")
    async def malenia(self, ctx: commands.Context) -> None:
        count = await self.bot.db.malenia_count(int(ctx.broadcaster.id))
        await ctx.reply(f"В этом чате вспомнили Малению {count:,} раз MaleniaTime" if count
                        else "Не удалось подсчитать упоминаний малений в этом чате NotLikeThis")

    # ----- по пользователю -----
    @chat_cooldown(20)
    @commands.command(name="подсчёт")
    async def word_count(self, ctx: commands.Context, target: str, word: str) -> None:
        login = login_arg(target)
        count = await self.bot.db.word_count(int(ctx.broadcaster.id), login, word)
        if count is None:
            await ctx.reply("Не удалось подсчитать упоминания NotLikeThis")
        elif count == 0:
            await ctx.reply(f"Пользователь @{login} ни разу не написал «{word}» в этом чате.")
        else:
            await ctx.reply(f"Пользователь @{login} написал «{word}» {count:,} раз(а) в этом чате.")

    @chat_cooldown(30)
    @commands.command(name="firstmessage")
    async def first_message(self, ctx: commands.Context, target: str) -> None:
        login = login_arg(target)
        result = await self.bot.db.first_message(int(ctx.broadcaster.id), login)
        if not result:
            await ctx.reply(f"Не нашёл ни одного сообщения от @{login} в этом чате NotLikeThis")
            return
        message, ts = result
        preview = message[:80] + "…" if len(message) > 80 else message
        await ctx.reply(f"Первое сообщение @{login} от {ts:%d.%m.%Y}: {preview}")

    @chat_cooldown(30)
    @commands.command(name="когда")
    async def since(self, ctx: commands.Context, target: str) -> None:
        login = login_arg(target)
        days = await self.bot.db.days_in_channel(int(ctx.broadcaster.id), login)
        if days is None:
            await ctx.reply(f"Не нашёл @{login} в этом чате NotLikeThis")
            return
        await ctx.reply(f"@{login} пишет в этом чате уже {days:,} {plural_ru(days, 'день', 'дня', 'дней')} PogChamp")

    @chat_cooldown(30)
    @commands.command(name="активность")
    async def activity(self, ctx: commands.Context, target: str) -> None:
        login = login_arg(target)
        result = await self.bot.db.activity(int(ctx.broadcaster.id), login)
        if not result:
            await ctx.reply(f"Не удалось получить активность @{login} NotLikeThis")
            return
        await ctx.reply(f"Активность @{login}: за 7 дней — {result[0]:,} сообщ., за 30 дней — {result[1]:,} сообщ.")

    @chat_cooldown(15)
    @commands.command(name="рандом")
    async def random_message(self, ctx: commands.Context, target: str) -> None:
        login = login_arg(target)
        message = await self.bot.db.random_message_by_login(int(ctx.broadcaster.id), login)
        await ctx.reply(f"@{login} однажды написал: {message}" if message
                        else f"Не нашёл сообщений от @{login} в этом чате NotLikeThis")

    @chat_cooldown(30)
    @commands.command(name="мертвец")
    async def silent_days(self, ctx: commands.Context, target: str) -> None:
        login = login_arg(target)
        days = await self.bot.db.silence_days(int(ctx.broadcaster.id), login)
        if days is None:
            await ctx.reply(f"Не нашёл @{login} в этом чате NotLikeThis")
        elif days == 0:
            await ctx.reply(f"@{login} писал сегодня, живой пока что PogChamp")
        else:
            await ctx.reply(f"@{login} молчит уже {days:,} {plural_ru(days, 'день', 'дня', 'дней')} monkaHmm")

    @chat_cooldown(30)
    @commands.command(name="сосед")
    async def neighbor(self, ctx: commands.Context) -> None:
        result = await self.bot.db.chat_neighbor(int(ctx.broadcaster.id), int(ctx.chatter.id))
        if not result:
            await ctx.reply(f"Не удалось найти соседа @{ctx.chatter.name} в этом чате NotLikeThis")
            return
        name, count = result
        await ctx.reply(f"Сосед @{ctx.chatter.name} по чату — {name} "
                        f"({count:,} {plural_ru(count, 'раз', 'раза', 'раз')} писал рядом) PogChamp")

    @chat_cooldown(30)
    @commands.command(name="любимоеслово")
    async def favorite_word(self, ctx: commands.Context, target: str) -> None:
        login = login_arg(target)
        result = await self.bot.db.favorite_word(int(ctx.broadcaster.id), login)
        if not result:
            await ctx.reply(f"Не удалось найти любимое слово @{login} в этом чате NotLikeThis")
            return
        word, count = result
        await ctx.reply(f"Любимое слово @{login} — {word} ({count:,} {plural_ru(count, 'раз', 'раза', 'раз')}) PogChamp")

    @chat_cooldown(30)
    @commands.command(name="процент")
    async def word_percent(self, ctx: commands.Context, target: str, word: str) -> None:
        login = login_arg(target)
        pct = await self.bot.db.word_percentage(int(ctx.broadcaster.id), login, word)
        await ctx.reply(f"{pct:g}% сообщений @{login} содержат слово {word}" if pct is not None
                        else f"Не удалось подсчитать для @{login} NotLikeThis")

    @commands.cooldown(rate=1, per=10, key=commands.BucketType.user)
    @commands.command(name="lastseen", aliases=["когдавидели"])
    async def last_seen(self, ctx: commands.Context, target: str | None = None) -> None:
        if target:
            users = await self.bot.fetch_users(logins=[login_arg(target)])
            if not users:
                await ctx.reply("Что-то пошло не так. Проверьте имя искомого пользователя eeeh")
                return
            user_id, name = int(users[0].id), users[0].name
        else:
            user_id, name = int(ctx.broadcaster.id), ctx.broadcaster.name
        last = await self.bot.db.last_activity(int(ctx.broadcaster.id), user_id)
        await ctx.reply(f"В последний раз {name} видели в чате {last:%d.%m.%Y в %H:%M:%S} CoolStoryBob" if last
                        else f"Я не помню когда в последний раз видел в чате {name} PoroSad")
