# -*- coding: utf-8 -*-
"""
Fresh Vision - Raspberry Pi Camera Module (picamera2) 래퍼

OpenCV의 VideoCapture 대신 picamera2를 사용.
get_frame()이 BGR(OpenCV 형식) numpy 배열을 반환하도록 맞춰서
classifier.py, main.py의 나머지 로직은 그대로 사용 가능.
"""

import time
from picamera2 import Picamera2
from config import CAMERA_WIDTH, CAMERA_HEIGHT, SWAP_RB


class RPiCamera:
    def __init__(self):
        self.picam2 = Picamera2()

        camera_config = self.picam2.create_video_configuration(
            main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"}
        )
        self.picam2.configure(camera_config)
        self.picam2.start()
        time.sleep(1)  # 카메라 워밍업 대기

    def get_frame(self):
        """
        RGB numpy 배열 반환 (Tkinter/PIL 및 Teachable Machine 모델 입력 형식).
        실패 시 None.

        색이 반전되어 보이면 config.py의 SWAP_RB 값을 바꾸세요.
        """
        try:
            frame = self.picam2.capture_array()
            if SWAP_RB:
                frame = frame[:, :, ::-1]  # R과 B 채널 교환
            return frame
        except Exception:
            return None

    def release(self):
        self.picam2.stop()
        self.picam2.close()