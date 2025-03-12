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
    current_price, prev_price = get_realtime_price("BTC_realtime_data.json")

    # 전략 1과 전략 2에서 각각 신호를 받아옴
    signal_1 = strategy_1(data, current_price)
    signal_2 = strategy_2(data, current_price, prev_price)

    # 매매 신호 결정
    if signal_1 == "long" or signal_2 == "long":
        final_signal = "LONG"
    elif signal_1 == "short" or signal_2 == "short":
        final_signal = "SHORT"
    else:
        final_signal = "HOLD"

    return final_signal


# ✅ 테스트 실행 코드
if __name__ == "__main__":
    while True:
        final_signal = get_final_signal()
        print(f"최종 매매 신호: {final_signal}")
        time.sleep(30)

