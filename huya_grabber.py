import requests
import re
import hashlib
import time
import json
import random

def get_huya_m3u8(room_id):
    # Menggunakan User-Agent iPhone untuk mendapatkan playlist HLS (.m3u8)
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/0.4',
        'Referer': f'https://m.huya.com/{room_id}',
        'Accept': 'application/json'
    }
    
    try:
        # Endpoint API Mobile Huya
        api_url = f'https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={room_id}'
        res = requests.get(api_url, headers=headers, timeout=10).json()
        
        if res.get('status') == 200 and res['data']['liveStatus'] == 'ON':
            # Mencari data di folder HLS
            stream_data = res['data']['stream']['hls']['multiLine'][0]['vStreamInfo'][0]
            
            sStreamName = stream_data['sStreamName']
            sAntiCode = stream_data['ssHlsAntiCode'] if 'sHlsAntiCode' in stream_data else stream_data['sFlvAntiCode']
            
            # Parsing wsTime dan ct
            ws_time = re.search(r'wsTime=([a-fA-F0-9]+)', sAntiCode).group(1)
            ct = re.search(r'ct=([a-fA-F0-9]+)', sAntiCode).group(1)
            
            # Kalkulasi Signature
            seq_id = str(int(time.time() * 1000))
            ws_secret = hashlib.md5(f"{seq_id}|{ct}|{sStreamName}|{ws_time}".encode()).hexdigest()
            
            # Membangun URL m3u8
            final_url = f"{stream_data['sHlsUrl']}/{sStreamName}.m3u8?wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={ct}&ver=1&u={random.randint(1000, 9999)}"
            return final_url.replace("http://", "https://")
            
    except Exception as e:
        print(f"Error: {e}")
    return None

# ID Badminton spesifik Anda
room_id = "30805928"
m3u8_link = get_huya_m3u8(room_id)

with open("live.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    if m3u8_link:
        f.write(f"#EXTINF:-1, Badminton Huya {room_id}\n")
        f.write(f"{m3u8_link}\n")
    else:
        # Jika offline, berikan link dummy agar GitHub Action tidak error saat git add
        f.write("#EXTINF:-1, Badminton Offline\n")
        f.write("https://raw.githubusercontent.com/empty/video.mp4\n")
