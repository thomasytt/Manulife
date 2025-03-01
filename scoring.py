# scripts/scoring.py
import pandas as pd
import numpy as np
from pathlib import Path
from ta.momentum import RSIIndicator
from ta.trend import CCIIndicator
from ta.volatility import BollingerBands

class Scorer:
    def __init__(self):
        # 初始化路徑
        self.project_root = Path(__file__).parent.parent
        # 加載宏利基金數據
        self.fund_data = pd.read_csv(
            self.project_root/'data'/'manulife_funds.csv',
            parse_dates=['Date'],
            index_col='Date'
        )
        # 基金-ETF映射表
        self.etf_map = {
            'SHK126': 'EWH',   # 香港股票基金 → iShares MSCI香港
            'SHK128': 'EPP',   # 亞太股票基金 → iShares MSCI亞太
            'SHK129': 'EZU',   # 歐洲股票基金 → iShares MSCI歐元區
            'SHK130': 'SPY',   # 北美股票基金 → SPDR標普500
            'SHK131': 'EWJ',   # 日本股票基金 → iShares MSCI日本
            'SHK136': 'MCHI'   # 中華威力基金 → iShares MSCI中國
        }
        # 加載VIX數據
        self.vix_data = pd.read_csv(
            self.project_root/'data'/'etfs'/'VIX.csv',
            parse_dates=['Date'],
            index_col='Date'
        )

    def load_etf(self, etf_code):
        """加載對應的ETF週線數據"""
        path = self.project_root/'data'/'etfs'/f"{etf_code}.csv"
        return pd.read_csv(path, parse_dates=['Date'], index_col='Date')

    # ================= 趨勢動量指標 =================
    def ema20_slope(self, fund_code):
        """
        計算EMA20斜率是否≥0度
        安全機制：數據不足時自動返回False
        """
        prices = self.fund_data[f"{fund_code}_Close"].dropna()
        if len(prices) < 20:
            return False
        # 計算EMA20
        ema = prices.ewm(span=20, min_periods=15).mean()
        # 計算斜率（角度制）
        slope_rad = np.arctan(ema.diff() / ema.shift(1))
        slope_deg = np.degrees(slope_rad)
        return slope_deg.iloc[-1] >= 0 if not np.isnan(slope_deg.iloc[-1]) else False

    def macd_expansion(self, fund_code):
        """
        判斷MACD柱狀體是否連續2週擴大
        安全機制：數據不足時返回False
        """
        prices = self.fund_data[f"{fund_code}_Close"].dropna()
        if len(prices) < 26:
            return False
        # 計算MACD
        exp12 = prices.ewm(span=12).mean()
        exp26 = prices.ewm(span=26).mean()
        macd_line = exp12 - exp26
        signal_line = macd_line.ewm(span=9).mean()
        histogram = macd_line - signal_line
        # 判斷最新兩週柱狀體擴大
        return (abs(histogram.iloc[-1]) > abs(histogram.iloc[-2])) and \
               (abs(histogram.iloc[-2]) > abs(histogram.iloc[-3]))

    # ================= CCI突破指標 =================
    def cci_breakthrough(self, fund_code, threshold=100):
        """
        日線CCI(20)突破±閾值
        返回：1（上穿-100）/ -1（下穿+100）/ 0（無信號）
        """
        # 獲取日線數據（假設列名為'SHK126_Daily_Close'等）
        daily_prices = self.fund_data[f"{fund_code}_Daily_Close"].dropna()
        if len(daily_prices) < 20:
            return 0
        # 計算CCI
        cci = CCIIndicator(
            high=daily_prices + 1,   # 因數據限制，假設價格波動範圍
            low=daily_prices - 1,
            close=daily_prices,
            window=20
        ).cci()
        # 判斷突破
        if cci.iloc[-2] < -threshold and cci.iloc[-1] >= -threshold:
            return 1   # 上穿-100，看多
        elif cci.iloc[-2] > threshold and cci.iloc[-1] <= threshold:
            return -1  # 下穿+100，看空
        else:
            return 0

    # ================= 價量背離指標 =================
    def volume_divergence(self, fund_code):
        """基於區域ETF的價量背離檢測"""
        etf_code = self.etf_map.get(fund_code)
        if not etf_code:
            return False
        # 加載ETF數據
        etf = self.load_etf(etf_code)
        if etf.empty:
            return False
        # 基金價格新高（允許3%誤差）
        fund_price = self.fund_data[f"{fund_code}_Close"].iloc[-1]
        etf_52_high = etf['Close'].rolling(52).max().iloc[-1]
        price_high = fund_price >= (etf_52_high * 0.97)
        # ETF成交量萎縮
        volume_avg_3m = etf['Volume'].rolling(12).mean().iloc[-1]
        volume_shrink = etf['Volume'].iloc[-1] < (volume_avg_3m * 0.85)
        return price_high and volume_shrink

    # ================= 波動率濾波 =================
    def volatility_filter(self, fund_code):
        """布林帶寬度 < 52週25%分位數"""
        prices = self.fund_data[f"{fund_code}_Close"].dropna()
        if len(prices) < 20:
            return False
        # 計算布林帶
        bb = BollingerBands(prices, window=20, window_dev=2)
        bandwidth = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
        # 計算歷史分位數
        hist_bandwidth = bandwidth.rolling(52).quantile(0.25).iloc[-1]
        return bandwidth.iloc[-1] < hist_bandwidth

    # ================= RSI共振 =================
    def rsi_resonance(self, fund_code):
        """週RSI>50且日RSI>55"""
        # 週線RSI
        weekly_prices = self.fund_data[f"{fund_code}_Close"]
        weekly_rsi = RSIIndicator(weekly_prices, window=14).rsi().iloc[-1]
        # 日線RSI（假設列名為'SHK126_Daily_Close'）
        daily_prices = self.fund_data[f"{fund_code}_Daily_Close"]
        daily_rsi = RSIIndicator(daily_prices, window=14).rsi().iloc[-1]
        return (weekly_rsi > 50) and (daily_rsi > 55)

    # ================= 綜合評分 =================
    def calculate_score(self, fund_code):
        """計算單個基金總評分（0-11分）"""
        score = 0
        
        # 趨勢動量（2分）
        if self.ema20_slope(fund_code):
            score += 1
        if self.macd_expansion(fund_code):
            score += 1
            
        # CCI突破（2分）
        cci_signal = self.cci_breakthrough(fund_code)
        score += 2 if cci_signal != 0 else 0
        
        # 價量背離（1分）
        if self.volume_divergence(fund_code):
            score += 1
            
        # 波動率濾波（1分）
        if self.volatility_filter(fund_code):
            score += 1
            
        # RSI共振（1分）
        if self.rsi_resonance(fund_code):
            score += 1
            
        # 區域輪動（2分）- 需額外實現
        # 跨市場相關性（1分）- 需額外實現
        # 行業資金流（1分）- 需額外實現
        
        return min(score, 11)  # 確保不超過11分

# ================= 測試代碼 =================
if __name__ == "__main__":
    scorer = Scorer()
    
    # 測試SHK126的EMA20斜率
    print("SHK126 EMA20斜率是否≥0°:", scorer.ema20_slope('SHK126'))
    
    # 測試SHK130的CCI突破
    print("SHK130 CCI突破信號:", scorer.cci_breakthrough('SHK130'))
    
    # 計算SHK128總評分
    print("SHK128總評分:", scorer.calculate_score('SHK128'))