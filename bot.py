from bot_settings import *
from some_data import *
from telegram_admin_notifier import telegram_admin_notifier
from twitchio.ext import commands, routines
from twitchio.user import User
from twitchio.channel import Channel
from db_client import db_message_log_client
import asyncio
from os import path, remove

import datetime
import calendar
from dateutil import tz
import random
import re
import requests
from bot_utilities import *

from gpiozero import CPUTemperature

class twitch_bot(commands.Bot):

    # name will be set in __init__
    db_log_client = db_message_log_client(DB_HOST, DB_NAME, DB_PORT, DB_USER, DB_PASSWORD)
    telegram_notifier = telegram_admin_notifier(TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID)
    msg_titles = ['сообщение', 'сообщения', 'сообщений']
    
    #Инициализация бота
    def __init__(self, name):
        super().__init__(token=ACCESS_TOKEN, prefix=PREFIX, initial_channels=INITIAL_CHANNELS)
        self.db_log_client.connect()
        self.disable_cmds_chanels: dict[str,bool] = {}

    #Обработка сообщений
    async def event_message(self, message):        
        if message.echo:
            author_id = self.user_id 
            author_name = self.bot_display_name
        else:
            author_id = message.author.id 
            author_name = message.author.display_name
        print(f'({message.channel.name}){author_name}:{message.content}')
        channel_user = await message.channel.user(False)
        self.db_log_client.insert_message(message.content, author_id, author_name, channel_user)
        
        if message.echo:
            return
        
        
        if str(message.content).startswith(PREFIX):
            
            if message.content.startswith('!подъём') and message.author.name in white_list:
                ctx = await self.get_context(message)
                if self.disable_cmds_chanels.get(message.channel):
                    self.disable_cmds_chanels[message.channel] = False
                    await ctx.reply('Я проснулся AYAYASleepy')
                else:
                    await ctx.reply('Я и не спал roflanTanec')
                return
            
            if self.disable_cmds_chanels.get(message.channel):
                return
            
            if message.content.startswith('!отбой') and message.author.name in white_list:
                self.disable_cmds_chanels[message.channel] = True
                ctx = await self.get_context(message)
                await ctx.reply('Я спать ppSleep')
                return
            
            await self.handle_commands(message)
            return
        
        
        ctx = await self.get_context(message)
        
        check_str = re.split(r',|!|;|\.|\?', message.content)[0]
        
        # Попугайничество
        if check_str in custom_copypast_cmd and message.channel.name in ALLOW_FLOOD:
            await message.channel.send(check_str)
            return

        # Приветствия 
        if check_str in hellos:
            await ctx.reply(f'{random.choice(hellos)}')
            return
        
        # Покатствия
        if check_str in byes:
            await ctx.reply(f'{random.choice(byes)}')
            return
        
        # Ответ на сообщение если было обращение к боту
        if(str(f'@{self.nick}') in str(message.content).lower()):
            channel_user = await message.channel.user()
            await ctx.reply(f'{self.db_log_client.get_random_message_by_user(channel_user.id)}')
            return
        
        # Опускание мубота
        if message.author.name == 'moobot':
            await ctx.reply(f'Мубот соси')
            return
        
    #Информационные команды
    @commands.command(name='тг', aliases=['телеграм', 'телега', 'telegram', 'tg'])
    async def telegram(self, ctx: commands.Context):
        msg = telegrams.get(ctx.channel.name)
        if(not msg == None):
            await ctx.reply(msg)
    
    @commands.command(name='вконтакте', aliases=['вк', 'vk', 'vkontakte'])
    async def vkontakte(self, ctx: commands.Context):
        msg = vks.get(ctx.channel.name)
        if(not msg == None):
            await ctx.reply(msg)
            
    @commands.command(name='бусти', aliases=['boosty', 'кошка'])
    async def boosty(self, ctx: commands.Context):
        msg = boostys.get(ctx.channel.name)
        if(not msg == None):
            await ctx.reply(msg)
                    
    @commands.command(name='донат', aliases=['donat', 'пожертвование'])
    async def donat(self, ctx: commands.Context):
        msg = donats.get(ctx.channel.name)
        if(not msg == None):
            await ctx.reply(msg)
    
    @commands.command(name='мем', aliases=['меме', 'meme'])
    async def meme(self, ctx: commands.Context):
        msg = memes.get(ctx.channel.name)
        if(not msg == None):
            await ctx.reply(msg)
            
    @commands.command(name='стим', aliases=['steam', 'игры'])
    async def steam(self, ctx: commands.Context):
        msg = steams.get(ctx.channel.name)
        if(not msg == None):
            await ctx.reply(msg)
            
    @commands.command(name='записи', aliases=['vods'])
    async def vods(self, ctx: commands.Context):
        msg = vods.get(ctx.channel.name)
        if(not msg == None):
            await ctx.reply(msg)
    
    @commands.command(name='смайлы', aliases=['7tv', 'smiles', 'emoji', 'смайлики', 'эмоуты'])
    async def SpecialSmiles(self, ctx: commands.Context):
        if ctx.channel.name in ALLOW_URL:
            await ctx.reply('Чтобы видеть и посылать крутые смайлы в чате устанавливайте расширение для браузера по ссылке: https://7tv.app/')
        
    @commands.command(name='help', aliases=['commands', 'команды', 'помощь', 'бот'])
    async def help_bot(self, ctx: commands.Context):
        # Получаем список всех команд бота
        command_list = [cmd for cmd in self.commands]
        # Формируем сообщение
        if command_list:
            message = f"@{ctx.author.name} Доступные команды: {', '.join(command_list)}"
        else:
            message = f"@{ctx.author.name} У меня нет команд PoroSad"

        for chunk in split_string_by_words(message):
            await ctx.reply(chunk)
            await asyncio.sleep(2)
    
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.user)
    @commands.command(name='lastseen', aliases=['когдавидели'])
    async def last_seen(self, ctx: commands.Context, phrase: str = None):
        try:
            channel_user = await ctx.channel.user()
            if phrase:
                username = phrase.lstrip('@')
                search_user = await self.fetch_channel(username)
                search_user = search_user.user
                search_username = username
            else:
                search_user = channel_user
                search_username = channel_user.name
            last_activity = self.db_log_client.get_user_last_activity(channel_user.id, search_user.id)
            if (last_activity):
                await ctx.reply(f'В последний раз {search_username} видели в чате {last_activity.strftime("%d.%m.%Y в %H:%M:%S")} CoolStoryBob')
            else:
                await ctx.reply(f'Я не помню когда в последний раз видел в чате {search_username} PoroSad')
        except:
            await ctx.reply(f'Что-то пошло не так. Проверьте имя искомого пользователя eeeh')
    
    @commands.cooldown(rate=1, per=300, bucket=commands.Bucket.member)
    @commands.command(name='followage', aliases=['возрастотслеживания'])
    async def followage(self, ctx: commands.Context):
        if ctx.author.name == ctx.channel.name:
            await ctx.reply(f'Ты не можешь отслеживать сам себя CoolStoryBob')
            return
        r = requests.get(f'https://api.ivr.fi/v2/twitch/subage/{ctx.author.name}/{ctx.channel.name}')
        if r.status_code >= 400:
            await ctx.reply(f'Не удалось выполнить запрос времени отслеживания PoroSad')
            return
        followedAt = r.json()["followedAt"]
        if followedAt :
            follow_age = datetime.datetime.now() - datetime.datetime.fromisoformat(followedAt.replace('Z',''))
            await ctx.reply(f'Ты отслеживаешь канал {ctx.channel.name} {follow_age.days} дней SeemsGood')
        else:
            await ctx.reply(f'Ты не отслеживаешь канал {ctx.channel.name} D:')
            
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.channel)
    @commands.command(name='день')
    async def whatdaytoday(self, ctx: commands.Context):
        await ctx.reply(f'{get_today_holiday()}')
      
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='погода', aliases=['weather'])
    async def weather(self, ctx: commands.Context, *, phrase: str = None):
        # Дефолтный смайлик в конце сообщения
        smile = 'peepoPls'

        def get_wind_direction(degrees):
            """Конвертирует градусы в направление ветра"""
            directions = ['С', 'ССВ', 'СВ', 'ВСВ', 'В', 'ВЮВ', 'ЮВ', 'ЮЮВ',
                        'Ю', 'ЮЮЗ', 'ЮЗ', 'ЗЮЗ', 'З', 'ЗСЗ', 'СЗ', 'ССЗ']
            index = round(degrees / 22.5) % 16
            return directions[index]
        
        url = "http://api.openweathermap.org/data/2.5/weather"
        
        params = {
            "q": phrase,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "ru"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Извлекаем данные
                city_name = data["name"]
                temp = data["main"]["temp"]
                description = data["weather"][0]["description"]
                wind_speed = data["wind"]["speed"]  # м/с
                wind_deg = data["wind"].get("deg", 0)
                
                # Определяем смайлик по температуре
                if temp <= 0:
                    smile = "Coldge"
                elif temp > 29:
                    smile = "hell"
                
                # Получаем направление ветра
                wind_dir = get_wind_direction(wind_deg)
                
                await ctx.reply(f'В {city_name} на данный момент {temp:.1f}°C. '
                            f'{description.capitalize()}. '
                            f'Ветер {wind_dir} {wind_speed:.1f} м/с. '
                            f'{smile}')
                            
            elif response.status_code == 404:
                await ctx.reply(f'Город "{phrase}" не найден PoroSad')
            else:
                await ctx.reply(f'Ошибка получения данных о погоде (код: {response.status_code}) PoroSad')
                
        except requests.exceptions.Timeout:
            await ctx.reply('Превышено время ожидания ответа от сервера погоды PoroSad')
        except requests.exceptions.RequestException:
            await ctx.reply('Не удалось выполнить запрос погоды PoroSad')
        except KeyError as e:
            await ctx.reply(f'Ошибка обработки данных погоды PoroSad')
        except Exception as e:
            await ctx.reply('Произошла неожиданная ошибка при получении погоды PoroSad')
    
    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name='время', aliases=['time'])
    async def time(self, ctx: commands.Context, *, phrase: str = None):
        if not phrase:
            return
        time = await get_current_time_in_city(phrase)
        if time:
            await ctx.reply(f'В {phrase} сейчас {time} MadgeTime')
        else:
            await ctx.reply(f'Не удалось узнать время в указаном месте PoroSad')
    
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.channel)
    @commands.command(name='курс')
    async def kurs(self, ctx: commands.Context):
        url = "https://www.cbr-xml-daily.ru/latest.js"
        response = requests.get(url)
        if response.status_code < 400:
            await ctx.reply(f'1 USD = {1 / response.json()["rates"]["USD"]:.2f} RUB GAGAGA')
        else:
            await ctx.reply(f'Не удалось получить курс доллара PoroSad')
       
    #Команды под оффлайн чат 
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.member)
    @commands.command(name='чмок')
    async def chmok(self, ctx: commands.Context, phrase: str = None):
        if await self.is_stream_online(ctx.channel):
            return
        if phrase:
            phrase = ''.join(c for c in phrase if c.isprintable())
        if phrase and len(phrase):
            if not is_valid_args(phrase):
                await ctx.reply(f'Бана хочешь моего?')
            elif ctx.author.name in phrase.lower():
                await ctx.reply(f'@{ctx.author.name} боюсь что это нереально. Давай лучше я 😘')
            elif self.nick in phrase.lower():
                await ctx.reply(f'И тебе чмок 😘')
            else:
                await ctx.reply(f'@{ctx.author.name} чмокнул {phrase} 😘')
        elif len(ctx.chatters) == 0:
            await ctx.reply('В этом чате некого чмокнуть PoroSad')
        else:
            random_chatter = random.choice(tuple(ctx.chatters)).name
            await ctx.reply(f'@{ctx.author.name} чмокнул @{random_chatter} 😘')
                
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.member)
    @commands.command(name='кусь')
    async def kus(self, ctx: commands.Context, phrase: str = None):
        if await self.is_stream_online(ctx.channel):
            return
        if phrase:
            phrase = ''.join(c for c in phrase if c.isprintable())
        if phrase and len(phrase):
            if not is_valid_args(phrase):
                await ctx.reply(f'Бана хочешь моего?')
            elif ctx.author.name in phrase.lower():
                await ctx.reply(f'@{ctx.author.name} странный ты eeeh')
            elif self.nick in phrase.lower():
                await ctx.reply(f'Stare')
            else:
                await ctx.reply(f'@{ctx.author.name} куснул {phrase} peepoGiggles')    
        elif len(ctx.chatters) == 0:
            await ctx.reply('В этом чате пусто PoroSad')
        else:
            random_chatter = random.choice(tuple(ctx.chatters)).name
            await ctx.reply(f'@{ctx.author.name} куснул @{random_chatter} peepoGiggles')
    
    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name='последнийстрим', aliases=['laststream'])
    async def last_stream(self, ctx: commands.Context, phrase: str = None):
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

    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name='анек', aliases=['кринж'])
    async def anek(self, ctx: commands.Context, *, phrase: str = None):
        if phrase:
            try:
                ai_anek = await get_ai_anek(phrase)
                full_text = f'Зацените прикол: "{ai_anek}". Классно, да?'
            except Exception as e:
                full_text = f"Нейросеть умерла: {e} FeelsBadMan"
        else:
            full_text = f'Зацените прикол: "{get_rand_anek()}". Классно, да?'

        for chunk in split_string_by_words(full_text):
            await ctx.reply(chunk)
            await asyncio.sleep(2)

    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command(name='факт', aliases=['fact'])
    async def fact(self, ctx: commands.Context, *, phrase: str = None):
        if phrase:
            try:
                ai_text = await get_ai_fact(phrase)
                full_text = f"{ai_text} rockFact"
            except Exception as e:
                full_text = f"Нейросеть умерла: {e} rockFact"
        else:
            full_text = f"{get_rand_fact()} rockFact"

        for chunk in split_string_by_words(full_text):
            await ctx.reply(chunk)
            await asyncio.sleep(2)
    
    @commands.cooldown(rate=1, per=180, bucket=commands.Bucket.channel)
    @commands.command(name='гороскоп', aliases=['prediction'])
    async def prediction(self, ctx: commands.Context, phrase: str = None):
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
        if await self.is_stream_online(ctx.channel):
            return
        channel_user = await ctx.channel.user()
        active_users = self.db_log_client.get_last_active_users(channel_user.id)
        if not active_users:
            await ctx.reply('Я не знаю кто был в чате недавно. Поэтому привет всем KonCha')
            return
        msg = f'Привет,'
        for user_row in active_users:
            msg = f' {msg} @{user_row[0]} '
        msg = msg + ' hi'
        await ctx.reply(msg)
        
    @commands.cooldown(rate=1, per=600, bucket=commands.Bucket.channel)
    @commands.command(name='топ', aliases=['top'])
    async def top(self, ctx: commands.Context):
        channel_user = await ctx.channel.user()
        top_users = self.db_log_client.get_top_of_month_users(channel_user.id)
        if not top_users:
            await ctx.reply('Не найдены сообщения для топа NotLikeThis')
            return
        msg = f'Топ месяца по сообщениям:'
        for user_row in top_users:
            msg = f' {msg} {user_row[0]} ({format_with_apostrophe(user_row[1])}),'
        msg = msg[:-1]
        msg = msg + ' PogChamp'
        await ctx.reply(msg)
    
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='ogeyofday', aliases=['огейдня', 'ogeyoftheday'])
    async def ogeyofday(self, ctx: commands.Context):
        if ctx.channel.name not in OGEY_OF_DAY_CHANNELS:
            return
        channel_user = await ctx.channel.user()
        ogey_name = self.db_log_client.get_ogey(channel_user.id)
        if ogey_name != None:
            await ctx.reply(f'Ogey дня сегодня {ogey_name}, можно только позавидовать этому чатеру EZ Clap')
        else:
            await ctx.reply(f'Ogey дня не определен PoroSad')
    
    @commands.cooldown(rate=1, per=600, bucket=commands.Bucket.channel)
    @commands.command(name='ogeysofmonth', aliases=['огеимесяца', 'ogeysofthemonth'])
    async def ogeysofmonth(self, ctx: commands.Context):
        channel_user = await ctx.channel.user()
        top_ogeys = self.db_log_client.get_top_of_month_ogey(channel_user.id)
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
        top_ogeys = self.db_log_client.get_top_ogeys(channel_user.id)
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
    async def skolkonasral(self, ctx: commands.Context, phrase: str = None):
        if await self.is_stream_online(ctx.channel):
            return
        channel_user = await ctx.channel.user()
        if phrase:
            name = phrase.lstrip('@')
        else:
            name = ctx.author.name
        msg_count = self.db_log_client.get_users_message_count_for_mounth_by_name(channel_user.id, name.lower())
        if not msg_count:
            await ctx.reply(f'Не удалось подсчитать сообщения запрошеного пользователя NotLikeThis.')
            return
        await ctx.reply(f"В этом месяце {name} написал в чате {format_with_apostrophe(msg_count)} {decl_of_num(msg_count, self.msg_titles)}, скорость: {(msg_count/hours_from_mounth_begin()):.2f} с/ч PogChamp")
        
    @commands.cooldown(rate=1, per=300, bucket=commands.Bucket.channel)
    @commands.command(name='всегонасрано')
    async def vsegonasrano(self, ctx: commands.Context):
        channel_user = await ctx.channel.user()
        msg_count = self.db_log_client.get_all_users_message_count_for_mounth(channel_user.id)
        if not msg_count:
            await ctx.reply(f'Не удалось подсчитать количество написаных сообщений NotLikeThis')
            return
        await ctx.reply(f"В этом месяце в чате насрали {msg_count:,} сообщений SHTO")
        
    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name='маления')
    async def malenia(self, ctx: commands.Context):
        channel_user = await ctx.channel.user()
        msg_count = self.db_log_client.get_malenia_in_channel(channel_user.id)
        if not msg_count:
            await ctx.reply(f'Не удалось подсчитать упоминаний малений в этом чате NotLikeThis')
            return
        await ctx.reply(f"В этом чате вспомнили Малению {msg_count:,} раз MaleniaTime")
    
    @commands.cooldown(rate=1, per=20, bucket=commands.Bucket.channel)
    @commands.command(name="подсчёт")
    async def word_count(self, ctx: commands.Context) -> None:
        """!подсчёт @имя_пользователя слово"""

        # Разбиваем на токены, пропуская само название команды
        parts = ctx.message.content.split()
        args  = parts[1:]  # [0] — «!подсчёт»

        # --- валидация количества аргументов ---
        if len(args) < 2:
            await ctx.reply(
                "Неверный формат! Используй: !подсчёт @имя_пользователя слово"
            )
            return

        username_arg, word, *_ = args  # лишние токены молча игнорируем

        # --- валидация формата никнейма ---
        if not username_arg.startswith("@"):
            await ctx.reply(
                "Неверный формат! Никнейм должен начинаться с «@». "
                "Пример: !подсчёт @имя_пользователя слово"
            )
            return

        username = username_arg[1:]  # убираем «@»

        if not username:
            await ctx.reply("Неверный формат! Укажи никнейм после «@».")
            return

        # --- валидация слова ---
        if not word:
            await ctx.reply("Неверный формат! Укажи слово для подсчёта.")
            return

        # --- запрос к БД ---
        channel_user = await ctx.channel.user()
        count = self.db_log_client.get_word_count_by_user(
            channel_user.id, username, word
        )

        if count is None:
            await ctx.reply("Не удалось подсчитать упоминания NotLikeThis")
            return

        if count == 0:
            await ctx.reply(
                f"Пользователь {username_arg} ни разу не написал «{word}» в этом чате."
            )
            return

        await ctx.reply(
            f"Пользователь {username_arg} написал «{word}» {count:,} раз(а) в этом чате."
        )
        
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
    async def sausage(self, ctx: commands.Context):
        length = random.randint(0, 37)
        width = random.randint(1, 13)
        
        # === ФОРМЫ (расширил сильно) ===
        shapes = [
            "идеально прямая", "прямая как стрела", "слегка изогнутая", 
            "элегантно изогнутая", "подозрительно кривоватая", "спиралевидная",
            "в форме банана", "волнообразная", "с характерным изгибом",
            "как вопросительный знак", "с шишечкой на конце", 
            "с узелком посередине", "двойная (сиамские близнецы)",
            "сердцеобразная", "как будто пережила тяжёлую жизнь",
            "абсолютно асимметричная", "с лёгкой венозностью",
            "в форме латинской S", "почти идеальная", "в форме бумеранга",
            "крючковатая", "с небольшим горбиком", "совершенно ровная",
            "в форме огурца", "закрученная в штопор", "с тремя изгибами",
            "каплевидная", "как сабля", "с лёгкой припухлостью",
            "гармошкой", "в форме молнии", "классическая сосисочная"
        ]

        # === СОСТОЯНИЯ (ещё больше) ===
        states = [
            "в полной боевой готовности", "отдыхает после трудов",
            "немного растеряна", "выглядит максимально уверенно",
            "сомневается в себе", "переживает не лучшие времена",
            "полна энтузиазма", "в пике своей формы", "скромно прячется",
            "доминирует в помещении", "игриво подмигивает",
            "философски задумчива", "гиперактивная", 
            "устала после вчерашнего", "готовится к великим делам",
            "в лёгкой депрессии", "максимально довольная жизнью",
            "нервно пульсирует", "спокойна и величественна",
            "заряженная на 100%", "сонная и вялая", "агрессивно стоит",
            "стеснительно прячется", "гордая и независимая",
            "в творческом кризисе", "в состоянии нирваны",
            "готовa к труду и обороне", "просто существует",
            "в боевом настроении", "расслабленная и счастливая"
        ]

        # === РЕДКОСТЬ ===
        rarity = get_val_by_max_val({
            3:  "трагического уровня",
            7:  "обычной редкости",
            12: "неплохая",
            17: "редкая",
            22: "эпическая",
            27: "мифическая",
            32: "божественного уровня",
            35: "ЛЕГЕНДАРНОГО КАЧЕСТВА",
            37: "БОЖЕСТВЕННАЯ"
        }, length)

        # === ЭМОДЗИ ===
        emote = get_val_by_max_val({
            3:  "PoroSad",
            8:  "Stare",
            13: "Hmm",
            18: "Hmmege",
            23: "SHTO",
            28: "EZ",
            32: "Pog",
            35: "POGCHAMP",
            37: "HYPERPOG"
        }, length)

        shape = random.choice(shapes)
        state = random.choice(states)

        # Специальные сообщения
        if length == 0:
            await ctx.reply(f"@{ctx.author.name} имеет сосиску: "
                            f"💀 Отсутствует (0 см)  📐 0 см\n"
                            f"Это уже не сосиска, это философский вакуум...")
            return

        if length >= 34:
            extra = "\n🌌 Это уже не сосиска. Это оружие массового поражения."
        elif length >= 29:
            extra = "\n🔥 Опасно мощная сосиска."
        elif length >= 25:
            extra = "\n💪 Внушает уважение."
        else:
            extra = ""

        await ctx.reply(
            f"@{ctx.author.name} имеет сосиску:\n"
            f" {emote} Длина: {length} см\n"
            f"📏 Ширина: {width} см\n"
            f"🌀 Форма: {shape}\n"
            f"✨ Редкость: {rarity}\n"
            f"🧠 Состояние: {state}"
            f"{extra}"
        )
        
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.user)
    @commands.command(name='донос')
    async def denunciation(self, ctx: commands.Context, *, phrase: str = None):
        if phrase:
            if not is_valid_args(phrase):
                await ctx.reply(f'Бана хочешь моего?')
                return
            else:
                donos_na = phrase
        else:
            donos_na = f'канал @{ctx.channel.name}'
        self.db_log_client.add_denunciations_from_user(ctx.author.id)
        await ctx.reply(f"@{ctx.author.name}, донос на {donos_na} был отправлен в соответствующие органы policeBear")
        
    @commands.cooldown(rate=1, per=300, bucket=commands.Bucket.user)
    @commands.command(name='топдоносчиков')
    async def top_denunciations(self, ctx: commands.Context):
        top_denunciation_users = self.db_log_client.get_top_denunciations_by_users()
        if not top_denunciation_users:
            await ctx.reply('Не найдены сообщения для топа доносчиков NotLikeThis')
            return
        msg = f'Топ доносчиков:'
        for user_row in top_denunciation_users:
            msg = f' {msg} {user_row[0]}({user_row[1]:,}),'
        msg = msg + ' POLICE'
        await ctx.reply(msg)
        
    @commands.cooldown(rate=1, per=10800, bucket=commands.Bucket.user)
    @commands.command(name='админу')
    async def to_admin(self, ctx: commands.Context, *, phrase: str = None):
        if phrase:
            success = await self.telegram_notifier.send_message(f'''{ctx.author.name} ({ctx.channel.name}): {phrase}''')
            if success:
                await ctx.reply(f'Ваше сообщение было отправлено админу NOTED')
            else:
                await ctx.reply(f'Не удалось отправить ваше сообщение админу NotLikeThis')
        else:
            await ctx.reply(f'Необходимо добавить текст сообщения в команде CaitThinking ')
               
    #Рутины
    @routines.routine(time = datetime.datetime(year = 2024, month = 6, day = 1, hour = 18, minute = 00))
    async def ogey_of_day_routine(self):
        for ch in OGEY_OF_DAY_CHANNELS:
            channels = await self.fetch_users([ch])
            channel_id = channels[0].id
            channel = self.get_channel(ch)
            ogey_id = self.db_log_client.get_random_user_by_last_n_hours(channel_id, 24)
            if self.db_log_client.update_ogey(channel_id, ogey_id):
                users = await self.fetch_users(None, [ogey_id])
                await channel.send(f'Ogey дня обновился. Им стал {users[0].display_name}, можно только позавидовать этому чатеру EZ Clap')
            else:
                await channel.send(f'Не удалось определить нового Ogey. PoroSad')
    
    @routines.routine(time = datetime.datetime(year = 2025, month = 4, day = 6, hour = 2, minute = 0))
    async def backup_db_routine(self):
        # Запускаем бэкап в фоне
        backup_path, message = await self.db_log_client.async_db_backup("db_backups", 9)
        
        if backup_path:
            # Отправка файла в телегу
            await self.telegram_notifier.send_file(backup_path)
            # Удаление файла с диска 
            if path.exists(backup_path):
                remove(backup_path)
        else:
            await self.telegram_notifier.send_message(f"{message}")
    
    #Команды для белого списка 
    @commands.command(name='горячесть', aliases=['температура', 'темп', 'temp'])
    async def temperature(self, ctx: commands.Context):
        if ctx.author.name in white_list:
            cpu_t = CPUTemperature()
            await ctx.reply(f'Моя горячесть равна {cpu_t.temperature} градусам')

    #Обработка исключений
    async def event_command_error(self, ctx, error: Exception) -> None:
        if isinstance(error, commands.CommandOnCooldown) and not await self.is_stream_online(ctx.channel):
            await ctx.reply(f'Команда "{error.command.name}" заряжается, еще {int(error.retry_after)} сек.') 
        print(error)
    
    #Событие подключения к чату
    async def event_join(self, channel: Channel, user: User):
        print(f'Пользователь {user.name} вошел в чат {channel.name}')
        if channel.name == user.name:
            channel_user = await channel.user() #id отсутвует в User поэтому приходится запрашивать
            # await channel.send(f'Привет, мир! KonCha')
            print(f'Стример в чате {channel_user.name}')
            
    async def event_ready(self):
        #Вывод информации о боте
        print(f'Вошел как | {self.nick}')
        print(f'Id пользователя | {self.user_id}')
        
        # Получаем полную информацию о себе
        users = await self.fetch_users([self.nick])
        if users:
            user = users[0]
            self.bot_display_name = user.display_name
            print(f"Display name бота: {self.bot_display_name}")
        
        #Старт рутин
        self.ogey_of_day_routine.start()
        self.backup_db_routine.start()
        
    #Дополнительные функции        
    async def is_stream_online(self, channel) -> bool:
        chan_user = await channel.user()
        streams = await self.fetch_streams([chan_user.id])
        if len(streams) == 0:
            return False
        return True
