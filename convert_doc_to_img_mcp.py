"""convert_doc_to_img_mcp.py

MCP Server for converting .doc/.docx files to PNG images.

This server provides a tool to convert Word documents in the ./file directory
to PNG images (first page or all pages).

Dependencies:
  pip install pymupdf Pillow docx2pdf mcp

Usage:
  python convert_doc_to_img_mcp.py
"""

import base64
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import fitz  # PyMuPDF
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("doc_convertor")

DOWNLOADS_DIR = Path(__file__).parent / "file" / "doc"
OUTPUT_DIR = Path(__file__).parent / "file" / "img"


def _safe_doc_filename(name: str) -> str:
    """
    Accepts:
      - "sample.docx" or "sample.doc"
      - "sample"  (auto adds .docx)
    Rejects path traversal or subpaths (e.g., "../", "/tmp/a.docx", "a/b.docx").
    """
    name = name.strip()

    if not name:
        raise ValueError("filename is empty")

    # Disallow any path components
    p = Path(name)
    if p.name != name:
        raise ValueError("filename must not include a path. Use only the file name, e.g., 'sample.docx'.")

    # Ensure extension
    if not name.lower().endswith((".doc", ".docx")):
        name = name + ".docx"

    return name


def _convert_doc_to_pdf_windows(doc_path: Path, pdf_path: Path) -> None:
    """Convert .doc/.docx to PDF using docx2pdf (Windows only)."""
    try:
        from docx2pdf import convert as docx2pdf_convert
        docx2pdf_convert(str(doc_path), str(pdf_path))
    except ImportError:
        raise RuntimeError("docx2pdf not available. Install with: pip install docx2pdf")
    except Exception as e:
        raise RuntimeError(f"Failed to convert using docx2pdf: {e}")


