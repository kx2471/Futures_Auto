import websocket
import json
from datetime import datetime, timezone, timedelta
import threading
import time

class BinanceWebSocket_realtimePrice:
    def __init__(self, symbol="btcusdt", data_file="BTC_realtime_data.json"):
        self.symbol = symbol
        self.data_file = data_file
        self.stream_url = f"wss://fstream.binance.com/ws/{self.symbol}@trade"
        self.ws = None
        self.data_buffer = []
        self.lock = threading.Lock()

        # 타이머 설정
        self.timer = threading.Timer(5, self.process_data)
        self.timer.start()

    def save_to_json(self, new_data):
        try:
            with open(self.data_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        # 현재 시간 (KST)
        current_time = datetime.now(timezone(timedelta(hours=9)))

        # 3일 이전 데이터 삭제
        data = [entry for entry in data if datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone(timedelta(hours=9))) > current_time - timedelta(days=3)]

        # 새 데이터를 추가
        data.append(new_data)

        # 데이터가 100개를 초과하면 오래된 데이터를 삭제
        if len(data) > 100:
            data = data[-100:]  # 가장 최근 100개의 데이터만 유지

        # 파일에 저장
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def process_data(self):
        with self.lock:
            if not self.data_buffer:
                print("데이터 버퍼가 비어 있습니다.")
                return

            first_data = self.data_buffer[0]
            timestamp = datetime.fromtimestamp(first_data['timestamp'] / 1000, tz=timezone.utc) + timedelta(hours=9)
            price = first_data['price']

            formatted_data = {
                "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "price": float(price)
            }

            self.save_to_json(formatted_data)
            print(f"1초 데이터 저장됨: {json.dumps(formatted_data, indent=4)}")

            self.data_buffer = []

        # 타이머 반복 실행 (1초마다 실행)
        self.timer = threading.Timer(1, self.process_data)
        self.timer.start()

    def on_message(self, ws, message):
        #print(f"메시지 수신됨: {message[:100]}...")  # 수신된 메시지 일부 로그 출력
        data = json.loads(message)
        with self.lock:
            self.data_buffer.append({
                "timestamp": data['T'],
                "price": float(data['p']),
                "quantity": float(data['q'])
            })
        #print(f"현재 데이터 버퍼 상태: {len(self.data_buffer)}개의 항목")

    def on_error(self, ws, error):
        print(f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("웹소켓 연결 종료")
        # 기존 타이머 정리
        if self.timer:
            self.timer.cancel()

        # 일정 시간 후 재연결 시도
        print("5초 후 재연결 시도...")
        time.sleep(5)
        self.start()

    def on_open(self, ws):
        print("웹소켓 연결 성공")

    def run_websocket(self):
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            self.stream_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open
        try:
            self.ws.run_forever()
        except Exception as e:
            print(f"웹소켓 연결 오류: {e}")
            self.on_close(self.ws, None, None)  # 연결 종료 후 재연결 시도

    def start(self):
        # 웹소켓 백그라운드 실행
        thread = threading.Thread(target=self.run_websocket)
        thread.daemon = True
        thread.start()

# if __name__ == "__main__":
#     print("테스트 시작: 웹소켓 실시간 가격 수신 및 저장")

#     try:
#         realtime_price = BinanceWebSocket_realtimePrice(symbol="btcusdt", data_file="BTC_realtime_data.json")
#         realtime_price.start()

#         time.sleep(20)
#         print("테스트 종료: 20초 동안 데이터 수신 완료")

#     except Exception as e:
#         print(f"테스트 중 오류 발생: {e}")

#     finally:
#         if realtime_price.ws:
#             realtime_price.ws.close()
#             print("웹소켓 연결 종료 완료")
