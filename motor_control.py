# -*- coding: utf-8 -*-
"""
Fresh Vision - 모터(DC, 서보) 및 LED 제어 모듈
"""

import RPi.GPIO as GPIO
import time
from config import (
    IN1_PIN, IN2_PIN, ENA_PIN,
    SERVO_PIN,
    LED_GREEN_PIN, LED_RED_PIN,
    MOTOR_SPEED,
    SERVO_NORMAL_ANGLE, SERVO_BAD_ANGLE, SERVO_NEUTRAL_ANGLE,
)


class DCMotor:
    """L298N을 통한 DC모터(컨베이어벨트) 제어"""

    def __init__(self):
        GPIO.setup(IN1_PIN, GPIO.OUT)
        GPIO.setup(IN2_PIN, GPIO.OUT)
        GPIO.setup(ENA_PIN, GPIO.OUT)

        self.pwm = GPIO.PWM(ENA_PIN, 1000)  # 1kHz PWM
        self.pwm.start(0)
        self.is_running = False

        # 정지 상태로 초기화
        GPIO.output(IN1_PIN, GPIO.LOW)
        GPIO.output(IN2_PIN, GPIO.LOW)

    def stop(self):
        """모터 정지 (브레이크 모드: IN1=IN2=HIGH로 모터를 꽉 잡아 미세 움직임 방지)"""
        GPIO.output(IN1_PIN, GPIO.HIGH)
        GPIO.output(IN2_PIN, GPIO.HIGH)
        self.pwm.ChangeDutyCycle(0)
        self.is_running = False

    def forward(self, speed=MOTOR_SPEED):
        """컨베이어벨트를 정방향으로 구동"""
        GPIO.output(IN1_PIN, GPIO.HIGH)
        GPIO.output(IN2_PIN, GPIO.LOW)
        self.pwm.ChangeDutyCycle(speed)
        self.is_running = True

    def cleanup(self):
        self.stop()
        self.pwm.stop()


class ServoMotor:
    """서보모터(SG90)를 이용한 분류 게이트 제어"""

    def __init__(self):
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        self.pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz (서보모터 표준)
        self.pwm.start(0)
        self.set_angle(SERVO_NEUTRAL_ANGLE)

    def set_angle(self, angle):
        """0~180도 각도로 서보모터 이동"""
        duty = 2 + (angle / 18)
        self.pwm.ChangeDutyCycle(duty)
        time.sleep(0.4)  # 모터가 움직일 시간 확보
        self.pwm.ChangeDutyCycle(0)  # 떨림(jitter) 방지

    def sort_normal(self):
        """정상 과일 방향으로 게이트 이동"""
        self.set_angle(SERVO_NORMAL_ANGLE)

    def sort_bad(self):
        """불량 과일 방향으로 게이트 이동"""
        self.set_angle(SERVO_BAD_ANGLE)

    def reset(self):
        """대기 위치로 복귀"""
        self.set_angle(SERVO_NEUTRAL_ANGLE)

    def cleanup(self):
        self.pwm.stop()


class LEDIndicator:
    """정상(초록) / 불량(빨강) LED 제어"""

    def __init__(self):
        GPIO.setup(LED_GREEN_PIN, GPIO.OUT)
        GPIO.setup(LED_RED_PIN, GPIO.OUT)
        self.all_off()

    def show_normal(self):
        """정상 판정 - 초록 LED ON"""
        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)
        GPIO.output(LED_RED_PIN, GPIO.LOW)

    def show_bad(self):
        """불량 판정 - 빨강 LED ON"""
        GPIO.output(LED_GREEN_PIN, GPIO.LOW)
        GPIO.output(LED_RED_PIN, GPIO.HIGH)

    def all_off(self):
        """모든 LED 끄기"""
        GPIO.output(LED_GREEN_PIN, GPIO.LOW)
        GPIO.output(LED_RED_PIN, GPIO.LOW)