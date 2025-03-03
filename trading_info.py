from binance.client import Client
import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("BIN_API_KEY")
API_SECRET = os.getenv("BIN_SEC_KEY")

#바이낸스 데이터 가져오기
def get_binance_data():
    client = Client(API_KEY, API_SECRET)

    # 1분봉 데이터 가져오기
    symbol = 'BTCUSDT'
    interval = Client.KLINE_INTERVAL_1MINUTE
    limit = 500

    # 데이터 요청
    klines = client.get_historical_klines(symbol, interval, limit=limit)

    # 데이터를 읽기 쉽게 수정 (키 추가)
    formatted_data = []
    for kline in klines:
        formatted_data.append({
            "timestamp": kline[0],
            "open": kline[1],
            "high": kline[2],
            "low": kline[3],
            "close": kline[4],
            "volume": kline[5],
            "close_time": kline[6],
            # "quote_asset_volume": kline[7],  # 제외
            "number_of_trades": kline[8],
            # "taker_buy_base_asset_volume": kline[9],  # 제외
            # "taker_buy_quote_asset_volume": kline[10],  # 제외
            # "ignore": kline[11]  # 제외
        })

    # JSON 형식으로 파일 저장 (읽기 쉽게 들여쓰기 적용)
    with open('BTC_data.json', 'w') as f:
        json.dump(formatted_data, f, indent=4)

    print("데이터가 'BTC_data.json' 파일로 저장되었습니다.")

# 데이터 로드 함수
def load_data():
    with open('BTC_data.json', 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

# SMA 계산
def get_sma(data, window=14):
    # Simple Moving Average (SMA) 계산
    return data['close'].astype(float).rolling(window=window).mean()

# WMA 계산
def get_wma(data, window=14):
    # Weighted Moving Average (WMA) 계산
    weights = np.arange(1, window+1)
    return data['close'].astype(float).rolling(window=window).apply(lambda prices: np.dot(prices, weights) / weights.sum(), raw=True)

# EMA 계산
def get_ema(data, window=14):
    # Exponential Moving Average (EMA) 계산
    return data['close'].astype(float).ewm(span=window, adjust=False).mean()

# RSI 계산
def get_rsi(data, window=14):
    # Relative Strength Index (RSI) 계산
    delta = data['close'].astype(float).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# MACD 계산
def get_macd(data, fast=12, slow=26, signal=9):
    # MACD (Moving Average Convergence Divergence) 계산
    fast_ema = get_ema(data, fast)
    slow_ema = get_ema(data, slow)
    macd = fast_ema - slow_ema
    signal_line = get_ema(data, signal)
    histogram = macd - signal_line
    
    return macd, signal_line, histogram

# 볼린저밴드 계산 (상중하)
def get_bb(data, window=20, num_std_dev=2):
    # Bollinger Bands (상, 중, 하) 계산
    sma = get_sma(data, window)
    rolling_std = data['close'].astype(float).rolling(window=window).std()
    
    upper_band = sma + (rolling_std * num_std_dev)
    lower_band = sma - (rolling_std * num_std_dev)
    
    return upper_band, sma, lower_band

# VWAP 계산
def get_vwap(data):
    # Volume Weighted Average Price (VWAP) 계산
    price_volume = data['close'].astype(float) * data['volume'].astype(float)
    vwap = price_volume.cumsum() / data['volume'].astype(float).cumsum()
    
    return vwap

# 지표 계산 예시
if __name__ == "__main__":
    #데이터 갱신
    get_binance_data()
    # 데이터 로드
    data = load_data()

    # 지표 계산
    sma = get_sma(data)
    wma = get_wma(data)
    ema = get_ema(data)
    rsi = get_rsi(data)
    macd, signal, histogram = get_macd(data)
    upper_band, sma_bb, lower_band = get_bb(data)
    vwap = get_vwap(data)

    # 결과 출력 (일부 지표 예시)
    print(f"SMA: {sma.tail()}")
    print(f"WMA: {wma.tail()}")
    print(f"EMA: {ema.tail()}")
    print(f"RSI: {rsi.tail()}")
    print(f"MACD: {macd.tail()}")
    print(f"Signal: {signal.tail()}")
    print(f"VWAP: {vwap.tail()}")