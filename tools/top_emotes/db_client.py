import psycopg2
import psycopg2.extensions

class db_top_emotes_client():
        
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
        
    def get_user_id_by_name(self, name):
        self._check_connection()
        try:
            #Добавляю сообщение в таблицу сообщений
            cur = self._conn.cursor()
            cur.execute("""
                        SELECT id FROM users
                        WHERE name = %s;
                        """, [name])
            res = cur.fetchall()
            if res:
                return res[0][0]
            else:
                return None
        except Exception as e:
            print(f'Failed get user id from db: {e}.')
    
    def count_messages_with_value_on_channel(self, channel_id, value):
        self._check_connection()
        try:
            valueL = f'{value} %'
            valueM = f'% {value} %'
            valueR = f'% {value}'
            cur = self._conn.cursor()
            cur.execute(""" 
            SELECT COUNT(message) FROM messages 
            WHERE channel_id = %s AND 
                (message LIKE %s OR 
                message LIKE %s OR 
                message LIKE %s OR 
                message = %s)
            """, (channel_id, valueL, valueM, valueR, value))
            res = cur.fetchall()
            if res:
                return res[0][0]
            else:
                return 0
        except Exception as e:
            print(f'Failed count messages from db: {e}.')
            self._conn.rollback()
            return 0
        
    def _check_connection(self):
        try:
            self._conn.cursor() #Через какоето время _conn теряется, поэтому проверяю таким способом его наличие
        except AttributeError as e:
            self.connect()