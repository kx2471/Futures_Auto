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
    return data['close'].astype(float).rolling(window=window).mean()

# WMA 계산
def get_wma(data, window=14):
    weights = np.arange(1, window + 1)
    return data['close'].astype(float).rolling(window=window).apply(lambda prices: np.dot(prices, weights) / weights.sum(), raw=True)

# EMA 계산
def get_ema(data, window=14):
    return data['close'].astype(float).ewm(span=window, adjust=False).mean()

# RSI 계산
def get_rsi(data, window=14):
    delta = data['close'].astype(float).diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# MACD 계산
def get_macd(data, fast=12, slow=26, signal=9):
    fast_ema = get_ema(data, fast)
    slow_ema = get_ema(data, slow)
    macd = fast_ema - slow_ema
    signal_line = get_ema(data, signal)
    histogram = macd - signal_line
    return macd, signal_line, histogram

# 볼린저밴드 계산
def get_bb(data, window=20, num_std_dev=2):
    # 먼저 단순이동평균(SMA)을 계산합니다.
    sma = get_sma(data, window)
    
    # 표준편차를 계산합니다. (rolling 함수는 처음 몇 구간에서 NaN을 생성할 수 있습니다)
    rolling_std = data['close'].astype(float).rolling(window=window).std()

    # 상한선과 하한선을 계산합니다.
    upper_band = sma + (rolling_std * num_std_dev)
    lower_band = sma - (rolling_std * num_std_dev)

    # NaN을 처리하는 방법
    # 여기서는 NaN이 포함된 구간을 제거하지 않고, NaN이 있을 경우 그대로 반환
    # 또는 필요한 경우 처음 몇 구간은 NaN을 제외한 계산으로 추가 로직을 넣을 수 있습니다.
    upper_band = upper_band.fillna(method='bfill')  # backward fill로 NaN을 채우기
    lower_band = lower_band.fillna(method='bfill')  # backward fill로 NaN을 채우기
    sma = sma.fillna(method='bfill')  # backward fill로 NaN을 채우기

    return upper_band, sma, lower_band



# VWAP 계산
def get_vwap(data):
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