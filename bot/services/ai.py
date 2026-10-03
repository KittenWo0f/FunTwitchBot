"""Генерация текста через OpenRouter."""
from __future__ import annotations

import logging

import aiohttp

from bot import config

log = logging.getLogger(__name__)
_URL = "https://openrouter.ai/api/v1/chat/completions"
_TIMEOUT = aiohttp.ClientTimeout(total=30)


class AIError(RuntimeError):
    pass


async def _ask(session: aiohttp.ClientSession, prompt: str) -> str:
    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {config.OPENROUTER_API_KEY}"}
    async with session.post(_URL, headers=headers, json=payload, timeout=_TIMEOUT) as resp:
        data = await resp.json(content_type=None)
        if resp.status != 200:
            log.warning("OpenRouter error %s: %s", resp.status, data)
            raise AIError(f"статус {resp.status}")
    return data["choices"][0]["message"]["content"].strip()


async def absurd_fact(session: aiohttp.ClientSession, topic: str) -> str:
    return await _ask(session, (
        f"Придумай абсурдный, смешной псевдонаучный факт про «{topic}». "
        "Один абзац, без вступлений, без кавычек, на русском. Желательно уложиться в 150 символов"))


async def joke(session: aiohttp.ClientSession, topic: str) -> str:
    return await _ask(session, (
        f"Придумай анекдот про «{topic}». Один абзац, без вступлений, без кавычек, на русском. "
        "Желательно уложиться в 200 символов"))
