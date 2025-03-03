import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt  
from binance.client import Client
import os
from dotenv import load_dotenv
import logging
load_dotenv()

API_KEY = os.getenv("BIN_API_KEY")
API_SECRET = os.getenv("BIN_SEC_KEY")
client = Client(API_KEY, API_SECRET)

# 🔹 로그 설정
logging.basicConfig(filename='log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 🔹 바이낸스 선물 데이터 가져오기
def get_binance_futures_data(symbol="BTCUSDT", interval="15m", limit=1000):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_asset_volume', 'trades', 
                                       'taker_buy_base', 'taker_buy_quote', 'ignore'])
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)
    return df

# 🔹 이동 평균 교차 + 손절/익절 전략
class SmaCrossStrategy(bt.Strategy):
    params = (("fast", 5), ("slow", 20), ("stop_loss", 0.01), ("take_profit", 0.02))

    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(period=self.params.fast)
        self.slow_ma = bt.indicators.SimpleMovingAverage(period=self.params.slow)
        self.order = None  # 현재 주문 추적

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None  # 주문이 완료되면 초기화
            if order.status == order.Completed:
                logging.info(f"주문 완료: {order.getordername()} at {order.executed.price} 가격으로 체결됨")

    def next(self):
        if self.order:
            return  # 주문이 체결되기 전까지는 새 주문 실행 안 함

        size = self.broker.get_cash() * 0.1 / self.data.close[0]  # 자본의 10%만 사용

        # 롱 포지션 진입
        if self.fast_ma[-1] < self.slow_ma[-1] and self.fast_ma[0] > self.slow_ma[0]:
            self.order = self.buy(size=size)
            stop_price = self.data.close[0] * (1 - self.params.stop_loss)  # -1% 손절
            take_profit_price = self.data.close[0] * (1 + self.params.take_profit)  # +2% 익절
            self.sell(exectype=bt.Order.Stop, price=stop_price)  # 손절
            self.sell(exectype=bt.Order.Limit, price=take_profit_price)  # 익절
            logging.info(f"매수 주문: {self.data.close[0]} 가격에서 진입, 손절: {stop_price}, 익절: {take_profit_price}")

        # 숏 포지션 진입
        elif self.fast_ma[-1] > self.slow_ma[-1] and self.fast_ma[0] < self.slow_ma[0]:
            self.order = self.sell(size=size)
            stop_price = self.data.close[0] * (1 + self.params.stop_loss)  # +1% 손절
            take_profit_price = self.data.close[0] * (1 - self.params.take_profit)  # -2% 익절
            self.buy(exectype=bt.Order.Stop, price=stop_price)  # 손절
            self.buy(exectype=bt.Order.Limit, price=take_profit_price)  # 익절
            logging.info(f"매도 주문: {self.data.close[0]} 가격에서 진입, 손절: {stop_price}, 익절: {take_profit_price}")

# 🔹 백테스트 실행
def run_backtest():
    df = get_binance_futures_data()
    data = bt.feeds.PandasData(dataname=df)

    cerebro = bt.Cerebro()
    cerebro.addstrategy(SmaCrossStrategy)
    
    cerebro.broker.set_cash(100)  # 🔥 초기 자본 100 USDT
    cerebro.broker.setcommission(commission=0.0004)  # 🔥 수수료 적용
    cerebro.broker.set_slippage_perc(0.001)  # 슬리피지 0.1%

    cerebro.adddata(data)

    logging.info(f"🟢 초기 자본: {cerebro.broker.getvalue():.2f} USDT")

    results = cerebro.run()
    strat = results[0]

    logging.info(f"🔴 최종 자본: {cerebro.broker.getvalue():.2f} USDT")

    fig = cerebro.plot()[0][0]  
    fig.savefig("backtest_result.png")  
    plt.show(block=False)

run_backtest()
