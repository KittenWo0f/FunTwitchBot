from random import choice as randChoise
from urllib.parse import urlparse
from regex_tests import *

def GetRandomEmotion() -> str:
    emotions = ['GunRun', 'GlitchCat', 'FallHalp', 'FallWinning', 'BrokeBack', 'BloodTrail', 'CaitlynS', 'CarlSmile']
    emotion = randChoise(emotions)
    return emotion

def checkRegexRule(val, rule):
    import re
    regex = re.compile(rule, re.IGNORECASE)
    res = re.search(regex, val)
    return res is not None

def isValidArgs(args) -> bool:
    for arg in args.split():
        if (checkRegexRule(str(arg), REGEX_IS_URL_TEST)):
            return False
        if (checkRegexRule(str(arg), REGEX_SPEC_SYMB_RULE_TEST)):
            return False
    return True