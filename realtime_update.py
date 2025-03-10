import websocket
import json
from datetime import datetime, timezone, timedelta
import threading

class BinanceWebSocket_realtimePrice:
    def __init__(self, symbol="btcusdt", data_file="BTC_realtime_data.json"):
        self.symbol = symbol
        self.data_file = data_file
        self.stream_url = f"wss://fstream.binance.com/ws/{self.symbol}@trade"
        self.ws = None
        self.data_buffer = []  # 데이터를 임시로 저장할 버퍼
        self.lock = threading.Lock()

        # 5초마다 데이터 저장 타이머 설정
        self.timer = threading.Timer(5, self.process_data)
        self.timer.start()

    def save_to_json(self, new_data):
        """ JSON 파일에 데이터를 저장하는 함수 """
        try:
            with open(self.data_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        # 현재 시간 (KST)
        current_time = datetime.now(timezone(timedelta(hours=9)))  # KST 시간대로 설정

        # 3일 이전 데이터 필터링
        data = [entry for entry in data if datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone(timedelta(hours=9))) > current_time - timedelta(days=3)]

        data.append(new_data)

        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)


    def process_data(self):
        """ 5초마다 데이터를 처리하여 저장 """
        with self.lock:
            if not self.data_buffer:
                return
            
            first_data = self.data_buffer[0]

            # KST 기준 타임스탬프 설정
            timestamp = datetime.fromtimestamp(first_data['timestamp'] / 1000, tz=timezone.utc) + timedelta(hours=9)

            price = first_data['price']

            formatted_data = {
                "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "price": float(price)
            }

            self.save_to_json(formatted_data)
            print(f"1초 데이터 저장됨: {json.dumps(formatted_data, indent=4)}")

            # 버퍼 초기화
            self.data_buffer = []

        # 다시 타이머 설정 (반복 호출)
        self.timer = threading.Timer(1, self.process_data)
        self.timer.start()

    def on_message(self, ws, message):
        """ 메시지가 도착하면 호출되는 콜백 함수 """
        data = json.loads(message)  # JSON 형식으로 메시지를 파싱
        
        with self.lock:
            self.data_buffer.append({
                "timestamp": data['T'],  # trade 타임스탬프
                "price": float(data['p']),  # 거래 가격
                "quantity": float(data['q'])  # 거래 수량
            })

    def on_error(self, ws, error):
        """ 웹소켓 에러 발생 시 호출되는 콜백 함수 """
        print(f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """ 웹소켓 연결 종료 시 호출되는 콜백 함수 """
        print("웹소켓 연결 종료")
        # 타이머 종료
        self.timer.cancel()

    def on_open(self, ws):
        """ 웹소켓 연결 성공 시 호출되는 콜백 함수 """
        print("웹소켓 연결 성공")

    def run_websocket(self):
        """ 웹소켓 연결 및 데이터 수신 """
        websocket.enableTrace(False)  # 디버깅 비활성화 가능
        self.ws = websocket.WebSocketApp(
            self.stream_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open
        self.ws.run_forever()

    def start(self):
        """ 웹소켓을 백그라운드에서 실행 """
        threading.Thread(target=self.run_websocket).start()
