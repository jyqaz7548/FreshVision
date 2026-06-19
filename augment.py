# -*- coding: utf-8 -*-
"""
데이터 증강 스크립트 (Data Augmentation)

기존 사과 사진들을 회전, 반전, 밝기 조절, 노이즈 추가 등으로
여러 버전으로 만들어서 데이터셋을 늘려줍니다.

사용법:
1. 아래 INPUT_DIR에 원본 사진 폴더 경로 지정
2. OUTPUT_DIR에 증강된 사진 저장 폴더 경로 지정
3. python augment.py 실행

폴더 구조 예시:
  data/
  ├── normal/      ← 정상 사과 원본 사진
  └── rotten/      ← 썩은 사과 원본 사진

실행 후:
  augmented/
  ├── normal/      ← 증강된 정상 사과 사진 (원본의 8배)
  └── rotten/      ← 증강된 썩은 사과 사진 (원본의 8배)
"""

import cv2
import numpy as np
import os

# ===== 설정 =====
INPUT_DIR = "data"       # 원본 사진 폴더
OUTPUT_DIR = "augmented" # 증강 결과 저장 폴더
CLASSES = ["normal", "rotten", "not_detected"]# 클래스 폴더 이름


def augment_image(img):
    """
    하나의 이미지를 여러 방식으로 변형해서 리스트로 반환.
    원본 1장 → 8장 생성
    """
    results = []

    # 1. 원본
    results.append(img)

    # 2. 좌우 반전
    results.append(cv2.flip(img, 1))

    # 3. 상하 반전
    results.append(cv2.flip(img, 0))

    # 4. 밝기 증가 (+50)
    bright = np.clip(img.astype(np.int32) + 50, 0, 255).astype(np.uint8)
    results.append(bright)

    # 5. 밝기 감소 (-50)
    dark = np.clip(img.astype(np.int32) - 50, 0, 255).astype(np.uint8)
    results.append(dark)

    # 6. 90도 회전
    results.append(cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE))

    # 7. 180도 회전
    results.append(cv2.rotate(img, cv2.ROTATE_180))

    # 8. 가우시안 노이즈 추가
    noise = np.random.normal(0, 15, img.shape).astype(np.int32)
    noisy = np.clip(img.astype(np.int32) + noise, 0, 255).astype(np.uint8)
    results.append(noisy)

    return results


def main():
    total_original = 0
    total_augmented = 0

    for cls in CLASSES:
        input_cls_dir = os.path.join(INPUT_DIR, cls)
        output_cls_dir = os.path.join(OUTPUT_DIR, cls)
        os.makedirs(output_cls_dir, exist_ok=True)

        if not os.path.exists(input_cls_dir):
            print(f"[경고] {input_cls_dir} 폴더가 없습니다. 건너뜁니다.")
            continue

        files = [f for f in os.listdir(input_cls_dir)
                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        print(f"\n[{cls}] 원본 {len(files)}장 처리 중...")
        count = 0

        for fname in files:
            img_path = os.path.join(input_cls_dir, fname)
            img = cv2.imread(img_path)

            if img is None:
                print(f"  [경고] {fname} 읽기 실패, 건너뜁니다.")
                continue

            augmented = augment_image(img)

            base_name = os.path.splitext(fname)[0]
            for i, aug_img in enumerate(augmented):
                out_name = f"{base_name}_aug{i}.jpg"
                out_path = os.path.join(output_cls_dir, out_name)
                cv2.imwrite(out_path, aug_img)
                count += 1

        print(f"  → {len(files)}장 → {count}장으로 증강 완료!")
        total_original += len(files)
        total_augmented += count

    print(f"\n전체 완료: {total_original}장 → {total_augmented}장")
    print(f"저장 위치: {os.path.abspath(OUTPUT_DIR)}")
    print("\nTeachable Machine에 augmented 폴더의 사진을 업로드해서 다시 학습하세요!")


if __name__ == "__main__":
    main()
