from twitchio.ext import commands
import requests
import datetime
from dateutil import tz
from utils.bot_utilities import *
from data.some_data import *
from bot_settings import *

class InfoCommands(commands.Cog):
    """Класс для информационных команд бота"""
    
    def __init__(self, bot):
        self.bot = bot

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
        command_list = [cmd for cmd in self.bot.commands]
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
                username = phrase.lstrip('@')
                search_user = await self.bot.fetch_channel(username)
                search_user = search_user.user
                search_username = username
            else:
                search_user = channel_user
                search_username = channel_user.name
            last_activity = self.bot.db_log_client.get_user_last_activity(channel_user.id, search_user.id)
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
                country = data["sys"]["country"]
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
                
                await ctx.reply(f'В {city_name} ({country}) на данный момент {temp:.1f}°C. '
                            f'{description.capitalize()}. '
                            f'Ветер {wind_dir} {wind_speed:.1f} м/с. '
                            f'{smile}')
                            
            elif response.status_code == 404:
                await ctx.reply(f'Город "{phrase}" не найден PoroSad')
            else:
                await ctx.reply(f'Ошибка получения данных о погоды (код: {response.status_code}) PoroSad')
                
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
    async def time(self, ctx: commands.Context, *, phrase: str | None):
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