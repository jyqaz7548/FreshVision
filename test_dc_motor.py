# -*- coding: utf-8 -*-
"""
ENA(GPIO13) - DC모터 단독 테스트 스크립트

점퍼 캡 제거 후 배선이 제대로 됐는지 확인용.
실행하면 모터가 5초간 50% 속도로 돌고 정지합니다.
"""

import RPi.GPIO as GPIO
import time

IN1_PIN = 5    # 물리 29번
IN2_PIN = 6    # 물리 31번
ENA_PIN = 13   # 물리 33번

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(IN1_PIN, GPIO.OUT)
GPIO.setup(IN2_PIN, GPIO.OUT)
GPIO.setup(ENA_PIN, GPIO.OUT)

pwm = GPIO.PWM(ENA_PIN, 1000)
pwm.start(0)

try:
    print("모터 정방향 50% 속도로 5초간 구동")
    GPIO.output(IN1_PIN, GPIO.HIGH)
    GPIO.output(IN2_PIN, GPIO.LOW)
    pwm.ChangeDutyCycle(50)
    time.sleep(5)

    print("모터 정지")
    pwm.ChangeDutyCycle(0)
    GPIO.output(IN1_PIN, GPIO.LOW)
    GPIO.output(IN2_PIN, GPIO.LOW)
    time.sleep(2)

    print("모터 정방향 100% 속도로 3초간 구동")
    GPIO.output(IN1_PIN, GPIO.HIGH)
    GPIO.output(IN2_PIN, GPIO.LOW)
    pwm.ChangeDutyCycle(100)
    time.sleep(3)

    print("최종 정지")
    pwm.ChangeDutyCycle(0)
    GPIO.output(IN1_PIN, GPIO.LOW)
    GPIO.output(IN2_PIN, GPIO.LOW)

finally:
    pwm.stop()
    GPIO.cleanup()
    print("테스트 종료")
