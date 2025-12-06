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
