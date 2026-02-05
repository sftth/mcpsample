# MCP Sample

Sample implementation of MCP (Model Context Protocol) servers using FastMCP.

## Overview

This repository contains example MCP servers demonstrating different transport methods:

- `server-stdio.py` - MCP server using stdio transport
- `server.py` - MCP server using HTTP transport

Both servers implement a simple `add` tool that adds two numbers together.

## Installation

```bash
pip install fastmcp
```

## Usage

### stdio Transport

```bash
python server-stdio.py
```

### HTTP Transport

```bash
python server.py
```

The HTTP server runs on `http://0.0.0.0:9999`

## Features

- Simple addition tool example
- Demonstrates both stdio and HTTP transports
- Built with FastMCP framework

## PDF 변환 사용 예시

PDF 파일을 이미지로 변환하는 간단한 스크립트(`convert_pdf_to_img.py`)를 추가했습니다. PyMuPDF(`pymupdf`)와 Pillow가 필요합니다.

설치:

```bash
pip install pymupdf pillow
```

예시 실행:

```bash
python convert_pdf_to_img.py sample.pdf --out-dir out_images --format jpg --dpi 150 --quality 85
```

출력 파일 이름 예시: `sample_page_001.jpg`, `sample_page_002.jpg`, ...

