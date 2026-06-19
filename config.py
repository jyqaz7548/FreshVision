# -*- coding: utf-8 -*-
"""
Fresh Vision - 핀맵 및 설정 상수
"""

# ===== 초음파 센서 (HC-SR04) =====
TRIG_PIN = 23   # 물리 16번
ECHO_PIN = 24   # 물리 18번 (전압분배 회로 거쳐서 연결)

# 거리 기준값 (cm)
DETECT_DISTANCE = 8     # 카메라 촬영 위치 (이 거리 이하면 정지)
PASS_DISTANCE = 1       # 분류 완료 위치 (서보모터 동작 위치)
DISTANCE_TOLERANCE = 0.5  # 거리 판정 허용 오차

# ===== DC 모터 (L298N) =====
IN1_PIN = 5     # 물리 29번
IN2_PIN = 6     # 물리 31번
ENA_PIN = 13    # 물리 33번 (PWM)

MOTOR_SPEED = 50  # DC모터 속도 (0~100)

# ===== 서보모터 (SG90) =====
SERVO_PIN = 18  # 물리 12번 (하드웨어 PWM)

SERVO_NORMAL_ANGLE = 0    # 정상 과일 방향 각도
SERVO_BAD_ANGLE = 90      # 불량 과일 방향 각도
SERVO_NEUTRAL_ANGLE = 45  # 대기 각도

# ===== LED =====
LED_GREEN_PIN = 25  # 물리 22번 - 정상(초록)
LED_RED_PIN = 26    # 물리 37번 - 불량(빨강)

# ===== AI 모델 =====
MODEL_PATH = "model.tflite"
LABELS_PATH = "labels.txt"

# Teachable Machine 모델 입력 크기 (보통 224x224)
MODEL_INPUT_SIZE = (224, 224)

# 판별 임계값 (정상 확률이 이 값 이상이면 정상으로 판정)
NORMAL_THRESHOLD = 0.7

# ===== 카메라 =====
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# 카메라 색상이 반전되어 보이면(R↔B 뒤바뀜) True로 변경
SWAP_RB = True

# ===== 타이밍 =====
SENSOR_CHECK_INTERVAL = 0.1  # 초음파센서 측정 주기 (초)
LED_DISPLAY_TIME = 3.0       # 판별 결과 LED 표시 시간 (초)