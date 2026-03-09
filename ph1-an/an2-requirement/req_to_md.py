#!/usr/bin/env python3
"""
이미지에서 요구사항 정보를 추출하여 spec-design.md 포맷으로 저장하는 스크립트

입력:
- 이미지: file/img/1650-01_요구사항정의서_v1.1_page_*.png
- 포맷: ph2-de/temp-design.md
- 저장: ph2-de/spec-design.md

처리:
1. 이미지 파일에서 텍스트 추출 (OCR - EasyOCR)
2. temp-design.md 포맷으로 변환
3. ph2-de/spec-design.md 파일로 저장
"""

import os
from pathlib import Path
import easyocr
import re

def extract_text_from_images(image_dir: str, pattern: str) -> dict:
    """이미지 파일들에서 텍스트 추출"""
    print("🔍 이미지 파일 검색 중...")
    image_path = Path(image_dir)
    image_files = sorted(image_path.glob(pattern))
    
    if not image_files:
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_dir}/{pattern}")
    
    print(f"📄 발견된 이미지 파일: {len(image_files)}개")
    for img in image_files:
        print(f"  - {img.name}")
    
    # EasyOCR reader 초기화 (한국어, 영어)
    print("\n🤖 OCR 모델 로딩 중...")
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    
    # 각 이미지에서 텍스트 추출
    extracted_data = {}
    for img_file in image_files:
        print(f"\n📖 텍스트 추출 중: {img_file.name}")
        result = reader.readtext(str(img_file))
        
        # 추출된 텍스트를 하나의 문자열로 결합
        text = '\n'.join([detection[1] for detection in result])
        extracted_data[img_file.name] = text
        
        print(f"  ✓ 추출된 텍스트 길이: {len(text)} 문자")
        print(f"  ✓ 추출된 텍스트 블록 수: {len(result)} 개")
    
    return extracted_data


