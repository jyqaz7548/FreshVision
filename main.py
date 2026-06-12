# -*- coding: utf-8 -*-
"""
Fresh Vision - 메인 실행 파일 (Tkinter GUI + 상태 머신)

상태 흐름:
  WAITING (대기/이동)
    -> 초음파센서 거리 <= DETECT_DISTANCE 이면 DC모터 정지 -> CLASSIFYING
  CLASSIFYING (카메라 촬영 + AI 판별)
    -> 판별 완료 -> LED 표시 -> SORTING
  SORTING (DC모터를 PASS_DISTANCE까지 구동 후 서보모터로 분류)
    -> 분류 완료 -> WAITING (다시 DC모터 구동)
"""

import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import RPi.GPIO as GPIO
import threading
import time

from config import (
    DETECT_DISTANCE, PASS_DISTANCE, DISTANCE_TOLERANCE,
    SENSOR_CHECK_INTERVAL, LED_DISPLAY_TIME,
    CAMERA_WIDTH, CAMERA_HEIGHT,
)
from sensor import UltrasonicSensor
from motor_control import DCMotor, ServoMotor, LEDIndicator
from classifier import FruitClassifier
from camera import RPiCamera


# 상태 정의
STATE_WAITING = "WAITING"
STATE_CLASSIFYING = "CLASSIFYING"
STATE_SORTING = "SORTING"


class FreshVisionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fresh Vision - 과일 신선도 판별기")
        self.root.geometry("800x650")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # ===== GPIO 초기화 =====
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.sensor = UltrasonicSensor()
        self.dc_motor = DCMotor()
        self.servo = ServoMotor()
        self.led = LEDIndicator()

        # ===== AI 모델 로드 =====
        self.classifier = FruitClassifier()

        # ===== 카메라 초기화 (RPi Camera Module) =====
        self.camera = RPiCamera()

        # ===== 상태 변수 =====
        self.state = STATE_WAITING
        self.current_frame = None
        self.running = True
        self.result_display_until = 0  # 결과 LED/텍스트 표시 종료 시각

        # ===== GUI 구성 =====
        self._build_gui()

        # ===== 메인 루프 시작 =====
        # 컨베이어벨트 최초 구동
        self.dc_motor.forward()
        self._update_camera()
        self._update_sensor_loop()

    # ------------------------------------------------------------------
    # GUI 구성
    # ------------------------------------------------------------------
    def _build_gui(self):
        # 좌측: 카메라 화면
        left_frame = tk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.camera_label = tk.Label(left_frame, bg="black",
                                       width=CAMERA_WIDTH, height=CAMERA_HEIGHT)
        self.camera_label.pack()

        # 우측: 상태 정보 패널
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_label = tk.Label(right_frame, text="Fresh Vision",
                                font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 20))

        # 과일 존재 여부
        self.fruit_present_label = tk.Label(
            right_frame, text="과일 감지: 없음",
            font=("Arial", 14), anchor="w")
        self.fruit_present_label.pack(fill=tk.X, pady=5)

        # 거리 표시
        self.distance_label = tk.Label(
            right_frame, text="거리: -- cm",
            font=("Arial", 14), anchor="w")
        self.distance_label.pack(fill=tk.X, pady=5)

        # DC모터 상태
        self.motor_label = tk.Label(
            right_frame, text="DC모터: 정지",
            font=("Arial", 14), anchor="w")
        self.motor_label.pack(fill=tk.X, pady=5)

        # 현재 상태(state machine)
        self.state_label = tk.Label(
            right_frame, text="상태: 대기 중",
            font=("Arial", 14), anchor="w")
        self.state_label.pack(fill=tk.X, pady=5)

        ttk.Separator(right_frame, orient="horizontal").pack(fill=tk.X, pady=15)

        # 판별 결과 표시 영역 (큰 텍스트 + 색상 배경)
        self.result_frame = tk.Frame(right_frame, bg="gray", height=150)
        self.result_frame.pack(fill=tk.X, pady=10)
        self.result_frame.pack_propagate(False)

        self.result_label = tk.Label(
            self.result_frame, text="판별 대기 중",
            font=("Arial", 24, "bold"), bg="gray", fg="white")
        self.result_label.pack(expand=True)

        # 확률 표시
        self.prob_label = tk.Label(
            right_frame, text="",
            font=("Arial", 12), anchor="w")
        self.prob_label.pack(fill=tk.X, pady=5)

    # ------------------------------------------------------------------
    # 카메라 화면 갱신 (항상 동작)
    # ------------------------------------------------------------------
    def _update_camera(self):
        if not self.running:
            return

        frame = self.camera.get_frame()
        if frame is not None:
            self.current_frame = frame.copy()

            # Tkinter에 표시할 이미지로 변환
            display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            display_frame = cv2.resize(display_frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
            img = Image.fromarray(display_frame)
            imgtk = ImageTk.PhotoImage(image=img)

            self.camera_label.imgtk = imgtk  # 참조 유지 (GC 방지)
            self.camera_label.configure(image=imgtk)

        # 약 30fps로 갱신
        self.root.after(33, self._update_camera)

    # ------------------------------------------------------------------
    # 센서/상태머신 루프 (별도 주기로 동작)
    # ------------------------------------------------------------------
    def _update_sensor_loop(self):
        if not self.running:
            return

        distance = self.sensor.get_distance_filtered()

        # ----- 거리 / 과일 감지 표시 갱신 -----
        if distance is not None:
            self.distance_label.config(text=f"거리: {distance} cm")
            # 일정 거리(예: 30cm) 이내면 "과일 있음"으로 표시
            if distance <= 30:
                self.fruit_present_label.config(text="과일 감지: 있음")
            else:
                self.fruit_present_label.config(text="과일 감지: 없음")
        else:
            self.distance_label.config(text="거리: -- cm")
            self.fruit_present_label.config(text="과일 감지: 없음")

        # ----- 상태머신 처리 -----
        if self.state == STATE_WAITING:
            self._handle_waiting(distance)

        elif self.state == STATE_CLASSIFYING:
            # 판별은 별도 스레드에서 처리 (GUI 멈춤 방지)
            pass  # _run_classification()이 알아서 상태 전환

        elif self.state == STATE_SORTING:
            self._handle_sorting(distance)

        # 상태 표시 갱신
        state_text_map = {
            STATE_WAITING: "대기 중 (이동)",
            STATE_CLASSIFYING: "판별 중...",
            STATE_SORTING: "분류 이동 중",
        }
        self.state_label.config(text=f"상태: {state_text_map.get(self.state, self.state)}")

        # DC모터 상태 표시
        if self.dc_motor.is_running:
            self.motor_label.config(text="DC모터: 구동 중")
        else:
            self.motor_label.config(text="DC모터: 정지")

        # 결과 표시 시간이 지나면 초기화
        if time.time() > self.result_display_until and self.state == STATE_WAITING:
            self._reset_result_display()

        self.root.after(int(SENSOR_CHECK_INTERVAL * 1000), self._update_sensor_loop)

    # ------------------------------------------------------------------
    # 상태별 처리
    # ------------------------------------------------------------------
    def _handle_waiting(self, distance):
        """1, 2단계: DC모터 구동하며 거리를 감지, 적정거리 도달 시 정지 후 판별 시작"""
        if not self.dc_motor.is_running:
            self.dc_motor.forward()

        if distance is not None and distance <= DETECT_DISTANCE:
            # 적정거리 도달 -> DC모터 정지
            self.dc_motor.stop()
            self.state = STATE_CLASSIFYING

            # 카메라 판별은 별도 스레드에서 실행 (GUI 끊김 방지)
            threading.Thread(target=self._run_classification, daemon=True).start()

    def _run_classification(self):
        """3단계: 현재 프레임으로 AI 판별 수행"""
        if self.current_frame is None:
            # 프레임이 없으면 대기 상태로 복귀
            self.state = STATE_WAITING
            return

        result = self.classifier.predict(self.current_frame)

        if not result["is_fruit_detected"]:
            # 과일이 인식되지 않음 -> 판별 없이 대기 상태로 복귀, 모터 재구동
            self.root.after(0, self._show_not_detected)
            self.state = STATE_WAITING
            self.dc_motor.forward()
            return

        # ----- 4단계: 결과에 따른 LED 표시 -----
        if result["is_normal"]:
            self.led.show_normal()
        else:
            self.led.show_bad()

        # GUI 갱신은 메인 스레드에서 처리
        self.root.after(0, self._show_result, result)

        # 결과 표시 유지 시간 설정
        self.result_display_until = time.time() + LED_DISPLAY_TIME

        # 분류 이동 단계로 전환
        self.sort_result = result
        self.state = STATE_SORTING

        # 모터 재구동 (PASS_DISTANCE까지)
        self.dc_motor.forward()

    def _handle_sorting(self, distance):
        """4단계: PASS_DISTANCE까지 이동 후 서보모터로 분류"""
        if distance is not None and distance <= PASS_DISTANCE:
            self.dc_motor.stop()

            # 서보모터로 분류
            if self.sort_result["is_normal"]:
                self.servo.sort_normal()
            else:
                self.servo.sort_bad()

            time.sleep(0.5)
            self.servo.reset()

            # 다음 과일을 위해 대기 상태로 복귀
            self.state = STATE_WAITING
            self.dc_motor.forward()

    # ------------------------------------------------------------------
    # 결과 화면 표시
    # ------------------------------------------------------------------
    def _show_not_detected(self):
        self.result_frame.config(bg="gray")
        self.result_label.config(text="과일 인식 안됨 - 재시도", bg="gray", fg="white")
        self.prob_label.config(text="")
        self.led.all_off()

    def _show_result(self, result):
        if result["is_normal"]:
            self.result_frame.config(bg="#2ecc71")  # 초록
            self.result_label.config(
                text="정상 사과 (GREEN)",
                bg="#2ecc71", fg="white")
        else:
            self.result_frame.config(bg="#e74c3c")  # 빨강
            self.result_label.config(
                text="썩은 사과 (RED)",
                bg="#e74c3c", fg="white")

        self.prob_label.config(
            text=f"정상: {result['normal_prob']*100:.1f}%  |  "
                 f"불량: {result['bad_prob']*100:.1f}%  |  "
                 f"미감지: {result['none_prob']*100:.1f}%")

    def _reset_result_display(self):
        self.result_frame.config(bg="gray")
        self.result_label.config(text="판별 대기 중", bg="gray", fg="white")
        self.prob_label.config(text="")
        self.led.all_off()

    # ------------------------------------------------------------------
    # 종료 처리
    # ------------------------------------------------------------------
    def on_close(self):
        self.running = False
        self.dc_motor.stop()
        self.dc_motor.cleanup()
        self.servo.cleanup()
        self.led.all_off()
        self.camera.release()
        GPIO.cleanup()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FreshVisionApp(root)
    root.mainloop()
