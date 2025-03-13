from ohlcv_update import BinanceWebSocket_ohlcv
from trading_info import TradingIndicators
import threading

def start_ohlcv():
    ohlcv = BinanceWebSocket_ohlcv(symbol="btcusdt", data_file="1min_BTC_OHLCV.json")
    ohlcv.start()


def start_trading_info():
    trading_indicators = TradingIndicators('1min_BTC_OHLCV.json')
    trading_indicators.run()

if __name__ == "__main__":
    # 세 개의 웹소켓을 각각의 스레드에서 실행
    ohlcv_thread = threading.Thread(target=start_ohlcv)
    trading_info_thread = threading.Thread(target=start_trading_info)

    # 스레드 시작
    ohlcv_thread.start()
    trading_info_thread.start()

    # 세 스레드가 끝날 때까지 기다림
    ohlcv_thread.join()
    trading_info_thread.join()
