from random import choice as randChoise
from urllib.parse import urlparse
from regex_tests import *
#Для парсера
from bs4 import BeautifulSoup
import requests
import random
#Для подсчета спецсимволов
from collections import Counter
#Для сохранения объектов
import pickle

def GetRandomEmotion() -> str:
    emotions = ['GunRun', 'GlitchCat', 'FallHalp', 'FallWinning', 'BrokeBack', 'BloodTrail', 'CaitlynS', 'CarlSmile']
    emotion = randChoise(emotions)
    return emotion

def CheckRegexRule(val, rule):
    import re
    regex = re.compile(rule, re.IGNORECASE)
    res = re.search(regex, val)
    return res is not None

def IsValidArgs(args) -> bool:
    if CheckRegexRule(str(args).replace(" ",""), REGEX_IS_URL_TEST):
        return False
    if not CheckRegexRule(str(args), REGEX_SPEC_SYMB_RULE_TEST):
        return False
    if GetCharCnt(args, set(SPEC_SYMBOLS)) > 7:
        return False
    if len(args) > 25 and not ' ' in args:
        return False
    for arg in args.split():
        if CheckRegexRule(str(arg), REGEX_IS_URL_TEST):
            return False
        if not CheckRegexRule(str(arg), REGEX_SPEC_SYMB_RULE_TEST):
            return False
    return True

def GetRandAnek() -> str:
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

def GetTodayHoliday() -> str:
    url = f'https://kakoysegodnyaprazdnik.ru//'
    header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    }
    req = requests.get(url, headers=header)
    soup = BeautifulSoup(req.content.decode('utf-8','ignore'), "html.parser")
    holiHTML = random.choice(soup.find_all('span', itemprop='text')).find_all(text = True, recursive=False)[0]
    return str(holiHTML)

def GetCharCnt(string, symbols) -> int:
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