def extract_images_to_spec():
    """이미지에서 텍스트를 추출하여 spec 포맷으로 저장"""
    
    print("=" * 60)
    print("이미지 → Spec 포맷 변환 시작")
    print("=" * 60)
    
    try:
        # 1. 이미지 파일에서 텍스트 추출
        image_dir = "file/img"
        pattern = "1650-01_요구사항정의서_v1.1_page_*.png"
        extracted_data = extract_text_from_images(image_dir, pattern)
        
        # 전체 텍스트 결합
        combined_text = "\n\n".join(extracted_data.values())
        print(f"\n✅ 총 {len(combined_text)} 문자 추출 완료")
        
        # 2. Spec 포맷으로 변환
        print("\n[3단계] Spec 포맷으로 변환 중...")
        spec_content = generate_spec_format(combined_text, extracted_data)
        
        # 3. 파일로 저장
        print("\n[4단계] 파일 저장 중...")
        output_path = "/home/ec2-user/mcpsample/ph2-de/spec-design.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        print(f"✅ 파일 저장 완료: {output_path}")
        
        print("\n" + "=" * 60)
        print("✅ 이미지 → Spec 포맷 변환 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def generate_spec_format(text: str, extracted_data: dict) -> str:
    """추출된 텍스트를 temp-design.md 포맷으로 변환"""
    
    spec_lines = []
    
    # 기본 정보
    spec_lines.append("## 기본 정보")
    request_id = extract_field(text, r'요청\s*ID|request[_\s]*id', 'req_20260309_001')
    project_name = extract_field(text, r'프로젝트명|project[_\s]*name|시스템명', 'extracted-project')
    spec_lines.append(f"- request_id: {request_id}")
    spec_lines.append(f"- project_name: {project_name}")
    spec_lines.append("")
    
    # 요구사항
    spec_lines.append("## 요구사항")
    concurrent_users = extract_number(text, r'동시\s*접속자|concurrent[_\s]*users', '1000')
    rps = extract_number(text, r'RPS|초당\s*요청', '500')
    peak_multiplier = extract_number(text, r'피크\s*배수|peak[_\s]*multiplier', '2.0')
    availability = extract_field(text, r'가용성|availability', '99.9%')
    response_time = extract_number(text, r'응답\s*시간|response[_\s]*time', '300')
    
    spec_lines.append(f"- 동시접속자: {concurrent_users}")
    spec_lines.append(f"- RPS: {rps}")
    spec_lines.append(f"- 피크 배수: {peak_multiplier}")
    spec_lines.append(f"- 가용성: {availability}")
    spec_lines.append(f"- 목표 응답시간(ms): {response_time}")
    spec_lines.append("")
    
    # 애플리케이션
    spec_lines.append("## 애플리케이션")
    app_type = extract_field(text, r'애플리케이션\s*타입|application[_\s]*type', 'java_web')
    framework = extract_field(text, r'프레임워크|framework', 'spring_boot')
    war_file = extract_field(text, r'WAR\s*파일|war[_\s]*file', 'application.war')
    context_path = extract_field(text, r'컨텍스트\s*경로|context[_\s]*path', '/')
    
    spec_lines.append(f"- 타입: {app_type}")
    spec_lines.append(f"- 프레임워크: {framework}")
    spec_lines.append(f"- WAR 파일: {war_file}")
    spec_lines.append(f"- 컨텍스트 경로: {context_path}")
    spec_lines.append("")
    
    # 인프라
    spec_lines.append("## 인프라")
    deployment = extract_field(text, r'배포\s*방식|deployment', 'vm')
    cloud = extract_field(text, r'클라우드|cloud', 'AWS')
    os = extract_field(text, r'운영체제|OS|operating[_\s]*system', 'Amazon Linux 2')
    
    spec_lines.append(f"- 배포 방식: {deployment}")
    spec_lines.append(f"- 클라우드: {cloud}")
    spec_lines.append(f"- OS: {os}")
    spec_lines.append("")
    
    # 토폴로지
    spec_lines.append("## 토폴로지")
    topology = extract_field(text, r'구성|topology', 'web-was-separated')
    web_count = extract_number(text, r'웹\s*서버\s*대수|web[_\s]*server[_\s]*count', '2')
    was_count = extract_number(text, r'WAS\s*대수|was[_\s]*count', '2')
    lb = extract_field(text, r'로드\s*밸런서|load[_\s]*balancer', 'AWS ALB')
    
    spec_lines.append(f"- 구성: {topology}")
    spec_lines.append(f"- 웹서버 대수: {web_count}")
    spec_lines.append(f"- WAS 대수: {was_count}")
    spec_lines.append(f"- 로드밸런서: {lb}")
    spec_lines.append("")
    
    # 미들웨어
    spec_lines.append("## 미들웨어")
    web_server = extract_field(text, r'웹\s*서버(?!\s*대수)|web[_\s]*server(?!\s*count)', 'apache')
    was = extract_field(text, r'WAS(?!\s*대수)', 'tomcat')
    connection = extract_field(text, r'연결\s*방식|connection[_\s]*type', 'ajp')
    session_clustering = extract_boolean(text, r'세션\s*클러스터링|session[_\s]*clustering')
    
    spec_lines.append(f"- 웹서버: {web_server}")
    spec_lines.append(f"- WAS: {was}")
    spec_lines.append(f"- 연결방식: {connection}")
    spec_lines.append(f"- session_clustering: {session_clustering}")
    spec_lines.append("")
    
    # 보안
    spec_lines.append("## 보안")
    ssl = extract_boolean(text, r'SSL|HTTPS')
    waf = extract_boolean(text, r'WAF|방화벽')
    ip_whitelist = extract_boolean(text, r'IP\s*화이트리스트|IP[_\s]*whitelist')
    
    spec_lines.append(f"- SSL: {ssl}")
    spec_lines.append(f"- WAF: {waf}")
    spec_lines.append(f"- IP 화이트리스트: {ip_whitelist}")
    spec_lines.append("")
    
    # 기타
    spec_lines.append("## 기타")
    dev_env = extract_field(text, r'개발\s*환경|dev[_\s]*environment', '필요')
    spec_lines.append(f"- dev 환경: {dev_env}")
    spec_lines.append("")
    
    # 원본 텍스트 (참고용) - 페이지별로 구분
    spec_lines.append("## 원본 텍스트 (참고)")
    spec_lines.append("")
    for page_name, page_text in extracted_data.items():
        spec_lines.append(f"### {page_name}")
        spec_lines.append("```")
        spec_lines.append(page_text[:1000])  # 각 페이지당 처음 1000자만 포함
        if len(page_text) > 1000:
            spec_lines.append("...")
            spec_lines.append(f"(총 {len(page_text)} 문자)")
        spec_lines.append("```")
        spec_lines.append("")
    
    return '\n'.join(spec_lines)


def extract_field(text, pattern, default=''):
    """정규식 패턴으로 필드 값 추출"""
    try:
        match = re.search(pattern + r'[:\s]+([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    except:
        pass
    return default


def extract_number(text, pattern, default='0'):
    """정규식 패턴으로 숫자 값 추출"""
    try:
        match = re.search(pattern + r'[:\s]+([0-9.,]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    except:
        pass
    return default


def extract_boolean(text, pattern):
    """정규식 패턴으로 boolean 값 추출"""
    try:
        # 패턴 주변 텍스트 검색
        match = re.search(pattern + r'[:\s]*(true|false|yes|no|필요|불필요|사용|미사용)', text, re.IGNORECASE)
        if match:
            value = match.group(1).lower()
            if value in ['true', 'yes', '필요', '사용']:
                return 'true'
            elif value in ['false', 'no', '불필요', '미사용']:
                return 'false'
    except:
        pass
    return 'false'


if __name__ == "__main__":
    exit(extract_images_to_spec())
