"""Чистые функции работы с текстом и числами (без I/O)."""
from __future__ import annotations

import re

from bot.data.regex_tests import REGEX_SPEC_SYMB_RULE_TEST, SPEC_SYMBOLS

_ARGS_RE = re.compile(REGEX_SPEC_SYMB_RULE_TEST, re.IGNORECASE)
_SPEC_SET = frozenset(SPEC_SYMBOLS)
_SPLIT_RE = re.compile(r",|!|;|\.|\?")

CHAT_LIMIT = 250  # безопасный лимит длины одного сообщения в Twitch (макс. 500)


def first_token(text: str) -> str:
    """Часть сообщения до первого знака препинания (для приветствий/копипасты)."""
    return _SPLIT_RE.split(text, maxsplit=1)[0]


def is_valid_args(args: str) -> bool:
    """Защита от спецсимволов в пользовательском вводе, который бот повторяет в чат."""
    if not _ARGS_RE.search(args):
        return False
    if sum(1 for ch in args if ch in _SPEC_SET) > 7:
        return False
    if len(args) > 25 and " " not in args:
        return False
    return True


def split_message(text: str, max_length: int = CHAT_LIMIT) -> list[str]:
    """Режет текст на куски <= max_length, не разрывая слова (длинные слова режутся жёстко)."""
    chunks: list[str] = []
    line = ""
    for word in text.split():
        while len(word) > max_length:  # слово длиннее лимита
            if line:
                chunks.append(line)
                line = ""
            chunks.append(word[:max_length])
            word = word[max_length:]
        candidate = f"{line} {word}" if line else word
        if len(candidate) <= max_length:
            line = candidate
        else:
            chunks.append(line)
            line = word
    if line:
        chunks.append(line)
    return chunks


def plural_ru(n: int, one: str, few: str, many: str) -> str:
    """Склонение после числительного: plural_ru(21, 'день', 'дня', 'дней') -> 'день'."""
    if 11 <= n % 100 <= 19:
        return many
    rem = n % 10
    if rem == 1:
        return one
    if 2 <= rem <= 4:
        return few
    return many


def fmt_num(n: int) -> str:
    """1234567 -> 1'234'567"""
    return f"{n:,}".replace(",", "'")


def value_by_threshold(table: dict[int, str], value: int) -> str | None:
    """Первое значение, у которого ключ >= value (таблицы редкости/смайлов)."""
    for limit, result in table.items():
        if value <= limit:
            return result
    return None
