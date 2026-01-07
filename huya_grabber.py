import requests
import re
import hashlib
import time
import json
import random

def get_huya_m3u8(room_id):
    # Proxy CORS yang Anda berikan
    proxy_base = "https://anywhere.flytv.my.id/"
    # Target API Huya
    target_api = f'https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={room_id}'
    
    # Gabungkan proxy dengan target
    url = f"{proxy_base}{target_api}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': 'https://m.huya.com/',
        # Menambahkan header palsu IP China untuk memperkuat bypass
        'X-Forwarded-For': f'117.{random.randint(10,200)}.{random.randint(10,200)}.{random.randint(10,200)}',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    
    try:
        # Request melalui proxy FlyTV
        response = requests.get(url, headers=headers, timeout=20)
        res = response.json()
        
        if res.get('status') == 200 and res['data']['liveStatus'] == 'ON':
            # Mengambil informasi stream HLS (m3u8)
            # Skrip ini mencoba mencari di beberapa lokasi data sekaligus
            stream_info = None
            try:
                stream_info = res['data']['stream']['hls']['multiLine'][0]['vStreamInfo'][0]
            except:
                try:
                    stream_info = res['data']['stream']['baseStamp'][0]['vStreamInfo'][0]
                except:
                    return None

            if stream_info:
                sStreamName = stream_info['sStreamName']
                sAntiCode = stream_info.get('sHlsAntiCode') or stream_info.get('sFlvAntiCode')
                
                # Parsing parameter wsTime dan ct dari AntiCode
                ws_time = re.search(r'wsTime=([a-fA-F0-9]+)', sAntiCode).group(1)
                ct = re.search(r'ct=([a-fA-F0-9]+)', sAntiCode).group(1)
                
                # Kalkulasi Signature Signature (Wajib agar link bisa diputar)
                seq_id = str(int(time.time() * 1000))
                hash_payload = f"{seq_id}|{ct}|{sStreamName}|{ws_time}"
                ws_secret = hashlib.md5(hash_payload.encode()).hexdigest()
                
                # UID acak agar tidak terdeteksi sebagai satu user tunggal
                uid = random.randint(1000000, 9999999)
                
                # Merakit URL M3U8 Final
                final_url = (
                    f"{stream_info['sHlsUrl']}/{sStreamName}.m3u8?"
                    f"wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={ct}&ver=1&u={uid}&t=100"
                )
                return final_url.replace("http://", "https://")
                
    except Exception as e:
        print(f"Error saat menggunakan proxy FlyTV: {e}")
    return None

# ID Room Badminton spesifik Anda
room_id = "30805928"
link = get_huya_m3u8(room_id)

# Simpan ke file live.m3u
with open("live.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    if link:
        f.write(f"#EXTINF:-1, Badminton Huya {room_id}\n")
        f.write(f"{link}\n")
        print(f"Berhasil! Link m3u8 didapat: {link}")
    else:
        f.write("#EXTINF:-1, Badminton Offline atau Proxy Blocked\n")
        f.write("https://example.com/offline.mp4\n")
        print("Gagal mendapatkan link. Cek apakah room sedang live.")
