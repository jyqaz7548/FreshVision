# Fresh Vision 🍎

라즈베리파이 기반 AI 과일(사과) 신선도 판별 및 분류 시스템

## 시스템 구성

| 부품 | 역할 |
|------|------|
| 초음파센서 (HC-SR04) | 과일 위치 감지 |
| 카메라 | 과일 촬영 → AI 판별 |
| DC모터 (L298N) | 컨베이어벨트 구동/정지 |
| 서보모터 (SG90) | 정상/불량 분류 게이트 |
| LED (초록/빨강) | 판별 결과 알림 |

## 동작 로직

1. DC모터 구동 → 과일 이동
2. 초음파센서가 적정거리(기본 8cm) 감지 → DC모터 정지
3. 카메라 촬영 → Teachable Machine 모델로 정상/불량 판별
4. 판별 결과에 따라 LED 점등 (정상: 초록 / 불량: 빨강)
5. DC모터 재구동 → 1cm 지점까지 이동 → 서보모터로 분류
6. 1번으로 복귀

## 설치

```bash
git clone <레포 주소>
cd freshvision
```

### 1. 시스템 패키지 (apt) - numpy, opencv, picamera2, Pillow ImageTk

```bash
sudo apt update
sudo apt install python3-numpy python3-opencv python3-picamera2 python3-pil.imagetk -y
```

> ⚠️ numpy/opencv/picamera2를 pip로 설치하면 ABI 충돌(`numpy.dtype size changed`, `multiarray failed to import`)이 발생합니다. 반드시 apt로 설치하세요.

### 2. 나머지 라이브러리 (pip)

```bash
pip install -r requirements.txt --break-system-packages
```

> `tflite-runtime` 설치가 안 되면 아래로 시도:
> ```bash
> pip install tflite-runtime --break-system-packages --extra-index-url https://google-coral.github.io/py-repo/
> ```

> raspi-config 또는 설정 앱에서 카메라 인터페이스가 활성화되어 있는지 확인하세요.

## 모델 파일

Google Teachable Machine에서 학습한 모델을 아래 위치에 넣어주세요.

```
freshvision/
├── model.tflite
├── labels.txt    (예: "0 normal apple", "1 rotten apple", "2 not detected")
```

> ⚠️ `labels.txt`에 "normal", "rotten", "not detected" 단어가 포함되어 있어야 코드가 올바르게 인식합니다.

## 실행

```bash
python main.py
```

## 설정 변경

`config.py`에서 다음 값들을 환경에 맞게 조정하세요.

- `DETECT_DISTANCE`: 카메라 촬영 위치 거리 (기본 8cm)
- `PASS_DISTANCE`: 분류 동작 위치 거리 (기본 1cm)
- `NORMAL_THRESHOLD`: 정상 판정 확률 임계값 (기본 0.7)
- `SERVO_NORMAL_ANGLE` / `SERVO_BAD_ANGLE`: 서보모터 분류 각도

## 핀맵

| 부품 | 핀 |
|------|-----|
| 초음파 TRIG | GPIO23 (물리 16) |
| 초음파 ECHO | GPIO24 (물리 18, 전압분배 필수) |
| DC모터 IN1 | GPIO5 (물리 29) |
| DC모터 IN2 | GPIO6 (물리 31) |
| DC모터 ENA | GPIO13 (물리 33) |
| 서보모터 PWM | GPIO18 (물리 12) |
| LED 초록 | GPIO25 (물리 22, 220Ω 직렬) |
| LED 빨강 | GPIO26 (물리 37, 220Ω 직렬) |
| 카메라 | CSI 포트 |