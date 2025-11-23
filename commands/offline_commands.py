from twitchio.ext import commands
import random
import datetime
from utils.bot_utilities import *
from data.some_data import *
from bot_settings import *

class OfflineCommands(commands.Cog):
    """Класс для команд, которые работают в оффлайн чате"""
    
    def __init__(self, bot):
        self.bot = bot

    #Команды под оффлайн чат 
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.member)
    @commands.command(name='чмок')
    async def chmok(self, ctx: commands.Context, phrase: str | None):
        if await self.bot.is_stream_online(ctx.channel):
            return
        if phrase:
            phrase = ''.join(c for c in phrase if c.isprintable())
        if phrase and len(phrase):
            if not is_valid_args(phrase):
                await ctx.reply(f'Бана хочешь моего?')
            elif ctx.author.name in phrase.lower():
                await ctx.reply(f'@{ctx.author.name} боюсь что это нереально. Давай лучше я 😘')
            elif self.bot.nick in phrase.lower():
                await ctx.reply(f'И тебе чмок 😘')
            else:
                await ctx.reply(f'@{ctx.author.name} чмокнул {phrase} 😘')
        elif len(ctx.chatters) == 0:
            await ctx.reply('В этом чате некого чмокнуть PoroSad')
        else:
            random_chatter = random.choice(tuple(ctx.chatters)).name
            await ctx.reply(f'@{ctx.author.name} чмокнул @{random_chatter} 😘')
                
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.member)
    @commands.command(name='лапочка')
    async def lapochka(self, ctx: commands.Context, phrase: str | None):
        if await self.bot.is_stream_online(ctx.channel):
            return
        if phrase:
            phrase = ''.join(c for c in phrase if c.isprintable())
        if phrase and len(phrase):
            if not is_valid_args(phrase):
                await ctx.reply(f'Бана хочешь моего?')
            elif ctx.author.name in phrase.lower():
                await ctx.reply(f'@{ctx.author.name} высокая самооценка это хорошо SeemsGood')
            elif self.bot.nick in phrase.lower():
                await ctx.reply(f'Ой спасибо bleedPurple')
            else:
                await ctx.reply(f'@{ctx.author.name} назвал лапочкой {phrase} <3')    
        elif len(ctx.chatters) == 0:
            await ctx.reply('В этом чате пусто PoroSad')
        else:
            random_chatter = random.choice(tuple(ctx.chatters)).name
            await ctx.reply(f'@{ctx.author.name} назвал лапочкой @{random_chatter} <3')

    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name='последнийстрим', aliases=['laststream'])
    async def last_stream(self, ctx: commands.Context, phrase: str | None):
        """Команда для проверки, когда канал последний раз был в эфире."""
        # Если канал не указан, используем текущий канал
        channel_name = ctx.channel.name
        if phrase and len(phrase):
            channel_name = phrase
                
        # Сначала получаем информацию о канале, чтобы узнать ID стримера
        headers = {
            "Client-ID": CLIENT_ID,
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
        
        # Получаем информацию о пользователе для получения ID стримера
        user_url = f"https://api.twitch.tv/helix/users?login={channel_name}"
        user_response = requests.get(user_url, headers=headers)
        
        if user_response.status_code != 200 or not user_response.json()["data"]:
            await ctx.reply(f"Не удалось найти канал: {channel_name} NotLikeThis")
            return
        
        broadcaster_id = user_response.json()["data"][0]["id"]
        
        # Получаем информацию о стриме для канала
        streams_url = f"https://api.twitch.tv/helix/channels?broadcaster_id={broadcaster_id}"
        streams_response = requests.get(streams_url, headers=headers)
        
        if streams_response.status_code != 200:
            await ctx.reply(f"Ошибка при получении данных о стриме: {streams_response.text} NotLikeThis")
            return
        
        # Получаем видео (прошлые трансляции), чтобы найти последний стрим
        videos_url = f"https://api.twitch.tv/helix/videos?user_id={broadcaster_id}&type=archive&first=1"
        videos_response = requests.get(videos_url, headers=headers)
        
        if videos_response.status_code != 200:
            await ctx.reply(f"Ошибка при получении данных о видео: {videos_response.text} NotLikeThis")
            return
        
        videos_data = videos_response.json()["data"]
        
        if not videos_data:
            await ctx.reply(f"У {channel_name} нет недавних стримов или записи не сохраняются NotLikeThis")
            return
        
        # Получаем самое свежее видео (стрим)
        latest_stream = videos_data[0]
        created_at = datetime.datetime.fromisoformat(latest_stream["created_at"].replace("Z", "+00:00"))
        
        # Форматируем разницу во времени
        now = datetime.datetime.now(datetime.timezone.utc)
        time_since = now - created_at
        
        days = time_since.days
        hours, remainder = divmod(time_since.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            time_str = f"{days} дней, {hours} часов, {minutes} минут назад"
        elif hours > 0:
            time_str = f"{hours} часов, {minutes} минут назад"
        else:
            time_str = f"{minutes} минут назад"
        
        # Отправляем ответ
        stream_title = latest_stream["title"]
        await ctx.reply(f"Последний стрим на канале {channel_name} был {time_str}. Название: \"{stream_title}\" weAreWaiting")

    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command(name='анек', aliases=['кринж'])
    async def anek(self, ctx: commands.Context):
        await ctx.reply(f'Зацените прикол: "{get_rand_anek()}". Классно, да?')
        
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command(name='факт', aliases=['fact'])
    async def fact(self, ctx: commands.Context):
        for chunk in split_string_by_words(get_rand_fact()):
            await ctx.reply(chunk)
            await asyncio.sleep(2)
    
    @commands.cooldown(rate=1, per=180, bucket=commands.Bucket.channel)
    @commands.command(name='гороскоп', aliases=['prediction'])
    async def prediction(self, ctx: commands.Context, phrase: str | None):
        prediction = get_prediction(phrase)
        if prediction:
            for chunk in split_string_by_words(prediction):
                await ctx.reply(chunk)
                await asyncio.sleep(2)
        else:
            await ctx.reply(f'Не удалось получить гороскоп по вашему запросу PoroSad')
        
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.user)
    @commands.command(name='ауф', aliases=['auf'])
    async def auf(self, ctx: commands.Context):
        await ctx.reply(random.choice(auf_messages))
        
    @commands.cooldown(rate=1, per=7200, bucket=commands.Bucket.channel)
    @commands.command(name='привет', aliases=['hello', 'hi'])
    async def hello(self, ctx: commands.Context):
        if await self.bot.is_stream_online(ctx.channel):
            return
        channel_user = await ctx.channel.user()
        active_users = self.bot.db_log_client.get_last_active_users(channel_user.id)
        if not active_users:
            await ctx.reply('Я не знаю кто был в чате недавно. Поэтому привет всем KonCha')
            return
        msg = f'Привет,'
        for user_row in active_users:
            msg = f' {msg} @{user_row[0]},'
        msg = msg + ' KonCha'
        await ctx.reply(msg)