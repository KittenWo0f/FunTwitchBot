"""Ежедневные «рулетки»: !сосиска, !вареник, !булки.

Три почти одинаковые команды из исходного кода сведены к одному движку:
различия (поля, формулировки, склонение) описаны данными в RollSpec.
Результат кэшируется на сутки на пользователя.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

from twitchio.ext import commands

from bot.components.base import BaseComponent
from bot.data import roll_data
from bot.text_utils import value_by_threshold

_EMOTE = {3: "PoroSad", 8: "Stare", 13: "Hmm", 18: "Hmmege", 23: "SHTO", 28: "EZ", 32: "Pog", 35: "POGCHAMP", 37: "HYPERPOG"}


@dataclass(frozen=True)
class RollSpec:
    key: str
    data: dict
    zero_message: str
    extras: tuple[tuple[int, str], ...]       # (порог, текст) по убыванию порога
    lines: tuple[str, ...]                    # шаблоны строк ответа
    choice_keys: tuple[str, ...]              # какие списки из data выбирать случайно
    side_range: tuple[int, int] = (1, 13)     # второй параметр (ширина/толщина/упругость)


SPECS = {
    "sausage": RollSpec(
        key="sausage", data=roll_data.SAUSAGE,
        zero_message="💀 Отсутствует (0 см)  📐 0 см\nЭто уже не сосиска, это философский вакуум...",
        extras=((34, "🌌 Это уже не сосиска. Это оружие массового поражения."),
                (29, "🔥 Опасно мощная сосиска."), (25, "💪 Внушает уважение.")),
        lines=("{emote} Длина: {main} см", "📏 Ширина: {side} см", "🌀 Форма: {shapes}",
               "✨ Редкость: {rarity}", "🧠 Состояние: {states}"),
        choice_keys=("shapes", "states")),
    "varenik": RollSpec(
        key="varenik", data=roll_data.VARENIK,
        zero_message="💀 Отсутствует (0 см)  📐 0 см\nЭто уже не вареник, это философский вакуум...",
        extras=((34, "🌌 Это уже не вареник. Это оружие массового насыщения."),
                (29, "🔥 Опасно мощный вареник."), (25, "💪 Внушает уважение (и аппетит).")),
        lines=("{emote} Размер: {main} см", "📏 Толщина теста: {side} мм", "🌀 Форма: {shapes}",
               "🥟 Начинка: {fillings}", "✨ Редкость: {rarity}", "🧠 Состояние: {states}"),
        choice_keys=("shapes", "fillings", "states")),
    "bulki": RollSpec(
        key="bulki", data=roll_data.BULKI,
        zero_message="💀 Отсутствуют (0 баллов)\nПлоскость как у стены. Тревожно.",
        extras=((34, "🌌 Это уже не булки. Это архитектурное достояние."),
                (29, "🔥 Опасно мощные булки."), (25, "💪 Внушают уважение (и зависть).")),
        lines=("{emote} Объём: {main} баллов", "📏 Упругость: {side}/13", "🌀 Форма: {shapes}",
               "🧠 Состояние: {conditions}", "✨ Редкость: {rarity}"),
        choice_keys=("shapes", "conditions")),
}
_NOUN = {"sausage": "сосиску", "varenik": "вареник", "bulki": "булки"}


class GamesComponent(BaseComponent):
    def __init__(self, bot) -> None:
        super().__init__(bot)
        self._day = date.today()
        self._cache: dict[tuple[str, str], dict] = {}

    def _roll(self, spec: RollSpec, user_id: str) -> dict:
        today = date.today()
        if today != self._day:  # новые сутки — сбрасываем кэш целиком
            self._day, self._cache = today, {}
        key = (spec.key, user_id)
        if key not in self._cache:
            main = random.randint(0, 37)
            result = {"main": main, "side": random.randint(*spec.side_range),
                      "rarity": value_by_threshold(spec.data["rarity"], main),
                      "emote": value_by_threshold(_EMOTE, main)}
            result.update({k: random.choice(spec.data[k]) for k in spec.choice_keys})
            self._cache[key] = result
        return self._cache[key]

    async def _send(self, ctx: commands.Context, spec_key: str) -> None:
        spec = SPECS[spec_key]
        res = self._roll(spec, ctx.chatter.id)
        head = f"@{ctx.chatter.name} имеет {_NOUN[spec_key]}:"
        if res["main"] == 0:
            await ctx.reply(f"{head} {spec.zero_message}")
            return
        extra = next((text for limit, text in spec.extras if res["main"] >= limit), "")
        body = "\n".join(line.format(**res) for line in spec.lines)
        await ctx.reply(f"{head}\n{body}" + (f"\n{extra}" if extra else ""))

    @commands.cooldown(rate=1, per=30, key=commands.BucketType.user)
    @commands.command(name="сосиска")
    async def sausage(self, ctx: commands.Context) -> None:
        await self._send(ctx, "sausage")

    @commands.cooldown(rate=1, per=30, key=commands.BucketType.user)
    @commands.command(name="вареник")
    async def varenik(self, ctx: commands.Context) -> None:
        await self._send(ctx, "varenik")

    @commands.cooldown(rate=1, per=30, key=commands.BucketType.user)
    @commands.command(name="булки")
    async def bulki(self, ctx: commands.Context) -> None:
        await self._send(ctx, "bulki")
