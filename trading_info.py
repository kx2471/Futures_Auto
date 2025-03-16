import json
import time
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
import os

class TradingIndicators:
    def __init__(self, data_file):
        self.data_file = data_file

    def load_data(self):
        with open(self.data_file, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)

    def get_sma(self, data, window=14):
        return data['close'].astype(float).rolling(window=window).mean()

    def get_wma(self, data, window=14):
        weights = np.arange(1, window + 1)
        return data['close'].astype(float).rolling(window=window).apply(lambda prices: np.dot(prices, weights) / weights.sum(), raw=True)

    def get_ema(self, data, window=14):
        return data['close'].astype(float).ewm(span=window, adjust=False).mean()

    def get_rsi(self, data, window=14):
        delta = data['close'].astype(float).diff()
        gain = delta.where(delta > 0, 0).rolling(window=window).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def get_macd(self, data, fast=12, slow=26, signal=9):
        fast_ema = self.get_ema(data, fast)
        slow_ema = self.get_ema(data, slow)
        macd = fast_ema - slow_ema
        return macd

    def get_bb(self, data, window=20, num_std_dev=2):
        sma = self.get_sma(data, window)
        rolling_std = data['close'].rolling(window=window).std()

        upper_band = sma + (rolling_std * num_std_dev)
        lower_band = sma - (rolling_std * num_std_dev)

        upper_band = upper_band.bfill()
        lower_band = lower_band.bfill()
        sma = sma.bfill()

        return upper_band, sma, lower_band

    def get_vwap(self, data):
        price_volume = data['close'].astype(float) * data['volume'].astype(float)
        vwap = price_volume.cumsum() / data['volume'].astype(float).cumsum()
        return vwap

    def save_indicators(self, data):
        # 지표 계산
        sma = self.get_sma(data)
        wma = self.get_wma(data)
        ema = self.get_ema(data)
        rsi = self.get_rsi(data)
        macd = self.get_macd(data)
        upper_band, sma_bb, lower_band = self.get_bb(data)
        vwap = self.get_vwap(data)

        # 현재 UTC 시간을 가져오기  
        timestamp = datetime.now(timezone.utc)
        kst_time = timestamp + timedelta(hours=9)  # 한국시간으로 변환
        formatted_timestamp = kst_time.strftime('%Y-%m-%d %H:%M:%S')



        # 지표 데이터 저장
        indicators = {
            "timestamp": formatted_timestamp,
            "sma": sma.tail(15).tolist(),
            "wma": wma.tail(15).tolist(),
            "ema": ema.tail(15).tolist(),
            "rsi": rsi.tail(15).tolist(),
            "macd": macd.tail(15).tolist(),
            "bb_upper": upper_band.tail(15).tolist(),
            "bb_sma": sma_bb.tail(15).tolist(),
            "bb_lower": lower_band.tail(15).tolist(),
            "vwap": vwap.tail(15).tolist()
        }

        if not os.path.exists('Technical_indicators.json'):
            print("File not found. Creating new file...")
        # JSON 파일에 저장
        with open('Technical_indicators.json', 'w') as f:
            json.dump(indicators, f, indent=4)

        print("Technical indicators saved to Technical_indijscators.json")

    def run(self):
        while True:
            # 데이터 로드
            data = self.load_data()

            # 지표 저장
            self.save_indicators(data)

            # 1분 대기
            time.sleep(10)

