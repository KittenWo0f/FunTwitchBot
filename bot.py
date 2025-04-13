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

    name = str()
    db_log_client = db_message_log_client(DB_HOST, DB_NAME, DB_PORT, DB_USER, DB_PASSWORD)
    telegram_notifier = telegram_admin_notifier(TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID)
    msg_titles = ['сообщение', 'сообщения', 'сообщений']
    
    #Инициализация бота
    def __init__(self, name):
        super().__init__(token=ACCESS_TOKEN, prefix=PREFIX, initial_channels=INITIAL_CHANNELS)
        self.db_log_client.connect()

    #Событие готовности бота
    async def event_ready(self):
        print(f'Вошел как | {self.nick}')
        print(f'Id пользователя | {self.user_id}')

    #Обработка сообщений
    async def event_message(self, message):        
        if message.echo:
            author_id = self.user_id 
            author_name = self.nick
        else:
            author_id = message.author.id 
            author_name = message.author.name
        print(f'({message.channel.name}){author_name}:{message.content}')
        channel_user = await message.channel.user(False)
        self.db_log_client.insert_message(message.content, author_id, author_name, channel_user)
        
        if message.echo:
            return
        
        if str(message.content).startswith(PREFIX):
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
    async def last_seen(self, ctx: commands.Context, phrase: str | None):
        try:
            channel_user = await ctx.channel.user()
            if phrase:
                search_user = await self.fetch_channel(phrase)
                search_user = search_user.user
                search_username = phrase
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
    async def weather(self, ctx: commands.Context, *, phrase: str | None):
        # Дефолтный смайлик в конце сообщения
        smile = 'peepoPls'
        direct_translate = {
            'N' : 'С',
            'W' : 'З',
            'S' : 'Ю',
            'E' : 'В'
        }
        url = "https://weatherapi-com.p.rapidapi.com/current.json"
        querystring = {"q":phrase,"lang":"ru"}
        response = requests.get(url, headers=weather_headers, params=querystring)
        if response.status_code < 400:
            jsonR = response.json()
            # Переводим нашу погоду в более float состояние
            location_temp = jsonR["current"]["temp_c"]
            if location_temp <= 0:
                smile = "Coldge"
            elif location_temp > 29: 
                smile = "hell"
            await ctx.reply(f'В {jsonR["location"]["name"]} на данный момент {jsonR["current"]["temp_c"]}°C. \
                            {jsonR["current"]["condition"]["text"]}. \
                            Ветер {replace_chars(jsonR["current"]["wind_dir"], direct_translate)} {jsonR["current"]["wind_kph"] * 1000 / 3600:.2f} м/с. \
                            {smile}')
        else:
            await ctx.reply(f'Не удалось выполнить запрос погоды PoroSad')
    
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.channel)
    @commands.command(name='курс')
    async def kurs(self, ctx: commands.Context):
        url = "https://www.cbr-xml-daily.ru/latest.js"
        response = requests.get(url)
        if response.status_code < 400:
            await ctx.reply(f'1 USD = {1 / response.json()["rates"]["USD"]:.2f} RUB GAGAGA')
        else:
            await ctx.reply(f'Не удалось получить курс доллара PoroSad')
    
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='ogeyofday')
    async def ogeyofday(self, ctx: commands.Context):
        if ctx.channel.name not in OGEY_OF_DAY_CHANNELS:
            return
        channel_user = await ctx.channel.user()
        ogey_name = self.db_log_client.get_ogey(channel_user.id)
        if ogey_name != None:
            await ctx.reply(f'Ogey дня сегодня {ogey_name}, можно только позавидовать этому чатеру EZ Clap')
        else:
            await ctx.reply(f'Ogey дня не определен PoroSad')
        
    #Команды под оффлайн чат 
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.member)
    @commands.command(name='чмок')
    async def chmok(self, ctx: commands.Context, *, phrase: str | None):
        if await self.is_stream_online(ctx.channel):
            return
        if len(ctx.chatters) == 0:
            await ctx.reply('В этом чате некого чмокнуть PoroSad')
        elif not phrase:
            await ctx.reply(f'@{ctx.author.name} чмокнул @{random.choice(tuple(ctx.chatters)).name} 😘')
        else:
            if not is_valid_args(phrase):
                await ctx.reply(f'Бана хочешь моего?')
            elif ctx.author.name in phrase.lower():
                await ctx.reply(f'@{ctx.author.name} боюсь что это нереально. Давай лучше я 😘')
            elif self.nick in phrase.lower():
                await ctx.reply(f'И тебе чмок 😘')
            else:
                await ctx.reply(f'@{ctx.author.name} чмокнул {phrase} 😘')
                
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.member)
    @commands.command(name='лапочка')
    async def lapochka(self, ctx: commands.Context, *, phrase: str | None):
        if await self.is_stream_online(ctx.channel):
            return
        if len(ctx.chatters) == 0:
            await ctx.reply('В этом чате пусто PoroSad')
        elif not phrase:
            await ctx.reply(f'@{ctx.author.name} назвал лапочкой @{random.choice(tuple(ctx.chatters)).name} <3')
        else:
            if not is_valid_args(phrase):
                await ctx.reply(f'Бана хочешь моего?')
            elif ctx.author.name in phrase.lower():
                await ctx.reply(f'@{ctx.author.name} высокая самооценка это хорошо SeemsGood')
            elif self.nick in phrase.lower():
                await ctx.reply(f'Ой спасибо bleedPurple')
            else:
                await ctx.reply(f'@{ctx.author.name} назвал лапочкой {phrase} <3')
                
    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name='анек', aliases=['кринж'])
    async def anek(self, ctx: commands.Context):
        await ctx.reply(get_rand_anek())
        
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
        if await self.is_stream_online(ctx.channel):
            return
        channel_user = await ctx.channel.user()
        active_users = self.db_log_client.get_last_active_users(channel_user.id)
        if not active_users:
            await ctx.reply('Я не знаю кто был в чате недавно. Поэтому привет всем KonCha')
            return
        msg = f'Привет,'
        for user_row in active_users:
            msg = f' {msg} @{user_row[0]},'
        msg = msg + ' KonCha'
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
        for i, user_row in enumerate(top_users):
            msg = f' {msg} {i + 1}. {user_row[0]} ({user_row[1]:,}, {(user_row[1]/hours_from_mounth_begin()):.2f} с/ч),'
        msg = msg + ' PogChamp'
        await ctx.reply(msg)
        
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.user)
    @commands.command(name='скольконасрал')
    async def skolkonasral(self, ctx: commands.Context, phrase: str | None):
        if await self.is_stream_online(ctx.channel):
            return
        channel_user = await ctx.channel.user()
        if phrase:
            name = phrase
        else:
            name = ctx.author.name
        msg_count = self.db_log_client.get_users_message_count_for_mounth_by_name(channel_user.id, name.lower())
        if not msg_count:
            await ctx.reply(f'Не удалось подсчитать сообщения запрошеного пользователя NotLikeThis.')
            return
        await ctx.reply(f"В этом месяце {name} написал в чате {msg_count:,} {decl_of_num(msg_count, self.msg_titles)}, скорость: {(msg_count/hours_from_mounth_begin()):.2f} с/ч PogChamp")
        
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
    async def to_admin(self, ctx: commands.Context, *, phrase: str | None):
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
            await self.telegram_admin_notifier.send_message(f"{message}")
    
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
