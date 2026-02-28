"""example_doc_to_img.py

Example script demonstrating how to use convert_doc_to_img.py

This script shows various ways to convert .doc/.docx files to images.
"""

from pathlib import Path
from convert_doc_to_img import convert

def main():
    # Example 1: Convert the .docx file in ./file directory to PNG images
    doc_file = Path("./file/요구사항정의서-20260225.docx")
    
    if doc_file.exists():
        print("=" * 60)
        print("Example 1: Converting .docx to PNG images (default settings)")
        print("=" * 60)
        
        try:
            # Convert with default settings (PNG, 150 DPI)
            output_files = convert(
                doc_path=str(doc_file),
                out_dir="./file/요구사항정의서-20260225_images",
                fmt="png",
                dpi=150
            )
            
            print(f"\n✓ Successfully converted {len(output_files)} pages!")
            print("\nGenerated files:")
            for file_path in output_files:
                print(f"  - {Path(file_path).name}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    else:
        print(f"File not found: {doc_file}")
    
    print("\n" + "=" * 60)
    print("Other usage examples:")
    print("=" * 60)
    
    # Example 2: High quality JPG conversion
    print("\n# Example 2: Convert to high-quality JPG (200 DPI)")
    print("output_files = convert(")
    print("    doc_path='./file/요구사항정의서-20260225.docx',")
    print("    fmt='jpg',")
    print("    dpi=200,")
    print("    quality=95")
    print(")")
    
    # Example 3: Convert specific pages only
    print("\n# Example 3: Convert only pages 1-3")
    print("output_files = convert(")
    print("    doc_path='./file/요구사항정의서-20260225.docx',")
    print("    start=1,")
    print("    end=3")
    print(")")
    
    # Example 4: Using LibreOffice (cross-platform)
    print("\n# Example 4: Use LibreOffice for conversion (cross-platform)")
    print("output_files = convert(")
    print("    doc_path='./file/요구사항정의서-20260225.docx',")
    print("    use_libreoffice=True")
    print(")")
    
    print("\n" + "=" * 60)
    print("Command-line usage:")
    print("=" * 60)
    print("\n# Basic usage:")
    print("python convert_doc_to_img.py ./file/요구사항정의서-20260225.docx")
    
    print("\n# With custom output directory and format:")
    print("python convert_doc_to_img.py ./file/요구사항정의서-20260225.docx --out-dir ./output --format jpg --dpi 200")
    
    print("\n# Convert specific pages:")
    print("python convert_doc_to_img.py ./file/요구사항정의서-20260225.docx --start 1 --end 3")
    
    print("\n# Use LibreOffice:")
    print("python convert_doc_to_img.py ./file/요구사항정의서-20260225.docx --use-libreoffice")


if __name__ == "__main__":
    main()
