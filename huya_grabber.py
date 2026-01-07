import requests
import re
import hashlib
import time
import json

def get_huya_url(room_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://www.huya.com/{room_id}'
    }
    
    # JALUR 1: Mencoba API Mobile (Cepat)
    try:
        api_url = f'https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={room_id}'
        res = requests.get(api_url, headers=headers, timeout=10).json()
        if res.get('status') == 200 and res['data']['liveStatus'] == 'ON':
            s = res['data']['stream']['baseStamp'][0]['vStreamInfo'][0]
            return build_url(s)
    except:
        pass

    # JALUR 2: Mencoba Scraping Halaman Web PC (Lebih Kuat)
    try:
        html = requests.get(f'https://www.huya.com/{room_id}', headers=headers, timeout=10).text
        data_match = re.search(r'window.HNF_GLOBAL_CONF = (.*?);', html)
        if data_match:
            conf = json.loads(data_match.group(1))
            if conf['roomInfo']['tLiveInfo']['sLiveStatus'] == 'ON':
                s = conf['roomInfo']['tLiveInfo']['tLiveStreamInfo']['vStreamInfo']['value'][0]
                return build_url(s)
    except:
        pass
    
    return None

def build_url(s):
    stream_name = s['sStreamName']
    anti_code = s['sFlvAntiCode']
    
    # Ekstrak wsTime dan ct
    ws_time = re.search(r'wsTime=([a-fA-F0-9]+)', anti_code).group(1)
    ct = re.search(r'ct=([a-fA-F0-9]+)', anti_code).group(1)
    
    # Generate Signature
    seq_id = str(int(time.time() * 1000))
    hash_str = f"{seq_id}|{ct}|{stream_name}|{ws_time}"
    ws_secret = hashlib.md5(hash_str.encode()).hexdigest()
    
    final_url = f"{s['sFlvUrl']}/{stream_name}.flv?wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={ct}&ver=1&u={int(time.time())}"
    return final_url.replace("http://", "https://")

# DAFTAR ID (Pastikan ID ini aktif di browser Anda sebelum tes)
ids = ["11342393", "94525"]

with open("live.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    found_any = False
    for room_id in ids:
        url = get_huya_url(room_id)
        if url:
            f.write(f"#EXTINF:-1, Huya Live {room_id}\n")
            f.write(f"{url}\n")
            found_any = True
    
    if not found_any:
        f.write("#EXTINF:-1, Semua Room Sedang Offline atau Terblokir IP\n")
        f.write("https://example.com/offline.mp4\n")
