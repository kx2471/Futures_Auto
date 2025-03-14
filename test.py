from binance.client import Client
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 바이낸스 API 키 설정
BINANCE_API_KEY = os.getenv("BIN_API_KEY")
BINANCE_API_SECRET = os.getenv("BIN_SEC_KEY")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

def get_futures_account_info():
    try:
        account_info = client.futures_account()
        print("\n=== 📊 선물 계좌 정보 ===")
        print(f"총 자산: {account_info['totalWalletBalance']} USDT")
        print(f"미실현 손익: {account_info['totalUnrealizedProfit']} USDT")
        print(f"총 마진 잔고: {account_info['totalMarginBalance']} USDT\n")
        
        print("=== 📝 포지션 정보 ===")
        positions = account_info['positions']
        for position in positions:
            if float(position['positionAmt']) != 0:
                print(f"심볼: {position['symbol']}")
                print(f"포지션 크기: {position['positionAmt']}")
                print(f"엔트리 가격: {position['entryPrice']}")
                print(f"미실현 손익: {position['unrealizedProfit']}")
                print(f"레버리지: {position['leverage']}배")
                print("-" * 30)

    except Exception as e:
        print(f"⚠️ 오류 발생: {e}")



def open_Position(final_signal):
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


if __name__ == "__main__":
    get_futures_account_info()
    open_Position("SHORT")

    positions = client.futures_position_information()
        
        # BTCUSDT 포지션 찾기
    btc_position = next((pos for pos in positions if pos['symbol'] == 'BTCUSDT'), None)

    if btc_position:
        # 포지션의 모든 정보를 출력해 봄 (디버깅 용)
        print("포지션 정보:", btc_position)