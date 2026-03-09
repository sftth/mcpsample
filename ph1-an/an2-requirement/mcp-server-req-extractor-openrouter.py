#!/usr/bin/env python3
"""
MCP Server: Requirements Extractor (OpenRouter Version)
이미지에서 요구사항을 추출하여 spec-design.md를 생성하는 MCP 서버
OpenRouter API를 통해 Claude Sonnet 4.5 모델 사용
"""

import asyncio
import json
import os
import base64
from pathlib import Path
from typing import Any
import httpx

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

# OpenRouter API 설정
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "anthropic/claude-sonnet-4.5"


def encode_image_to_base64(image_path: Path) -> str:
    """이미지를 base64로 인코딩"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


async def extract_text_from_image_with_claude(image_path: Path) -> str:
    """Claude API를 사용하여 이미지에서 텍스트 추출"""
    
    # 이미지를 base64로 인코딩
    base64_image = encode_image_to_base64(image_path)
    
    # 이미지 확장자 확인
    image_ext = image_path.suffix.lower()
    media_type = "image/png" if image_ext == ".png" else "image/jpeg"
    
    # OpenRouter API 요청
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/sftth/mcpsample",
        "X-Title": "Requirements Extractor MCP"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "이 이미지에서 모든 텍스트를 추출해주세요. 한글과 영어 모두 정확하게 추출하고, 원본 텍스트 그대로 반환해주세요."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4000
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # 응답에서 텍스트 추출
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise ValueError("API 응답에서 텍스트를 찾을 수 없습니다")


async def extract_text_from_images(image_dir: str, pattern: str) -> dict:
    """이미지 파일들에서 텍스트 추출 (Claude API 사용)"""
    image_path = Path(image_dir)
    image_files = sorted(image_path.glob(pattern))
    
    if not image_files:
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_dir}/{pattern}")
    
    # 각 이미지에서 텍스트 추출
    extracted_data = {}
    for img_file in image_files:
        text = await extract_text_from_image_with_claude(img_file)
        extracted_data[img_file.name] = text
    
    return extracted_data


async def analyze_requirements_with_claude(combined_text: str, section: str) -> str:
    """Claude API를 사용하여 특정 섹션의 요구사항 분석"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/sftth/mcpsample",
        "X-Title": "Requirements Extractor MCP"
    }
    
    prompt = f"""다음 텍스트에서 "{section}" 관련 정보를 추출하여 아래 포맷으로 정리해주세요:

## {section}
- 항목1: 정보1
- 항목2: 정보2

텍스트:
{combined_text}

주의사항:
1. 정확한 정보만 추출하세요
2. 정보가 없으면 기본값을 사용하세요
3. 마크다운 포맷을 정확히 지켜주세요
"""
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise ValueError("API 응답에서 텍스트를 찾을 수 없습니다")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """사용 가능한 도구 목록 반환"""
    return [
        Tool(
            name="extract_requirements_from_images",
            description="이미지 파일에서 요구사항을 추출하여 spec-design.md 파일을 생성합니다. "
                       "OpenRouter API를 통해 Claude Sonnet 4.5를 사용하여 이미지에서 텍스트를 추출하고, "
                       "각 섹션별로 요구사항을 분석하여 구조화된 문서를 생성합니다.",
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
        
        extracted_data = await extract_text_from_images(image_dir, image_pattern)
        
        result_text += f"✅ {len(extracted_data)}개의 이미지에서 텍스트 추출 완료\n"
        for img_name in extracted_data.keys():
            result_text += f"   - {img_name}\n"
        
        # 전체 텍스트 결합
        combined_text = "\n\n".join(extracted_data.values())
        result_text += f"\n📝 총 {len(combined_text)} 문자 추출\n\n"
        
        # 2. 각 섹션별로 요구사항 분석
        sections = [
            "기본정보",
            "비기능 요구사항",
            "애플리케이션",
            "인프라",
            "토폴로지",
            "미들웨어",
            "보안",
            "기타"
        ]
        
        spec_content = ""
        for section in sections:
            result_text += f"🔄 {section} 분석 중...\n"
            section_content = await analyze_requirements_with_claude(combined_text, section)
            spec_content += section_content + "\n\n"
        
        # 3. 파일로 저장
        output_path = Path(output_dir) / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        result_text += f"\n✅ 파일 저장 완료: {output_path}\n\n"
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
                server_version="2.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