def _convert_doc_to_pdf_libreoffice(doc_path: Path, pdf_path: Path) -> None:
    """Convert .doc/.docx to PDF using LibreOffice (cross-platform)."""
    import subprocess
    
    # Try common LibreOffice paths
    libreoffice_paths = [
        "libreoffice",
        "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/usr/bin/libreoffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]
    
    libreoffice_cmd = None
    for path in libreoffice_paths:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, timeout=5)
            if result.returncode == 0:
                libreoffice_cmd = path
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    if libreoffice_cmd is None:
        raise RuntimeError("LibreOffice not found. Please install LibreOffice.")
    
    # Convert using LibreOffice headless mode
    out_dir = pdf_path.parent
    result = subprocess.run(
        [
            libreoffice_cmd,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(doc_path)
        ],
        capture_output=True,
        timeout=60
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice conversion failed: {result.stderr.decode()}")
    
    # LibreOffice creates PDF with same name as input
    generated_pdf = out_dir / f"{doc_path.stem}.pdf"
    if generated_pdf != pdf_path and generated_pdf.exists():
        generated_pdf.rename(pdf_path)


def _pdf_to_png_first_page(pdf_path: Path, png_path: Path, dpi: int = 200) -> None:
    """Convert first page of PDF to PNG."""
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
    doc.close()


def _pdf_to_png_all_pages(pdf_path: Path, out_dir: Path, dpi: int = 200) -> list[str]:
    """Convert all pages of PDF to PNG images."""
    doc = fitz.open(str(pdf_path))
    page_count = doc.page_count
    
    if page_count < 1:
        raise ValueError("PDF has no pages.")
    
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    
    out_files = []
    for i in range(page_count):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Normalize CMYK etc. to RGB
        if pix.n >= 5:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        
        png_bytes = pix.tobytes("png")
        
        # Create output filename with page number
        seq = str(i + 1).zfill(3)
        png_name = f"{pdf_path.stem}_page_{seq}.png"
        png_path = out_dir / png_name
        
        png_path.write_bytes(png_bytes)
        out_files.append(str(png_path))
    
    doc.close()
    return out_files


def _png_file_to_data_url(png_path: Path) -> str:
    """Convert PNG file to data URL."""
    b64 = base64.b64encode(png_path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


@mcp.tool()
def convert_doc_in_downloads_to_png(
    filename: str,
    dpi: int = 200,
    overwrite: bool = True,
    return_data_url: bool = True,
    first_page_only: bool = True,
    use_libreoffice: bool = False,
) -> Dict[str, Any]:
    """
    Given a DOC/DOCX filename, read ./file/<filename>.docx
    and write ./file/<filename>.png (first page) or multiple PNG files (all pages).

    Args:
      filename: e.g. "sample.docx", "sample.doc", or "sample"
      dpi: render dpi (default 200)
      overwrite: overwrite png if exists
      return_data_url: if True, also return data URL so Claude can display it
      first_page_only: if True, convert only first page; if False, convert all pages
      use_libreoffice: if True, use LibreOffice; if False, try docx2pdf first (Windows)

    Returns:
      {
        "doc_path": "...",
        "png_path": "..." or "png_paths": [...],
        "written": true,
        "image_data_url": "data:image/png;base64,...",   # optional, first page only
      }
    """
    try:
        safe_name = _safe_doc_filename(filename)

        doc_path = (DOWNLOADS_DIR / safe_name).resolve()

        # Hard guard: must remain within Downloads
        if DOWNLOADS_DIR not in doc_path.parents:
            raise PermissionError("Access outside Downloads is not allowed.")

        if not doc_path.exists():
            raise FileNotFoundError(f"Document not found: {doc_path}")

        # Create temporary directory for PDF conversion
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pdf = Path(temp_dir) / f"{doc_path.stem}.pdf"
            
            # Step 1: Convert DOC/DOCX to PDF
            print(f"[doc_convertor] Converting {doc_path.name} to PDF...", file=sys.stderr)
            
            if use_libreoffice:
                _convert_doc_to_pdf_libreoffice(doc_path, temp_pdf)
            else:
                try:
                    _convert_doc_to_pdf_windows(doc_path, temp_pdf)
                except RuntimeError as e:
                    print(f"[doc_convertor] Windows conversion failed, trying LibreOffice: {e}", file=sys.stderr)
                    _convert_doc_to_pdf_libreoffice(doc_path, temp_pdf)
            
            if not temp_pdf.exists():
                raise RuntimeError("Failed to convert document to PDF")
            
            # Step 2: Convert PDF to PNG
            # Ensure output directory exists
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            
            if first_page_only:
                png_name = doc_path.stem + ".png"
                png_path = (OUTPUT_DIR / png_name).resolve()

                if (not overwrite) and png_path.exists():
                    return {
                        "doc_path": str(doc_path),
                        "png_path": str(png_path),
                        "written": False,
                        "note": "PNG already exists and overwrite=false",
                        **({"image_data_url": _png_file_to_data_url(png_path)} if return_data_url else {}),
                    }

                print(f"[doc_convertor] Converting PDF to PNG (first page)...", file=sys.stderr)
                _pdf_to_png_first_page(temp_pdf, png_path, dpi=dpi)

                result: Dict[str, Any] = {
                    "doc_path": str(doc_path),
                    "png_path": str(png_path),
                    "written": True,
                }

                if return_data_url:
                    result["image_data_url"] = _png_file_to_data_url(png_path)

                return result
            
            else:
                # Convert all pages
                out_dir = DOWNLOADS_DIR / f"{doc_path.stem}_images"
                out_dir.mkdir(parents=True, exist_ok=True)
                
                print(f"[doc_convertor] Converting PDF to PNG (all pages)...", file=sys.stderr)
                png_paths = _pdf_to_png_all_pages(temp_pdf, out_dir, dpi=dpi)
                
                result: Dict[str, Any] = {
                    "doc_path": str(doc_path),
                    "png_paths": png_paths,
                    "page_count": len(png_paths),
                    "output_dir": str(out_dir),
                    "written": True,
                }
                
                # Return data URL for first page if requested
                if return_data_url and png_paths:
                    result["image_data_url"] = _png_file_to_data_url(Path(png_paths[0]))
                
                return result

    except Exception as e:
        # IMPORTANT: stderr only (stdout is reserved for JSON-RPC)
        print(f"[doc_convertor] ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"error": str(e)}


if __name__ == "__main__":
    # STDIO transport (Claude Desktop will talk JSON-RPC over stdin/stdout)
    print(f"[doc_convertor] CWD: {os.getcwd()}", file=sys.stderr)
    print(f"[doc_convertor] DOWNLOADS_DIR: {DOWNLOADS_DIR}", file=sys.stderr)
    mcp.run()
