import psycopg2
import psycopg2.extensions

class db_message_log_client():
        
    def __init__(self, connstr):
        self._conn = None
        self._connstr = connstr
    def __del__(self):
        self._conn.close()
    
    def connect(self) -> bool:
        try:
            self._conn = psycopg2.connect(self._connstr)
        except Exception as e:
            print(f'Failed connect to db: {e}.')
            return False
        return True
        
    def insert_message(self, message, author_id, author_name, channel, timestamp):
        self._check_connection()
        self._check_user_exist(channel.id, channel.name)
        self._check_user_exist(author_id, author_name)
        try:
            #Добавляю сообщение в таблицу сообщений
            self._conn.cursor().execute("INSERT INTO messages (timestamp, channel_id, author_id, message) VALUES (%s, %s, %s, %s)", (timestamp, channel.id, author_id, message))
            self._conn.commit()
        except Exception as e:
            print(f'Failed insert to db: {e}.')
    
    def get_channel_author_last_activity(self, id):
        self._check_connection()
        try:
            cur = self._conn.cursor()
            cur.execute(""" 
            SELECT timestamp FROM messages 
            WHERE author_id = %s AND
                channel_id = %s
            ORDER BY timestamp DESC
            LIMIT 1;
            """, (id, id))
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
            self._conn.cursor().execute("INSERT INTO users (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING", (id, name))
            self._conn.commit()
        except Exception as e:
            print(f'Failed check user in db: {e}.')
        
    def _check_connection(self):
        try:
            self._conn.cursor() #Через какоето время _conn теряется, поэтому проверяю таким способом его наличие
        except AttributeError as e:
            self.connect()

            