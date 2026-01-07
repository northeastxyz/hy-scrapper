import cloudscraper
import re
import hashlib
import time
import json
import random

def get_huya_url(room_id):
    scraper = cloudscraper.create_scraper()
    uid = str(random.randint(1000000000, 2147483647))
    
    # Proxy yang Anda berikan
    custom_proxy = "http://116.198.45.213:8080/"
    target_api = f'https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={room_id}'
    
    # Menggabungkan proxy dengan target (mengasumsikan ini adalah simple reverse proxy)
    # Jika proxy tersebut adalah HTTP Proxy standar, kita gunakan parameter 'proxies'
    proxy_config = {
        "http": custom_proxy,
        "https": custom_proxy
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': 'https://m.huya.com/',
        'Accept': 'application/json'
    }
    
    try:
        # Mencoba request menggunakan proxy tersebut
        response = scraper.get(target_api, headers=headers, proxies=proxy_config, timeout=20)
        res_data = response.json()
            
        if res_data.get('status') == 200 and res_data['data']['liveStatus'] == 'ON':
            # Mencari data HLS (m3u8) agar kompatibel dengan IPTV Player
            try:
                stream_info = res_data['data']['stream']['hls']['multiLine'][0]['vStreamInfo'][0]
            except:
                stream_info = res_data['data']['stream']['baseStamp'][0]['vStreamInfo'][0]
            
            return build_final_url(stream_info, uid)
        else:
            print(f"Room {room_id} offline atau proxy diblokir.")
    except Exception as e:
        print(f"Gagal akses melalui proxy {custom_proxy}: {e}")
    
    return None

def build_final_url(s, uid):
    stream_name = s['sStreamName']
    anti_code = s['sFlvAntiCode']
    
    # Parsing wsTime dan ct
    ws_time = re.search(r'wsTime=([a-fA-F0-9]+)', anti_code).group(1)
    ct = re.search(r'ct=([a-fA-F0-9]+)', anti_code).group(1)
    
    # Signature MD5
    seq_id = str(int(time.time() * 1000))
    hash_str = f"{seq_id}|{ct}|{stream_name}|{ws_time}"
    ws_secret = hashlib.md5(hash_str.encode()).hexdigest()
    
    base_url = s.get('sHlsUrl') or s.get('sFlvUrl')
    suffix = s.get('sHlsUrlSuffix') or s.get('sFlvUrlSuffix') or 'm3u8'
    
    # Rakit URL Final
    final = f"{base_url}/{stream_name}.{suffix}?wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={ct}&ver=1&u={uid}&t=100"
    return final.replace("http://", "https://")

# Daftar ID Room
ids = ["11342393", "94525"]

with open("live.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    found = False
    for rid in ids:
        url = get_huya_url(rid)
        if url:
            f.write(f"#EXTINF:-1, Huya Room {rid}\n{url}\n")
            found = True
    
    if not found:
        f.write("#EXTINF:-1, Status: Offline atau Proxy Error\nhttps://0.0.0.0/offline.mp4\n")
