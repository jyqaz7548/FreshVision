# -*- coding: utf-8 -*-
"""
카메라 + AI 모델 단독 테스트 스크립트 (test_camera_model.py)

GPIO, 모터, LED 없이 카메라와 Teachable Machine 모델만으로
사과 판별이 제대로 되는지 확인합니다.

실행: python3 test_camera_model.py
종료: Ctrl + C 또는 창 닫기
"""

import cv2
import tkinter as tk
from PIL import Image, ImageTk
from picamera2 import Picamera2
import numpy as np
import tflite_runtime.interpreter as tflite
import time

from config import (
    CAMERA_WIDTH, CAMERA_HEIGHT, SWAP_RB,
    MODEL_PATH, LABELS_PATH, MODEL_INPUT_SIZE,
)


# ------------------------------------------------------------------
# 모델 로드
# ------------------------------------------------------------------
def load_model():
    interpreter = tflite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    labels = []
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split(maxsplit=1)
                labels.append(parts[1] if len(parts) == 2 else line)

    return interpreter, input_details, output_details, labels


def predict(interpreter, input_details, output_details, labels, frame):
    img = cv2.resize(frame, MODEL_INPUT_SIZE)
    input_dtype = input_details[0]["dtype"]

    if input_dtype == np.float32:
        img = img.astype(np.float32)
        img = (img / 127.5) - 1.0
    else:
        img = img.astype(np.uint8)

    img = np.expand_dims(img, axis=0)
    interpreter.set_tensor(input_details[0]["index"], img)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]["index"])[0]

    # 양자화 모델 처리
    if input_dtype != np.float32:
        scale, zero_point = output_details[0]["quantization"]
        if scale > 0:
            output = (output.astype(np.float32) - zero_point) * scale

    results = {labels[i]: float(output[i]) for i in range(len(labels))}
    best_label = max(results, key=results.get)
    return best_label, results


# ------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------
class CameraModelTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fresh Vision - 카메라 + 모델 테스트")
        self.root.geometry("900x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.running = True

        # 카메라 초기화
        self.picam2 = Picamera2()
        config = self.picam2.create_video_configuration(
            main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(1)

        # 모델 로드
        self.interpreter, self.input_details, self.output_details, self.labels = load_model()
        print(f"모델 로드 완료! 클래스: {self.labels}")

        self._build_gui()
        self._update()

    def _build_gui(self):
        # 좌측: 카메라
        left = tk.Frame(self.root)
        left.pack(side=tk.LEFT, padx=10, pady=10)

        tk.Label(left, text="카메라 화면", font=("Arial", 13, "bold")).pack()
        self.camera_label = tk.Label(left, bg="black")
        self.camera_label.pack()

        # 우측: 판별 결과
        right = tk.Frame(self.root)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(right, text="판별 결과", font=("Arial", 16, "bold")).pack(pady=(0, 20))

        # 결과 패널
        self.result_frame = tk.Frame(right, bg="gray", height=120)
        self.result_frame.pack(fill=tk.X, pady=10)
        self.result_frame.pack_propagate(False)

        self.result_label = tk.Label(
            self.result_frame, text="판별 중...",
            font=("Arial", 22, "bold"), bg="gray", fg="white")
        self.result_label.pack(expand=True)

        # 확률 바 영역
        tk.Label(right, text="확률", font=("Arial", 13, "bold")).pack(pady=(15, 5))

        self.prob_bars = {}
        self.prob_labels = {}

        for label in self.labels:
            row = tk.Frame(right)
            row.pack(fill=tk.X, pady=3)

            name_label = tk.Label(row, text=label, width=16, anchor="w",
                                   font=("Arial", 11))
            name_label.pack(side=tk.LEFT)

            bar_bg = tk.Frame(row, bg="#ddd", width=200, height=22)
            bar_bg.pack(side=tk.LEFT, padx=5)
            bar_bg.pack_propagate(False)

            bar = tk.Frame(bar_bg, bg="#3498db", width=0, height=22)
            bar.place(x=0, y=0, relheight=1)

            pct_label = tk.Label(row, text="0.0%", font=("Arial", 11), width=7)
            pct_label.pack(side=tk.LEFT)

            self.prob_bars[label] = (bar, bar_bg)
            self.prob_labels[label] = pct_label

        # 판별 횟수 / 통계
        tk.Label(right, text="", font=("Arial", 1)).pack(pady=10)
        self.stats_label = tk.Label(right, text="총 판별: 0회",
                                     font=("Arial", 11), fg="gray")
        self.stats_label.pack()

        self.count = 0
        self.last_predict_time = 0

    def _update(self):
        if not self.running:
            return

        # 카메라 프레임 받기
        frame = self.picam2.capture_array()
        if SWAP_RB:
            frame = frame[:, :, ::-1]

        # 화면 표시
        display = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
        img = Image.fromarray(display)
        imgtk = ImageTk.PhotoImage(image=img)
        self.camera_label.imgtk = imgtk
        self.camera_label.configure(image=imgtk)

        # 0.5초마다 판별 (너무 빠르면 라즈베리파이 부하)
        now = time.time()
        if now - self.last_predict_time >= 0.5:
            self.last_predict_time = now
            best_label, results = predict(
                self.interpreter, self.input_details,
                self.output_details, self.labels, frame
            )
            self._show_result(best_label, results)
            self.count += 1
            self.stats_label.config(text=f"총 판별: {self.count}회")

        self.root.after(33, self._update)

    def _show_result(self, best_label, results):
        # 결과 패널 색상
        label_lower = best_label.lower()
        if "normal" in label_lower:
            bg = "#2ecc71"
            text = f"✅ {best_label}"
        elif "rotten" in label_lower:
            bg = "#e74c3c"
            text = f"❌ {best_label}"
        else:
            bg = "gray"
            text = f"❓ {best_label}"

        self.result_frame.config(bg=bg)
        self.result_label.config(text=text, bg=bg)

        # 확률 바 업데이트
        bar_colors = {
            "normal": "#2ecc71",
            "rotten": "#e74c3c",
            "not":    "#95a5a6",
        }

        for label, prob in results.items():
            if label not in self.prob_bars:
                continue

            bar, bar_bg = self.prob_bars[label]
            pct_label = self.prob_labels[label]

            # 바 너비 계산
            bar_bg.update_idletasks()
            max_width = bar_bg.winfo_width()
            bar_width = int(max_width * prob)

            # 색상 결정
            label_lower = label.lower()
            color = "#3498db"
            for key, c in bar_colors.items():
                if key in label_lower:
                    color = c
                    break

            bar.config(width=bar_width, bg=color)
            bar.place(x=0, y=0, width=bar_width, relheight=1)
            pct_label.config(text=f"{prob*100:.1f}%")

    def on_close(self):
        self.running = False
        self.picam2.stop()
        self.picam2.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CameraModelTestApp(root)
    root.mainloop()
