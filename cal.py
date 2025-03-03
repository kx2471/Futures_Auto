from datetime import datetime, timezone, timedelta

# 사용자 입력 받기
timestamp_ms = int(input("타임스탬프 (ms 단위) 입력: "))

# UTC 시간 변환
utc_time = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
print(f"UTC 시간: {utc_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 한국 시간 (UTC+9) 변환
kst_time = utc_time + timedelta(hours=9)
print(f"KST 시간: {kst_time.strftime('%Y-%m-%d %H:%M:%S')}")