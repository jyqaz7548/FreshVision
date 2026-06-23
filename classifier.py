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
        # 카메라 이미지를 모델 입력 크기(224x224)로 리사이즈
        img = cv2.resize(frame, MODEL_INPUT_SIZE)
        # 픽셀값을 정수(0~255)에서 실수형으로 변환
        img = img.astype(np.float32)
        # 픽셀값을 -1~1 사이로 정규화 (Teachable Machine 기본 전처리 방식)
        img = (img / 127.5) - 1.0
        # 모델 입력 형식에 맞게 배치 차원 추가 (224,224,3) → (1,224,224,3)
        img = np.expand_dims(img, axis=0)

        # 전처리된 이미지를 모델의 입력 텐서에 전달
        self.interpreter.set_tensor(self.input_details[0]["index"], img)
        # 모델 추론 실행
        self.interpreter.invoke()
        # 모델 출력 텐서에서 확률값 추출 ex) [0.92, 0.05, 0.03]
        output = self.interpreter.get_tensor(self.output_details[0]["index"])[0]

        # 각 클래스별 확률값 추출
        normal_prob = float(output[self.normal_index])  # 정상 사과 확률
        bad_prob    = float(output[self.bad_index])     # 썩은 사과 확률
        none_prob   = float(output[self.none_index]) if self.none_index >= 0 else 0.0  # 감지안됨 확률

        # 딕셔너리로 묶어서 가장 높은 확률의 클래스 선택
        probs = {"normal": normal_prob, "rotten": bad_prob, "none": none_prob}
        best  = max(probs, key=probs.get)

        # 영어 클래스명을 한글 라벨로 변환
        if best == "normal":
            label = "정상"
        elif best == "rotten":
            label = "불량"
        else:
            label = "감지안됨"

        # 판별 결과를 딕셔너리로 반환
        return {
            "label": label,                      # 최종 판별 결과 (정상/불량/감지안됨)
            "is_fruit_detected": best != "none", # 과일 감지 여부
            "is_normal": best == "normal",       # 정상 여부
            "normal_prob": normal_prob,          # 정상 확률
            "bad_prob": bad_prob,                # 불량 확률
            "none_prob": none_prob,              # 감지안됨 확률
        }
