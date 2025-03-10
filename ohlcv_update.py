import websocket
import json
from datetime import datetime, timezone, timedelta
import threading

class BinanceWebSocket_ohlcv:
    def __init__(self, symbol="btcusdt", data_file="1min_BTC_OHLCV.json"):
        self.symbol = symbol
        self.data_file = data_file
        self.stream_url = f"wss://fstream.binance.com/ws/{self.symbol}@trade"
        self.ws = None
        self.data_buffer = []  # 데이터를 임시로 저장할 버퍼
        self.lock = threading.Lock()

        # 캔들봉 버퍼, 각 1분 캔들봉을 저장
        self.candle_buffer = []
        self.last_candle_time = None

        # 1초마다 데이터 저장 타이머 설정
        self.timer = threading.Timer(1, self.process_data)
        self.timer.start()

    def save_to_json(self, new_data):
        """ JSON 파일에 데이터를 저장하는 함수 """
        try:
            with open(self.data_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        # 새로운 1분 캔들봉 데이터를 data에 추가
        data.append(new_data)

        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def process_data(self):
        """ 1초마다 데이터를 처리하여 저장 """
        with self.lock:
            if not self.data_buffer:
                return
            
            # 현재 시간을 기준으로 1분 캔들봉을 생성
            current_time = datetime.now(timezone.utc)  # UTC 시간 사용
            current_minute = current_time.replace(second=0, microsecond=0)

            if self.last_candle_time and self.last_candle_time != current_minute:
                # 새 1분이 시작되었으므로 이전 1분 캔들봉을 저장
                if self.candle_buffer:
                    ohlcv = self.create_candle(self.candle_buffer)
                    print(f"1분 캔들봉: {ohlcv}")
                    self.save_to_json(ohlcv)
                
                # 버퍼 초기화
                self.candle_buffer = []
                
            self.last_candle_time = current_minute

        # 1초마다 반복 실행
        self.timer = threading.Timer(1, self.process_data)
        self.timer.start()

    def create_candle(self, trade_data):
        """ 거래 데이터를 바탕으로 1분 캔들봉 생성 """
    
        # price가 0보다 큰 데이터만 필터링
        filtered_trade_data = [data for data in trade_data if data['price'] > 0]

        # 필터링된 데이터가 없으면 빈 캔들 반환
        if not filtered_trade_data:
            return None

        # 첫 번째 거래 데이터를 오픈 시간으로 설정
        open_price = filtered_trade_data[0]['price']
        close_price = filtered_trade_data[-1]['price']
        high_price = max(data['price'] for data in filtered_trade_data)
        low_price = min(data['price'] for data in filtered_trade_data)
        volume = sum(data['quantity'] for data in filtered_trade_data)

        # 첫 번째 거래의 timestamp를 캔들봉의 오픈 시간으로 설정
        timestamp = filtered_trade_data[0]['timestamp']
        formatted_timestamp = datetime.utcfromtimestamp(timestamp / 1000) + timedelta(hours=9)
        formatted_timestamp = formatted_timestamp.strftime('%Y-%m-%d %H:%M:%S')

        formatted_data = {
            "timestamp": formatted_timestamp,
            "open": float(open_price),
            "high": float(high_price),
            "low": float(low_price),
            "close": float(close_price),
            "volume": float(volume)
        }

        return formatted_data

    def on_message(self, ws, message):
        """ 메시지가 도착하면 호출되는 콜백 함수 """
        data = json.loads(message)  # JSON 형식으로 메시지를 파싱
        
        with self.lock:
            # 가격 (p) 값 저장
            trade_data = {
                "timestamp": data['T'],  # 거래 타임스탬프
                "price": float(data['p']),  # 거래 가격
                "quantity": float(data['q'])  # 거래 수량
            }
            self.data_buffer.append(trade_data)
            self.candle_buffer.append(trade_data)

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
