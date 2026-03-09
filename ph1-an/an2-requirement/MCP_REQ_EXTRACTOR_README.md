# MCP Server: Requirements Extractor

이미지에서 요구사항을 추출하여 spec-design.md를 생성하는 MCP 서버입니다.

## 개요

이 MCP 서버는 다음 작업을 자동화합니다:
1. 이미지 파일에서 텍스트 추출 (EasyOCR 사용)
2. 추출된 텍스트를 파싱하여 구조화된 요구사항 문서 생성
3. spec-design.md 포맷으로 저장

## 기능

### Tool: `extract_requirements_from_images`

이미지 파일에서 요구사항을 추출하여 spec-design.md 파일을 생성합니다.

**입력 파라미터:**
- `image_dir` (string): 이미지 파일이 있는 디렉토리 경로 (기본값: "file/img")
- `image_pattern` (string): 이미지 파일 패턴 (기본값: "1650-01_요구사항정의서_v1.1_page_*.png")
- `output_dir` (string): 출력 파일을 저장할 디렉토리 (기본값: "ph2-de")
- `output_filename` (string): 출력 파일명 (기본값: "spec-design.md")

**추출되는 섹션:**
- 기본 정보 (request_id, project_name)
- 요구사항 (동시접속자, RPS, 피크 배수, 가용성, 목표 응답시간)
- 애플리케이션 (타입, 프레임워크, WAR 파일, 컨텍스트 경로)
- 인프라 (배포 방식, 클라우드, OS)
- 토폴로지 (구성, 웹서버 대수, WAS 대수, 로드밸런서)
- 미들웨어 (웹서버, WAS, 연결방식, session_clustering)
- 보안 (SSL, WAF, IP 화이트리스트)
- 기타 (dev 환경)

## 설치

### 1. 의존성 설치

```bash
cd /home/ec2-user/mcpsample
uv pip install easyocr mcp
```

### 2. MCP 서버 설정

Claude Desktop 또는 다른 MCP 클라이언트의 설정 파일에 다음을 추가:

```json
{
  "mcpServers": {
    "requirements-extractor": {
      "command": "uv",
      "args": [
        "run",
        "/home/ec2-user/mcpsample/mcp-server-req-extractor.py"
      ],
      "description": "이미지에서 요구사항을 추출하여 spec-design.md를 생성하는 MCP 서버"
    }
  }
}
```

또는 제공된 설정 파일 사용:
```bash
cp mcp-config-req-extractor.json ~/.config/claude/mcp-settings.json
```

## 사용 방법

### MCP 클라이언트에서 사용

1. MCP 클라이언트 재시작
2. `extract_requirements_from_images` 도구 호출

**예시:**
```json
{
  "image_dir": "file/img",
  "image_pattern": "1650-01_요구사항정의서_v1.1_page_*.png",
  "output_dir": "ph2-de",
  "output_filename": "spec-design.md"
}
```

### 직접 실행 (테스트용)

```bash
cd /home/ec2-user/mcpsample
uv run mcp-server-req-extractor.py
```

## 출력 예시

생성되는 `spec-design.md` 파일 형식:

```markdown
## 기본 정보
- request_id: req_20260306_001
- project_name: 자산관리시스템 구축

## 요구사항
- 동시접속자: 5000
- RPS: 1000
- 피크 배수: 3.0
- 가용성: 99.9%
- 목표 응답시간(ms): 200

## 애플리케이션
- 타입: java_web
- 프레임워크: spring_boot
- WAR 파일: assetmanagement.war
- 컨텍스트 경로: /asset

## 인프라
- 배포 방식: vm
- 클라우드: AWS
- OS: Amazon Linux 2

## 토폴로지
- 구성: web-was-separated
- 웹서버 대수: 2
- WAS 대수: 2
- 로드밸런서: AWS ALB

## 미들웨어
- 웹서버: apache
- WAS: tomcat
- 연결방식: ajp
- session_clustering: true

## 보안
- SSL: true
- WAF: true
- IP 화이트리스트: false

## 기타
- dev 환경: 필요 (web 1대, was 1대, spec 최소)
```

## 기술 스택

- **Python 3.13+**
- **EasyOCR**: 한글/영어 OCR 엔진
- **MCP SDK**: Model Context Protocol 서버 구현
- **정규식**: 텍스트 파싱 및 정보 추출

## 작동 원리

1. **이미지 검색**: 지정된 디렉토리에서 패턴에 맞는 이미지 파일 검색
2. **OCR 처리**: EasyOCR을 사용하여 각 이미지에서 한글/영어 텍스트 추출
3. **텍스트 파싱**: 정규식을 사용하여 구조화된 정보 추출
   - 기본 정보: 요구사항 ID, 프로젝트명
   - 비기능 요구사항: 동시접속자, RPS, 피크 배수 등
   - 애플리케이션 정보: 타입, 프레임워크, WAR 파일 등
   - 인프라 정보: 클라우드, OS, 배포 방식
   - 토폴로지: 서버 구성, 대수, 로드밸런서
   - 미들웨어: 웹서버, WAS, 연결 방식
   - 보안: SSL, WAF, IP 화이트리스트
4. **포맷 변환**: temp-design.md 포맷에 맞춰 마크다운 생성
5. **파일 저장**: 지정된 경로에 spec-design.md 저장

## 파일 구조

```
/home/ec2-user/mcpsample/
├── mcp-server-req-extractor.py      # MCP 서버 메인 파일
├── mcp-config-req-extractor.json    # MCP 서버 설정 파일
├── MCP_REQ_EXTRACTOR_README.md      # 이 문서
├── file/img/                         # 입력 이미지 디렉토리
│   └── 1650-01_요구사항정의서_v1.1_page_*.png
└── ph2-de/                           # 출력 디렉토리
    └── spec-design.md                # 생성된 요구사항 문서
```

## 문제 해결

### OCR 모델 로딩이 느린 경우
- 첫 실행 시 EasyOCR 모델을 다운로드하므로 시간이 걸릴 수 있습니다
- 이후 실행에서는 캐시된 모델을 사용하여 빠르게 실행됩니다

### 한글 인식이 정확하지 않은 경우
- 이미지 품질을 확인하세요 (해상도, 선명도)
- OCR은 완벽하지 않으므로 생성된 문서를 검토하고 필요시 수정하세요

### 특정 필드가 추출되지 않는 경우
- `mcp-server-req-extractor.py`의 정규식 패턴을 조정하세요
- `extract_field()`, `extract_number()`, `extract_boolean()` 함수 참조

## 라이선스

이 프로젝트는 샘플 코드입니다.

## 작성자

- Jacob Park
- 2026-03-09
