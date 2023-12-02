from bot_settings import *
from some_data import *
from twitchio.ext import commands
from twitchio.user import User
from twitchio.channel import Channel
from db_client import DbMessageLogClient

import datetime
from dateutil import tz
import random
import re
import http3
from bot_utilities import *

from gpiozero import CPUTemperature

class Bot(commands.Bot):

    name = str()
    dbLogClient = DbMessageLogClient(DB_CONNECTION_STRING)
    
    #Инициализация бота
    def __init__(self, name):
        super().__init__(token=ACCESS_TOKEN, prefix=PREFIX, initial_channels=INITIAL_CHANNELS)
        self.dbLogClient.Connect()

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
       
        utcTime = message.timestamp
        utcTime = utcTime.replace(tzinfo=tz.tzutc())
        localTime = utcTime.astimezone(tz.tzlocal())
        print(f'{localTime}({message.channel.name}){author_name}:{message.content}')
        channelUser = await message.channel.user(False)
        self.dbLogClient.InsertMessage(message.content, author_id, author_name, channelUser, localTime)
        
        if message.echo:
            return
        
        if str(message.content).startswith(PREFIX):
            await self.handle_commands(message)
            return
        
        #Опускание мубота
        if message.author.name == 'moobot':
            await message.channel.send(f'@{message.author.name}, мубот соси')
            return

        #Приветствия и покатствия
        lower_message = message.content.lower();
        check_str = re.split(r',|!|;|\.|\?', message.content)[0]
        if check_str in hellos:
            await message.channel.send(f'@{message.author.name}, {random.choice(hellos)}')
            return
        if check_str in byes:
            await message.channel.send(f'@{message.author.name}, {random.choice(byes)}')
            return
        
        if 'двач' in lower_message:
            await message.channel.send(f'@{message.author.name},  двачеры сосут большой и толстый (леденец) KappaPride')
            return
        
        if check_str in custom_copypast_cmd and message.channel.name in ALLOW_FLOOD:
            await message.channel.send(check_str)
            return
            
        if(str(f'@{self.nick}') in str(message.content).lower()):
            await message.channel.send(f'@{message.author.name}, {random.choice(bot_messages)}')
            return
        
    #Информационные команды
    @commands.command(name='тг', aliases=['телеграм', 'телега', 'telegram', 'tg'])
    async def telegram(self, ctx: commands.Context):
        msg = telegrams.get(ctx.channel.name)
        if(not msg == None):
            await ctx.send(msg)
    
    @commands.command(name='вконтакте', aliases=['вк', 'vk', 'vkontakte'])
    async def vkontakte(self, ctx: commands.Context):
        msg = vks.get(ctx.channel.name)
        if(not msg == None):
            await ctx.send(msg)
            
    @commands.command(name='бусти', aliases=['boosty', 'кошка'])
    async def boosty(self, ctx: commands.Context):
        msg = boostys.get(ctx.channel.name)
        if(not msg == None):
            await ctx.send(msg)
                    
    @commands.command(name='донат', aliases=['donat', 'пожертвование'])
    async def donat(self, ctx: commands.Context):
        msg = donats.get(ctx.channel.name)
        if(not msg == None):
            await ctx.send(msg)
    
    @commands.command(name='мем', aliases=['меме', 'meme'])
    async def meme(self, ctx: commands.Context):
        msg = memes.get(ctx.channel.name)
        if(not msg == None):
            await ctx.send(msg)
    
    @commands.command(name='смайлы', aliases=['7tv', 'smiles', 'emoji', 'смайлики', 'эмоуты'])
    async def SpecialSmiles(self, ctx: commands.Context):
        if ctx.channel.name in ALLOW_URL:
            await ctx.send('Чтобы видеть и посылать крутые смайлы в чате устанавливайте расширение для браузера по ссылке: https://7tv.app/')
        
    @commands.command(name='help', aliases=['commands', 'команды', 'помощь', 'бот'])
    async def help_bot(self, ctx: commands.Context):
        await ctx.send(f'@{ctx.author.name} Я бот и я ничего не умею 4Head')
    
    @commands.cooldown(rate=1, per=60, bucket=commands.Bucket.channel)
    @commands.command(name='lastseen', aliases=['когдавидели'])
    async def last_seen(self, ctx: commands.Context):
        channel_user = await ctx.channel.user()
        last_activity = self.dbLogClient.GetUserLastActivity(channel_user.id)
        if (last_activity):
            await ctx.send(f'@{ctx.author.name}, в последний раз {ctx.channel.name} видели в чате {last_activity.strftime("%d.%m.%Y в %H:%M:%S")} CoolStoryBob');
        else:
            await ctx.send(f'@{ctx.author.name}, я не помню когда в последний раз видел в чате {ctx.channel.name} PoroSad');
    
    @commands.cooldown(rate=1, per=300, bucket=commands.Bucket.member)
    @commands.command(name='followage', aliases=['возрастотслеживания'])
    async def followage(self, ctx: commands.Context):    
        if ctx.author.name == ctx.channel.name:
            await ctx.send(f'@{ctx.author.name}, ты не можешь отслеживать сам себя CoolStoryBob')
            return
        client = http3.AsyncClient()
        r = await client.get(f'https://api.ivr.fi/v2/twitch/subage/{ctx.author.name}/{ctx.channel.name}')
        if r.status_code >= 400:
            await ctx.send(f'@{ctx.author.name}, не удалось выполнить запрос времени отслеживания PoroSad')
            return
        followedAt = r.json()["followedAt"]
        if followedAt :
            follow_age = datetime.datetime.now() - datetime.datetime.fromisoformat(followedAt.replace('Z',''))
            await ctx.send(f'@{ctx.author.name}, ты отслеживаешь канал {ctx.channel.name} {follow_age.days} дней SeemsGood')
        else:
            await ctx.send(f'@{ctx.author.name}, ты не отслеживаешь канал {ctx.channel.name} D:')
            
    @commands.cooldown(rate=1, per=300, bucket=commands.Bucket.channel)
    @commands.command(name='день')
    async def whatdaytoday(self, ctx: commands.Context):
        await ctx.send(f'@{ctx.author.name}, {GetTodayHoliday()}')
        
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='погода', aliases=['weather'])
    async def weather(self, ctx: commands.Context):
        url = "https://weatherapi-com.p.rapidapi.com/current.json"
        arg = ctx.message.content.rstrip(' ').split(' ', 1)[1]
        querystring = {"q":arg,"lang":"ru"}
        client = http3.AsyncClient()
        response = await client.get(url, headers=weather_headers, params=querystring)
        if response.status_code < 400:
            jsonR = response.json()
            await ctx.send(f'@{ctx.author.name}, в {jsonR["location"]["name"]} на данный момент {jsonR["current"]["temp_c"]}°C. {jsonR["current"]["condition"]["text"]} peepoPls')
        else:
            await ctx.send(f'@{ctx.author.name}, не удалось выполнить запрос погоды PoroSad')
        
    #Команды под оффлайн чат 
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.member)
    @commands.command(name='чмок')
    async def chmok(self, ctx: commands.Context):
        if await self.is_stream_online(ctx.channel):
            return
        sArgs = ctx.message.content.rstrip(' ').split(' ', 1)
        if len(ctx.chatters) == 0:
            await ctx.send('В этом чате некого чмокнуть PoroSad')
        elif len(sArgs) == 1:
            await ctx.send(f'@{ctx.author.name} чмокнул @{random.choice(tuple(ctx.chatters)).name} 😘')
        else:
            if not IsValidArgs(sArgs[1].rstrip(' ')):
                await ctx.send(f'@{ctx.author.name}, бана хочешь моего?')
            elif ctx.author.name in sArgs[1].lower():
                await ctx.send(f'@{ctx.author.name} боюсь что это нереально? Давай лучше я 😘')
            elif self.nick in sArgs[1].lower():
                await ctx.send(f'@{ctx.author.name}, и тебе чмок 😘')
            else:
                await ctx.send(f'@{ctx.author.name} чмокнул {str(sArgs[1])} 😘')
                
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.member)
    @commands.command(name='лапочка')
    async def lapochka(self, ctx: commands.Context):
        if await self.is_stream_online(ctx.channel):
            return
        sArgs = ctx.message.content.rstrip(' ').split(' ', 1)
        if len(ctx.chatters) == 0:
            await ctx.send('В этом чате пусто PoroSad')
        elif len(sArgs) == 1:
            await ctx.send(f'@{ctx.author.name} назвал лапочкой @{random.choice(tuple(ctx.chatters)).name} <3')
        else:
            if not IsValidArgs(sArgs[1].rstrip(' ')):
                await ctx.send(f'@{ctx.author.name}, бана хочешь моего?')
            elif ctx.author.name in sArgs[1].lower():
                await ctx.send(f'@{ctx.author.name} высокая самооценка это хорошо SeemsGood')
            elif self.nick in sArgs[1].lower():
                await ctx.send(f'@{ctx.author.name}, ой спасибо bleedPurple')
            else:
                await ctx.send(f'@{ctx.author.name} назвал лапочкой {str(sArgs[1])} <3')
                
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command(name='анек', aliases=['кринж'])
    async def anek(self, ctx: commands.Context):
        if await self.is_stream_online(ctx.channel):
            return
        await ctx.send(GetRandAnek())
        
    #Команды для белого списка 
    @commands.command(name='горячесть', aliases=['температура', 'темп', 'temp'])
    async def temperature(self, ctx: commands.Context):
        if ctx.author.name in white_list:
            cpuT = CPUTemperature()
            await ctx.send(f'Моя горячесть равна {cpuT.temperature} градусам')

    #Обработка исключений
    async def event_command_error(self, ctx, error: Exception) -> None:
        if isinstance(error, commands.CommandOnCooldown) and not await self.is_stream_online(ctx.channel):
            await ctx.send(f'Команда "{error.command.name}" заряжается, еще {int(error.retry_after)} сек.') 
        print(error)
    
    #Событие подключения к чату
    async def event_join(self, channel: Channel, user: User):
        print(f'{datetime.datetime.now()}: Пользователь {user.name} вошел в чат {channel.name}')
        if channel.name == user.name:
            channel_user = await channel.user() #id отсутвует в User поэтому приходится запрашивать
            await channel.send(f'@{channel_user.name}, привет стример! 😘')
            self.dbLogClient.UpdateUserLastActivity(channel_user.id, channel_user.name, datetime.datetime.now())
            print(f'{datetime.datetime.now()}: Стример в чате {channel_user.name}')
    
    #Дополнительные функции        
    async def is_stream_online(self, channel) -> bool:
        chan_user = await channel.user()
        streams = await self.fetch_streams([chan_user.id])
        if len(streams) == 0:
            return False
        return True
