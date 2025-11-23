from twitchio.ext import commands, routines
from twitchio.user import User
from twitchio.channel import Channel
import asyncio
import datetime
from gpiozero import CPUTemperature
from utils.bot_utilities import *
from database.db_client import db_message_log_client
from data.some_data import *
from telegram_admin_notifier import telegram_admin_notifier
from bot_settings import *

class twitch_bot(commands.Bot):

    # name will be set in __init__
    db_log_client = db_message_log_client(DB_HOST, DB_NAME, DB_PORT, DB_USER, DB_PASSWORD)
    telegram_notifier = telegram_admin_notifier(TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID)
    msg_titles = ['сообщение', 'сообщения', 'сообщений']
    
    #Инициализация бота
    def __init__(self, name):
        super().__init__(token=ACCESS_TOKEN, prefix=PREFIX, initial_channels=INITIAL_CHANNELS)
        self.db_log_client.connect()

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

    #Обработка исключений
    async def event_command_error(self, ctx, error: Exception) -> None:
        if isinstance(error, commands.CommandOnCooldown) and not await self.is_stream_online(ctx.channel):
            await ctx.reply(f'Команда \"{error.command.name}\" заряжается, еще {int(error.retry_after)} сек.') 
        print(error)
        
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

    #Команда для связи с админом
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