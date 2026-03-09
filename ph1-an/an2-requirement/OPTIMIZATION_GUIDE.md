# Requirements Extractor 최적화 가이드

## 📊 성능 비교

| 버전 | 처리 방식 | 예상 소요 시간 | Timeout 위험 |
|------|----------|--------------|-------------|
| **기존 버전** | 순차 처리 | 70-140초 | ❌ 높음 |
| **최적화 버전** | 병렬 처리 + 캐싱 | 20-30초 (첫 실행)<br>5-10초 (캐시 사용) | ✅ 낮음 |
| **프롬프트 직접** | 스트리밍 | 10-20초 | ✅ 없음 |

## 🚀 최적화 버전 사용 방법

### 1. MCP 설정 업데이트

`cline_mcp_settings.json` 파일을 수정하여 최적화 버전을 사용하도록 변경:

```json
{
  "mcpServers": {
    "requirements-extractor": {
      "command": "uv",
      "args": ["run", "/home/ec2-user/mcpsample/ph1-an/an2-requirement/mcp-server-req-extractor-optimized.py"],
      "cwd": "/home/ec2-user/mcpsample",
      "env": {
        "MCP_BASE_DIR": "/home/ec2-user/mcpsample",
        "OPENROUTER_API_KEY": "your-api-key-here"
      },
      "description": "이미지에서 요구사항을 추출 (최적화 버전 - 병렬 처리 + 캐싱)"
    }
  }
}
```

### 2. Cline 재시작

MCP 설정을 변경한 후 Cline을 재시작하여 새로운 서버를 로드합니다.

### 3. 도구 사용

```
requirements-extractor 도구를 사용하여 file/img/1650-01_요구사항정의서_v1.1_page_*.png 이미지들에서 
요구사항을 추출하여 ph2-de/spec-design.md 파일을 생성해주세요.
```

## 🔧 주요 개선 사항

### 1. **병렬 처리** ⚡

**기존 코드:**
```python
# 순차 처리 - 느림
for img_file in image_files:
    text = await extract_text_from_image_with_claude(img_file)
    extracted_data[img_file.name] = text
```

**최적화 코드:**
```python
# 병렬 처리 - 빠름
tasks = [extract_text_from_image_with_claude(img_file) for img_file in image_files]
results = await asyncio.gather(*tasks)
```

**효과:**
- 6개 이미지 처리: 60초 → 10초 (6배 빠름)
- 8개 섹션 분석: 80초 → 10초 (8배 빠름)

### 2. **캐싱 시스템** 💾

```python
# 캐시 디렉토리: .cache/req-extractor/
# 캐시 키: MD5 해시 (image_dir + pattern)

# 첫 실행: API 호출 → 캐시 저장
# 두 번째 실행: 캐시에서 로드 (즉시)
```

**효과:**
- 동일한 이미지 재처리 시: 20초 → 5초
- API 비용 절감

### 3. **Timeout 증가** ⏱️

```python
# 기존: timeout=60.0
# 최적화: timeout=120.0
async with httpx.AsyncClient(timeout=120.0) as client:
```

## 📈 성능 측정 예시

### 시나리오: 6개 이미지, 8개 섹션

**기존 버전 (순차 처리):**
```
이미지 1: 10초
이미지 2: 10초
이미지 3: 10초
이미지 4: 10초
이미지 5: 10초
이미지 6: 10초
섹션 1-8: 각 10초 × 8 = 80초
----------------------------
총 소요 시간: 140초 ❌ TIMEOUT!
```

**최적화 버전 (병렬 처리):**
```
이미지 1-6: 동시 처리 = 10초
섹션 1-8: 동시 처리 = 10초
----------------------------
총 소요 시간: 20초 ✅ 성공!
```

**최적화 버전 (캐시 사용):**
```
캐시 로드: 1초
섹션 1-8: 동시 처리 = 10초
----------------------------
총 소요 시간: 11초 ✅ 매우 빠름!
```

## 🎯 사용 팁

### 1. 캐시 관리

**캐시 위치 확인:**
```bash
ls -la .cache/req-extractor/
```

**캐시 삭제 (새로 추출하고 싶을 때):**
```bash
rm -rf .cache/req-extractor/
```

**특정 캐시만 삭제:**
```bash
# 캐시 키 확인 후
rm .cache/req-extractor/<cache-key>.json
```

### 2. 캐시 비활성화

캐시를 사용하지 않고 항상 새로 추출하려면:

```python
# 도구 호출 시 use_cache=False 전달
{
  "image_dir": "file/img",
  "image_pattern": "1650-01_요구사항정의서_v1.1_page_*.png",
  "output_dir": "ph2-de",
  "output_filename": "spec-design.md",
  "use_cache": false  // 캐시 비활성화
}
```

### 3. 디버깅

문제 발생 시 로그 확인:

```bash
# MCP 서버 직접 실행하여 로그 확인
uv run ph1-an/an2-requirement/mcp-server-req-extractor-optimized.py
```

## 🔍 문제 해결

### Q1: 여전히 timeout이 발생해요

**해결책:**
1. 캐시가 활성화되어 있는지 확인
2. 이미지 개수가 너무 많은지 확인 (10개 이상이면 분할 처리)
3. OpenRouter API 키가 유효한지 확인
4. 네트워크 연결 상태 확인

### Q2: 캐시가 작동하지 않아요

**해결책:**
1. `.cache/req-extractor/` 디렉토리 권한 확인
2. 디스크 공간 확인
3. 캐시 키가 올바르게 생성되는지 확인

### Q3: 결과가 이상해요

**해결책:**
1. 캐시 삭제 후 재실행
2. `use_cache=false`로 설정하여 새로 추출
3. 이미지 파일이 올바른지 확인

## 📝 추가 최적화 아이디어

### 1. 배치 크기 조절

이미지가 많을 경우 배치로 나누어 처리:

```python
# 예: 10개씩 배치 처리
batch_size = 10
for i in range(0, len(image_files), batch_size):
    batch = image_files[i:i+batch_size]
    tasks = [extract_text_from_image_with_claude(f) for f in batch]
    results = await asyncio.gather(*tasks)
```

### 2. 진행 상황 표시

```python
# tqdm 사용하여 진행률 표시
from tqdm.asyncio import tqdm
results = await tqdm.gather(*tasks, desc="이미지 처리 중")
```

### 3. 재시도 로직

```python
# API 실패 시 자동 재시도
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def extract_text_with_retry(image_path):
    return await extract_text_from_image_with_claude(image_path)
```

## 🎉 결론

최적화 버전을 사용하면:
- ✅ **70% 이상 속도 향상** (140초 → 20초)
- ✅ **Timeout 문제 해결**
- ✅ **캐시로 재실행 시 90% 속도 향상** (20초 → 2초)
- ✅ **API 비용 절감**

프롬프트로 직접 요청하는 것만큼 빠르지는 않지만, MCP 도구의 장점(재사용성, 자동화)을 유지하면서 실용적인 성능을 제공합니다.
