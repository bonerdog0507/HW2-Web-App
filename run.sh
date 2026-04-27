#!/bin/bash

# 建立並啟動虛擬環境
echo "📦 正在建立 Python 虛擬環境..."
python3 -m venv venv
source venv/bin/activate

# 安裝相依套件
echo "📦 正在安裝相依套件..."
pip install -r requirements.txt

# 執行爬蟲程式抓取資料
echo "🔍 正在抓取氣象資料..."
python scraper.py

# 啟動 Streamlit 網頁應用程式
echo "🚀 正在啟動 Streamlit 應用程式..."
streamlit run app.py
