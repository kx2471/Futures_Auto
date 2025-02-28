import backtrader as bt
import pandas as pd
from binance.client import Client

# 🔹 바이낸스 API 설정 (API 키는 보안상 .env에서 관리하는 게 좋음)
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"

client = Client(API_KEY, API_SECRET)

# 🔹 바이낸스 선물 데이터 가져오기
def get_binance_futures_data(symbol="BTCUSDT", interval="1h", limit=500):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_asset_volume', 'trades', 
                                       'taker_buy_base', 'taker_buy_quote', 'ignore'])
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)
    return df

# 🔹 이동 평균 교차 전략
class SmaCrossStrategy(bt.Strategy):
    params = (("fast", 5), ("slow", 20),)

    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(period=self.params.fast)
        self.slow_ma = bt.indicators.SimpleMovingAverage(period=self.params.slow)

    def next(self):
        if self.fast_ma[0] > self.slow_ma[0] and self.fast_ma[-1] <= self.slow_ma[-1]:
            self.buy()  # 롱 포지션 진입
        elif self.fast_ma[0] < self.slow_ma[0] and self.fast_ma[-1] >= self.slow_ma[-1]:
            self.sell()  # 숏 포지션 진입

# 🔹 백테스트 실행
def run_backtest():
    df = get_binance_futures_data()
    data = bt.feeds.PandasData(dataname=df)
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SmaCrossStrategy)
    cerebro.adddata(data)
    cerebro.run()
    cerebro.plot()

run_backtest()
