"""convert_doc_to_img.py

Convert .doc/.docx files to PNG or JPG images.

Dependencies:
  pip install python-docx docx2pdf pymupdf pillow

Notes:
  - Uses docx2pdf to convert .doc/.docx to PDF (Windows only, uses MS Word COM)
  - For cross-platform support, consider using LibreOffice headless mode
  - PyMuPDF (pymupdf) renders PDF pages to images
  - Output files will be named <docname>_page_001.png (or .jpg)

Usage example:
  python convert_doc_to_img.py input.docx --out-dir out_images --format png --dpi 150

"""
from __future__ import annotations

import argparse
import math
import os
import tempfile
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
    from docx2pdf import convert as docx2pdf_convert
except Exception:
    # Fallback: try using LibreOffice if docx2pdf is not available
    docx2pdf_convert = None


def _ensure_out_dir(path: Path) -> None:
    """Create output directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def _to_int_or_default(x, default=0):
    """Convert to int or return default."""
    try:
        return int(x)
    except Exception:
        return default


def _convert_doc_to_pdf_windows(doc_path: Path, pdf_path: Path) -> None:
    """Convert .doc/.docx to PDF using docx2pdf (Windows only)."""
    if docx2pdf_convert is None:
        raise SystemExit("docx2pdf not available. Install with: pip install docx2pdf")
    
    docx2pdf_convert(str(doc_path), str(pdf_path))


def _convert_doc_to_pdf_libreoffice(doc_path: Path, pdf_path: Path) -> None:
    """Convert .doc/.docx to PDF using LibreOffice (cross-platform)."""
    import subprocess
    
    # Try common LibreOffice paths
    libreoffice_paths = [
        "/opt/libreoffice26.2/program/soffice",
        "/opt/libreoffice25.8/program/soffice",
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
        raise SystemExit("LibreOffice not found. Please install LibreOffice or use docx2pdf on Windows.")
    
    # Convert using LibreOffice headless mode
    out_dir = pdf_path.parent
    subprocess.run(
        [
            libreoffice_cmd,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(doc_path)
        ],
        check=True,
        capture_output=True
    )
    
    # LibreOffice creates PDF with same name as input
    generated_pdf = out_dir / f"{doc_path.stem}.pdf"
    if generated_pdf != pdf_path and generated_pdf.exists():
        generated_pdf.rename(pdf_path)


def _convert_pdf_to_images(pdf_path: Path, out_dir: Path, fmt: str, dpi: int, start: int | None, end: int | None, quality: int) -> list[str]:
    """Convert PDF pages to images."""
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
        out_name = f"{pdf_path.stem}_page_{seq}.{('jpg' if fmt.lower() in ('jpg','jpeg') else 'png')}"
        out_path = out_dir / out_name

        if fmt.lower() in ("png",):
            img.save(out_path, format="PNG")
        else:
            q = max(1, min(95, int(quality)))
            img = img.convert("RGB")
            img.save(out_path, format="JPEG", quality=q, optimize=True)

        out_files.append(str(out_path))

    doc.close()
    return out_files


def convert(doc_path: str, out_dir: str | None = None, fmt: str = "png", dpi: int = 150, start: int | None = None, end: int | None = None, quality: int = 85, use_libreoffice: bool = False) -> list[str]:
    """Convert .doc/.docx file to images.

    Args:
        doc_path: Path to .doc or .docx file.
        out_dir: Directory to save images. Defaults to same dir as doc + '/images'.
        fmt: 'png' or 'jpg'.
        dpi: Rendering DPI (pixels per inch).
        start: 1-based start page (inclusive). If None, starts at 1.
        end: 1-based end page (inclusive). If None, goes to last page.
        quality: JPEG quality (1-95), ignored for PNG.
        use_libreoffice: Use LibreOffice instead of docx2pdf (cross-platform).

    Returns:
        List of output image file paths.
    """
    doc = Path(doc_path)
    if not doc.exists():
        raise FileNotFoundError(f"Document not found: {doc}")

    if doc.suffix.lower() not in ('.doc', '.docx'):
        raise ValueError("File must be .doc or .docx format")

    if fmt.lower() not in ("png", "jpg", "jpeg"):
        raise ValueError("format must be 'png' or 'jpg'")

    out_dir_path = Path(out_dir) if out_dir else doc.parent / (doc.stem + "_images")
    _ensure_out_dir(out_dir_path)

    # Step 1: Convert .doc/.docx to PDF
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_pdf = Path(temp_dir) / f"{doc.stem}.pdf"
        
        print(f"Converting {doc.name} to PDF...")
        if use_libreoffice:
            _convert_doc_to_pdf_libreoffice(doc, temp_pdf)
        else:
            try:
                _convert_doc_to_pdf_windows(doc, temp_pdf)
            except SystemExit:
                print("Falling back to LibreOffice...")
                _convert_doc_to_pdf_libreoffice(doc, temp_pdf)
        
        if not temp_pdf.exists():
            raise RuntimeError("Failed to convert document to PDF")
        
        # Step 2: Convert PDF to images
        print(f"Converting PDF to {fmt.upper()} images...")
        out_files = _convert_pdf_to_images(temp_pdf, out_dir_path, fmt, dpi, start, end, quality)
    
    return out_files


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Convert .doc/.docx files to PNG or JPG images")
    p.add_argument("doc", help="Input .doc or .docx file path")
    p.add_argument("--out-dir", help="Output directory (default: <doc>_images)")
    p.add_argument("--format", choices=["png", "jpg"], default="png", help="Output image format")
    p.add_argument("--dpi", type=int, default=150, help="Render DPI (default 150)")
    p.add_argument("--start", type=int, help="1-based start page (inclusive)")
    p.add_argument("--end", type=int, help="1-based end page (inclusive)")
    p.add_argument("--quality", type=int, default=85, help="JPEG quality 1-95 (only for jpg)")
    p.add_argument("--use-libreoffice", action="store_true", help="Use LibreOffice instead of docx2pdf")
    return p


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        out = convert(args.doc, args.out_dir, args.format, args.dpi, args.start, args.end, args.quality, args.use_libreoffice)
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1)

    out_dir_display = args.out_dir or (Path(args.doc).parent / (Path(args.doc).stem + '_images'))
    print(f"✓ Successfully saved {len(out)} images to {out_dir_display}")
    for f in out:
        print(f"  - {Path(f).name}")


if __name__ == "__main__":
    main()
