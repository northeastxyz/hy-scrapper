import cloudscraper
import re
import hashlib
import time
import json

def get_huya_url(room_id):
    # Menggunakan cloudscraper untuk bypass proteksi Cloudflare/WAF
    scraper = cloudscraper.create_scraper()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://www.huya.com/{room_id}',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    
    try:
        # Mencoba API profile (lebih ringan dan sering lolos dari blokir IP)
        api_url = f'https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={room_id}'
        response = scraper.get(api_url, headers=headers, timeout=15)
        res = response.json()
        
        if res.get('status') == 200 and res['data']['liveStatus'] == 'ON':
            # Mencari data stream secara mendalam
            stream_info = None
            try:
                stream_info = res['data']['stream']['baseStamp'][0]['vStreamInfo'][0]
            except:
                stream_info = res['data']['stream']['flv']['multiLine'][0]['vStreamInfo'][0]
            
            if stream_info:
                return build_final_url(stream_info)
        
        # Jika API gagal, coba scraping halaman utama (PC Web)
        html_res = scraper.get(f'https://www.huya.com/{room_id}', headers=headers, timeout=15).text
        data_match = re.search(r'window.HNF_GLOBAL_CONF = (.*?);', html_res)
        if data_match:
            conf = json.loads(data_match.group(1))
            if conf['roomInfo']['tLiveInfo']['sLiveStatus'] == 'ON':
                s = conf['roomInfo']['tLiveInfo']['tLiveStreamInfo']['vStreamInfo']['value'][0]
                return build_final_url(s)

    except Exception as e:
        print(f"Error for {room_id}: {e}")
    
    return None

def build_final_url(s):
    stream_name = s['sStreamName']
    anti_code = s['sFlvAntiCode']
    
    # Ekstrak wsTime dan ct menggunakan regex
    ws_time = re.search(r'wsTime=([a-fA-F0-9]+)', anti_code).group(1)
    ct = re.search(r'ct=([a-fA-F0-9]+)', anti_code).group(1)
    
    # Perhitungan Signature MD5
    seq_id = str(int(time.time() * 1000))
    hash_str = f"{seq_id}|{ct}|{stream_name}|{ws_time}"
    ws_secret = hashlib.md5(hash_str.encode()).hexdigest()
    
    # Merakit URL final (FLV)
    final_url = f"{s['sFlvUrl']}/{stream_name}.flv?wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={ct}&ver=1&u={int(time.time())}"
    return final_url.replace("http://", "https://")

# Masukkan daftar ID Room yang ingin dipantau
ids = ["11342393", "94525"]

# Generate File M3U
with open("live.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    found_any = False
    for rid in ids:
        url = get_huya_url(rid)
        if url:
            f.write(f"#EXTINF:-1, Huya Room {rid}\n")
            f.write(f"{url}\n")
            found_any = True
            print(f"Success grabbing {rid}")
    
    if not found_any:
        f.write("#EXTINF:-1, Error: Semua Room Offline atau IP Terblokir\n")
        f.write("https://example.com/offline.mp4\n")
