import os
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

def main():
    input_path = "File/1506.02640v5.pdf"
    output_dir = "File/docling_output"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Converting {input_path} with Docling...")
    
    converter = DocumentConverter()
    result = converter.convert(input_path)
    
    # Export to Markdown
    md_content = result.document.export_to_markdown()
    
    output_filename = os.path.splitext(os.path.basename(input_path))[0] + ".md"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"Successfully converted to {output_path}")

if __name__ == "__main__":
    main()
