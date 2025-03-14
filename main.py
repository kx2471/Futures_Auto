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
    
    # 레버리지
    leverage = 25
    client.futures_change_leverage(symbol='BTCUSDT', leverage=leverage)

    # 레버리지를 적용한 금액으로 수량 계산 (소수점 3자리로 반올림 → 최소 거래 단위 맞춤)
    quantity = round(amount_to_use * leverage / current_price, 3)

    # 명목 가치 계산 (레버리지 적용)
    notional_value = current_price * quantity * leverage
    
    # 명목 가치가 100 USDT 미만이면 최소 100 USDT에 해당하는 수량으로 변경
    if notional_value < 100:
        # 최소 명목 가치를 100 USDT로 설정하여 수량 조정
        quantity = round(100 / (current_price * leverage), 3)
        print(f"수량이 너무 적어서 명목 가치를 100 USDT 이상으로 맞췄습니다. 새로운 수량: {quantity} BTC")

    
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



def close_position():
    try:
        # 현재 포지션 정보 가져오기
        positions = client.futures_position_information(symbol='BTCUSDT')
        
        # BTCUSDT 포지션 찾기
        btc_position = next((pos for pos in positions if pos['symbol'] == 'BTCUSDT'), None)

        if btc_position:
            # 포지션의 미실현 손익
            unrealized_profit = float(btc_position['unRealizedProfit'])
            
            # 현재 포지션 수량
            position_size = float(btc_position['positionAmt'])
            
            # 레버리지 정보 가져오기
            leverage = 25

            if position_size != 0:
                # 포지션 진입 가격
                entry_price = float(btc_position['entryPrice'])
                
                # 현재 가격 가져오기
                current_price = float(client.futures_symbol_ticker(symbol='BTCUSDT')['price'])
                
                # 레버리지 적용 후 실제 투자 금액
                entry_value = entry_price * position_size / leverage
                
                # 손익 비율 계산: (미실현 손익 / 실제 투자 금액) * 100
                if entry_value == 0:
                    print("⚠️ 진입 가격이 0입니다. 손익 비율 계산을 할 수 없습니다.")
                    return
                
                if position_size > 0:  # LONG 포지션
                    profit_rate = (unrealized_profit / entry_value) * 100
                else:  # SHORT 포지션
                    profit_rate = (-unrealized_profit / entry_value) * 100  # SHORT은 반대로 계산
                
                print(f"현재 손익: {unrealized_profit} USDT, 손익 비율: {profit_rate:.2f}%")
                
                # +5% 이상 또는 -2.5% 이하일 경우 포지션 클로즈
                if profit_rate >= 5:
                    print("📈 손익 +5% 이상: 포지션을 클로즈합니다.")
                    # 포지션 클로즈 (매도)
                    order = client.futures_create_order(
                        symbol='BTCUSDT',
                        side='SELL' if position_size > 0 else 'BUY',  # LONG이면 'SELL', SHORT이면 'BUY'
                        type='MARKET',
                        quantity=abs(position_size)
                    )
                    print(f"✅ 포지션 클로즈: {abs(position_size)} BTC")
                    return order
                elif profit_rate <= -2.5:
                    print("📉 손익 -2.5% 이하: 포지션을 클로즈합니다.")
                    # 포지션 클로즈 (매도)
                    order = client.futures_create_order(
                        symbol='BTCUSDT',
                        side='SELL' if position_size > 0 else 'BUY',  # LONG이면 'SELL', SHORT이면 'BUY'
                        type='MARKET',
                        quantity=abs(position_size)
                    )
                    print(f"✅ 포지션 클로즈: {abs(position_size)} BTC")
                    return order
                else:
                    print("🟡 손익 비율이 클로즈 조건을 만족하지 않습니다. 포지션을 유지합니다.")
            else:
                print("포지션이 없습니다.")
        else:
            print("BTCUSDT 포지션 없음")

    except Exception as e:
        print(f"⚠️ 오류 발생: {e}")









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


def check_and_execute():
    while True:
        try:
            # 현재 포지션 정보 가져오기
            positions = client.futures_position_information(symbol='BTCUSDT')
            btc_position = next((pos for pos in positions if pos['symbol'] == 'BTCUSDT'), None)
            
            
            # 포지션이 없으면 open_Position 호출
            if btc_position is None or float(btc_position['positionAmt']) == 0:
                print("포지션 없음, open_Position 실행 중...")
                open_Position()

                # 포지션이 있으면 close_Position 호출
            else:
                print("포지션 있음, close_Position 실행 중...")
                close_position()

                # 10초마다 확인
            time.sleep(10)

        except Exception as e:
            print(f"⚠️ 오류 발생: {e}")
            time.sleep(10)  # 오류 발생 시 10초 후 재시도

# ✅ 테스트 실행 코드
if __name__ == "__main__":
    check_and_execute()

