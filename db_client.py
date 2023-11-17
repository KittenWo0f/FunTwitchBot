import psycopg2
import psycopg2.extensions

class DbMessageLogClient():
        
    def __init__(self):
        self.conn : psycopg2.extensions.connection
        self.cur : psycopg2.extensions.cursor
    def __del__(self):
        self.cur.close()
        self.conn.close()
    
    def Connect(self, connstr) -> bool:
        try:
            self.conn = psycopg2.connect(connstr)
            self.cur = self.conn.cursor()
        except Exception as e:
            print(f'Failed connect to db: {e}.')
            return False
        return True
        
    def InsertMessage(self, message, author, channel, timestamp):
        try:
            #Добавляю пользователя если его нет в таблицу пользователей
            #TODO При подключении считывать таблицу пользователей в память и искать Id в памяти и потом пытаться записать пользователя в БД
            users = ((channel.id, channel.name), (author.id, author.name))
            self.cur.executemany("INSERT INTO users (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING", users)
            self.conn.commit()
            #Добавляю сообщение в таблицу сообщений
            self.cur.execute("INSERT INTO messages (timestamp, channel_id, author_id, message) VALUES (%s, %s, %s, %s)", (timestamp, channel.id, author.id, message))
            self.conn.commit()
        except Exception as e:
            print(f'Failed insert to db: {e}.')
        

            