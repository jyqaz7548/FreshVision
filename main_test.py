# -*- coding: utf-8 -*-
"""
Fresh Vision - 노트북 GUI 테스트용 (main_test.py)

라즈베리파이 하드웨어(GPIO, picamera2, tflite-runtime) 없이
노트북 웹캠으로 GUI 레이아웃과 동작 흐름만 확인하기 위한 파일입니다.

- 카메라: 노트북 웹캠 (cv2.VideoCapture)
- 초음파센서: 가짜 거리값 (시간에 따라 변하는 값으로 시뮬레이션)
- DC모터/서보모터/LED: 콘솔에 출력만 함
- AI 판별: 랜덤으로 정상/불량/감지안됨 반환

실제 라즈베리파이에서는 main.py를 사용하세요.
"""

import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import threading
import time
import random


# ===== 설정값 (config.py와 동일한 값들) =====
DETECT_DISTANCE = 8
PASS_DISTANCE = 1
SENSOR_CHECK_INTERVAL = 0.1
LED_DISPLAY_TIME = 3.0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


# 상태 정의
STATE_WAITING = "WAITING"
STATE_CLASSIFYING = "CLASSIFYING"
STATE_SORTING = "SORTING"


# ------------------------------------------------------------------
# Mock(가짜) 하드웨어 클래스들
# ------------------------------------------------------------------
class MockUltrasonicSensor:
    """
    초음파센서 흉내.
    시간이 지날수록 거리값이 줄어들다가, 0 근처에서 다시 멀어지는
    "과일이 다가왔다가 지나가는" 상황을 시뮬레이션.
    """
    def __init__(self):
        self.distance = 30.0
        self.direction = -1  # -1: 가까워짐, +1: 멀어짐

    def get_distance_filtered(self, samples=3):
        self.distance += self.direction * 0.5
        if self.distance <= 0:
            self.distance = 0
            self.direction = 1
        if self.distance >= 30:
            self.distance = 30
            self.direction = -1
        return round(self.distance, 1)


class MockDCMotor:
    def __init__(self):
        self.is_running = False

    def forward(self, speed=50):
        if not self.is_running:
            print("[Mock] DC모터 구동 시작")
        self.is_running = True

    def stop(self):
        if self.is_running:
            print("[Mock] DC모터 정지")
        self.is_running = False

    def cleanup(self):
        self.stop()


class MockServoMotor:
    def sort_normal(self):
        print("[Mock] 서보모터 -> 정상 박스 방향")

    def sort_bad(self):
        print("[Mock] 서보모터 -> 불량 박스 방향")

    def reset(self):
        print("[Mock] 서보모터 -> 대기 위치 복귀")

    def cleanup(self):
        pass


class MockLEDIndicator:
    def show_normal(self):
        print("[Mock] LED: 초록 ON")

    def show_bad(self):
        print("[Mock] LED: 빨강 ON")

    def all_off(self):
        print("[Mock] LED: 모두 OFF")


class MockFruitClassifier:
    """실제 모델 대신 랜덤 결과를 반환"""

    def predict(self, frame):
        choice = random.choices(
            ["normal", "rotten", "none"],
            weights=[0.45, 0.45, 0.10],
        )[0]

        normal_prob = random.uniform(0.6, 0.95) if choice == "normal" else random.uniform(0.0, 0.4)
        bad_prob = random.uniform(0.6, 0.95) if choice == "rotten" else random.uniform(0.0, 0.4)
        none_prob = random.uniform(0.6, 0.95) if choice == "none" else random.uniform(0.0, 0.2)

        is_fruit_detected = (choice != "none")
        is_normal = (choice == "normal")

        label_map = {"normal": "정상", "rotten": "불량", "none": "감지안됨"}

        return {
            "label": label_map[choice],
            "is_fruit_detected": is_fruit_detected,
            "is_normal": is_normal,
            "normal_prob": normal_prob,
            "bad_prob": bad_prob,
            "none_prob": none_prob,
        }


class MockRPiCamera:
    """노트북 웹캠을 사용 (실제 카메라 화면)"""

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    def get_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None

    def release(self):
        self.cap.release()


