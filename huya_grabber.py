import cloudscraper
import re
import hashlib
import time
import json
import random

def get_huya_url(room_id):
    # Menggunakan cloudscraper untuk menembus proteksi awal
    scraper = cloudscraper.create_scraper()
    
    # Generate UID acak agar tidak dianggap sebagai satu user yang sama terus menerus
    uid = str(random.randint(1000000000, 2147483647))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/0.4',
        'Referer': f'https://m.huya.com/{room_id}',
        'Accept': 'application/json',
        'Origin': 'https://m.huya.com'
    }
    
    try:
        # Endpoint API Mobile yang sering digunakan proxy pihak ketiga
        api_url = f'https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={room_id}'
        response = scraper.get(api_url, headers=headers, timeout=15)
        res = response.json()
        
        if res.get('status') == 200 and res['data']['liveStatus'] == 'ON':
            # Mencoba mengambil data HLS (m3u8) agar sama dengan cfss.cc
            stream_info = None
            try:
                # Coba jalur HLS MultiLine
                stream_info = res['data']['stream']['hls']['multiLine'][0]['vStreamInfo'][0]
            except:
                try:
                    # Jalur cadangan baseStamp
                    stream_info = res['data']['stream']['baseStamp'][0]['vStreamInfo'][0]
                except:
                    return None

            if stream_info:
                return build_final_url(stream_info, uid)
    except Exception as e:
        print(f"Error fetching ID {room_id}: {e}")
    
    return None

def build_final_url(s, uid):
    stream_name = s['sStreamName']
    anti_code = s['sFlvAntiCode']
    
    # Parsing wsTime dan ct
    ws_time = re.search(r'wsTime=([a-fA-F0-9]+)', anti_code).group(1)
    ct = re.search(r'ct=([a-fA-F0-9]+)', anti_code).group(1)
    
    # Kalkulasi Signature MD5
    seq_id = str(int(time.time() * 1000))
    hash_str = f"{seq_id}|{ct}|{stream_name}|{ws_time}"
    ws_secret = hashlib.md5(hash_str.encode()).hexdigest()
    
    # Mendapatkan base URL dan suffix (m3u8 atau flv)
    base_url = s.get('sHlsUrl') or s.get('sFlvUrl')
    suffix = s.get('sHlsUrlSuffix') or s.get('sFlvUrlSuffix') or 'm3u8'
    
    # Rakit URL Final dengan HTTPS
    final_url = f"{base_url}/{stream_name}.{suffix}?wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={ct}&ver=1&u={uid}&t=100"
    
    return final_url.replace("http://", "https://")

# Masukkan ID Room di sini
ids = ["11342393", "94525"]

with open("live.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    found = False
    for rid in ids:
        url = get_huya_url(rid)
        if url:
            f.write(f"#EXTINF:-1, Huya Room {rid}\n{url}\n")
            found = True
            print(f"ID {rid} OK")
    
    if not found:
        # Baris ini penting agar GitHub Action tidak error saat 'git add'
        f.write("#EXTINF:-1, Info: Semua Offline/IP Blocked\nhttps://0.0.0.0/offline.mp4\n")
