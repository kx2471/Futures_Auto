from ohlcv_update import BinanceWebSocket


def ohlcv(): #ohlcv_update 실행함수
    ws_client = BinanceWebSocket()
    ws_client.start()

    # 메인 스레드가 종료되지 않도록 대기
    while True:
        pass  # 또는 time.sleep(1)
