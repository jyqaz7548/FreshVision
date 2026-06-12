# -*- coding: utf-8 -*-
"""
Fresh Vision - Raspberry Pi Camera Module (picamera2) 래퍼

OpenCV의 VideoCapture 대신 picamera2를 사용.
get_frame()이 BGR(OpenCV 형식) numpy 배열을 반환하도록 맞춰서
classifier.py, main.py의 나머지 로직은 그대로 사용 가능.
"""

import cv2
from picamera2 import Picamera2
from config import CAMERA_WIDTH, CAMERA_HEIGHT


class RPiCamera:
    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()

    def get_frame(self):
        """
        BGR(OpenCV 형식) numpy 배열 반환.
        실패 시 None.
        """
        try:
            frame = self.picam2.capture_array()  # RGB888
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame_bgr
        except Exception:
            return None

    def release(self):
        self.picam2.stop()
        self.picam2.close()
