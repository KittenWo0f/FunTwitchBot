from bot_settings import *
from some_data import *
from twitchio.ext import commands
from twitchio.user import User
from twitchio.channel import Channel

import time
import datetime
import random
import re
from bot_utilities import *

from gpiozero import CPUTemperature

class Bot(commands.Bot):

    #Инициализация бота
    def __init__(self):
        super().__init__(token=ACCESS_TOKEN, prefix=PREFIX, initial_channels=INITIAL_CHANNELS)

    #Событие готовности бота
    async def event_ready(self):
        print(f'Вошел как | {self.nick}')
        print(f'Id пользователя | {self.user_id}')

    #Обработка сообщений
    async def event_message(self, message):
        if message.echo:
            return
        print(f'{message.timestamp}({message.channel.name}){message.author.name}:{message.content}')
        
        if str(message.content).startswith(PREFIX):
            await self.handle_commands(message)
            return
        
        #Опускание мубота
        if message.author.name == 'moobot':
            await message.channel.send(f'@{message.author.name}, мубот соси')
            return

        check_str = re.split(r',|!|;|\.|\?', message.content)[0]
        cust_com = custom_commands_with_tag.get(str(check_str.lower()))
        if(cust_com):
            await message.channel.send(f'@{message.author.name}, {random.choice(cust_com)}')
            return
        
        if(check_str in custom_copypast_cmd):
            await message.channel.send(check_str)
            return
            
        if(str(f'@{self.nick}') in str(message.content).lower()):
            await message.channel.send(f'@{message.author.name}, {random.choice(bot_messages)}')
            return
            

    # #Команды
    # @commands.command(name='привет', aliases=['hello'])
    # async def hello(self, ctx: commands.Context):
    #     await ctx.send(f'Здорова заебал, @{ctx.author.name}!')
        
    # @commands.command(name='пока', aliases=['bye'])
    # async def bye(self, ctx: commands.Context):
    #     await ctx.send(f'Не уходи, @{ctx.author.name} PoroSad')

    @commands.command(name='пинг', aliases=['ping'])
    async def ping(self, ctx: commands.Context):
        await ctx.send(f'Понг {ctx.author.name}!')

    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.member)
    @commands.command(name='чмок')
    async def chmok(self, ctx: commands.Context):
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
                
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='чмо')
    async def chmo(self, ctx: commands.Context):
        sArgs = ctx.message.content.rstrip(' ').split(' ', 1)
        if len(ctx.chatters) == 0:
            await ctx.send('В этом чате пусто PoroSad')
        elif len(sArgs) == 1:
            await ctx.send(f'@{ctx.author.name} назвал чмом @{random.choice(tuple(ctx.chatters)).name} 🤪')
        else:
            if not IsValidArgs(sArgs[1].rstrip(' ')):
                await ctx.send(f'@{ctx.author.name}, бана хочешь моего?')
            elif ctx.author.name in sArgs[1].lower():
                await ctx.send(f'@{ctx.author.name} не надо так с собой Stare')
            elif self.nick in sArgs[1].lower():
                await ctx.send(f'@{ctx.author.name}, что я тебе плохого сделал? PoroSad')
            else:
                await ctx.send(f'@{ctx.author.name} назвал чмом {str(sArgs[1])} 🤪')
            
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='база')
    async def baza(self, ctx: commands.Context):
        await ctx.send(f'хуяза')
        
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.channel)
    @commands.command(name='анек', aliases=['кринж'])
    async def anek(self, ctx: commands.Context):
        await ctx.send(GetRandAnek())
        
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.member)
    @commands.command(name='праздник', aliases=['holiday'])
    async def Holiday(self, ctx: commands.Context):
        await ctx.send(GetTodayHoliday())
    
    @commands.cooldown(rate=1, per=3600, bucket=commands.Bucket.channel)
    @commands.command(name='дыня', aliases=['melon'])
    async def dinya(self, ctx: commands.Context):
        if (not ctx.channel.name == 'gufovicky'):
            return
        for kuplet in dinya:
            time.sleep(1.5)
            await ctx.send(kuplet.replace("\n", " "))
            
    @commands.cooldown(rate=1, per=1800, bucket=commands.Bucket.channel)
    @commands.command(name='хрюковский')
    async def hrykovsciy(self, ctx: commands.Context):
        if (not ctx.channel.name == 'gufovicky'):
            return
        for kuplet in hrykovskiy:
            time.sleep(1.5)
            await ctx.send(kuplet.replace("\n", " "))
    
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
        
    @commands.command(name='help', aliases=['commands', 'команды', 'помощь'])
    async def help_bot(self, ctx: commands.Context):
        await ctx.send(f'@{ctx.author.name} Я бот и я могу: !пинг, !чмок, !чмо, !база, !кринж, !анек. На некоторых каналах: !вк, !бусти, !тг')
        
    #Команды для белого списка 
    @commands.command(name='горячесть', aliases=['температура', 'темп', 'temp'])
    async def help_bot(self, ctx: commands.Context):
        if ctx.author.name in white_list:
            cpuT = CPUTemperature()
            await ctx.send(f'Моя горячесть равна {cpuT.temperature} градусам')

    #Обработка исключений
    async def event_command_error(self, ctx, error: Exception) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'Команда "{error.command.name}" на кулдауне еще {int(error.retry_after)} сек.')
        else:
            print(error)
    
    #Событие подключения к чату
    async def event_join(self, channel: Channel, user: User):
        print(f'{datetime.datetime.now()}: Пользователь {user.name} вошел в чат {channel.name}')
        # if user.name == 'moobot':
        #     await channel.send(f'@{user.name}, че приперся?')
        if channel.name == user.name:
            await channel.send(f'@{user.name}, привет стример! 😘')
            print(f'{datetime.datetime.now()}: Стример в чате {user.name}')

bot = Bot()
bot.run()
