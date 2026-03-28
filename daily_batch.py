import os
import requests
from datetime import datetime, timedelta, timezone

# 日本全国空港リスト (ICAOコード, TAFの有無)
# True = TAFあり, False = METARのみ
AIRPORT_LIST = [
    # 北海道
    ("RJCC", True), ("RJCB", True), ("RJCH", True), ("RJCK", True), ("RJCM", True),
    ("RJEC", True), ("RJCN", False), ("RJCW", False), ("RJEB", False), ("RJCJ", False),
    ("RJER", False), ("RJCT", False), ("RJCA", False), ("RJCO", False), ("RJEO", False),
    # 東北
    ("RJSS", True), ("RJSA", True), ("RJSF", True), ("RJSK", True), ("RJSN", True),
    ("RJSR", False), ("RJSI", False), ("RJSY", False), ("RJSC", False), ("RJSM", False),
    ("RJSO", False), ("RJSH", False), ("RJST", False), ("RJSU", False),
    # 関東
    ("RJTT", True), ("RJAA", True), ("RJAH", True), ("RJTY", True), ("RJTF", False),
    ("RJTI", False), ("RJTO", False), ("RJAW", False), ("RJTH", False), ("RJTU", False),
    ("RJTS", False), ("RJTJ", False), ("RJTR", False), ("RJTC", False), ("RJTA", False),
    ("RJAI", False), ("RJTX", False), ("RJAK", False), ("RJTL", False), ("RJTK", False),
    ("RJTE", False), ("RJAN", False), ("RJAZ", False), ("RJTQ", False), ("RJAM", False), ("RJAO", False),
    # 東海・北陸
    ("RJGG", True), ("RJNK", True), ("RJNS", True), ("RJNT", True), ("RJNW", False),
    ("RJAF", False), ("RJNF", False), ("RJAT", False), ("RJNY", False), ("RJNH", False),
    ("RJNA", False), ("RJNG", False),
    # 近畿・四国
    ("RJBB", True), ("RJOO", True), ("RJBE", False), ("RJOK", True), ("RJOM", True),
    ("RJOT", True), ("RJOY", False), ("RJBT", False), ("RJBD", False), ("RJBM", False),
    ("RJOE", False), ("RJOS", False), ("RJOP", False),
    # 中国
    ("RJOA", True), ("RJOB", True), ("RJOC", True), ("RJOH", True), ("RJOI", True),
    ("RJOR", False), ("RJOW", False), ("RJDC", False), ("RJNO", False), ("RJOF", False), ("RJOZ", False),
    # 九州
    ("RJFF", True), ("RJFK", True), ("RJFM", True), ("RJFO", True), ("RJFR", True),
    ("RJFT", True), ("RJFU", True), ("RJFS", True), ("RJDT", False), ("RJFG", False),
    ("RJKA", False), ("RJDB", False), ("RJFE", False), ("RJFA", False), ("RJFZ", False),
    ("RJDM", False), ("RJDA", False), ("RJFN", False), ("RJFY", False), ("RJFC", False),
    ("RJKI", False), ("RJKN", False), ("RJKB", False), ("RORY", False),
    # 沖縄
    ("ROAH", True), ("ROIG", True), ("ROTM", True), ("RODN", True), ("ROMY", False),
    ("RORS", False), ("ROKJ", False), ("RORK", False), ("ROMD", False), ("RORA", False),
    ("RORT", False), ("RORH", False), ("ROYN", False),
    # 主要海外空港（おまけ）
    ("VHHH", True), ("VTBS", True), ("WSSS", True), ("KLAX", True), ("KSFO", True), ("KJFK", True), ("EGLL", True), ("LFPG", True)
]

def fetch_weather(icao, has_taf):
    metar_url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{icao}.TXT"
    taf_url = f"https://tgftp.nws.noaa.gov/data/forecasts/taf/stations/{icao}.TXT"
    
    data = f"=== {icao} ===\n"
    # METAR取得
    try:
        m = requests.get(metar_url, timeout=10)
        data += f"[METAR]\n{m.text}\n" if m.status_code == 200 else "[METAR] N/A\n"
    except:
        data += "[METAR] Error\n"
    
    # TAF取得（対象空港のみ）
    if has_taf:
        try:
            t = requests.get(taf_url, timeout=10)
            data += f"[TAF]\n{t.text}\n" if t.status_code == 200 else "[TAF] N/A\n"
        except:
            data += "[TAF] Error\n"
    
    return data + "\n"

def main():
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    timestamp = now.strftime('%Y%m%d_%H%M')
    
    os.makedirs("daily_upload", exist_ok=True)
    report = f"Japan/World Aviation Weather Archive\nRun Time: {now.strftime('%Y-%m-%d %H:%M:%S')} JST\n"
    report += "="*40 + "\n\n"
    
    for icao, has_taf in AIRPORT_LIST:
        report += fetch_weather(icao, has_taf)
    
    filename = f"daily_upload/{timestamp}_JapanWeatherArchive.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()
