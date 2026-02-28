import easyocr

# PNG 파일 경로
png_path = r"C:\IDE\ws-ai\mcpsample\file\1213-01_VNB continuous management_v1.1.png"

# EasyOCR reader 초기화 (영어)
print("OCR 모델 로딩 중...")
reader = easyocr.Reader(['en'])

# 텍스트 추출
print("텍스트 추출 중...")
result = reader.readtext(png_path)

# 추출된 텍스트를 하나의 문자열로 결합
text = '\n'.join([detection[1] for detection in result])

# result.txt 파일로 저장
output_path = r"C:\IDE\ws-ai\mcpsample\result.txt"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"텍스트 추출 완료: {output_path}")
print(f"추출된 텍스트 길이: {len(text)} 문자")
print(f"추출된 텍스트 블록 수: {len(result)} 개")
