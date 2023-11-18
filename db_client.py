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
        try:
            self._conn.cursor() #Через какоето время _conn теряется, поэтому проверяю таким способом его наличие
        except AttributeError as e:
            self.Connect()
            
        try:
            #Добавляю пользователя если его нет в таблицу пользователей
            #TODO При подключении считывать таблицу пользователей в память и искать Id в памяти и потом пытаться записать пользователя в БД
            users = ((channel.id, channel.name), (author_id, author_name))
            self._conn.cursor().executemany("INSERT INTO users (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING", users)
            self._conn.commit()
            #Добавляю сообщение в таблицу сообщений
            self._conn.cursor().execute("INSERT INTO messages (timestamp, channel_id, author_id, message) VALUES (%s, %s, %s, %s)", (timestamp, channel.id, author_id, message))
            self._conn.commit()
        except Exception as e:
            print(f'Failed insert to db: {e}.')
        

            