# fetch_etf_data.py（完整修正版）
import yfinance as yf
import pandas as pd
from pathlib import Path
import os

# 配置參數
ETF_MAP = {
       'SHK126': 'EWH',    # 香港股票
       'SHK127': 'SPY',    # 国际股票→标普500
       'SHK128': 'EPP',    # 亚太原除日本
       'SHK129': 'EZU',    # 欧洲
       'SHK130': 'SPY',    # 北美（保持原SPY）
       'SHK131': 'EWJ',    # 日本
       'SHK136': 'MCHI',   # 中华威力
       'SHK137': 'XLV',    # 康健护理
       'SHK145': 'EWH'     # 恒指ESG→同用MSCI香港
   }
VIX_SYMBOL = '^VIX'
PROJECT_ROOT = Path(__file__).parent.parent  # 關鍵修正點
DATA_DIR = PROJECT_ROOT / "data" / "etfs"

def ensure_dir():
    """強制建立目錄（防呆設計）"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[目錄狀態] 數據將保存至：{DATA_DIR.absolute()}")

def safe_download(ticker, interval='1wk'):
    """安全下載函數（最終版）"""
    try:
        df = yf.download(ticker, period='max', interval=interval, progress=False)
        if df.empty:
            print(f"警告：{ticker} 無數據，請檢查代碼")
        return df
    except Exception as e:
        print(f"下載失敗：{ticker}，錯誤：{str(e)}")
        return pd.DataFrame()

def main():
    ensure_dir()
    
    # 抓取區域ETF數據
    for fund_code, etf_ticker in ETF_MAP.items():
        print(f"▶ 正在處理 {fund_code} -> {etf_ticker}")
        data = safe_download(etf_ticker)
        if not data.empty:
            save_path = DATA_DIR / f"{etf_ticker}.csv"
            data.to_csv(save_path)
            print(f"  已保存：{save_path.absolute()}")
    
    # 抓取VIX數據
    print("▶ 正在下載波動率指數 VIX...")
    vix_data = safe_download(VIX_SYMBOL, interval='1d')
    if not vix_data.empty:
        vix_save_path = DATA_DIR / "VIX.csv"
        vix_data.to_csv(vix_save_path)
        print(f"  已保存：{vix_save_path.absolute()}")

if __name__ == "__main__":
    main()