#!/usr/bin/env python3
"""
Standalone script to extract requirements from images
"""

import easyocr
import re
from pathlib import Path


def extract_text_from_images(image_dir: str, pattern: str) -> dict:
    """이미지 파일들에서 텍스트 추출"""
    image_path = Path(image_dir)
    image_files = sorted(image_path.glob(pattern))
    
    if not image_files:
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_dir}/{pattern}")
    
    print(f"🔍 이미지 파일 검색 중...")
    print(f"   경로: {image_dir}/{pattern}")
    print(f"   발견된 파일: {len(image_files)}개\n")
    
    # EasyOCR reader 초기화
    print("📚 EasyOCR 모델 로딩 중... (첫 실행 시 시간이 걸릴 수 있습니다)")
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    print("✅ OCR 모델 로딩 완료\n")
    
    # 각 이미지에서 텍스트 추출
    extracted_data = {}
    for i, img_file in enumerate(image_files, 1):
        print(f"📄 [{i}/{len(image_files)}] 처리 중: {img_file.name}")
        result = reader.readtext(str(img_file))
        text = '\n'.join([detection[1] for detection in result])
