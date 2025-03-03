import ccxt
import pandas as pd
import numpy as np
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
import os
from dotenv import load_dotenv
import logging
load_dotenv()

API_KEY = os.getenv("BIN_API_KEY")
API_SECRET = os.getenv("BIN_SEC_KEY")

# 바이낸스 API 설정
api_key = API_KEY
api_secret = API_SECRET
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'options': {'defaultType': 'future'}  # 선물 거래 활성화
})

# 바이낸스 API 설정
exchange = ccxt.binance()
symbol = 'BTC/USDT'
timeframe = '1h'

# 초기 자본 및 레버리지 설정
initial_balance = 100  # 시작 잔고
leverage = 10  # 10배 레버리지
balance = initial_balance
position = None  # 현재 포지션 ('LONG', 'SHORT' 또는 None)
entry_price = None  # 진입 가격

# 손실 및 수익 제한 설정
max_loss = -3 / 100  # -3%
max_profit = 5 / 100  # 5%

log_file = "logsma.txt"

# 데이터 가져오기
def fetch_data(symbol, timeframe, limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# 지표 계산
def calculate_indicators(df):
    df['RSI'] = RSIIndicator(df['close'], window=14).rsi()
    bb = BollingerBands(df['close'], window=20, window_dev=2)
    df['BB_upper'] = bb.bollinger_hband()
    df['BB_lower'] = bb.bollinger_lband()
    return df

# 백테스트 실행
def run_backtest():
    global balance, position, entry_price
    df = fetch_data(symbol, timeframe)
    df = calculate_indicators(df)

    with open(log_file, "w") as log:
        for i in range(1, len(df)):
            latest = df.iloc[i]
            prev = df.iloc[i - 1]
            
            if position is None:
                if latest['RSI'] < 30 and latest['close'] <= latest['BB_lower']:
                    position = 'LONG'
                    entry_price = latest['close']
                    log.write(f"LONG 진입: {latest['timestamp']} @ {entry_price}\n")
                elif latest['RSI'] > 70 and latest['close'] >= latest['BB_upper']:
                    position = 'SHORT'
                    entry_price = latest['close']
                    log.write(f"SHORT 진입: {latest['timestamp']} @ {entry_price}\n")
            
            elif position == 'LONG':
                profit = (latest['high'] - entry_price) / entry_price
                loss = (latest['low'] - entry_price) / entry_price
                if profit >= max_profit or loss <= max_loss:
                    balance *= (1 + min(profit, max_loss) * leverage)
                    log.write(f"LONG 청산: {latest['timestamp']} @ {latest['close']} | PnL: {min(profit, max_loss) * 100:.2f}% | 잔고: ${balance:.2f}\n")
                    position = None
                    entry_price = None
            
            elif position == 'SHORT':
                profit = (entry_price - latest['low']) / entry_price
                loss = (entry_price - latest['high']) / entry_price
                if profit >= max_profit or loss <= max_loss:
                    balance *= (1 + min(profit, max_loss) * leverage)
                    log.write(f"SHORT 청산: {latest['timestamp']} @ {latest['close']} | PnL: {min(profit, max_loss) * 100:.2f}% | 잔고: ${balance:.2f}\n")
                    position = None
                    entry_price = None
    
        log.write(f"백테스트 종료 - 최종 잔고: ${balance:.2f}\n")
    print(f"백테스트 종료 - 최종 잔고: ${balance:.2f}")

if __name__ == "__main__":
    run_backtest()