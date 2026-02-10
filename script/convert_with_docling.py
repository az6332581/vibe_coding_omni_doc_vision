import os
from docling.document_converter import DocumentConverter
from pathlib import Path

def convert_docx_to_md_with_docling():
    source_dir = Path("File")
    files = [f for f in source_dir.glob("*.docx") if not f.name.startswith("~$")]
    
    if not files:
        print("No docx files found in File directory.")
        return

    print(f"Found {len(files)} docx files. Starting conversion with Docling...")
    converter = DocumentConverter()

    for docx_path in files:
        try:
            print(f"Converting: {docx_path.name}")
            result = converter.convert(docx_path)
            
            # Export to markdown
            md_output = result.document.export_to_markdown()
            
            md_path = docx_path.with_suffix(".md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_output)
            
            print(f"Successfully converted to: {md_path.name}")
        except Exception as e:
            print(f"Error converting {docx_path.name}: {e}")

if __name__ == "__main__":
    convert_docx_to_md_with_docling()
