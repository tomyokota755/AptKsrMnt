import os
import requests
import json
from datetime import datetime, timedelta, timezone

LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

AREAS = {
    "新千歳": [{"range": [42.50, 42.75, 141.60, 141.85], "msg": "新千歳01L、01R"},{"range": [42.85, 43.10, 141.65, 141.90], "msg": "新千歳19L、19R"}],
    "成田": [{"range": [35.50, 35.75, 140.40, 140.70], "msg": "成田34L、34R"},{"range": [35.80, 36.10, 140.15, 140.45], "msg": "成田16L、16R"}],
    "羽田": [
        {"range": [35.25, 35.50, 139.70, 140.00], "msg": "羽田34L、34R"},
        {"range": [35.55, 35.80, 139.60, 139.85], "track": [140, 180], "msg": "羽田16L、16R"},
        {"range": [35.55, 35.80, 139.85, 140.10], "track": [200, 260], "msg": "羽田22、23"}
    ],
    "中部": [{"range": [34.70,34.80,136.75,136.85], "msg": "中部36"},{"range": [34.95,35.05,136.75,136.85], "msg": "中部18"}],
    "関空": [{"range": [34.25,34.40,135.10,135.30], "msg": "関空06L、06R"},{"range": [34.45,34.60,135.35,135.55], "msg": "関空24L、24R"}],
    "福岡": [{"range": [33.45,33.55,130.45,130.60], "msg": "福岡34"},{"range": [33.65,33.75,130.35,130.50], "msg": "福岡16"}],
    "那覇": [{"range": [26.00,26.15,127.60,127.70], "msg": "那覇36L、36R"},{"range": [26.25,26.40,127.65,127.80], "msg": "那覇18L、18R"}]
}

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    data = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": f"{message}に変わりました。"}]}
    requests.post(url, headers=headers, json=data)

def monitor():
    # 日本時間の現在時刻を取得
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    
    # 【朝6時リセット】 6:00〜6:10の間なら、前日の記憶を消去して「ベース通知」を準備
    if now.hour == 6 and now.minute < 10:
        print("6:00 AM Reset: Starting fresh for the day.")
        current_state = {}
    else:
        current_state = load_state()

    changed = False
    url = "https://opensky-network.org/api/states/all"
    params = {"lamin": 24.0, "lamax": 46.0, "lomin": 122.0, "lomax": 146.0}
    
    try:
        res = requests.get(url, params=params, timeout=15).json()
        states = res.get("states", [])
        if not states: return

        detected_airports = set()

        for s in states:
            lat, lon, alt_m, track, vert_rate = s[6], s[5], s[7], s[10], s[11]
            if any(v is None for v in [lat, lon, alt_m, vert_rate]): continue
            alt_ft = alt_m * 3.28084

            if vert_rate < -0.5 and alt_ft < 3000:
                for name, corridors in AREAS.items():
                    if name in detected_airports: continue
                    
                    for corridor in corridors:
                        r = corridor["range"]
                        if r[0] <= lat <= r[1] and r[2] <= lon <= r[3]:
                            if "track" in corridor and not (corridor["track"][0] <= track <= corridor["track"][1]):
                                continue
                            
                            new_mode = corridor["msg"]
                            # 前回の状態と違う（または朝一番で記憶がない）場合のみ通知
                            if current_state.get(name) != new_mode:
                                # 朝6時台ならメッセージに【朝一番】と付けることも可能です
                                prefix = "【朝のベース】" if now.hour == 6 else ""
                                send_line(f"{prefix}{new_mode}")
                                current_state[name] = new_mode
                                changed = True
                            
                            detected_airports.add(name)
        
        if changed:
            save_state(current_state)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    monitor()
