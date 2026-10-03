"""Асинхронные запросы к внешним сайтам. Сессию aiohttp создаёт и закрывает бот."""
from __future__ import annotations

import random
import zoneinfo
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from timezonefinder import TimezoneFinder

from bot import config

_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/39.0.2171.95 Safari/537.36"}
_TIMEOUT = aiohttp.ClientTimeout(total=10)
_tf = TimezoneFinder()  # создание дорогое — держим один экземпляр

ZODIAC = {
    "овен": "aries", "телец": "taurus", "близнецы": "gemini", "рак": "cancer",
    "лев": "leo", "дева": "virgo", "весы": "libra", "скорпион": "scorpio",
    "стрелец": "sagittarius", "козерог": "capricorn", "водолей": "aquarius", "рыбы": "pisces",
}


async def _get_text(session: aiohttp.ClientSession, url: str, **kw) -> str:
    async with session.get(url, headers=_UA, timeout=_TIMEOUT, **kw) as resp:
        resp.raise_for_status()
        return await resp.text(errors="ignore")


async def random_anek(session: aiohttp.ClientSession) -> str:
    html = await _get_text(session, f"https://anekdotbar.ru/page/{random.randrange(1, 756)}/")
    blocks = BeautifulSoup(html, "html.parser").find_all("div", class_="tecst")
    parts = random.choice(blocks).find_all(string=True, recursive=False)
    return " ".join(parts).strip()


async def today_holiday(session: aiohttp.ClientSession) -> str:
    html = await _get_text(session, "https://kakoysegodnyaprazdnik.ru/")
    spans = BeautifulSoup(html, "html.parser").find_all("span", itemprop="text")
    return str(random.choice(spans).find_all(string=True, recursive=False)[0])


async def random_fact(session: aiohttp.ClientSession) -> str | None:
    html = await _get_text(session, "https://randstuff.ru/fact/")
    cell = BeautifulSoup(html, "html.parser").select_one("div#fact table.text td")
    return cell.get_text(strip=True) if cell else None


async def horoscope(session: aiohttp.ClientSession, sign: str) -> str | None:
    slug = ZODIAC.get(sign.lower())
    if not slug:
        return None
    html = await _get_text(session, f"https://horoscopes.rambler.ru/{slug}/")
    block = BeautifulSoup(html, "html.parser").find("div", itemprop="articleBody")
    para = block.find("p") if block else None
    return para.get_text(strip=True) if para else None


async def usd_rub(session: aiohttp.ClientSession) -> float:
    async with session.get("https://www.cbr-xml-daily.ru/latest.js", timeout=_TIMEOUT) as resp:
        resp.raise_for_status()
        data = await resp.json(content_type=None)
    return 1 / data["rates"]["USD"]


async def weather(session: aiohttp.ClientSession, city: str) -> tuple[int, dict]:
    params = {"q": city, "appid": config.OPENWEATHER_API_KEY, "units": "metric", "lang": "ru"}
    async with session.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=_TIMEOUT) as resp:
        return resp.status, await resp.json(content_type=None)


async def current_time_in_city(session: aiohttp.ClientSession, city: str) -> str | None:
    """Геокодинг через Nominatim -> часовой пояс -> локальное время HH:MM:SS."""
    params = {"q": city, "format": "json", "limit": 1}
    headers = {"User-Agent": "twitch-chat-bot/1.0 (self-hosted)"}  # Nominatim требует осмысленный UA
    try:
        async with session.get("https://nominatim.openstreetmap.org/search", params=params,
                               headers=headers, timeout=_TIMEOUT) as resp:
            data = await resp.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError):
        return None
    if not data:
        return None
    tz_name = _tf.timezone_at(lat=float(data[0]["lat"]), lng=float(data[0]["lon"]))
    if not tz_name:
        return None
    return datetime.now(zoneinfo.ZoneInfo(tz_name)).strftime("%H:%M:%S")
