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
    try:
        # Menggunakan API profil yang lebih stabil untuk GitHub Actions
        api_url = f'https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={room_id}'
        res = requests.get(api_url, headers=headers, timeout=10).json()
        
        if res.get('status') == 200 and res['data']['liveStatus'] == 'ON':
            # Mencari data stream di baseStamp atau multiLine
            stream_data = res['data']['stream']['baseStamp'][0]['vStreamInfo'][0]
            
            sStreamName = stream_data['sStreamName']
            sFlvAntiCode = stream_data['sFlvAntiCode']
            
            # Parsing parameter anti-code
            params = dict(x.split('=') for x in sFlvAntiCode.split('&'))
            ws_time = params.get('wsTime')
            ct = params.get('ct')
            
            # Generate Signature
            seq_id = str(int(time.time() * 1000))
            hash_str = f"{seq_id}|{ct}|{sStreamName}|{ws_time}"
            ws_secret = hashlib.md5(hash_str.encode()).hexdigest()
            
            final_url = f"{stream_data['sFlvUrl']}/{sStreamName}.flv?wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={ct}&ver=1&u={int(time.time())}"
            return final_url.replace("http://", "https://")
        
        return None
    except Exception as e:
        print(f"Error grab ID {room_id}: {e}")
        return None

# DAFTAR ID ROOM (Bisa ditambah banyak)
ids = ["11342393", "94525"]

# PROSES PEMBUATAN FILE (PASTI TERBUAT)
with open("live.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    found_any = False
    for room_id in ids:
        url = get_huya_url(room_id)
        if url:
            f.write(f"#EXTINF:-1, Huya Live {room_id}\n")
            f.write(f"{url}\n")
            found_any = True
            print(f"Berhasil ambil link untuk ID: {room_id}")
    
    if not found_any:
        f.write("#EXTINF:-1, Semua Room Sedang Offline\n")
        f.write("https://example.com/offline.mp4\n")

print("File live.m3u berhasil diperbarui.")
