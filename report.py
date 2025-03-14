from ohlcv_update import BinanceWebSocket_ohlcv
from trading_info import TradingIndicators
import json
import time
import os
import threading
from datetime import datetime, timedelta, timezone


def check_timestamp():
    try:
        with open('Technical_indicators.json', 'r') as f:
            data = json.load(f)

        # timestamp를 offset-aware로 변환
        timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        
        # 현재 시간 한국 시간 기준 변환
        now_kst = datetime.now(timezone.utc) + timedelta(hours=9)
        time_diff = now_kst - timestamp

        if time_diff.total_seconds() > 300:  # 5분 초과 시
            print("⛔ 데이터가 5분 이상 경과했습니다. 스크립트를 재시작합니다.")
            restart_script()
        else:
            print("✅ 데이터가 최신 상태입니다.")

    except Exception as e:
        print(f"⚠️ 오류 발생: {e}")
        restart_script()

def restart_script():
    python = os.sys.executable  # 현재 실행 중인 Python 경로 사용
    print("🔄 스크립트를 재시작합니다...")
    os.execl(python, python, *os.sys.argv)


def start_ohlcv():
    ohlcv = BinanceWebSocket_ohlcv(symbol="btcusdt", data_file="1min_BTC_OHLCV.json")
    ohlcv.start()


def start_trading_info():
    trading_indicators = TradingIndicators('1min_BTC_OHLCV.json')
    trading_indicators.run()


def start_check_timestamp():
    print("⏳ 1분 후에 타임스탬프 체크 시작...")
    time.sleep(60)  # 1분 대기 후 실행
    while True:
        check_timestamp()
        time.sleep(10)  # 1분 간격으로 체크


if __name__ == "__main__":
    # 스레드 설정
    ohlcv_thread = threading.Thread(target=start_ohlcv)
    trading_info_thread = threading.Thread(target=start_trading_info)
    check_thread = threading.Thread(target=start_check_timestamp)

    # 스레드 시작
    ohlcv_thread.start()
    trading_info_thread.start()
    check_thread.start()

    # 스레드 종료 대기
    ohlcv_thread.join()
    trading_info_thread.join()
    check_thread.join()
