#!/usr/bin/env python3
"""
MCP Server: Requirements Extractor
이미지에서 요구사항을 추출하여 spec-design.md를 생성하는 MCP 서버
"""

import asyncio
import json
from pathlib import Path
from typing import Any
import easyocr
import re

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# MCP 서버 인스턴스 생성
server = Server("requirements-extractor")

# EasyOCR reader (전역 변수로 한 번만 로드)
reader = None


def get_reader():
    """OCR reader를 lazy loading"""
    global reader
    if reader is None:
        reader = easyocr.Reader(['ko', 'en'], gpu=False)
    return reader


def extract_text_from_images(image_dir: str, pattern: str) -> dict:
    """이미지 파일들에서 텍스트 추출"""
    image_path = Path(image_dir)
    image_files = sorted(image_path.glob(pattern))
    
    if not image_files:
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_dir}/{pattern}")
    
    ocr_reader = get_reader()
    
    # 각 이미지에서 텍스트 추출
    extracted_data = {}
    for img_file in image_files:
        result = ocr_reader.readtext(str(img_file))
        text = '\n'.join([detection[1] for detection in result])
        extracted_data[img_file.name] = text
    
    return extracted_data


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


def generate_spec_format(text: str, extracted_data: dict) -> str:
    """추출된 텍스트를 spec-design.md 포맷으로 변환"""
    
    spec_lines = []
    
    # 기본 정보
    spec_lines.append("## 기본 정보")
    request_id = extract_field(text, r'요청\s*ID|요구사항\s*아이디|request[_\s]*id', 'req_unknown')
    project_name = extract_field(text, r'프로젝트명|프로직트|project[_\s]*name|시스템명', 'unknown-project')
    spec_lines.append(f"- request_id: {request_id}")
    spec_lines.append(f"- project_name: {project_name}")
    spec_lines.append("")
    
    # 요구사항 (비기능 요구사항)
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
    app_type = extract_field(text, r'타입.*?java|애플리케이션\s*타입', 'java_web')
    framework = extract_field(text, r'프레임워크|프레임위크|framework', 'spring_boot')
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
    cloud = extract_field(text, r'플라우드|클라우드|cloud', 'AWS')
    os = extract_field(text, r'OS|운영체제|operating[_\s]*system', 'Amazon Linux 2')
    
    spec_lines.append(f"- 배포 방식: {deployment}")
    spec_lines.append(f"- 클라우드: {cloud}")
    spec_lines.append(f"- OS: {os}")
    spec_lines.append("")
    
    # 토폴로지
    spec_lines.append("## 토폴로지")
    topology = extract_field(text, r'구성|topology', 'web-was-separated')
    web_count = extract_number(text, r'웹\s*서버\s*대수|월서버.*?대수|web[_\s]*server[_\s]*count', '2')
    was_count = extract_number(text, r'WAS\s*대수|was[_\s]*count', '2')
    lb = extract_field(text, r'로드\s*밸런서|로드\s*뱉런서|load[_\s]*balancer', 'AWS ALB')
    
    spec_lines.append(f"- 구성: {topology}")
    spec_lines.append(f"- 웹서버 대수: {web_count}")
    spec_lines.append(f"- WAS 대수: {was_count}")
    spec_lines.append(f"- 로드밸런서: {lb}")
    spec_lines.append("")
    
    # 미들웨어
    spec_lines.append("## 미들웨어")
    web_server = extract_field(text, r'Web\s*Server.*?apache|웹\s*서버.*?apache', 'apache')
    was = extract_field(text, r'WAS.*?tomcat', 'tomcat')
    connection = extract_field(text, r'연결\s*방식|connection[_\s]*type', 'ajp')
    session_clustering = extract_boolean(text, r'session\s*clustering|세션\s*클러스터링')
    
    spec_lines.append(f"- 웹서버: {web_server}")
    spec_lines.append(f"- WAS: {was}")
    spec_lines.append(f"- 연결방식: {connection}")
    spec_lines.append(f"- session_clustering: {session_clustering}")
    spec_lines.append("")
    
    # 보안
    spec_lines.append("## 보안")
    ssl = extract_boolean(text, r'SSL')
    waf = extract_boolean(text, r'WAF')
    ip_whitelist = extract_boolean(text, r'IP\s*화이트리스트|IP\s*하이트리스트|IP[_\s]*whitelist')
    
    spec_lines.append(f"- SSL: {ssl}")
    spec_lines.append(f"- WAF: {waf}")
    spec_lines.append(f"- IP 화이트리스트: {ip_whitelist}")
    spec_lines.append("")
    
    # 기타
    spec_lines.append("## 기타")
    dev_env_match = re.search(r'dev\s*환경.*?필요.*?([^\n]+)', text, re.IGNORECASE)
    if dev_env_match:
        dev_env = f"필요 ({dev_env_match.group(1).strip()})"
    else:
        dev_env = "필요"
    spec_lines.append(f"- dev 환경: {dev_env}")
    spec_lines.append("")
    
    return '\n'.join(spec_lines)


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """사용 가능한 도구 목록 반환"""
    return [
        Tool(
            name="extract_requirements_from_images",
            description="이미지 파일에서 요구사항을 추출하여 spec-design.md 파일을 생성합니다. "
                       "EasyOCR을 사용하여 한글/영어 텍스트를 추출하고, 정규식으로 파싱하여 구조화된 문서를 생성합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_dir": {
                        "type": "string",
                        "description": "이미지 파일이 있는 디렉토리 경로 (예: file/img)",
                        "default": "file/img"
                    },
                    "image_pattern": {
                        "type": "string",
                        "description": "이미지 파일 패턴 (예: 1650-01_요구사항정의서_v1.1_page_*.png)",
                        "default": "1650-01_요구사항정의서_v1.1_page_*.png"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "출력 파일을 저장할 디렉토리 (예: ph2-de)",
                        "default": "ph2-de"
                    },
                    "output_filename": {
                        "type": "string",
                        "description": "출력 파일명 (예: spec-design.md)",
                        "default": "spec-design.md"
                    }
                },
                "required": ["image_dir", "image_pattern", "output_dir", "output_filename"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """도구 호출 처리"""
    
    if name != "extract_requirements_from_images":
        raise ValueError(f"Unknown tool: {name}")
    
    if not arguments:
        raise ValueError("Missing arguments")
    
    # 인자 추출
    image_dir = arguments.get("image_dir", "file/img")
    image_pattern = arguments.get("image_pattern", "1650-01_요구사항정의서_v1.1_page_*.png")
    output_dir = arguments.get("output_dir", "ph2-de")
    output_filename = arguments.get("output_filename", "spec-design.md")
    
    try:
        # 1. 이미지에서 텍스트 추출
        result_text = f"🔍 이미지 파일 검색 중...\n"
        result_text += f"   경로: {image_dir}/{image_pattern}\n\n"
        
        extracted_data = extract_text_from_images(image_dir, image_pattern)
        
        result_text += f"✅ {len(extracted_data)}개의 이미지에서 텍스트 추출 완료\n"
        for img_name in extracted_data.keys():
            result_text += f"   - {img_name}\n"
        
        # 전체 텍스트 결합
        combined_text = "\n\n".join(extracted_data.values())
        result_text += f"\n📝 총 {len(combined_text)} 문자 추출\n\n"
        
        # 2. Spec 포맷으로 변환
        result_text += "🔄 Spec 포맷으로 변환 중...\n"
        spec_content = generate_spec_format(combined_text, extracted_data)
        
        # 3. 파일로 저장
        output_path = Path(output_dir) / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        result_text += f"✅ 파일 저장 완료: {output_path}\n\n"
        result_text += "=" * 60 + "\n"
        result_text += "생성된 spec-design.md 내용:\n"
        result_text += "=" * 60 + "\n"
        result_text += spec_content
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        error_msg = f"❌ 오류 발생: {str(e)}\n"
        import traceback
        error_msg += traceback.format_exc()
        return [TextContent(type="text", text=error_msg)]


async def main():
    """MCP 서버 실행"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="requirements-extractor",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
