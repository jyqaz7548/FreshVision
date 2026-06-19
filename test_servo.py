# -*- coding: utf-8 -*-
"""
서보모터(SG90) 단독 테스트 스크립트

PWM(GPIO18, 물리 12번)으로 서보모터를 여러 각도로 움직입니다.
정상 분류 위치(0도), 대기 위치(45도), 불량 분류 위치(90도)를 순서대로 이동.

실행: python3 test_servo.py
종료: Ctrl + C
"""

import RPi.GPIO as GPIO
import time

# config.py와 동일한 핀/각도
SERVO_PIN = 18  # 물리 12번
SERVO_NORMAL_ANGLE = 0
SERVO_NEUTRAL_ANGLE = 45
SERVO_BAD_ANGLE = 90

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz
pwm.start(0)


def set_angle(angle):
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)  # 떨림 방지


try:
    print("서보모터 테스트 시작 (Ctrl+C로 종료)")
    while True:
        print("대기 위치 (45도)")
        set_angle(SERVO_NEUTRAL_ANGLE)
        time.sleep(1)

        print("정상 분류 위치 (0도)")
        set_angle(SERVO_NORMAL_ANGLE)
        time.sleep(1)

        print("대기 위치 (45도)")
        set_angle(SERVO_NEUTRAL_ANGLE)
        time.sleep(1)

        print("불량 분류 위치 (90도)")
        set_angle(SERVO_BAD_ANGLE)
        time.sleep(1)

except KeyboardInterrupt:
    print("\n테스트 종료")

finally:
    pwm.stop()
    GPIO.cleanup()