# ------------------------------------------------------------------
# GUI + 상태머신 (main.py와 거의 동일한 구조)
# ------------------------------------------------------------------
class FreshVisionTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fresh Vision - GUI 테스트 (노트북, Mock)")
        self.root.geometry("800x650")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Mock 하드웨어
        self.sensor = MockUltrasonicSensor()
        self.dc_motor = MockDCMotor()
        self.servo = MockServoMotor()
        self.led = MockLEDIndicator()
        self.classifier = MockFruitClassifier()
        self.camera = MockRPiCamera()

        self.state = STATE_WAITING
        self.current_frame = None
        self.running = True
        self.result_display_until = 0

        self._build_gui()

        self.dc_motor.forward()
        self._update_camera()
        self._update_sensor_loop()

    # ------------------------------------------------------------
    def _build_gui(self):
        left_frame = tk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.camera_label = tk.Label(left_frame, bg="black",
                                       width=CAMERA_WIDTH, height=CAMERA_HEIGHT)
        self.camera_label.pack()

        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_label = tk.Label(right_frame, text="Fresh Vision (테스트 모드)",
                                font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))

        self.fruit_present_label = tk.Label(
            right_frame, text="과일 감지: 없음", font=("Arial", 14), anchor="w")
        self.fruit_present_label.pack(fill=tk.X, pady=5)

        self.distance_label = tk.Label(
            right_frame, text="거리: -- cm", font=("Arial", 14), anchor="w")
        self.distance_label.pack(fill=tk.X, pady=5)

        self.motor_label = tk.Label(
            right_frame, text="DC모터: 정지", font=("Arial", 14), anchor="w")
        self.motor_label.pack(fill=tk.X, pady=5)

        self.state_label = tk.Label(
            right_frame, text="상태: 대기 중", font=("Arial", 14), anchor="w")
        self.state_label.pack(fill=tk.X, pady=5)

        ttk.Separator(right_frame, orient="horizontal").pack(fill=tk.X, pady=15)

        self.result_frame = tk.Frame(right_frame, bg="gray", height=150)
        self.result_frame.pack(fill=tk.X, pady=10)
        self.result_frame.pack_propagate(False)

        self.result_label = tk.Label(
            self.result_frame, text="판별 대기 중",
            font=("Arial", 24, "bold"), bg="gray", fg="white")
        self.result_label.pack(expand=True)

        self.prob_label = tk.Label(right_frame, text="", font=("Arial", 12), anchor="w")
        self.prob_label.pack(fill=tk.X, pady=5)

        note = tk.Label(
            right_frame,
            text="※ 테스트 모드: 거리/판별 결과는 임의로 시뮬레이션됩니다.",
            font=("Arial", 10), fg="gray", anchor="w", justify="left", wraplength=300)
        note.pack(fill=tk.X, pady=(20, 0))

    # ------------------------------------------------------------
    def _update_camera(self):
        if not self.running:
            return

        frame = self.camera.get_frame()
        if frame is not None:
            self.current_frame = frame.copy()
            display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            display_frame = cv2.resize(display_frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
            img = Image.fromarray(display_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.camera_label.imgtk = imgtk
            self.camera_label.configure(image=imgtk)

        self.root.after(33, self._update_camera)

    # ------------------------------------------------------------
    def _update_sensor_loop(self):
        if not self.running:
            return

        distance = self.sensor.get_distance_filtered()

        if distance is not None:
            self.distance_label.config(text=f"거리: {distance} cm")
            if distance <= 30:
                self.fruit_present_label.config(text="과일 감지: 있음")
            else:
                self.fruit_present_label.config(text="과일 감지: 없음")

        if self.state == STATE_WAITING:
            self._handle_waiting(distance)
        elif self.state == STATE_SORTING:
            self._handle_sorting(distance)

        state_text_map = {
            STATE_WAITING: "대기 중 (이동)",
            STATE_CLASSIFYING: "판별 중...",
            STATE_SORTING: "분류 이동 중",
        }
        self.state_label.config(text=f"상태: {state_text_map.get(self.state, self.state)}")
        self.motor_label.config(
            text="DC모터: 구동 중" if self.dc_motor.is_running else "DC모터: 정지")

        if time.time() > self.result_display_until and self.state == STATE_WAITING:
            self._reset_result_display()

        self.root.after(int(SENSOR_CHECK_INTERVAL * 1000), self._update_sensor_loop)

    # ------------------------------------------------------------
    def _handle_waiting(self, distance):
        if not self.dc_motor.is_running:
            self.dc_motor.forward()

        if distance is not None and distance <= DETECT_DISTANCE:
            self.dc_motor.stop()
            self.state = STATE_CLASSIFYING
            threading.Thread(target=self._run_classification, daemon=True).start()

    def _run_classification(self):
        if self.current_frame is None:
            self.state = STATE_WAITING
            return

        time.sleep(0.5)  # 실제 추론 시간을 흉내내기 위한 약간의 지연
        result = self.classifier.predict(self.current_frame)

        if not result["is_fruit_detected"]:
            self.root.after(0, self._show_not_detected)
            self.state = STATE_WAITING
            self.dc_motor.forward()
            return

        if result["is_normal"]:
            self.led.show_normal()
        else:
            self.led.show_bad()

        self.root.after(0, self._show_result, result)
        self.result_display_until = time.time() + LED_DISPLAY_TIME

        self.sort_result = result
        self.state = STATE_SORTING
        self.dc_motor.forward()

    def _handle_sorting(self, distance):
        if distance is not None and distance <= PASS_DISTANCE:
            self.dc_motor.stop()

            if self.sort_result["is_normal"]:
                self.servo.sort_normal()
            else:
                self.servo.sort_bad()

            time.sleep(0.5)
            self.servo.reset()

            self.state = STATE_WAITING
            self.dc_motor.forward()

    # ------------------------------------------------------------
    def _show_not_detected(self):
        self.result_frame.config(bg="gray")
        self.result_label.config(text="과일 인식 안됨 - 재시도", bg="gray", fg="white")
        self.prob_label.config(text="")
        self.led.all_off()

    def _show_result(self, result):
        if result["is_normal"]:
            self.result_frame.config(bg="#2ecc71")
            self.result_label.config(text="정상 사과 (GREEN)", bg="#2ecc71", fg="white")
        else:
            self.result_frame.config(bg="#e74c3c")
            self.result_label.config(text="썩은 사과 (RED)", bg="#e74c3c", fg="white")

        self.prob_label.config(
            text=f"정상: {result['normal_prob']*100:.1f}%  |  "
                 f"불량: {result['bad_prob']*100:.1f}%  |  "
                 f"미감지: {result['none_prob']*100:.1f}%")

    def _reset_result_display(self):
        self.result_frame.config(bg="gray")
        self.result_label.config(text="판별 대기 중", bg="gray", fg="white")
        self.prob_label.config(text="")
        self.led.all_off()

    # ------------------------------------------------------------
    def on_close(self):
        self.running = False
        self.dc_motor.cleanup()
        self.servo.cleanup()
        self.camera.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FreshVisionTestApp(root)
    root.mainloop()
