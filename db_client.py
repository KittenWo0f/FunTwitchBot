import psycopg2
import psycopg2.extensions
# Для бэкапа
import asyncio
import os
import datetime
from typing import Optional, Tuple

class db_message_log_client():
        
    def __init__(self, 
                host: str,
                db_name: str,
                port: int,
                user: str,
                password: str):
        self._conn = None
        self._host = host
        self._db_name = db_name
        self._port = port
        self._user = user
        self._password = password
    def __del__(self):
        self._conn.close()
    
    def connect(self) -> bool:
        try:
            self._conn = psycopg2.connect(f'''dbname={self._db_name} 
                                          user={self._user} 
                                          password={self._password}
                                          host={self._host} 
                                          port={self._port}''')
        except Exception as e:
            print(f'Failed connect to db: {e}.')
            return False
        return True
        
    def insert_message(self, message, author_id, author_name, channel):
        self._check_connection()
        self._check_user_exist(channel.id, channel.name)
        self._check_user_exist(author_id, author_name)
        try:
            #Добавляю сообщение в таблицу сообщений
            self._conn.cursor().execute("INSERT INTO messages (timestamp, channel_id, author_id, message) VALUES (now(), %s, %s, %s)", (channel.id, author_id, message))
            self._conn.commit()
        except Exception as e:
            print(f'Failed insert to db: {e}.')
    
    def get_user_last_activity(self, channel_id, author_id):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute(""" 
            SELECT timestamp FROM messages 
            WHERE author_id = %s AND
                channel_id = %s
            ORDER BY timestamp DESC
            LIMIT 1;
            """, (author_id, channel_id))
            res = cur.fetchall()
            if res:
                return res[0][0]
            else:
                return None
        except Exception as e:
            print(f'Failed get user last activity in db: {e}.')
            return None
        
    def get_last_active_users(self, chanel_id):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        SELECT u.name
                        FROM messages AS m
                        JOIN users AS u ON u.id=m.author_id
                        WHERE m.timestamp >= date_trunc('second', now()) - INTERVAL '43200 second'
                        AND m.timestamp < (date_trunc('second', now()))
                        AND m.channel_id = '%s'
                        GROUP BY u.id
                        ORDER BY MAX(m.timestamp) DESC
                        LIMIT 20
                        """,
                        [chanel_id])
            res = cur.fetchall()
            if res:
                return res
        except Exception as e:
            print(f'Failed check last active users in db: {e}.')
            return None
    
    def get_random_message_by_user(self, user_id):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        SELECT message FROM public.messages AS m
                        WHERE author_id='%s'
                        ORDER BY random()
                        LIMIT 1
                        """,
                        [user_id])
            res = cur.fetchall()
            if res:
                return res[0][0]
        except Exception as e:
            print(f'Failed check last active users in db: {e}.')
            return None
        
    def get_random_user_by_last_n_hours(self, channel_id, hours):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        SELECT author_id FROM public.messages
                        WHERE timestamp BETWEEN now() - interval '%s hours' AND now()
                                AND channel_id = '%s'
                        GROUP BY author_id
                        ORDER BY random()
                        LIMIT 1
                        """,
                        (hours, channel_id))
            res = cur.fetchall()
            if res:
                return res[0][0]
        except Exception as e:
            print(f'Failed GetRandomUserByLastNHours in db: {e}.')
            return None
        
    def update_ogey(self, channel_id, ogey_id):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        INSERT INTO ogeyofday (channel_id, ogey_id, timestamp) 
                        VALUES (%s, %s, now())
                        ON CONFLICT (channel_id) DO UPDATE 
                        SET ogey_id = %s,
                            timestamp = now();
                        """,
                        (channel_id, ogey_id, ogey_id))
            self._conn.commit()
        except Exception as e:
            print(f'Failed UpdateOgey in db: {e}.')
            return False
        return True
        
    def get_ogey(self, channel_id):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        SELECT u.name FROM ogeyofday AS o
                        JOIN users AS u ON u.id = o.ogey_id
                        WHERE o.channel_id = '%s'
                        """,
                        [channel_id])
            res = cur.fetchall()
            if res:
                return res[0][0]
        except Exception as e:
            print(f'Failed GetOgey in db: {e}.')
            return None
        
    def get_top_of_month_users(self, channel_id):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        SELECT ua.name, COUNT(*) FROM messages AS m
                        JOIN users AS ua ON ua.id = m.author_id
                        WHERE  m.timestamp >= date_trunc('month', now())
                        AND    m.timestamp <  date_trunc('day'  , now()) + interval '1 day'
                        AND	   m.channel_id = '%s'
                        GROUP BY ua.id
                        ORDER BY COUNT(m.author_id) DESC
                        LIMIT 15
                        """,
                        [channel_id])
            res = cur.fetchall()
            if res:
                return res
        except Exception as e:
            print(f'Failed get top of month users in db: {e}.')
            return None
        
    def get_users_message_count_for_mounth_by_name(self, channel_id, user_name):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        SELECT COUNT(*) FROM messages AS m
                        JOIN users AS ua ON ua.id = m.author_id
                        WHERE  m.timestamp >= date_trunc('month', now())
                        AND    m.timestamp <  date_trunc('day'  , now()) + interval '1 day'
                        AND	   m.channel_id = %s
                        AND    ua.name = %s
                        """,
                        (channel_id, user_name))
            res = cur.fetchall()
            if res:
                return res[0][0]
        except Exception as e:
            print(f'Failed get message count of month for user {user_name} in db: {e}.')
            return None
        
    def get_all_users_message_count_for_mounth(self, channel_id):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        SELECT COUNT(*) FROM messages AS m
                        JOIN users AS ua ON ua.id = m.author_id
                        WHERE  m.timestamp >= date_trunc('month', now())
                        AND    m.timestamp <  date_trunc('day'  , now()) + interval '1 day'
                        AND	   m.channel_id = %s
                        """,
                        [channel_id])
            res = cur.fetchall()
            if res:
                return res[0][0]
        except Exception as e:
            print(f'Failed get message count of month for channel {channel_id} in db: {e}.')
            return None
        
    def get_malenia_in_channel(self, channel_id):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        SELECT COUNT(*) FROM messages AS m
                        WHERE m.channel_id = '%s'
                        AND (m.message ILIKE '%%мален%%' OR 
                            m.message ILIKE '%%маслени%%' OR 
                            m.message ILIKE '%%мелани%%' OR
                            m.message ILIKE '%%милани%%'
                            )
                        """,
                        [channel_id])
            res = cur.fetchall()
            if res:
                return res[0][0]
        except Exception as e:
            print(f'Failed GetMaleniaInChannel {channel_id} in db: {e}.')
            return None
        
    def add_denunciations_from_user(self, user_id):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        INSERT INTO denunciations (user_id, den_count) 
                        VALUES (%s, 1)
                        ON CONFLICT (user_id) DO UPDATE
                        SET den_count = denunciations.den_count + 1
                        """,
                        [user_id])
            self._conn.commit()
        except Exception as e:
            print(f'Failed add_denunciations_from_user in db: {e}.')
            return False
        return True
    
    def get_top_denunciations_by_users(self):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                        SELECT u.name, den.den_count 
                        FROM users AS u 
                        JOIN denunciations AS den ON den.user_id = u.id
                        ORDER BY den.den_count DESC
                        LIMIT 10
                        """)
            res = cur.fetchall()
            if res:
                return res
        except Exception as e:
            print(f'Failed get top of month denunciations users in db: {e}.')
            return None
        
    
    def _check_user_exist(self, id, name):
        try:
            #Добавляю пользователя если его нет в таблицу пользователей
            #TODO При подключении считывать таблицу пользователей в память и искать Id в памяти и потом пытаться записать пользователя в БД
            self._conn.cursor().execute("INSERT INTO users (id, name) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET name = %s WHERE users.name != %s", (id, name, name, name))
            self._conn.commit()
        except Exception as e:
            print(f'Failed check user in db: {e}.')
        
    def _check_connection(self):
        try:
            self._conn.cursor() #Через какоето время _conn теряется, поэтому проверяю таким способом его наличие
        except AttributeError as e:
            self.connect()
            
    async def async_db_backup(
        self,
        backup_dir: str,
        compress_level: int = 0
        ) -> Tuple[str, str]:
        try:
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_path = os.path.join(backup_dir, f"{self._db_name}_{timestamp}.backup")
            
            command = [
                'pg_dump',
                '--host', self._host,
                '--port', str(self._port),
                '--username', self._user,
                '--format', 'custom',
                '--blobs',
                '--file', backup_path,
                self._db_name
            ]
            
            if compress_level > 0:
                command.extend(['--compress', str(compress_level)])
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self._password
            
            process = await asyncio.create_subprocess_exec(
                *command,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await process.communicate()
            
            if process.returncode != 0:
                error = stderr.decode('utf-8') if stderr else "Unknown error"
                return None, f"Ошибка бэкапа: {error}"
            
            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            return backup_path, f"Бэкап создан. Размер: {size_mb:.2f} МБ"
        
        except Exception as e:
            return None, f"Ошибка бэкапа: {str(e)}"


            