import psycopg2
import psycopg2.extensions

class DbMessageLogClient():
        
    def __init__(self, connstr):
        self._conn = None
        self._connstr = connstr
    def __del__(self):
        self._conn.close()
    
    def Connect(self) -> bool:
        try:
            self._conn = psycopg2.connect(self._connstr)
        except Exception as e:
            print(f'Failed connect to db: {e}.')
            return False
        return True
        
    def InsertMessage(self, message, author_id, author_name, channel, timestamp):
        self._CheckConnection()
        self._CheckUserExist(channel.id, channel.name)
        self._CheckUserExist(author_id, author_name)
        try:
            #Добавляю сообщение в таблицу сообщений
            self._conn.cursor().execute("INSERT INTO messages (timestamp, channel_id, author_id, message) VALUES (%s, %s, %s, %s)", (timestamp, channel.id, author_id, message))
            self._conn.commit()
        except Exception as e:
            print(f'Failed insert to db: {e}.')
            
    def UpdateUserLastActivity(self, id, name, timestamp):
        self._CheckConnection()
        self._CheckUserExist(id, name)
        try:
            self._conn.cursor().execute("""
            INSERT INTO users_activities (user_id, last_seen) 
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE 
            SET last_seen = excluded.last_seen;
            """, (id, timestamp))
            self._conn.commit() 
        except Exception as e:
            print(f'Failed update user last activity in db: {e}.')
    
    def GetUserLastActivity(self, id):
        self._CheckConnection()
        try:
            cur = self._conn.cursor()
            cur.execute(""" 
            SELECT last_seen FROM users_activities WHERE user_id=%s
            """, [id])
            res = cur.fetchall()
            if res:
                return res[0][0]
            else:
                return None
        except Exception as e:
            print(f'Failed get user last activity in db: {e}.')
            return None
        
    def GetLastActiveUsers(self, chanel_id):
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
    
    def GetRandomMessageByUser(self, user_id):
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
        
    def GetRandomUserByLastNHours(self, channel_id, hours):
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
        
    def UpdateOgey(self, channel_id, ogey_id):
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
        
    def GetOgey(self, channel_id):
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
        
    def GetTopOfMonthUsers(self, channel_id):
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
        
    def GetUsersMessageCountForMounthByName(self, channel_id, user_name):
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
    
    def _CheckUserExist(self, id, name):
        try:
            #Добавляю пользователя если его нет в таблицу пользователей
            #TODO При подключении считывать таблицу пользователей в память и искать Id в памяти и потом пытаться записать пользователя в БД
            self._conn.cursor().execute("INSERT INTO users (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING", (id, name))
            self._conn.commit()
        except Exception as e:
            print(f'Failed check user in db: {e}.')
        
    def _CheckConnection(self):
        try:
            self._conn.cursor() #Через какоето время _conn теряется, поэтому проверяю таким способом его наличие
        except AttributeError as e:
            self.Connect()

            