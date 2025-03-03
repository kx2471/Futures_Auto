from binance.client import Client
import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
import os


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
    print(f"bbUP: {upper_band.tail()}")
    print(f"bbmid: {sma_bb.tail()}")
    print(f"bbDown: {lower_band.tail()}")
    print(f"VWAP: {vwap.tail()}")