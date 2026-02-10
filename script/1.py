import os
import torch
import re
import json
import logging
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    PictureDescriptionApiOptions,
    AcceleratorOptions,
    AcceleratorDevice
)
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling_core.types.doc.document import PictureItem, TableItem

# --- 基礎配置 ---
torch._dynamo.config.disable = True
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

VLM_URL = 'http://localhost:11434/v1/chat/completions'
VLM_MODEL = 'granite3.2-vision'

def get_vlm_options():
    return PictureDescriptionApiOptions(
        url=VLM_URL,
        params=dict(model=VLM_MODEL, seed=42),
        prompt="請用中文簡潔地描述這張圖片或表格的內容與關鍵數據，約三句話。",
        timeout=120,
    )

def main():
    input_file = "File/1506.02640v5.pdf" 
    output_dir = Path("File/1506.02640v5_vlm")
    assets_dir = output_dir / "assets"
    output_md_path = output_dir / "output.md"
    
    assets_dir.mkdir(parents=True, exist_ok=True)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.generate_picture_images = True
    pipeline_options.generate_table_images = True
    pipeline_options.enable_remote_services = True
    pipeline_options.do_picture_description = True
    pipeline_options.picture_description_options = get_vlm_options()
    pipeline_options.accelerator_options = AcceleratorOptions(num_threads=8, device=AcceleratorDevice.AUTO)

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend
            )
        }
    )

    print(f"🚀 正在轉換 PDF 並請求 VLM 描述...")
    result = converter.convert(input_file)
    doc = result.document

    print("📸 正在儲存圖片並建立索引...")
    asset_counter = {}
    replacement_list = [] 

    for item, _ in doc.iterate_items():
        if isinstance(item, (PictureItem, TableItem)):
            if hasattr(item, 'image') and item.image:
                page_no = item.prov[0].page_no if (item.prov) else 0
                asset_counter[page_no] = asset_counter.get(page_no, 0) + 1
                
                prefix = "img" if isinstance(item, PictureItem) else "table"
                img_filename = f"page_{page_no}_{prefix}_{asset_counter[page_no]}.png"
                img_relative_path = f"assets/{img_filename}"
                
                item.image.pil_image.save(assets_dir / img_filename)
                
                # --- 修正 DeprecationWarning: 使用 meta 替代 annotations ---
                ai_desc = ""
                if hasattr(item, 'meta') and item.meta and item.meta.description:
                    ai_desc = item.meta.description.text
                elif hasattr(item, 'annotations') and item.annotations: # 備用舊版相容
                    ai_desc = item.annotations[0].text

                meta_json = json.dumps({"image_path": img_relative_path}, ensure_ascii=False)
                formatted_block = (
                    f"\n\n![Image]({img_relative_path})\n"
                    f"> **AI 中文描述:** {ai_desc}\n"
                    f"\n\n"
                )
                replacement_list.append(formatted_block)

    print("✍️ 正在將路徑與 AI 描述寫回 Markdown...")
    raw_md = doc.export_to_markdown()


    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(raw_md)

    print(f"📝 Markdown: {output_md_path}")

if __name__ == "__main__":
    main()