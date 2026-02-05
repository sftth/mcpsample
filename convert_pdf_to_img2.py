import base64
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import fitz  # PyMuPDF
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("convertor")

DOWNLOADS_DIR = Path("/Users/summit/Downloads").expanduser().resolve()


def _safe_pdf_filename(name: str) -> str:
    """
    Accepts:
      - "sample.pdf"
      - "sample"  (auto adds .pdf)
    Rejects path traversal or subpaths (e.g., "../", "/tmp/a.pdf", "a/b.pdf").
    """
    name = name.strip()

    if not name:
        raise ValueError("filename is empty")

    # Disallow any path components
    p = Path(name)
    if p.name != name:
        raise ValueError("filename must not include a path. Use only the file name, e.g., 'sample.pdf'.")

    # Ensure extension
    if not name.lower().endswith(".pdf"):
        name = name + ".pdf"

    return name


def _pdf_to_png_first_page(pdf_path: Path, png_path: Path, dpi: int = 200) -> None:
    doc = fitz.open(str(pdf_path))
    if doc.page_count < 1:
        raise ValueError("PDF has no pages.")

    page = doc.load_page(0)  # first page
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    pix = page.get_pixmap(matrix=mat, alpha=False)
    # Normalize CMYK etc. to RGB
    if pix.n >= 5:
        pix = fitz.Pixmap(fitz.csRGB, pix)

    png_bytes = pix.tobytes("png")
    png_path.write_bytes(png_bytes)


def _png_file_to_data_url(png_path: Path) -> str:
    b64 = base64.b64encode(png_path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


@mcp.tool()
def convert_pdf_in_downloads_to_png(
    filename: str,
    dpi: int = 200,
    overwrite: bool = True,
    return_data_url: bool = True,
) -> Dict[str, Any]:
    """
    Given a PDF filename, read /Users/summit/Downloads/<filename>.pdf
    and write /Users/summit/Downloads/<filename>.png (first page).

    Args:
      filename: e.g. "sample.pdf" or "sample"
      dpi: render dpi (default 200)
      overwrite: overwrite png if exists
      return_data_url: if True, also return data URL so Claude can display it

    Returns:
      {
        "pdf_path": "...",
        "png_path": "...",
        "written": true,
        "image_data_url": "data:image/png;base64,...",   # optional
      }
    """
    try:
        safe_name = _safe_pdf_filename(filename)

        pdf_path = (DOWNLOADS_DIR / safe_name).resolve()

        # Hard guard: must remain within Downloads
        if DOWNLOADS_DIR not in pdf_path.parents:
            raise PermissionError("Access outside Downloads is not allowed.")

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        png_name = pdf_path.stem + ".png"
        png_path = (DOWNLOADS_DIR / png_name).resolve()

        if (not overwrite) and png_path.exists():
            return {
                "pdf_path": str(pdf_path),
                "png_path": str(png_path),
                "written": False,
                "note": "PNG already exists and overwrite=false",
                **({"image_data_url": _png_file_to_data_url(png_path)} if return_data_url else {}),
            }

        _pdf_to_png_first_page(pdf_path, png_path, dpi=dpi)

        result: Dict[str, Any] = {
            "pdf_path": str(pdf_path),
            "png_path": str(png_path),
            "written": True,
        }

        if return_data_url:
            result["image_data_url"] = _png_file_to_data_url(png_path)

        return result

    except Exception as e:
        # IMPORTANT: stderr only (stdout is reserved for JSON-RPC)
        print(f"[convertor] ERROR: {e}", file=sys.stderr)
        return {"error": str(e)}


if __name__ == "__main__":
    # STDIO transport (Claude Desktop will talk JSON-RPC over stdin/stdout)
    mcp.run()
