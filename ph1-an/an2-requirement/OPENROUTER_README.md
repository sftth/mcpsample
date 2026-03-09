# Requirements Extractor MCP Server (OpenRouter Version)

이미지에서 요구사항을 추출하여 spec-design.md를 생성하는 MCP 서버입니다.
OpenRouter API를 통해 Claude Sonnet 4.5 모델을 사용합니다.

## 주요 변경사항

### EasyOCR 버전 → OpenRouter 버전

**이전 (EasyOCR):**
- EasyOCR 라이브러리를 사용하여 이미지에서 텍스트 추출
- 정규식 기반으로 요구사항 파싱
- 로컬에서 실행되어 API 비용 없음
- 한글 인식 정확도가 낮을 수 있음

**현재 (OpenRouter/Claude Sonnet 4.5):**
- Claude Sonnet 4.5를 사용하여 이미지에서 텍스트 추출
- AI 기반으로 각 섹션별 요구사항 분석
- API 호출 비용 발생
- 높은 정확도와 문맥 이해

## 설치 및 설정

### 1. 필수 패키지 설치

```bash
# httpx 패키지 추가 (비동기 HTTP 클라이언트)
uv add httpx
```

### 2. OpenRouter API 키 설정

OpenRouter API 키를 환경변수로 설정해야 합니다:

```bash
# ~/.bashrc 또는 ~/.bash_profile에 추가
export OPENROUTER_API_KEY="your-api-key-here"

# 또는 현재 세션에서만 사용
export OPENROUTER_API_KEY="your-api-key-here"
```

**API 키 발급 방법:**
1. https://openrouter.ai/ 접속
2. 회원가입 및 로그인
3. API Keys 메뉴에서 새 키 생성
4. 크레딧 충전 (사용량에 따라 과금)

### 3. MCP 설정 파일 업데이트

`cline_mcp_settings.json` 파일이 다음과 같이 설정되어 있는지 확인:

```json
{
  "mcpServers": {
    "requirements-extractor": {
      "command": "uv",
      "args": ["run", "/home/ec2-user/mcpsample/ph1-an/an2-requirement/mcp-server-req-extractor-openrouter.py"],
      "cwd": "/home/ec2-user/mcpsample",
      "env": {
        "MCP_BASE_DIR": "/home/ec2-user/mcpsample",
        "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}"
      },
      "description": "이미지에서 요구사항을 추출하여 spec-design.md를 생성하는 MCP 서버 (OpenRouter/Claude Sonnet 4.5)"
    }
  }
}
```

## 사용 방법

### MCP Tool 사용

```python
# MCP 클라이언트에서 호출
result = await mcp_client.call_tool(
    "extract_requirements_from_images",
    {
        "image_dir": "file/img",
        "image_pattern": "1650-01_요구사항정의서_v1.1_page_*.png",
        "output_dir": "ph2-de",
        "output_filename": "spec-design.md"
    }
)
```

### 직접 실행 (테스트용)

```bash
cd /home/ec2-user/mcpsample
export OPENROUTER_API_KEY="your-api-key-here"
uv run ph1-an/an2-requirement/mcp-server-req-extractor-openrouter.py
```

## 작동 방식

1. **이미지 검색**: 지정된 디렉토리에서 패턴에 맞는 이미지 파일 검색
2. **텍스트 추출**: 각 이미지를 Claude Sonnet 4.5에 전송하여 텍스트 추출
3. **섹션별 분석**: 추출된 텍스트를 8개 섹션으로 분류하여 분석
   - 기본정보
   - 비기능 요구사항
   - 애플리케이션
   - 인프라
   - 토폴로지
   - 미들웨어
   - 보안
   - 기타
4. **문서 생성**: 분석 결과를 마크다운 형식으로 저장

## API 비용

OpenRouter를 통한 Claude Sonnet 4.5 사용 비용:
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens

예상 비용 (6페이지 이미지 기준):
- 이미지 → 텍스트 추출: 6회 API 호출
- 섹션별 분석: 8회 API 호출
- 총 14회 API 호출
- 예상 비용: $0.10 ~ $0.50 (이미지 크기와 텍스트 양에 따라 다름)

## 장단점 비교

### OpenRouter 버전 장점
✅ 높은 텍스트 인식 정확도 (특히 한글)
✅ 문맥 이해를 통한 지능적인 정보 추출
✅ 복잡한 레이아웃도 정확하게 파싱
✅ 정규식 패턴 유지보수 불필요

### OpenRouter 버전 단점
❌ API 비용 발생
❌ 인터넷 연결 필요
❌ API 응답 시간으로 인한 처리 속도 저하
❌ API 키 관리 필요

### EasyOCR 버전 장점
✅ 무료 (로컬 실행)
✅ 오프라인 사용 가능
✅ 빠른 처리 속도

### EasyOCR 버전 단점
❌ 한글 인식 정확도 낮음
❌ 정규식 패턴 유지보수 필요
❌ 복잡한 레이아웃 처리 어려움

## 문제 해결

### API 키 오류
```
Error: OPENROUTER_API_KEY not set
```
→ 환경변수가 설정되지 않았습니다. 위의 "2. OpenRouter API 키 설정" 참조

### 네트워크 오류
```
Error: Connection timeout
```
→ 인터넷 연결을 확인하거나 timeout 값을 늘려보세요 (현재 60초)

### 이미지 파일 없음
```
FileNotFoundError: 이미지 파일을 찾을 수 없습니다
```
→ image_dir과 image_pattern이 올바른지 확인하세요

## 참고 자료

- OpenRouter 공식 문서: https://openrouter.ai/docs
- Claude API 문서: https://docs.anthropic.com/
- MCP 프로토콜: https://modelcontextprotocol.io/
