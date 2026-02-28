# DOC to Image Converter

.doc/.docx 파일을 PNG 또는 JPG 이미지로 변환하는 Python 스크립트입니다.

## 파일 구성

- **convert_doc_to_img.py** - 명령줄/Python 모듈 버전
- **convert_doc_to_img_mcp.py** - MCP 서버 버전 (Claude Desktop 통합)
- **example_doc_to_img.py** - 사용 예제

## 기능

- ✅ .doc 및 .docx 파일 지원
- ✅ PNG 또는 JPG 형식으로 출력
- ✅ DPI 설정 가능 (해상도 조절)
- ✅ 특정 페이지만 선택적으로 변환
- ✅ Windows (docx2pdf) 및 크로스 플랫폼 (LibreOffice) 지원
- ✅ 명령줄, Python 모듈, MCP 서버로 사용 가능

## 설치

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

또는 개별 설치:

```bash
pip install pymupdf Pillow python-docx docx2pdf
```

### 2. 추가 요구사항

#### Windows 사용자
- **Microsoft Word**가 설치되어 있어야 합니다 (docx2pdf가 Word COM을 사용)
- 또는 **LibreOffice**를 설치하고 `--use-libreoffice` 옵션 사용

#### Linux/Mac 사용자
- **LibreOffice**를 설치해야 합니다:
  - Ubuntu/Debian: `sudo apt-get install libreoffice`
  - Mac: `brew install libreoffice`
  - 또는 [LibreOffice 공식 사이트](https://www.libreoffice.org/)에서 다운로드

## 사용 방법

### 1. 명령줄 사용

#### 기본 사용법
```bash
python convert_doc_to_img.py ./file/요구사항정의서-20260225.docx
```

#### 출력 디렉토리 및 형식 지정
```bash
python convert_doc_to_img.py ./file/요구사항정의서-20260225.docx --out-dir ./output --format jpg --dpi 200
```

#### 특정 페이지만 변환
```bash
python convert_doc_to_img.py ./file/요구사항정의서-20260225.docx --start 1 --end 3
```

#### LibreOffice 사용 (크로스 플랫폼)
```bash
python convert_doc_to_img.py ./file/요구사항정의서-20260225.docx --use-libreoffice
```

#### 고품질 JPG 변환
```bash
python convert_doc_to_img.py ./file/요구사항정의서-20260225.docx --format jpg --quality 95 --dpi 300
```

### 2. Python 모듈로 사용

```python
from convert_doc_to_img import convert

# 기본 변환 (PNG, 150 DPI)
output_files = convert(
    doc_path="./file/요구사항정의서-20260225.docx"
)

# 고품질 JPG 변환
output_files = convert(
    doc_path="./file/요구사항정의서-20260225.docx",
    out_dir="./output",
    fmt="jpg",
    dpi=200,
    quality=95
)

# 특정 페이지만 변환
output_files = convert(
    doc_path="./file/요구사항정의서-20260225.docx",
    start=1,
    end=3
)

# LibreOffice 사용
output_files = convert(
    doc_path="./file/요구사항정의서-20260225.docx",
    use_libreoffice=True
)

print(f"변환된 파일: {output_files}")
```

### 3. MCP 서버로 사용 (Claude Desktop 통합)

MCP 서버를 실행하여 Claude Desktop에서 직접 사용할 수 있습니다.

#### MCP 서버 실행
```bash
python convert_doc_to_img_mcp.py
```

#### Claude Desktop 설정

`claude_desktop_config.json` 파일에 다음을 추가:

```json
{
  "mcpServers": {
    "doc_convertor": {
      "command": "python",
      "args": ["c:/IDE/ws-ai/mcpsample/convert_doc_to_img_mcp.py"]
    }
  }
}
```

#### MCP 도구 사용

Claude Desktop에서 다음과 같이 사용:

```
요구사항정의서-20260225.docx 파일을 이미지로 변환해줘
```

MCP 서버는 다음 도구를 제공합니다:

**convert_doc_in_downloads_to_png**
- `filename`: 파일명 (예: "요구사항정의서-20260225.docx")
- `dpi`: 렌더링 DPI (기본값: 200)
- `overwrite`: 기존 파일 덮어쓰기 (기본값: true)
- `return_data_url`: 이미지 데이터 URL 반환 (기본값: true)
- `first_page_only`: 첫 페이지만 변환 (기본값: true)
- `use_libreoffice`: LibreOffice 사용 (기본값: false)

### 4. 예제 스크립트 실행

```bash
python example_doc_to_img.py
```

## 명령줄 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `doc` | 입력 .doc 또는 .docx 파일 경로 (필수) | - |
| `--out-dir` | 출력 디렉토리 | `<파일명>_images` |
| `--format` | 출력 형식 (png 또는 jpg) | `png` |
| `--dpi` | 렌더링 DPI (해상도) | `150` |
| `--start` | 시작 페이지 (1부터 시작) | `1` |
| `--end` | 종료 페이지 | 마지막 페이지 |
| `--quality` | JPEG 품질 (1-95, jpg만 해당) | `85` |
| `--use-libreoffice` | LibreOffice 사용 (크로스 플랫폼) | `False` |

## 작동 원리

1. **DOC/DOCX → PDF 변환**
   - Windows: `docx2pdf` 사용 (Microsoft Word COM)
   - 크로스 플랫폼: LibreOffice headless 모드 사용

2. **PDF → 이미지 변환**
   - PyMuPDF (fitz)를 사용하여 PDF 페이지를 렌더링
   - Pillow를 사용하여 PNG 또는 JPG로 저장

## 출력 파일 형식

변환된 이미지는 다음과 같은 형식으로 저장됩니다:

```
<문서명>_page_001.png
<문서명>_page_002.png
<문서명>_page_003.png
...
```

## 문제 해결

### Windows에서 "docx2pdf not available" 오류
- Microsoft Word가 설치되어 있는지 확인
- 또는 LibreOffice를 설치하고 `--use-libreoffice` 옵션 사용

### Linux/Mac에서 "LibreOffice not found" 오류
- LibreOffice 설치: `sudo apt-get install libreoffice` (Ubuntu/Debian)
- 또는 공식 사이트에서 다운로드

### 한글 파일명 문제
- Python 3.7 이상 사용 권장
- UTF-8 인코딩 지원 확인

## 라이선스

이 스크립트는 교육 및 개인 사용 목적으로 제공됩니다.

## 의존성

- **pymupdf**: PDF 렌더링
- **Pillow**: 이미지 처리
- **python-docx**: DOCX 파일 처리 (선택적)
- **docx2pdf**: Windows에서 DOC/DOCX → PDF 변환
