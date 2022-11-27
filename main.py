from bot_settings import *
from twitchio.ext import commands
from twitchio.user import User
from twitchio.channel import Channel

import time
import datetime
import random
from bot_utilities import *

class Bot(commands.Bot):

    #Инициализация бота
    def __init__(self):
        super().__init__(token=ACCESS_TOKEN, prefix='!', initial_channels=INITIAL_CHANNELS)

    #Событие готовности бота
    async def event_ready(self):
        print(f'Вошел как | {self.nick}')
        print(f'Id пользователя | {self.user_id}')

    #Обработка сообщений
    async def event_message(self, message):
        if message.echo:
            return
        print(f'{message.timestamp}({message.channel.name}){message.author.name}:{message.content}')

        if message.author.name == 'moobot':
            await message.channel.send(f'@{message.author.name}, мубот соси')
        elif message.author.name == 'gufather':
            time.sleep(2)
            await message.channel.send(f'хороший бот {GetRandomEmotion()}')
        await self.handle_commands(message)

    #Команды
    @commands.command(name='привет')
    async def hello(self, ctx: commands.Context):
        await ctx.send(f'Здорова заебал, @{ctx.author.name}!')
        
    @commands.command(name='пока')
    async def bye(self, ctx: commands.Context):
        await ctx.send(f'Не уходи, @{ctx.author.name} PoroSad')

    @commands.command(name='пинг')
    async def ping(self, ctx: commands.Context):
        await ctx.send(f'Понг {ctx.author.name}!')

    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='чмок')
    async def chmok(self, ctx: commands.Context):
        sArgs = ctx.message.content.split(' ', 1)
        if len(ctx.chatters) == 0:
            await ctx.send('В этом чате некого чмокнуть PoroSad')
        elif len(sArgs) == 1:
            await ctx.send(f'@{ctx.author.name} чмокнул @{random.choice(tuple(ctx.chatters)).name} 😘')
        else:
            if not IsValidArgs(sArgs[1]):
                await ctx.send(f'@{ctx.author.name}, бана хочешь моего?')
            else:
                await ctx.send(f'@{ctx.author.name} чмокнул {str(sArgs[1])} 😘')
                
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='чмо')
    async def chmo(self, ctx: commands.Context):
        sArgs = ctx.message.content.split(' ', 1)
        if len(ctx.chatters) == 0:
            await ctx.send('В этом чате пусто PoroSad')
        elif len(sArgs) == 1:
            await ctx.send(f'@{ctx.author.name} назвал чмом @{random.choice(tuple(ctx.chatters)).name} 🤪')
        else:
            if not IsValidArgs(sArgs[1]):
                await ctx.send(f'@{ctx.author.name}, бана хочешь моего?')
            else:
                await ctx.send(f'@{ctx.author.name} назвал чмом {str(sArgs[1])} 🤪')
            
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='база')
    async def baza(self, ctx: commands.Context):
        await ctx.send(f'хуяза')
        
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.channel)
    @commands.command(name='анек')
    async def anek(self, ctx: commands.Context):
        await ctx.send(GetRandAnek())
    
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
            
    @commands.command(name='бусти', aliases=['boosty'])
    async def boosty(self, ctx: commands.Context):
        msg = boostys.get(ctx.channel.name)
        if(not msg == None):
            await ctx.send(msg)        

    #Обработка исключений
    async def event_command_error(self, ctx, error: Exception) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'Команда "{error.command.name}" на кулдауне еще {int(error.retry_after)} сек.')
        else:
            print(error)
    
    #Событие подключения к чату
    async def event_join(self, channel: Channel, user: User):
        if channel.name == user.name:
            await channel.send(f'@{user.name}, привет стример! 😘')
            print(f'{datetime.datetime.now()}: Стример в чате {user.name}')
        print(f'{datetime.datetime.now()}: Пользователь {user.name} вошел в чат {channel.name}')

bot = Bot()
bot.run()
