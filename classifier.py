# -*- coding: utf-8 -*-
"""
Fresh Vision - Teachable Machine TFLite 모델 추론 모듈
"""

import numpy as np
import cv2
import tflite_runtime.interpreter as tflite
from config import MODEL_PATH, LABELS_PATH, MODEL_INPUT_SIZE


class FruitClassifier:
    def __init__(self):
        # 모델 로드
        self.interpreter = tflite.Interpreter(model_path=MODEL_PATH)
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # 라벨 로드 (예: "0 정상", "1 불량")
        self.labels = self._load_labels()

        # 라벨 인덱스 찾기
        self.normal_index = self._find_label_index("normal")
        self.bad_index = self._find_label_index("rotten")
        self.none_index = self._find_label_index("not detected")

    def _load_labels(self):
        labels = []
        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    # "0 정상" 형식에서 라벨 텍스트만 추출
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        labels.append(parts[1])
                    else:
                        labels.append(line)
        return labels

    def _find_label_index(self, keyword):
        for i, label in enumerate(self.labels):
            if keyword.lower() in label.lower():
                return i
        # 못 찾으면 기본값
        defaults = {"normal": 0, "rotten": 1, "not detected": 2}
        return defaults.get(keyword, -1)

    def predict(self, frame):
        """
        카메라 프레임(BGR)을 입력받아 판별 결과를 반환.

        Returns:
            dict: {
                "label": "정상" 또는 "불량",
                "is_normal": bool,
                "normal_prob": float (0~1),
                "bad_prob": float (0~1)
            }
        """
        # 전처리: 리사이즈, BGR -> RGB, 정규화
        img = cv2.resize(frame, MODEL_INPUT_SIZE)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        input_dtype = self.input_details[0]["dtype"]

        if input_dtype == np.float32:
            img = img.astype(np.float32)
            img = (img / 127.5) - 1.0  # -1 ~ 1 정규화 (Teachable Machine 기본)
        else:
            img = img.astype(np.uint8)

        img = np.expand_dims(img, axis=0)

        # 추론 실행
        self.interpreter.set_tensor(self.input_details[0]["index"], img)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]["index"])[0]

        # 양자화 모델인 경우 결과값을 0~1로 스케일 변환
        if input_dtype != np.float32:
            scale, zero_point = self.output_details[0]["quantization"]
            if scale > 0:
                output = (output.astype(np.float32) - zero_point) * scale

        normal_prob = float(output[self.normal_index])
        bad_prob = float(output[self.bad_index])
        none_prob = float(output[self.none_index]) if self.none_index >= 0 else 0.0

        # 가장 확률 높은 클래스 결정
        probs = {"normal": normal_prob, "rotten": bad_prob, "none": none_prob}
        best = max(probs, key=probs.get)

        is_fruit_detected = (best != "none")
        is_normal = (best == "normal")

        if best == "normal":
            label = "정상"
        elif best == "rotten":
            label = "불량"
        else:
            label = "감지안됨"

        return {
            "label": label,
            "is_fruit_detected": is_fruit_detected,
            "is_normal": is_normal,
            "normal_prob": normal_prob,
            "bad_prob": bad_prob,
            "none_prob": none_prob,
        }
