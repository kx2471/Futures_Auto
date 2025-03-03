import websocket
import json
from datetime import datetime, timezone, timedelta
import time

class BinanceWebSocket:
    def __init__(self, symbol="btcusdt", interval="1m", data_file="BTC_data.json"):
        self.symbol = symbol
        self.interval = interval
        self.data_file = data_file
        self.stream_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{self.interval}"
        self.ws = None
        self.data_buffer = []  # 데이터를 임시로 저장할 버퍼
        self.last_timestamp = None

    def save_to_json(self, new_data):
        """ JSON 파일에 데이터를 저장하는 함수 """
        try:
            with open(self.data_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(new_data)

        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def process_data(self):
        """ 5초마다 데이터를 처리하여 저장 """
        if not self.data_buffer:
            return

        # 5초 동안 받은 데이터 중 첫 번째 데이터를 기준으로 설정
        first_data = self.data_buffer[0]
        last_data = self.data_buffer[-1]

        # timestamp: 5초 동안 받은 데이터 중 첫 번째 데이터의 timestamp
        timestamp = datetime.fromtimestamp(first_data['t'] / 1000, tz=timezone.utc) + timedelta(hours=9)
        close_time = datetime.fromtimestamp(last_data['T'] / 1000, tz=timezone.utc) + timedelta(hours=9)

        # open: 첫 번째 데이터의 open 가격
        open_price = first_data['o']
        # close: 마지막 데이터의 close 가격
        close_price = last_data['c']

        # high: 5초 동안 받은 데이터 중 가장 높은 open 가격
        high_price = max(data['h'] for data in self.data_buffer)
        # low: 5초 동안 받은 데이터 중 가장 낮은 open 가격
        low_price = min(data['l'] for data in self.data_buffer)

        # volume: 5초 동안 받은 데이터의 volume 평균
        avg_volume = sum(data['v'] for data in self.data_buffer) / len(self.data_buffer)

        formatted_data = {
            "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # KST 변환 후 저장
            "open": float(open_price),
            "high": float(high_price),
            "low": float(low_price),
            "close": float(close_price),
            "volume": float(avg_volume),
            "close_time": close_time.strftime('%Y-%m-%d %H:%M:%S')  # KST 변환 후 저장
        }

        self.save_to_json(formatted_data)
        print(f"5초 데이터 저장됨: {json.dumps(formatted_data, indent=4)}")

        # 버퍼 초기화
        self.data_buffer = []

    def on_message(self, ws, message):
        """ 메시지가 도착하면 호출되는 콜백 함수 """
        data = json.loads(message)  # JSON 형식으로 메시지를 파싱
        kline = data['k']  # kline(캔들) 데이터 추출

        # 받은 데이터를 버퍼에 저장
        self.data_buffer.append({
            "t": kline['t'],  # timestamp
            "T": kline['T'],  # close timestamp
            "o": float(kline['o']),  # open
            "h": float(kline['h']),  # high
            "l": float(kline['l']),  # low
            "c": float(kline['c']),  # close
            "v": float(kline['v'])   # volume
        })

        # 5초마다 데이터를 처리
        if len(self.data_buffer) >= 5:  # 5개의 데이터가 모이면 처리
            self.process_data()

    def on_error(self, ws, error):
        """ 웹소켓 에러 발생 시 호출되는 콜백 함수 """
        print(f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """ 웹소켓 연결 종료 시 호출되는 콜백 함수 """
        print("웹소켓 연결 종료")

    def on_open(self, ws):
        """ 웹소켓 연결 성공 시 호출되는 콜백 함수 """
        print("웹소켓 연결 성공")

    def run_websocket(self):
        """ 웹소켓 연결 및 데이터 수신 """
        websocket.enableTrace(True)  # 디버깅을 위해 트레이스 출력
        ws = websocket.WebSocketApp(self.stream_url, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        ws.on_open = self.on_open  # 연결이 열렸을 때 실행될 함수 설정
        ws.run_forever()  # 웹소켓 연결을 계속 유지

    def start(self):
        """ 웹소켓을 백그라운드에서 실행 """
        self.run_websocket()


if __name__ == "__main__":
    # 웹소켓 클라이언트 실행
    ws_client = BinanceWebSocket()
    ws_client.start()
