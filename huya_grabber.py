import requests
import re
import hashlib
import time

def get_huya_url(room_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        html = requests.get(f'https://www.huya.com/{room_id}', headers=headers).text
        data = re.search(r'window.HNF_GLOBAL_CONF = (.*?);', html)
        if not data: return None
        
        import json
        conf = json.loads(data.group(1))
        s = conf['roomInfo']['tLiveInfo']['tLiveStreamInfo']['vStreamInfo']['value'][0]
        
        stream_name = s['sStreamName']
        ws_time = re.search(r'wsTime=([a-fA-F0-9]+)', s['sFlvAntiCode']).group(1)
        ct = re.search(r'ct=([a-fA-F0-9]+)', s['sFlvAntiCode']).group(1)
        
        seq_id = str(int(time.time() * 1000))
        hash_str = f"{seq_id}|{ct}|{stream_name}|{ws_time}"
        ws_secret = hashlib.md5(hash_str.encode()).hexdigest()
        
        final_url = f"{s['sFlvUrl']}/{stream_name}.flv?wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={ct}&ver=1"
        return final_url
    except:
        return None

# Contoh: Menghasilkan file M3U
room_id = "11342393"
url = get_huya_url(room_id)
if url:
    with open("live.m3u", "w") as f:
        f.write("#EXTM3U\n")
        f.write(f"#EXTINF:-1,Huya Live {room_id}\n")
        f.write(f"{url}\n")
