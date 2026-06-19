# -*- coding: utf-8 -*-
"""
LED 단독 테스트 스크립트

초록 LED(GPIO25, 물리 22번), 빨강 LED(GPIO26, 물리 37번)를
번갈아 켜고 끄면서 배선을 확인합니다.

실행: python3 test_led.py
종료: Ctrl + C
"""

import RPi.GPIO as GPIO
import time

# config.py와 동일한 핀
LED_GREEN_PIN = 25  # 물리 22번
LED_RED_PIN = 26    # 물리 37번

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(LED_GREEN_PIN, GPIO.OUT)
GPIO.setup(LED_RED_PIN, GPIO.OUT)

try:
    print("LED 테스트 시작 (Ctrl+C로 종료)")
    while True:
        print("초록 LED ON")
        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)
        GPIO.output(LED_RED_PIN, GPIO.LOW)
        time.sleep(1)

        print("빨강 LED ON")
        GPIO.output(LED_GREEN_PIN, GPIO.LOW)
        GPIO.output(LED_RED_PIN, GPIO.HIGH)
        time.sleep(1)

        print("둘 다 ON")
        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)
        GPIO.output(LED_RED_PIN, GPIO.HIGH)
        time.sleep(1)

        print("둘 다 OFF")
        GPIO.output(LED_GREEN_PIN, GPIO.LOW)
        GPIO.output(LED_RED_PIN, GPIO.LOW)
        time.sleep(1)

except KeyboardInterrupt:
    print("\n테스트 종료")

finally:
    GPIO.output(LED_GREEN_PIN, GPIO.LOW)
    GPIO.output(LED_RED_PIN, GPIO.LOW)
    GPIO.cleanup()
