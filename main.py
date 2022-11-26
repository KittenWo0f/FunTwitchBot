from twitch_tokens import *
from twitchio.ext import commands
import time
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
        await ctx.send(f'Hello {ctx.author.name}!')

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
            await ctx.send(f'@{ctx.author.name} чмокнул {sArgs[1]} 😘')
            
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='чмо')
    async def chmo(self, ctx: commands.Context):
        sArgs = ctx.message.content.split(' ', 1)
        if len(ctx.chatters == 0):
            await ctx.send('В этом чате нет никого')
        elif len(sArgs) == 1:
            await ctx.send(f'@{ctx.author.name} назвал чмом @{random.choice(tuple(ctx.chatters)).name} 🤪')
        else:
            await ctx.send(f'@{ctx.author.name} назвал чмом {sArgs[1]} 🤪')
            
    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
    @commands.command(name='база')
    async def baza(self, ctx: commands.Context):
        await ctx.send(f'хуяза')

    #Обработка исключений
    async def event_command_error(self, ctx, error: Exception) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'Команда "{error.command.name}" на кулдауне еще {int(error.retry_after)} сек.')
            

bot = Bot()
bot.run()
