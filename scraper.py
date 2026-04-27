import requests
import json
import pandas as pd
import urllib3
import sqlite3

# 忽略 SSL 憑證警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CWA API 網址 (F-A0010-001)
API_URL = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-A0010-001?Authorization=CWA-C7098B83-282B-4AB8-B3EA-1BCB981113C8&downloadType=WEB&format=JSON"

def fetch_weather_data():
    try:
        print("正在取得氣象資料...")
        # 忽略 SSL 驗證
        response = requests.get(API_URL, verify=False)
        response.raise_for_status()
        
        data = response.json()
        
        # 解析 JSON 結構
        locations = data.get('cwaopendata', {}).get('resources', {}).get('resource', {}).get('data', {}).get('agrWeatherForecasts', {}).get('weatherForecasts', {}).get('location', [])
        
        if not locations:
            print("無法找到地區資料。")
            return
            
        weather_records = []
        
        # 目標地區
        target_regions = ["北部地區", "中部地區", "南部地區", "東北部地區", "東部地區", "東南部地區"]
        
        for loc in locations:
            loc_name = loc.get('locationName')
            if loc_name not in target_regions:
                continue
                
            weather_elements = loc.get('weatherElements', {})
            
            # 取得每日最高溫與最低溫
            max_t_daily = weather_elements.get('MaxT', {}).get('daily', [])
            min_t_daily = weather_elements.get('MinT', {}).get('daily', [])
            
            # 因為 MaxT 和 MinT 的 daily 長度應該一樣，使用 zip 進行迴圈
            for mx, mn in zip(max_t_daily, min_t_daily):
                date = mx.get('dataDate')
                max_temp = float(mx.get('temperature', 0))
                min_temp = float(mn.get('temperature', 0))
                
                weather_records.append((
                    loc_name,
                    date,
                    min_temp,
                    max_temp
                ))
                
        # 寫入 SQLite3 資料庫
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # 建立資料表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TemperatureForecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regionName TEXT,
                dataDate TEXT,
                mint REAL,
                maxt REAL
            )
        ''')
        
        # 清除舊資料 (可選，這裡為了確保不重複，每次抓取都重新寫入或新增)
        cursor.execute('DELETE FROM TemperatureForecasts')
        
        # 插入新資料
        cursor.executemany('''
            INSERT INTO TemperatureForecasts (regionName, dataDate, mint, maxt)
            VALUES (?, ?, ?, ?)
        ''', weather_records)
        
        conn.commit()
        conn.close()
        
        print("氣象資料已成功儲存至 data.db 的 TemperatureForecasts 資料表")
        
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    fetch_weather_data()
