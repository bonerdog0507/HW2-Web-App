import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import sqlite3
import scraper

# 設定網頁版面
st.set_page_config(page_title="台灣農業氣象預報", layout="wide")

st.title("☀️ 台灣農業氣象預報")

# 區域對應的大致座標 (緯度, 經度)
REGION_COORDS = {
    "北部地區": (25.0330, 121.5654), # 台北
    "中部地區": (24.1477, 120.6736), # 台中
    "南部地區": (22.6273, 120.3014), # 高雄
    "東北部地區": (24.7523, 121.7569), # 宜蘭
    "東部地區": (23.9769, 121.6044),   # 花蓮
    "東南部地區": (22.7562, 121.1495)  # 台東
}

def get_color(avg_temp):
    """根據平均溫度決定顏色"""
    if avg_temp < 20:
        return "blue"
    elif 20 <= avg_temp < 25:
        return "green"
    elif 25 <= avg_temp <= 30:
        return "orange" # 使用 orange 替代黃色，因為 folium 的 default icon 顏色支援 orange 較好，或者用 circle_marker 的 fill_color
    else:
        return "red"

def get_hex_color(avg_temp):
    if avg_temp < 20:
        return "#3186cc" # Blue
    elif 20 <= avg_temp < 25:
        return "#2ca02c" # Green
    elif 25 <= avg_temp <= 30:
        return "#ffcc00" # Yellow
    else:
        return "#d62728" # Red

# 載入資料
@st.cache_data
def load_data():
    if not os.path.exists("data.db"):
        st.info("初次執行或找不到資料庫，正在自動抓取最新氣象資料...")
        scraper.fetch_weather_data()
        
    if not os.path.exists("data.db"):
        return None
        
    conn = sqlite3.connect("data.db")
    
    # 從資料庫讀取資料
    query = "SELECT regionName as Region, dataDate as Date, mint as MinT, maxt as MaxT FROM TemperatureForecasts"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 計算平均溫度
    if not df.empty:
        df['AvgT'] = (df['MinT'] + df['MaxT']) / 2
        
    return df

df = load_data()

if df is None or df.empty:
    st.warning("找不到氣象資料，請先執行 scraper.py 抓取資料！")
else:
    # 建立左右兩欄
    col1, col2 = st.columns([1, 1])
    
    with col2:
        st.subheader("📅 資料篩選與詳細資訊")
        # 取得所有可用日期
        available_dates = df['Date'].unique().tolist()
        
        # 下拉選單選擇日期
        selected_date = st.selectbox("請選擇日期：", available_dates)
        
        # 篩選資料
        filtered_df = df[df['Date'] == selected_date].copy()
        
        st.write(f"**{selected_date} 氣象資料表：**")
        st.dataframe(filtered_df.style.format({
            'MinT': '{:.1f} °C',
            'MaxT': '{:.1f} °C',
            'AvgT': '{:.1f} °C'
        }), use_container_width=True)

    with col1:
        st.subheader("🗺️ 台灣氣溫分佈圖")
        
        # 建立台灣地圖
        m = folium.Map(location=[23.5, 121.0], zoom_start=7, tiles="CartoDB positron")
        
        # 在地圖上標示各區
        for index, row in filtered_df.iterrows():
            region = row['Region']
            if region in REGION_COORDS:
                coords = REGION_COORDS[region]
                avg_t = row['AvgT']
                min_t = row['MinT']
                max_t = row['MaxT']
                
                # Popup 內容
                popup_html = f"""
                <div style='font-size: 14px; width: 150px;'>
                    <b>{region}</b><br>
                    平均溫度: {avg_t:.1f}°C<br>
                    最高溫: {max_t:.1f}°C<br>
                    最低溫: {min_t:.1f}°C
                </div>
                """
                
                # 加入圓形標記
                folium.CircleMarker(
                    location=coords,
                    radius=15,
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=region,
                    color=get_hex_color(avg_t),
                    fill=True,
                    fill_color=get_hex_color(avg_t),
                    fill_opacity=0.7
                ).add_to(m)
        
        # 顯示圖例
        st.markdown(
            "**圖例**： "
            "<span style='color:#3186cc'>🔵 < 20°C</span> | "
            "<span style='color:#2ca02c'>🟢 20-25°C</span> | "
            "<span style='color:#ffcc00'>🟡 25-30°C</span> | "
            "<span style='color:#d62728'>🔴 > 30°C</span>", 
            unsafe_allow_html=True
        )
        
        # 在 Streamlit 中顯示 Folium 地圖
        st_folium(m, width=700, height=500)
