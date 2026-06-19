# -*- coding: utf-8 -*-
"""
초음파센서(HC-SR04) 단독 테스트 스크립트

TRIG(GPIO23, 물리 16번), ECHO(GPIO24, 물리 18번)로
거리를 측정해서 0.5초마다 출력합니다.

⚠️ ECHO 핀은 전압분배 회로(1kΩ, 2kΩ)를 거쳐 연결되어 있어야 합니다.

실행: python3 test_ultrasonic.py
종료: Ctrl + C
"""

import RPi.GPIO as GPIO
import time

# config.py와 동일한 핀
TRIG_PIN = 23   # 물리 16번
ECHO_PIN = 24   # 물리 18번

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.output(TRIG_PIN, False)

print("센서 안정화 대기 중...")
time.sleep(2)


def get_distance(timeout=0.05):
    """거리를 cm 단위로 측정. 실패 시 None."""
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    start_time = time.time()
    pulse_start = start_time

    # ECHO가 HIGH로 올라갈 때까지 대기
    while GPIO.input(ECHO_PIN) == 0:
        pulse_start = time.time()
        if pulse_start - start_time > timeout:
            return None

    pulse_end = pulse_start

    # ECHO가 LOW로 떨어질 때까지 대기
    while GPIO.input(ECHO_PIN) == 1:
        pulse_end = time.time()
        if pulse_end - pulse_start > timeout:
            return None

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 34300 / 2

    if distance < 2 or distance > 400:
        return None

    return round(distance, 1)


try:
    print("초음파센서 테스트 시작 (Ctrl+C로 종료)")
    while True:
        d = get_distance()
        if d is not None:
            print(f"거리: {d} cm")
        else:
            print("측정 실패 (범위 밖이거나 배선 확인 필요)")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n테스트 종료")

finally:
    GPIO.cleanup()
