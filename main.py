import os
import requests
import json
from datetime import datetime, timedelta, timezone

LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 判定エリアを拡大（5分間隔でも逃さない15〜20マイル設定）
AREAS = {
    "新千歳": [{"range": [42.40, 42.75, 141.55, 141.95], "msg": "新千歳01L、01R"},{"range": [42.85, 43.20, 141.60, 142.00], "msg": "新千歳19L、19R"}],
    "成田": [{"range": [35.40, 35.75, 140.35, 140.75], "msg": "成田34L、34R"},{"range": [35.80, 36.15, 140.05, 140.45], "msg": "成田16L、16R"}],
    "羽田": [
        {"range": [35.15, 35.50, 139.65, 140.05], "msg": "羽田34L、34R"},
        {"range": [35.55, 35.85, 139.55, 139.85], "track": [140, 180], "msg": "羽田16L、16R"},
        {"range": [35.55, 35.85, 139.80, 140.15], "track": [200, 260], "msg": "羽田22、23"}
    ],
    "中部": [{"range": [34.60, 34.85, 136.70, 136.95], "msg": "中部36"},{"range": [34.90, 35.15, 136.70, 136.95], "msg": "中部18"}],
    "関空": [{"range": [34.15, 34.45, 135.00, 135.35], "msg": "関空06L、06R"},{"range": [34.40, 34.70, 135.30, 135.65], "msg": "関空24L、24R"}],
    "福岡": [{"range": [33.35, 33.58, 130.40, 130.65], "msg": "福岡34"},{"range": [33.62, 33.85, 130.30, 130.55], "msg": "福岡16"}],
    "那覇": [{"range": [25.95, 26.18, 127.55, 127.75], "msg": "那覇36L、36R"},{"range": [26.22, 26.45, 127.60, 127.85], "msg": "那覇18L、18R"}]
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
    try:
        requests.post(url, headers=headers, json=data)
    except:
        pass

def monitor():
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    
    # 6時台リセット
    if now.hour == 6 and now.minute < 10:
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

            # 3500ft以下で降下中
            if vert_rate < -0.5 and alt_ft < 3500:
                for name, corridors in AREAS.items():
                    if name in detected_airports: continue
                    for corridor in corridors:
                        r = corridor["range"]
                        # タイポ修正箇所
                        if r[0] <= lat <= r[1] and r[2] <= lon <= r[3]:
                            if "track" in corridor and not (corridor["track"][0] <= track <= corridor["track"][1]):
                                continue
                            
                            new_mode = corridor["msg"]
                            if current_state.get(name) != new_mode:
                                prefix = "【ベース】" if now.hour == 6 else ""
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
