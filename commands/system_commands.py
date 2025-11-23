from twitchio.ext import commands
from gpiozero import CPUTemperature
from bot_settings import *

class SystemCommands(commands.Cog):
    """Класс для системных команд"""
    
    def __init__(self, bot):
        self.bot = bot

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
            success = await self.bot.telegram_notifier.send_message(f'''{ctx.author.name} ({ctx.channel.name}): {phrase}''')
            if success:
                await ctx.reply(f'Ваше сообщение было отправлено админу NOTED')
            else:
                await ctx.reply(f'Не удалось отправить ваше сообщение админу NotLikeThis')
        else:
            await ctx.reply(f'Необходимо добавить текст сообщения в команде CaitThinking ')