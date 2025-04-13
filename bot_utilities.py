from random import choice as randChoise
from urllib.parse import urlparse
from regex_tests import *
import datetime
# Для парсера
from bs4 import BeautifulSoup
import requests
import random
# Для подсчета спецсимволов
from collections import Counter
# Для сохранения объектов
import pickle
# Для времени 
import pytz
from timezonefinder import TimezoneFinder
import aiohttp

def get_random_emotion() -> str:
    emotions = ['GunRun', 'GlitchCat', 'FallHalp', 'FallWinning', 'BrokeBack', 'BloodTrail', 'CaitlynS', 'CarlSmile']
    emotion = randChoise(emotions)
    return emotion

def check_regex_rule(val, rule):
    import re
    regex = re.compile(rule, re.IGNORECASE)
    res = re.search(regex, val)
    return res is not None

def is_valid_args(args) -> bool:
    if not check_regex_rule(str(args), REGEX_SPEC_SYMB_RULE_TEST):
        return False
    if get_char_cnt(args, set(SPEC_SYMBOLS)) > 7:
        return False
    if len(args) > 25 and not ' ' in args:
        return False
    for arg in args.split():
        if not check_regex_rule(str(arg), REGEX_SPEC_SYMB_RULE_TEST):
            return False
    return True

def get_rand_anek() -> str:
    # url = f'https://anekdotbar.ru/korotkie/page/{random.randrange(1,33)}/'
    #TODO Спарсить всё на диск и брать оттуда
    url = f'https://anekdotbar.ru/page/{random.randrange(1,756)}/' 
    req = requests.get(url)
    soup = BeautifulSoup(req.text, "html.parser")
    aneksHTML = soup.find_all('div', class_ = 'tecst')
    
    fullAnek = ''
    while True:
        aneksList = random.choice(tuple(aneksHTML)).find_all(text = True, recursive=False)
        fullAnek = ' '.join(aneksList).strip()
        if len(fullAnek) < 250:
            break
    return fullAnek

def get_today_holiday() -> str:
    url = f'https://kakoysegodnyaprazdnik.ru//'
    header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    }
    req = requests.get(url, headers=header)
    soup = BeautifulSoup(req.content.decode('utf-8','ignore'), "html.parser")
    holiHTML = random.choice(soup.find_all('span', itemprop='text')).find_all(text = True, recursive=False)[0]
    return str(holiHTML)

def get_rand_fact() -> str:
    url = f'https://randstuff.ru/fact/'
    header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    }
    req = requests.get(url, headers=header)
    soup = BeautifulSoup(req.content.decode('utf-8','ignore'), "html.parser")
    fact_div = soup.find('div', id='fact')
    res_fact = None
    if fact_div:
        fact_table = fact_div.find('table', class_='text')
        if fact_table:
            fact_td = fact_table.find('td')
            if fact_td:
                res_fact = fact_td.get_text(strip=True)
    return res_fact

def get_prediction(sign: str) -> str | None:
    sign = sign.lower()
    signes = {
        "овен": "aries",
        "телец": "taurus",
        "близнецы": "gemini",
        "рак": "cancer",
        "лев": "leo",
        "дева": "virgo",
        "весы": "libra",
        "скорпион": "scorpio",
        "стрелец": "sagittarius",
        "козерог": "capricorn",
        "водолей": "aquarius",
        "рыбы": "pisces"
    }
    
    sign_name = signes.get(sign)
    if not sign_name:
        return None
    
    url = f'https://horoscopes.rambler.ru/{sign_name}/'
    header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    }
    req = requests.get(url, headers=header)
    soup = BeautifulSoup(req.content.decode('utf-8','ignore'), "html.parser")

    # Находим элемент с текстом гороскопа
    horoscope_block = soup.find('div', itemprop='articleBody')
    if horoscope_block:
        horoscope_text = horoscope_block.find('p').get_text(strip=True)
        return horoscope_text
    else:
        return None

def split_string_by_words(text, max_length=250) -> list: 
    """
    Разбивает строку на подстроки, сохраняя целостность слов.
    
    :param text: Исходная строка для разбиения
    :param max_length: Максимальная длина подстроки (по умолчанию 250)
    :return: Список подстрок
    """
    if not text:
        return []
    
    words = text.split()
    result = []
    current_line = []
    current_length = 0
    
    for word in words:
        # Проверяем, поместится ли слово в текущую строку
        # Учитываем пробел между словами (если это не первое слово)
        word_length = len(word)
        space_length = 1 if current_line else 0
        
        if current_length + space_length + word_length <= max_length:
            current_line.append(word)
            current_length += space_length + word_length
        else:
            # Если строка не пустая, добавляем её в результат
            if current_line:
                result.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                # Если слово само по себе длиннее max_length, разбиваем его принудительно
                result.append(word[:max_length])
                current_line = [word[max_length:]]
                current_length = len(word[max_length:])
    
    # Добавляем последнюю строку, если она не пустая
    if current_line:
        result.append(' '.join(current_line))
        
    return result

def get_char_cnt(string, symbols) -> int:
    cnt = 0
    counter = Counter(string)
    for char in symbols:
        cnt += counter[char]
    return cnt

def save_obj(obj, name):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    try:
        with open('obj/' + name + '.pkl', 'rb') as f:
            return pickle.load(f)
    except (OSError, IOError) as e:
        return None
def decl_of_num(n, titles):
    if n%10==1 and n%100!=11:
        return titles[0]
    elif n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20):
        return titles[1]
    else:
        return titles[2]

def replace_chars(s, chars_map):
    res = str()
    for char in s:
        res += chars_map[char]
    return res

def get_val_by_max_val(dictionary, val):
    for k, v in dictionary.items():
        if val <= k:
            return v
    return None

def hours_from_mounth_begin() -> float:
    now = datetime.datetime.now()
    first_day_of_month = datetime.datetime(now.year, now.month, 1)
    time_passed = now - first_day_of_month
    hours_passed = (time_passed.total_seconds() + 1) // 3600
    return hours_passed

async def fetch_location(city_name: str, session: aiohttp.ClientSession) -> tuple:
    """Асинхронный геокодинг через Nominatim API"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': city_name,
        'format': 'json',
        'limit': 1
    }
    
    async with session.get(url, params=params) as response:
        data = await response.json()
        if not data:
            raise ValueError("Город не найден")
        return float(data[0]['lat']), float(data[0]['lon'])

async def get_current_time_in_city(city_name: str) -> str | None:
    async with aiohttp.ClientSession() as session:
        try:
            # Получаем координаты
            lat, lon = await fetch_location(city_name, session)
            
            # Определяем временную зону
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lat=lat, lng=lon)
            if not timezone_str:
                return None
            
            # Получаем текущее время
            timezone = pytz.timezone(timezone_str)
            current_time = datetime.datetime.now(timezone)
            return current_time.strftime('%H:%M:%S')
        
        except ValueError as e:
            return None
        except Exception as e:
            return None