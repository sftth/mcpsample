"""convert_pdf_to_img.py

Convert PDF pages to PNG or JPG images.

Dependencies:
  pip install pymupdf pillow

Notes:
  - PyMuPDF (pymupdf) renders PDF pages without external poppler dependency.
  - Output files will be named <pdfname>_page_001.png (or .jpg).

Usage example:
  python convert_pdf_to_img.py input.pdf --out-dir out_images --format jpg --dpi 150 --quality 85

"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception as e:
    raise SystemExit("Missing dependency 'pymupdf'. Install with: pip install pymupdf")

try:
    from PIL import Image
except Exception:
    raise SystemExit("Missing dependency 'Pillow'. Install with: pip install pillow")

try:
    from mcp.server.fastmcp import FastMCP
except Exception:
    # fallback to fastmcp package name if installed differently
    try:
        from fastmcp import FastMCP
    except Exception:
        raise SystemExit("Missing dependency 'fastmcp' (for MCP server). Install with: pip install fastmcp")


def _ensure_out_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _to_int_or_default(x, default=0):
    try:
        return int(x)
    except Exception:
        return default


def convert(pdf_path: str, out_dir: str | None = None, fmt: str = "png", dpi: int = 150, start: int | None = None, end: int | None = None, quality: int = 85) -> list[str]:
    """Convert PDF pages to images.

    Args:
        pdf_path: Path to PDF file.
        out_dir: Directory to save images. Defaults to same dir as PDF + '/images'.
        fmt: 'png' or 'jpg'.
        dpi: Rendering DPI (pixels per inch).
        start: 1-based start page (inclusive). If None, starts at 1.
        end: 1-based end page (inclusive). If None, goes to last page.
        quality: JPEG quality (1-95), ignored for PNG.

    Returns:
        List of output file paths.
    """
    pdf = Path(pdf_path)
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf}")

    if fmt.lower() not in ("png", "jpg", "jpeg"):
        raise ValueError("format must be 'png' or 'jpg'")

    out_dir_path = Path(out_dir) if out_dir else pdf.parent / (pdf.stem + "_images")
    _ensure_out_dir(out_dir_path)

    doc = fitz.open(str(pdf_path))
    page_count = doc.page_count

    s = 1 if start is None else max(1, _to_int_or_default(start, 1))
    e = page_count if end is None else min(page_count, _to_int_or_default(end, page_count))
    if s > e:
        raise ValueError("start page must be <= end page")

    # scale matrix: zoom = dpi/72
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    out_files: list[str] = []
    for i in range(s - 1, e):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Create PIL Image from pixmap
        mode = "RGB"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)

        seq = str(i + 1).zfill(max(3, int(math.log10(page_count)) + 1))
        out_name = f"{pdf.stem}_page_{seq}.{('jpg' if fmt.lower() in ('jpg','jpeg') else 'png')}"
        out_path = out_dir_path / out_name

        if fmt.lower() in ("png",):
            img.save(out_path, format="PNG")
        else:
            q = max(1, min(95, int(quality)))
            img = img.convert("RGB")
            img.save(out_path, format="JPEG", quality=q, optimize=True)

        out_files.append(str(out_path))

    doc.close()
    return out_files


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Convert PDF pages to PNG or JPG images")
    p.add_argument("pdf", help="Input PDF file path")
    p.add_argument("--out-dir", help="Output directory (default: <pdf>_images)")
    p.add_argument("--format", choices=["png", "jpg"], default="png", help="Output image format")
    p.add_argument("--dpi", type=int, default=150, help="Render DPI (default 150)")
    p.add_argument("--start", type=int, help="1-based start page (inclusive)")
    p.add_argument("--end", type=int, help="1-based end page (inclusive)")
    p.add_argument("--quality", type=int, default=85, help="JPEG quality 1-95 (only for jpg)")
    return p


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        out = convert(args.pdf, args.out_dir, args.format, args.dpi, args.start, args.end, args.quality)
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1)

    print(f"Saved {len(out)} images to {args.out_dir or (Path(args.pdf).parent / (Path(args.pdf).stem + '_images'))}")


# --- MCP server setup (stdio transport) ---
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP()


@mcp.tool()
def convert_pdf(pdf: str, out_dir: str | None = None, fmt: str = "png", dpi: int = 150, start: int | None = None, end: int | None = None, quality: int = 85) -> list[str]:
    """Convert PDF to images via MCP tool.

    Args align with the CLI `convert()` function. `pdf` is a path to the file on disk.
    Returns list of written file paths.
    """
    return convert(pdf, out_dir, fmt, dpi, start, end, quality)


if __name__ == "__main__":
    # Run as MCP stdio server
    mcp.run()
