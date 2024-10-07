import requests
from db_client import db_top_emotes_client
import csv
from variables import *

def main(channel_name, emotes_url, provider, db_conn_str, out_file):
    # Подключение к БД
    db_client = db_top_emotes_client(db_conn_str)
    if (db_client.connect() == False): 
        print("Failed connect to db")
        return
    # Получение id пользователя
    channel_id = db_client.get_user_id_by_name(channel_name)
    if (channel_id == None):
        print("Channel not found")
        return
    # Открытие файла для записи
    writer = csv.writer(open(out_file, 'w', newline=''), delimiter=";")
    for emotes_source in (["global", f'{emotes_url}/v1/global/{provider}'], [f'channel {channel_name}', f'{emotes_url}/v1/channel/{channel_name}/{provider}']): 
        # Получение списка эмоутов
        source_name = emotes_source[0]
        url=emotes_source[1]
        print(f'Loading {source_name} emotes for "{provider}" provider')
        r = requests.get(url)
        if r.status_code >= 400:
            print("Bad request global emotes")
            continue
        emotes_tuples = []   
        current_index = 1
        # Подсчёт смайлов
        length = len(r.json())
        print(f'Counting {source_name} emotes')
        for i in r.json():
            emote = i["code"]
            src = i["urls"][0]["url"]
            count = db_client.count_messages_with_value_on_channel(channel_id, emote)
            emotes_tuples.append((count, emote, src))
            print ("{}/{}: {:<20} {:<5} {:<20}".format(current_index, length, emote, count, src))
            current_index+=1
        # Сортировка
        emotes_tuples = sorted(emotes_tuples, key=lambda emote: emote[0], reverse=True)
        # Вывод в файл
        writer.writerow([source_name])
        writer.writerow(["count", "emote", "src"])
        for i in emotes_tuples:
            writer.writerow(i)
    
try:
    main(CHANNEL_NAME, EMOTES_URL, PROVIDER, DB_CONN_STR, OUT_FILE)
except Exception as e:
    print(e)