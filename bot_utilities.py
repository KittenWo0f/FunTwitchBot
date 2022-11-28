from random import choice as randChoise
from urllib.parse import urlparse
from regex_tests import *
#Для парсера
from bs4 import BeautifulSoup
import requests
import random

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
    for arg in args.split():
        if CheckRegexRule(str(arg), REGEX_IS_URL_TEST):
            return False
        if not CheckRegexRule(str(arg), REGEX_SPEC_SYMB_RULE_TEST):
            return False
    return True

def GetRandAnek() -> str:
    url = f'https://anekdotbar.ru/korotkie/page/{random.randrange(1,33)}/'
    req = requests.get(url)
    soup = BeautifulSoup(req.text, "html.parser")
    aneksHTML = soup.find_all('div', class_ = 'tecst')
    aneksList = random.choice(tuple(aneksHTML)).find_all(text = True, recursive=False)
    return ' '.join(aneksList).strip()
