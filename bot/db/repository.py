"""Доступ к PostgreSQL.

Что изменено относительно db_message_log_client:
  * пул соединений вместо одного соединения; после ошибки выполняется rollback
    (раньше соединение оставалось в «aborted transaction» и все дальнейшие запросы падали);
  * psycopg2 синхронный, поэтому каждый вызов уходит в поток (asyncio.to_thread) и
    не блокирует event loop бота;
  * параметры передаются как %s без кавычек (раньше '%s' / INTERVAL '%s hours');
  * кэш известных пользователей — не пишем в users на каждое сообщение.
Публичные методы возвращают None при ошибке БД (как и раньше).
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
import os
import re
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from psycopg2 import pool

log = logging.getLogger(__name__)
_ASYNC_LOCK_TIMEOUT = 600


class Database:
    def __init__(self, host: str, port: int, name: str, user: str, password: str) -> None:
        self._conn_args = dict(host=host, port=port, dbname=name, user=user, password=password)
        self._name, self._host, self._port, self._user, self._password = name, host, port, user, password
        self._pool: pool.ThreadedConnectionPool | None = None
        self._known_users: dict[int, tuple[str, str]] = {}

    # ---------- жизненный цикл ----------
    def connect(self) -> bool:
        try:
            self._pool = pool.ThreadedConnectionPool(1, 5, **self._conn_args)
        except Exception:
            log.exception("Не удалось подключиться к БД")
            return False
        return True

    def close(self) -> None:
        if self._pool:
            self._pool.closeall()
            self._pool = None

    # ---------- низкоуровневые помощники (синхронные) ----------
    @contextmanager
    def _cursor(self, commit: bool = False) -> Iterator[Any]:
        if self._pool is None and not self.connect():
            raise ConnectionError("БД недоступна")
        conn = self._pool.getconn()  # type: ignore[union-attr]
        try:
            with conn.cursor() as cur:
                yield cur
            conn.commit() if commit else conn.rollback()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)  # type: ignore[union-attr]

    def _fetchall(self, sql: str, params: Sequence[Any] | dict[str, Any] = ()) -> list[tuple] | None:
        try:
            with self._cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()
        except Exception:
            log.exception("Ошибка запроса к БД")
            return None

    def _fetchone(self, sql: str, params: Sequence[Any] | dict[str, Any] = ()) -> tuple | None:
        rows = self._fetchall(sql, params)
        return rows[0] if rows else None

    def _execute(self, sql: str, params: Sequence[Any] | dict[str, Any] = ()) -> bool:
        try:
            with self._cursor(commit=True) as cur:
                cur.execute(sql, params)
            return True
        except Exception:
            log.exception("Ошибка записи в БД")
            return False

    @staticmethod
    async def _run(fn, *args):
        return await asyncio.to_thread(fn, *args)

    # ---------- запись ----------
    def _ensure_user(self, user_id: int, display_name: str) -> None:
        name = display_name.lower()
        if self._known_users.get(user_id) == (name, display_name):
            return
        ok = self._execute(
            """INSERT INTO users (id, name, display_name) VALUES (%s, %s, %s)
               ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, display_name = EXCLUDED.display_name
               WHERE users.name != EXCLUDED.name OR users.display_name != EXCLUDED.display_name""",
            (user_id, name, display_name))
        if ok:
            self._known_users[user_id] = (name, display_name)

    def _log_message(self, text: str, author_id: int, author_name: str, channel_id: int, channel_name: str) -> None:
        self._ensure_user(channel_id, channel_name)
        self._ensure_user(author_id, author_name)
        self._execute("INSERT INTO messages (timestamp, channel_id, author_id, message) VALUES (now(), %s, %s, %s)",
                      (channel_id, author_id, text))

    async def log_message(self, text: str, author_id: int, author_name: str, channel_id: int, channel_name: str) -> None:
        await self._run(self._log_message, text, author_id, author_name, channel_id, channel_name)

    async def add_denunciation(self, user_id: int) -> bool:
        return await self._run(self._execute, """
            INSERT INTO denunciations (user_id, den_count) VALUES (%s, 1)
            ON CONFLICT (user_id) DO UPDATE SET den_count = denunciations.den_count + 1""", (user_id,))

    async def set_ogey(self, channel_id: int, ogey_id: int) -> bool:
        return await self._run(self._execute,
            "INSERT INTO ogeyofday_history (id, channel_id, date) VALUES (%s, %s, now())", (ogey_id, channel_id))

    # ---------- чтение: простые значения ----------
    async def last_activity(self, channel_id: int, author_id: int) -> dt.datetime | None:
        row = await self._run(self._fetchone,
            "SELECT timestamp FROM messages WHERE author_id = %s AND channel_id = %s ORDER BY timestamp DESC LIMIT 1",
            (author_id, channel_id))
        return row[0] if row else None

    async def last_active_users(self, channel_id: int, hours: int = 12, limit: int = 20) -> list[str] | None:
        rows = await self._run(self._fetchall, """
            SELECT u.display_name FROM messages m JOIN users u ON u.id = m.author_id
            WHERE m.timestamp >= now() - make_interval(hours => %s) AND m.channel_id = %s
            GROUP BY u.id ORDER BY MAX(m.timestamp) DESC LIMIT %s""", (hours, channel_id, limit))
        return None if rows is None else [r[0] for r in rows]

    async def random_message_of_ogey_or_streamer(self, channel_id: int) -> str | None:
        row = await self._run(self._fetchone, """
            SELECT message FROM messages
            WHERE author_id = COALESCE(
                (SELECT id FROM ogeyofday_history WHERE channel_id = %s ORDER BY date DESC LIMIT 1), %s)
            ORDER BY random() LIMIT 1""", (channel_id, channel_id))
        return row[0] if row else None

    async def random_user_last_hours(self, channel_id: int, hours: int) -> int | None:
        row = await self._run(self._fetchone, """
            SELECT author_id FROM messages
            WHERE timestamp BETWEEN now() - make_interval(hours => %s) AND now() AND channel_id = %s
            GROUP BY author_id ORDER BY random() LIMIT 1""", (hours, channel_id))
        return row[0] if row else None

    async def current_ogey(self, channel_id: int) -> str | None:
        row = await self._run(self._fetchone, """
            SELECT u.display_name FROM ogeyofday_history oh JOIN users u ON u.id = oh.id
            WHERE oh.channel_id = %s ORDER BY date DESC LIMIT 1""", (channel_id,))
        return row[0] if row else None

    # ---------- чтение: топы ----------
    async def top_users_month(self, channel_id: int) -> list[tuple[str, int]] | None:
        return await self._run(self._fetchall, """
            SELECT u.display_name, COUNT(*) FROM messages m JOIN users u ON u.id = m.author_id
            WHERE m.timestamp >= date_trunc('month', now()) AND m.channel_id = %s
            GROUP BY u.id ORDER BY COUNT(*) DESC LIMIT 15""", (channel_id,))

    async def top_ogeys_month(self, channel_id: int) -> list[tuple[str, int]] | None:
        return await self._run(self._fetchall, """
            SELECT u.display_name, COUNT(*) FROM ogeyofday_history oh JOIN users u ON u.id = oh.id
            WHERE oh.date >= date_trunc('month', now()) AND oh.channel_id = %s
            GROUP BY u.id ORDER BY COUNT(*) DESC LIMIT 10""", (channel_id,))

    async def top_ogeys_all(self, channel_id: int) -> list[tuple[str, int]] | None:
        return await self._run(self._fetchall, """
            SELECT u.display_name, COUNT(*) FROM ogeyofday_history oh JOIN users u ON u.id = oh.id
            WHERE oh.channel_id = %s GROUP BY u.id ORDER BY COUNT(*) DESC LIMIT 10""", (channel_id,))

    async def top_denunciations(self) -> list[tuple[str, int]] | None:
        return await self._run(self._fetchall, """
            SELECT u.display_name, d.den_count FROM users u JOIN denunciations d ON d.user_id = u.id
            ORDER BY d.den_count DESC LIMIT 10""")

    # ---------- чтение: статистика ----------
    async def user_month_count(self, channel_id: int, login: str) -> int | None:
        row = await self._run(self._fetchone, """
            SELECT COUNT(*) FROM messages m JOIN users u ON u.id = m.author_id
            WHERE m.timestamp >= date_trunc('month', now()) AND m.channel_id = %s AND u.name = LOWER(%s)""",
            (channel_id, login))
        return row[0] if row else None

    async def channel_month_count(self, channel_id: int) -> int | None:
        row = await self._run(self._fetchone,
            "SELECT COUNT(*) FROM messages WHERE timestamp >= date_trunc('month', now()) AND channel_id = %s",
            (channel_id,))
        return row[0] if row else None

    async def malenia_count(self, channel_id: int) -> int | None:
        row = await self._run(self._fetchone,
            "SELECT COUNT(*) FROM messages WHERE channel_id = %s AND message ~* 'мален|маслени|мелани|милани'",
            (channel_id,))
        return row[0] if row else None

    async def word_count(self, channel_id: int, login: str, word: str) -> int | None:
        row = await self._run(self._fetchone, """
            SELECT COALESCE(SUM((LENGTH(LOWER(m.message)) - LENGTH(REPLACE(LOWER(m.message), LOWER(%s), ''))) / LENGTH(%s)), 0)
            FROM messages m JOIN users u ON u.id = m.author_id
            WHERE LOWER(u.name) = LOWER(%s) AND m.channel_id = %s AND m.message IS NOT NULL AND LENGTH(%s) > 0""",
            (word, word, login, channel_id, word))
        return int(row[0]) if row else None

    async def first_message(self, channel_id: int, login: str) -> tuple[str, dt.datetime] | None:
        row = await self._run(self._fetchone, """
            SELECT m.message, m.timestamp FROM messages m JOIN users u ON u.id = m.author_id
            WHERE LOWER(u.name) = LOWER(%s) AND m.channel_id = %s AND m.message IS NOT NULL
            ORDER BY m.timestamp ASC LIMIT 1""", (login, channel_id))
        return (row[0], row[1]) if row else None

    async def days_in_channel(self, channel_id: int, login: str) -> int | None:
        row = await self._run(self._fetchone, """
            SELECT EXTRACT(DAY FROM now() - MIN(m.timestamp))::int FROM messages m JOIN users u ON u.id = m.author_id
            WHERE LOWER(u.name) = LOWER(%s) AND m.channel_id = %s""", (login, channel_id))
        return row[0] if row and row[0] is not None else None

    async def silence_days(self, channel_id: int, login: str) -> int | None:
        row = await self._run(self._fetchone, """
            SELECT EXTRACT(DAY FROM now() - MAX(m.timestamp))::int FROM messages m JOIN users u ON u.id = m.author_id
            WHERE LOWER(u.name) = LOWER(%s) AND m.channel_id = %s""", (login, channel_id))
        return row[0] if row and row[0] is not None else None

    async def activity(self, channel_id: int, login: str) -> tuple[int, int] | None:
        row = await self._run(self._fetchone, """
            SELECT COUNT(*) FILTER (WHERE m.timestamp >= now() - INTERVAL '7 days'),
                   COUNT(*) FILTER (WHERE m.timestamp >= now() - INTERVAL '30 days')
            FROM messages m JOIN users u ON u.id = m.author_id
            WHERE LOWER(u.name) = LOWER(%s) AND m.channel_id = %s""", (login, channel_id))
        return (int(row[0]), int(row[1])) if row else None

    async def random_message_by_login(self, channel_id: int, login: str) -> str | None:
        row = await self._run(self._fetchone, """
            SELECT m.message FROM messages m JOIN users u ON u.id = m.author_id
            WHERE LOWER(u.name) = LOWER(%s) AND m.channel_id = %s AND m.message IS NOT NULL
            ORDER BY random() LIMIT 1""", (login, channel_id))
        return row[0] if row else None

    async def favorite_word(self, channel_id: int, login: str) -> tuple[str, int] | None:
        row = await self._run(self._fetchone, r"""
            WITH words AS (
                SELECT LOWER(w.word) AS word FROM messages m JOIN users u ON u.id = m.author_id
                CROSS JOIN LATERAL regexp_split_to_table(m.message, '\s+') AS w(word)
                WHERE LOWER(u.name) = LOWER(%s) AND m.channel_id = %s AND m.message IS NOT NULL)
            SELECT word, COUNT(*) AS cnt FROM words
            WHERE LENGTH(word) > 3 AND word ~ '^[а-яёa-z]+$'
            GROUP BY word ORDER BY cnt DESC LIMIT 1""", (login, channel_id))
        return (row[0], int(row[1])) if row else None

    async def word_percentage(self, channel_id: int, login: str, word: str) -> float | None:
        pattern = r"(?<![а-яёА-ЯЁa-zA-Z])" + re.escape(word) + r"(?![а-яёА-ЯЁa-zA-Z])"
        row = await self._run(self._fetchone, """
            SELECT ROUND(COUNT(*) FILTER (WHERE m.message ~* %s)::numeric / NULLIF(COUNT(*), 0) * 100, 2)
            FROM messages m JOIN users u ON u.id = m.author_id
            WHERE LOWER(u.name) = LOWER(%s) AND m.channel_id = %s AND m.message IS NOT NULL""",
            (pattern, login, channel_id))
        return float(row[0]) if row and row[0] is not None else None

    async def chat_neighbor(self, channel_id: int, user_id: int) -> tuple[str, int] | None:
        row = await self._run(self._fetchone, """
            WITH ordered AS (
                SELECT author_id,
                       LAG(author_id)  OVER (ORDER BY timestamp) AS prev_author,
                       LEAD(author_id) OVER (ORDER BY timestamp) AS next_author
                FROM messages WHERE channel_id = %(ch)s),
            neighbors AS (
                SELECT prev_author AS neighbor FROM ordered
                WHERE author_id = %(u)s AND prev_author IS NOT NULL AND prev_author != %(u)s
                UNION ALL
                SELECT next_author FROM ordered
                WHERE author_id = %(u)s AND next_author IS NOT NULL AND next_author != %(u)s)
            SELECT u.display_name, COUNT(*) AS cnt FROM neighbors n JOIN users u ON u.id = n.neighbor
            GROUP BY u.id, u.display_name ORDER BY cnt DESC LIMIT 1""", {"ch": channel_id, "u": user_id})
        return (row[0], int(row[1])) if row else None

    # ---------- бэкап ----------
    async def backup(self, backup_dir: str, compress_level: int = 0) -> tuple[str | None, str]:
        try:
            os.makedirs(backup_dir, exist_ok=True)
            stamp = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            path = os.path.join(backup_dir, f"{self._name}_{stamp}.backup")
            cmd = ["pg_dump", "--host", self._host, "--port", str(self._port), "--username", self._user,
                   "--format", "custom", "--blobs", "--file", path, self._name]
            if compress_level > 0:
                cmd += ["--compress", str(compress_level)]
            proc = await asyncio.create_subprocess_exec(
                *cmd, env={**os.environ, "PGPASSWORD": self._password},
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=_ASYNC_LOCK_TIMEOUT)
            if proc.returncode != 0:
                return None, f"Ошибка бэкапа: {stderr.decode('utf-8', 'ignore') or 'unknown error'}"
            return path, f"Бэкап создан. Размер: {os.path.getsize(path) / 1024 / 1024:.2f} МБ"
        except Exception as e:
            log.exception("Ошибка бэкапа")
            return None, f"Ошибка бэкапа: {e}"
