# -*- coding: utf-8 -*-
"""
Fresh Vision - 초음파센서 (HC-SR04) 제어 모듈
"""

import RPi.GPIO as GPIO
import time
from config import TRIG_PIN, ECHO_PIN


class UltrasonicSensor:
    def __init__(self):
        GPIO.setup(TRIG_PIN, GPIO.OUT)
        GPIO.setup(ECHO_PIN, GPIO.IN)
        GPIO.output(TRIG_PIN, False)
        time.sleep(0.5)  # 센서 안정화 대기

    def get_distance(self, timeout=0.05):
        """
        거리를 cm 단위로 측정해서 반환.
        측정 실패(타임아웃) 시 None 반환.
        """
        # 트리거 신호 발생 (10us)
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

        # ECHO가 LOW로 떨어질 때까지 대기 (펄스 폭 측정)
        while GPIO.input(ECHO_PIN) == 1:
            pulse_end = time.time()
            if pulse_end - pulse_start > timeout:
                return None

        pulse_duration = pulse_end - pulse_start

        # 거리 계산 (음속 34300 cm/s, 왕복이므로 2로 나눔)
        distance = pulse_duration * 34300 / 2

        # 비정상적인 값 필터링 (HC-SR04 측정 범위: 2cm ~ 400cm)
        if distance < 2 or distance > 400:
            return None

        return round(distance, 1)

    def get_distance_filtered(self, samples=3):
        """
        여러 번 측정해서 평균값을 반환 (노이즈 감소용).
        """
        readings = []
        for _ in range(samples):
            d = self.get_distance()
            if d is not None:
                readings.append(d)
            time.sleep(0.01)

        if not readings:
            return None

        return round(sum(readings) / len(readings), 1)
