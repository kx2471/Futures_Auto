import json
import time

# 📌 파일 로드 함수
def load_data():
    with open("Technical_indicators.json", 'r') as file:
        data = json.load(file)
    return data

# 📌 실시간 가격 로드 함수 (가장 최신 값 사용)
def get_realtime_price(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    latest_price = data[-1]['price']  # 가장 최신 값 사용
    prev_price = data[-2]['price']  # 두 번째 최신 값 사용
    return latest_price, prev_price

# 📌 전략 1 로직
def strategy_1(data, current_price):
    rsi = data['rsi'][0]
    sma = data['sma'][0]

    signal = None

    if (rsi <= 40)  and (current_price > sma) :
        signal = "long"
        
    if (rsi >= 60)  and (current_price < sma) :
        signal = "short"

    return signal
    

# 📌 전략 2 로직
def strategy_2(data, current_price, prev_price):
    
    vwap = data['vwap'][0]
    bb_upper = data['bb_upper'][0]
    bb_lower = data['bb_lower'][0]

    signal = None
    
    if (current_price > vwap) and (prev_price <= bb_lower and current_price > prev_price) :
        signal = "long"
    if (current_price < vwap) and (prev_price >= bb_upper and current_price < prev_price):
        signal = "short"

    return signal

# 📌 최종 신호 판단
def get_final_signal(data):

    data = load_data()
    # 실시간 가격 가져오기
    current_price, prev_price = get_realtime_price("BTC_realtime_data.json")

    # 전략 1과 전략 2에서 각각 신호를 받아옴
    signal_1 = strategy_1(data, current_price)
    signal_2 = strategy_2(data, current_price, prev_price)

    # 매매 신호 결정
    if signal_1 == "long" and signal_2 == "long":
        final_signal = "BUY"
    elif signal_1 == "short" and signal_2 == "short":
        final_signal = "SELL"
    else:
        final_signal = "HOLD"

    return final_signal


