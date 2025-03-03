import json
import websocket
import threading
import os
import time
from datetime import datetime, timezone, timedelta

class BinanceWebSocket:
    def __init__(self, symbol="btcusdt", interval="1m", data_file="BTC_data.json"):
        self.symbol = symbol
        self.interval = interval
        self.data_file = data_file
        self.stream_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{self.interval}"
        self.ws = None
        self.thread = None

    def save_to_json(self, new_data):
        """ JSON 파일에 데이터를 저장하는 함수 """
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        data.append(new_data)

        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def on_message(self, ws, message):
        """ 새로운 1분봉이 닫힐 때만 데이터 저장 """
        data = json.loads(message)
        kline = data['k']

        if kline["x"]:  # x=True이면 캔들이 종료된 것
            timestamp_utc = datetime.fromtimestamp(kline['t'] / 1000, tz=timezone.utc)
            close_time_utc = datetime.fromtimestamp(kline['T'] / 1000, tz=timezone.utc)
            
            timestamp_kst = timestamp_utc + timedelta(hours=9)
            close_time_kst = close_time_utc + timedelta(hours=9)

            formatted_data = {
                "timestamp": timestamp_kst.strftime('%Y-%m-%d %H:%M:%S'),  # KST 변환 후 저장
                "open": float(kline['o']),
                "high": float(kline['h']),
                "low": float(kline['l']),
                "close": float(kline['c']),
                "volume": float(kline['v']),
                "close_time": close_time_kst.strftime('%Y-%m-%d %H:%M:%S')  # KST 변환 후 저장
            }

            self.save_to_json(formatted_data)
            print(f"새로운 데이터 저장됨: {formatted_data}")

    def on_error(self, ws, error):
        print(f"WebSocket Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket Closed")
        self.reconnect()

    def on_open(self, ws):
        print("WebSocket 연결 성공!")

    def reconnect(self):
        """ 웹소켓 재연결 """
        print("웹소켓 재연결 중...")
        self.run_websocket()

    def run_websocket(self):
        """ 웹소켓을 실행하는 함수 (연결 유지) """
        self.ws = websocket.WebSocketApp(self.stream_url, 
                                         on_message=self.on_message, 
                                         on_error=self.on_error, 
                                         on_close=self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever()

    def start(self):
        """ 웹소켓을 백그라운드에서 실행 """
        self.thread = threading.Thread(target=self.run_websocket)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """ 웹소켓 종료 """
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join()



if __name__ == "__main__":
    ws_client = BinanceWebSocket()
    ws_client.start()

    # 메인 스레드가 종료되지 않도록 유지
    while True:
        time.sleep(1)