import os
import torch
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

# Disable torch compilation
torch._dynamo.config.disable = True

def main():
    input_path = "File/1506.02640v5.pdf"
    output_dir = Path("File/docling_advanced_output")
    assets_dir = output_dir / "assets"
    output_md_path = output_dir / "output.md"
    
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting processing for {input_path}...")

    # Configure pipeline
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.do_picture_classification = True
    pipeline_options.images_scale = 2.0
    # Enable internal image cache
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True # TRY THIS
    pipeline_options.generate_table_images = True   # TRY THIS
    
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend
            )
        }
    )
    
    result = converter.convert(input_path)
    doc = result.document
    
    print("Exporting and searching for images...")
    
    image_counter = {}

    from docling_core.types.doc.document import PictureItem, TableItem
    
    for item, _ in doc.iterate_items():
        image_to_save = None
        if isinstance(item, (PictureItem, TableItem)):
            if hasattr(item, 'image') and item.image:
                image_to_save = item.image.pil_image
            
            if image_to_save:
                page_no = item.prov[0].page_no if (hasattr(item, 'prov') and item.prov) else 0
                if page_no not in image_counter:
                    image_counter[page_no] = 1
                else:
                    image_counter[page_no] += 1
                    
                img_filename = f"page_{page_no}_img_{image_counter[page_no]}.png"
                image_to_save.save(assets_dir / img_filename)

    md_content = doc.export_to_markdown()
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    total = sum(image_counter.values())
    print(f"Done! Extracted {total} images.")

if __name__ == "__main__":
    main()