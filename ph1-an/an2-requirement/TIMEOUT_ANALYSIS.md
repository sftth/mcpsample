# Requirements Extractor MCP Timeout 분석

## 문제 상황
프롬프트로 직접 요청하면 빠르게 처리되는데, MCP 도구(`requirements-extractor`)를 사용하면 timeout이 발생합니다.

## 원인 분석

### 1. **순차적 API 호출 구조** ⚠️ 주요 원인
현재 MCP 서버는 다음과 같이 동작합니다:

```python
# 1단계: 각 이미지마다 텍스트 추출 (순차 처리)
for img_file in image_files:
    text = await extract_text_from_image_with_claude(img_file)  # API 호출 1
    extracted_data[img_file.name] = text

# 2단계: 각 섹션마다 분석 (순차 처리)
for section in sections:  # 8개 섹션
    section_content = await analyze_requirements_with_claude(combined_text, section)  # API 호출 2
    spec_content += section_content + "\n\n"
```

**총 API 호출 횟수**: 이미지 개수 + 8개 섹션
- 예: 6개 이미지 → 6 + 8 = **14번의 순차적 API 호출**
- 각 API 호출당 평균 5-10초 소요
- **총 소요 시간: 70-140초** (timeout 발생!)

### 2. **프롬프트 직접 사용 시의 차이점** ✅
프롬프트로 직접 요청하면:
- **단일 대화 세션**에서 모든 이미지를 한 번에 처리
- Claude가 **컨텍스트를 유지**하면서 연속 처리
- 중간 API 호출 없이 **스트리밍 방식**으로 응답
- 총 소요 시간: 10-20초

### 3. **MCP 도구의 제약사항**
- MCP 도구는 **동기적으로 완료**되어야 함
- 중간 진행 상황을 사용자에게 보여줄 수 없음
- 모든 처리가 끝날 때까지 대기
- Cline의 기본 timeout (보통 60-120초)을 초과

## 해결 방안

### 방안 1: **병렬 처리로 최적화** (권장) ⭐
```python
# 이미지 텍스트 추출을 병렬로 처리
tasks = [extract_text_from_image_with_claude(img_file) for img_file in image_files]
results = await asyncio.gather(*tasks)

# 섹션 분석도 병렬로 처리
section_tasks = [analyze_requirements_with_claude(combined_text, section) for section in sections]
section_results = await asyncio.gather(*section_tasks)
```

**예상 효과**:
- 이미지 6개 병렬 처리: 10초
- 섹션 8개 병렬 처리: 10초
- **총 소요 시간: 약 20-30초** ✅

### 방안 2: **단일 API 호출로 통합**
모든 이미지와 섹션을 하나의 프롬프트로 처리:
```python
# 모든 이미지를 한 번에 전송하고, 모든 섹션을 한 번에 요청
payload = {
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "다음 이미지들에서 8개 섹션 추출..."},
            *[{"type": "image_url", "image_url": {...}} for img in images]
        ]
    }]
}
```

**예상 효과**:
- API 호출 1회
- **총 소요 시간: 15-25초** ✅

### 방안 3: **Timeout 설정 증가** (임시 방편)
```python
# httpx timeout 증가
async with httpx.AsyncClient(timeout=300.0) as client:  # 60초 → 300초
```

**단점**: 근본적인 해결책이 아님

### 방안 4: **캐싱 전략**
```python
# 이미 추출한 이미지는 캐시에서 재사용
cache_file = Path(f".cache/{image_pattern}.json")
if cache_file.exists():
    extracted_data = json.loads(cache_file.read_text())
else:
    extracted_data = await extract_text_from_images(...)
    cache_file.write_text(json.dumps(extracted_data))
```

## 권장 해결책

**최적의 조합**: 방안 1 (병렬 처리) + 방안 4 (캐싱)

### 구현 예시:
```python
async def extract_requirements_optimized(image_dir, pattern, sections):
    # 1. 캐시 확인
    cache_key = f"{image_dir}_{pattern}"
    cached_text = load_from_cache(cache_key)
    
    if not cached_text:
        # 2. 병렬로 이미지 텍스트 추출
        image_files = sorted(Path(image_dir).glob(pattern))
        tasks = [extract_text_from_image_with_claude(f) for f in image_files]
        results = await asyncio.gather(*tasks)
        combined_text = "\n\n".join(results)
        save_to_cache(cache_key, combined_text)
    else:
        combined_text = cached_text
    
    # 3. 병렬로 섹션 분석
    section_tasks = [
        analyze_requirements_with_claude(combined_text, section) 
        for section in sections
    ]
    section_results = await asyncio.gather(*section_tasks)
    
    return "\n\n".join(section_results)
```

## 비교표

| 방식 | API 호출 횟수 | 소요 시간 | Timeout 위험 |
|------|--------------|----------|-------------|
| 현재 MCP (순차) | 14회 | 70-140초 | ❌ 높음 |
| 병렬 처리 | 14회 (동시) | 20-30초 | ✅ 낮음 |
| 단일 API 호출 | 1회 | 15-25초 | ✅ 매우 낮음 |
| 프롬프트 직접 | 1회 (스트리밍) | 10-20초 | ✅ 없음 |

## 결론

MCP 도구가 timeout되는 이유는 **순차적인 다중 API 호출** 때문입니다. 
프롬프트로 직접 요청하면 단일 세션에서 스트리밍 방식으로 처리되어 빠르지만, 
MCP 도구는 각 단계마다 별도의 API 호출을 하고 완료를 기다려야 하므로 시간이 오래 걸립니다.

**즉시 적용 가능한 해결책**: 병렬 처리 구현 (소요 시간 70% 감소)
