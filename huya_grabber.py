import requests
import re
import hashlib
import time
import json
import random

def get_huya_m3u8(room_id):
    # Menggunakan User-Agent yang meniru Aplikasi Huya Android asli
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-S906B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Referer': f'https://m.huya.com/{room_id}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    
    try:
        # Step 1: Ambil info room dari API Mobile
        api_url = f'https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={room_id}'
        response = requests.get(api_url, headers=headers, timeout=10)
        res = response.json()
        
        if res.get('status') == 200 and res['data']['liveStatus'] == 'ON':
            # Step 2: Cari data stream HLS (m3u8)
            # Huya sering memindahkan lokasi data, kita cek beberapa kemungkinan
            stream_info = None
            try:
                # Coba jalur utama HLS
                stream_info = res['data']['stream']['hls']['multiLine'][0]['vStreamInfo'][0]
            except:
                try:
                    # Jalur cadangan (baseStamp)
                    stream_info = res['data']['stream']['baseStamp'][0]['vStreamInfo'][0]
                except:
                    return None

            if stream_info:
                sStreamName = stream_info['sStreamName']
                # Mengambil AntiCode (kunci enkripsi)
                sAntiCode = stream_info.get('sHlsAntiCode') or stream_info.get('sFlvAntiCode')
                
                # Step 3: Kalkulasi Signature Manual
                ws_time = re.search(r'wsTime=([a-fA-F0-9]+)', sAntiCode).group(1)
                ct = re.search(r'ct=([a-fA-F0-9]+)', sAntiCode).group(1)
                seq_id = str(int(time.time() * 1000))
                
                # Format Hash: md5(seqId + | + ct + | + streamName + | + wsTime)
                hash_payload = f"{seq_id}|{ct}|{sStreamName}|{ws_time}"
                ws_secret = hashlib.md5(hash_payload.encode()).hexdigest()
                
                # Step 4: Susun URL m3u8 Final
                # Menambahkan parameter 'u' (UID) dan 't' (Type) agar dianggap valid
                uid = random.randint(12345678, 99999999)
                final_url = (
                    f"{stream_info['sHlsUrl']}/{sStreamName}.m3u8?"
                    f"wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={ct}&ver=1&u={uid}&t=100"
                )
                return final_url.replace("http://", "https://")
                
    except Exception as e:
        print(f"Error for {room_id}: {e}")
    return None

# ID Badminton Badminton
room_id = "30805928"
m3u8_link = get_huya_m3u8(room_id)

with open("live.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    if m3u8_link:
        f.write(f"#EXTINF:-1, Badminton Live {room_id}\n")
        f.write(f"{m3u8_link}\n")
        print(f"Berhasil mendapatkan link: {m3u8_link}")
    else:
        f.write("#EXTINF:-1, Badminton Offline/Blocked\n")
        f.write("https://example.com/offline.mp4\n")
        print("Gagal: Room Offline atau IP GitHub diblokir.")
