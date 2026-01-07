import requests
import re
import hashlib
import time
import json
import random

def get_huya_m3u8(room_id):
    # Menggunakan Proxy FlyTV seperti yang Anda minta sebelumnya untuk bypass IP GitHub
    proxy_base = "https://anywhere.flytv.my.id/"
    api_url = f"https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={room_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': f'https://m.huya.com/{room_id}'
    }

    try:
        # Mengambil data melalui proxy
        full_url = proxy_base + api_url
        response = requests.get(full_url, headers=headers, timeout=15)
        data = response.json()

        if data.get('status') == 200 and data['data']['liveStatus'] == 'ON':
            # Mengikuti logika StreamCap: Mengambil stream m3u8 dari multiLine
            stream_info = data['data']['stream']['hls']['multiLine'][0]['vStreamInfo'][0]
            
            sStreamName = stream_info['sStreamName']
            sAntiCode = stream_info.get('sHlsAntiCode') or stream_info.get('sFlvAntiCode')
            
            # Analisis Kode Enkripsi (Logic by StreamCap)
            # wsTime adalah batas waktu link, ct adalah client type
            ws_time = re.search(r'wsTime=([a-fA-F0-9]+)', sAntiCode).group(1)
            ct = re.search(r'ct=([a-fA-F0-9]+)', sAntiCode).group(1)
            
            # Membuat Signature yang valid
            # StreamCap menekankan penggunaan timestamp milidetik (seqid)
            seq_id = str(int(time.time() * 1000))
            # Format signature Huya: md5(seqid|ct|streamname|wstime)
            hash_payload = f"{seq_id}|{ct}|{sStreamName}|{ws_time}"
            ws_secret = hashlib.md5(hash_payload.encode()).hexdigest()
            
            # Merakit URL final (HLS/m3u8)
            # Parameter 'u' dan 't' seringkali diperlukan untuk bypass deteksi bot
            uid = random.randint(12345678, 87654321)
            final_url = f"{stream_info['sHlsUrl']}/{sStreamName}.m3u8?wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={ct}&ver=1&u={uid}&t=100"
            
            return final_url.replace("http://", "https://")

    except Exception as e:
        print(f"Error logic StreamCap: {e}")
    return None

# ID Badminton Spesifik
room_id = "30805928"
m3u8_link = get_huya_m3u8(room_id)

with open("live.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    if m3u8_link:
        f.write(f"#EXTINF:-1, Badminton Live Huya\n")
        f.write(f"{m3u8_link}\n")
        print(f"SUCCESS: Link didapat untuk {room_id}")
    else:
        f.write("#EXTINF:-1, Badminton Offline atau Enkripsi Gagal\n")
        f.write("https://raw.githubusercontent.com/empty/video.mp4\n")
