from twitchio.ext import commands
import random
import datetime
import calendar
from utils.bot_utilities import *
from bot_settings import *

class StatsCommands(commands.Cog):
    """Класс для команд топа и статистики"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(rate=1, per=600, bucket=commands.Bucket.channel)
    @commands.command(name='топ', aliases=['top'])
    async def top(self, ctx: commands.Context):
        channel_user = await ctx.channel.user()
        top_users = self.bot.db_log_client.get_top_of_month_users(channel_user.id)
        if not top_users:
            await ctx.reply('Не найдены сообщения для топа NotLikeThis')
            return
        msg = f'Топ месяца по сообщениям:'
        for user_row in top_users:
            msg = f' {msg} {user_row[0]} ({format_with_apostrophe(user_row[1])}, {(user_row[1]/hours_from_mounth_begin()):.2f} с/ч),'
        msg = msg[:-1]
        msg = msg + ' PogChamp'
        await ctx.reply(msg)
    
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='ogeyofday', aliases=['огейдня', 'ogeyoftheday'])
    async def ogeyofday(self, ctx: commands.Context):
        if ctx.channel.name not in OGEY_OF_DAY_CHANNELS:
            return
        channel_user = await ctx.channel.user()
        ogey_name = self.bot.db_log_client.get_ogey(channel_user.id)
        if ogey_name != None:
            await ctx.reply(f'Ogey дня сегодня {ogey_name}, можно только позавидовать этому чатеру EZ Clap')
        else:
            await ctx.reply(f'Ogey дня не определен PoroSad')
    
    @commands.cooldown(rate=1, per=600, bucket=commands.Bucket.channel)
    @commands.command(name='ogeysofmonth', aliases=['огеимесяца', 'ogeysofthemonth'])
    async def ogeysofmonth(self, ctx: commands.Context):
        channel_user = await ctx.channel.user()
        top_ogeys = self.bot.db_log_client.get_top_of_month_ogey(channel_user.id)
        if not top_ogeys:
            await ctx.reply('Не найдены сообщения для топа огеев NotLikeThis')
            return
        msg = f'Топ Ogey месяца:'
        for user_row in top_ogeys:
            msg = f' {msg} {user_row[0]} ({format_with_apostrophe(user_row[1])}),'
        msg = msg[:-1]
        msg = msg + ' KappaPride'
        await ctx.reply(msg)
        
    @commands.cooldown(rate=1, per=600, bucket=commands.Bucket.channel)
    @commands.command(name='topogeys', aliases=['топогеев'])
    async def ogeystop(self, ctx: commands.Context):
        channel_user = await ctx.channel.user()
        top_ogeys = self.bot.db_log_client.get_top_ogeys(channel_user.id)
        if not top_ogeys:
            await ctx.reply('Не найдены сообщения для топа огеев NotLikeThis')
            return
        msg = f'Топ Ogey за всё время:'
        for user_row in top_ogeys:
            msg = f' {msg} {user_row[0]} ({format_with_apostrophe(user_row[1])}),'
        msg = msg[:-1]
        msg = msg + ' KappaPride'
        await ctx.reply(msg)
        
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.user)
    @commands.command(name='скольконасрал')
    async def skolkonasral(self, ctx: commands.Context, phrase: str | None):
        if await self.bot.is_stream_online(ctx.channel):
            return
        channel_user = await ctx.channel.user()
        if phrase:
            name = phrase.lstrip('@')
        else:
            name = ctx.author.name
        msg_count = self.bot.db_log_client.get_users_message_count_for_mounth_by_name(channel_user.id, name.lower())
        if not msg_count:
            await ctx.reply(f'Не удалось подсчитать сообщения запрошеного пользователя NotLikeThis.')
            return
        await ctx.reply(f"В этом месяце {name} написал в чате {format_with_apostrophe(msg_count)} {decl_of_num(msg_count, self.bot.msg_titles)}, скорость: {(msg_count/hours_from_mounth_begin()):.2f} с/ч PogChamp")
        
    @commands.cooldown(rate=1, per=300, bucket=commands.Bucket.channel)
    @commands.command(name='всегонасрано')
    async def vsegonasrano(self, ctx: commands.Context):
        channel_user = await ctx.channel.user()
        msg_count = self.bot.db_log_client.get_all_users_message_count_for_mounth(channel_user.id)
        if not msg_count:
            await ctx.reply(f'Не удалось подсчитать количество написаных сообщений NotLikeThis')
            return
        await ctx.reply(f"В этом месяце в чате насрали {msg_count:,} сообщений SHTO")
        
    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name='маления')
    async def malenia(self, ctx: commands.Context):
        channel_user = await ctx.channel.user()
        msg_count = self.bot.db_log_client.get_malenia_in_channel(channel_user.id)
        if not msg_count:
            await ctx.reply(f'Не удалось подсчитать упоминаний малений в этом чате NotLikeThis')
            return
        await ctx.reply(f"В этом чате вспомнили Малению {msg_count:,} раз MaleniaTime")
        
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command(name='год', aliases=['year', 'прогресс'])
    async def year(self, ctx: commands.Context):
        now = datetime.datetime.now()
        start_of_year = now.replace(day=1, month=1, year=now.year)
        days_passed = (now - start_of_year).days
        seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        await ctx.reply(f"@{ctx.author.name}, прогресс года: {(days_passed * 86400 + seconds_since_midnight) / ((365 + calendar.isleap(datetime.datetime.now().year)) * 86400) * 100:.10f}% catDespair")
        
    @commands.cooldown(rate=1, per=600, bucket=commands.Bucket.user)
    @commands.command(name='сосиска')
    async def sousage(self, ctx: commands.Context):
        length = random.randint(0, 30)
        emote = get_val_by_max_val({5: "PoroSad", 
                                    10: "Stare",
                                    15: "Hmm",
                                    20: "Hmmege",
                                    25: "SHTO",
                                    30: "EZ"}, length)
        await ctx.reply(f"@{ctx.author.name} имеет сосиску {length} см. {emote}")
        
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.user)
    @commands.command(name='донос')
    async def denunciation(self, ctx: commands.Context, *, phrase: str | None):
        if phrase:
            if not is_valid_args(phrase):
                await ctx.reply(f'Бана хочешь моего?')
                return
            else:
                donos_na = phrase
        else:
            donos_na = f'канал @{ctx.channel.name}'
        self.bot.db_log_client.add_denunciations_from_user(ctx.author.id)
        await ctx.reply(f"@{ctx.author.name}, донос на {donos_na} был отправлен в соответствующие органы policeBear")
        
    @commands.cooldown(rate=1, per=300, bucket=commands.Bucket.user)
    @commands.command(name='топдоносчиков')
    async def top_denunciations(self, ctx: commands.Context):
        top_denunciation_users = self.bot.db_log_client.get_top_denunciations_by_users()
        if not top_denunciation_users:
            await ctx.reply('Не найдены сообщения для топа доносчиков NotLikeThis')
            return
        msg = f'Топ доносчиков:'
        for user_row in top_denunciation_users:
            msg = f' {msg} {user_row[0]}({user_row[1]:,}),'
        msg = msg + ' POLICE'
        await ctx.reply(msg)