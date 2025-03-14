import json
import time
from binance.client import Client
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 바이낸스 API 키 설정
BINANCE_API_KEY = os.getenv("BIN_API_KEY")
BINANCE_API_SECRET = os.getenv("BIN_SEC_KEY")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)



def open_Position():
    # 현재 잔고 가져오기
    balance = float([x for x in client.futures_account_balance() if x['asset'] == 'USDT'][0]['balance'])
    
    # 사용할 금액 = 잔고의 90%
    amount_to_use = balance * 0.9
    
    # 현재 가격 가져오기
    current_price = float(client.futures_symbol_ticker(symbol='BTCUSDT')['price'])
    
    # 수량 계산 (소수점 3자리로 반올림 → 최소 거래 단위 맞춤)
    quantity = round(amount_to_use / current_price, 3)

    # 레버리지
    leverage = 25
    client.futures_change_leverage(symbol='BTCUSDT', leverage=leverage)

    #파이널시그널 얻어오기
    final_signal = get_final_signal()

    if final_signal == "LONG":
        order = client.futures_create_order(
            symbol='BTCUSDT',
            side='BUY',
            type='MARKET',
            quantity=quantity
        )
        print(f"✅ LONG 진입: {quantity} BTC at {current_price} USDT")
        return order
    
    elif final_signal == "SHORT":
        order = client.futures_create_order(
            symbol='BTCUSDT',
            side='SELL',
            type='MARKET',
            quantity=quantity
        )
        print(f"✅ Short 진입: {quantity} BTC at {current_price} USDT")
        return order
     
    else:
        print(f"🟡 HOLD 상태 유지")



def close_Position():
    return


def get_unrealized_profit():
    # 현재 포지션 정보 가져오기
    positions = client.futures_position_information()
    
    # BTCUSDT 포지션 찾기
    btc_position = next((pos for pos in positions if pos['symbol'] == 'BTCUSDT'), None)

    if btc_position:
        # 포지션의 미실현 손익
        unrealized_profit = float(btc_position['unrealizedProfit'])
        
        # 현재 포지션 수량
        position_size = float(btc_position['positionAmt'])
        
        if position_size != 0:
            # 손실률 계산: 손익 / 포지션 진입 가치
            entry_price = float(btc_position['entryPrice'])
            current_price = float(client.futures_symbol_ticker(symbol='BTCUSDT')['price'])
            entry_value = entry_price * position_size

            # 손실률 계산
            loss_rate = (unrealized_profit / entry_value) * 100  # %로 계산
            print(f"현재 손실률: {loss_rate:.2f}%")
            return loss_rate
        else:
            print("포지션 없음")
            return 0
    else:
        print("BTCUSDT 포지션 없음")
        return 0






# 📌 파일 로드 함수
def load_data():
    with open("Technical_indicators.json", 'r') as file:
        data = json.load(file)
    return data

# 📌 실시간 가격 로드 함수 (가장 최신 값 사용)
def get_realtime_price(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    latest_price = data[-1]['close']  # 가장 최신 값 사용
    prev_price = data[-2]['close']  # 두 번째 최신 값 사용
    return latest_price, prev_price

# 📌 전략 1 로직
def strategy_1(data, current_price):
    rsi = data['rsi'][0]
    sma = data['sma'][0]

    signal = None

    if (rsi <= 40)  and (current_price > sma) :
        signal = "long"
        
    elif (rsi >= 60)  and (current_price < sma) :
        signal = "short"
    else:
        signal = "hold"

    print(f"[STRATEGY 1] RSI: {rsi}, SMA: {sma}, Current Price: {current_price}")
    print(f"전략1: {signal}")

    return signal
    

# 📌 전략 2 로직
def strategy_2(data, current_price, prev_price):
    
    vwap = data['vwap'][0]
    bb_upper = data['bb_upper'][0]
    bb_lower = data['bb_lower'][0]

    signal = None
    
    if (current_price > vwap) and (prev_price <= bb_lower and current_price > prev_price) :
        signal = "long"
    elif (current_price < vwap) and (prev_price >= bb_upper and current_price < prev_price):
        signal = "short"
    else:
        signal = "hold"

    print(f"[STRATEGY 2] vwap: {vwap}, bb_upper: {bb_upper}, bb_lower: {bb_lower}, current_price = {current_price}, prev_price = {prev_price}")
    print(f"전략2: {signal}")

    return signal

# 📌 최종 신호 판단
def get_final_signal():

    data = load_data()
    # 실시간 가격 가져오기
    current_price, prev_price = get_realtime_price("1min_BTC_OHLCV.json")

    # 전략 1과 전략 2에서 각각 신호를 받아옴
    signal_1 = strategy_1(data, current_price)
    signal_2 = strategy_2(data, current_price, prev_price)

    # 매매 신호 결정
    if (signal_1 == "long" and (signal_2 == "long" or "hold")) or ((signal_1 == "long" or "hold") and signal_2 == "long"):
        final_signal = "LONG"
    elif (signal_1 == "short" and (signal_2 == "short" or "hold")) or ((signal_1 == "short" or "hold") and signal_2 == "short"):
        final_signal = "SHORT"
    else:
        final_signal = "HOLD"

    return final_signal


# ✅ 테스트 실행 코드
if __name__ == "__main__":
    while True:
        final_signal = get_final_signal()
        print(f"최종 매매 신호: {final_signal}")
        time.sleep(10)

