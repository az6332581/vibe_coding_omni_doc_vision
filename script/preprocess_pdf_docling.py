import os
import torch
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
from docling_core.types.doc.document import PictureItem, TableItem
from langchain_core.documents import Document

# --- 基礎配置 ---
torch._dynamo.config.disable = True
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

VLM_URL = 'http://localhost:11434/v1/chat/completions'
VLM_MODEL = 'granite3.2-vision'

def get_vlm_options():
    return PictureDescriptionApiOptions(
        url=VLM_URL,
        params=dict(model=VLM_MODEL, seed=42),
        prompt="請用中文簡潔描述這張圖表內容與關鍵數據，約三句話。",
        timeout=120,
    )

def main():
    input_file = "File/1506.02640v5.pdf" 
    output_dir = Path("File/RAG_FINAL_PACKAGE")
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True
    pipeline_options.generate_table_images = True
    pipeline_options.enable_remote_services = True
    pipeline_options.do_picture_description = True
    pipeline_options.picture_description_options = get_vlm_options()
    pipeline_options.accelerator_options = AcceleratorOptions(num_threads=8, device=AcceleratorDevice.AUTO)

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )

    print(f"🚀 正在解析 PDF 並產生 AI 描述...")
    result = converter.convert(input_file)
    doc = result.document

    final_langchain_docs = []
    asset_counter = {}

    print("📦 正在執行「三合一」物件封裝...")
    for item, _ in doc.iterate_items():
        # 1. 處理圖表（圖片或表格）
        if isinstance(item, (PictureItem, TableItem)):
            page_no = item.prov[0].page_no if item.prov else 0
            asset_counter[page_no] = asset_counter.get(page_no, 0) + 1
            
            prefix = "img" if isinstance(item, PictureItem) else "table"
            img_filename = f"page_{page_no}_{prefix}_{asset_counter[page_no]}.png"
            img_path = str(assets_dir / img_filename)
            
            # 儲存圖片
            if hasattr(item, 'image') and item.image:
                item.image.pil_image.save(img_path)

            # --- 提取三要素 ---
            # A. 圖片原本的描述 (Caption)
            original_caption = item.caption.text if (hasattr(item, 'caption') and item.caption) else "無原生描述"
            
            # B. AI 生成的描述 (VLM)
            ai_desc = ""
            if item.meta and item.meta.description:
                ai_desc = item.meta.description.text
            
            # C. 圖片路徑 (已經在 img_path 變數中)

            # 建立 Document 物件
            lc_doc = Document(
                # page_content 是給向量資料庫檢索用的，把兩種描述都放進去效果最好
                page_content=f"【原生標題】: {original_caption}\n【AI 內容描述】: {ai_desc}",
                metadata={
                    "source": input_file,
                    "is_visual": True,
                    "type": prefix,
                    "image_path": img_path,          # 路徑
                    "original_caption": original_caption, # 原生描述
                    "ai_description": ai_desc,       # AI描述
                    "page_no": page_no
                }
            )
            final_langchain_docs.append(lc_doc)
            print(f"✅ 已封裝: {img_filename}")

        # 2. 處理一般文字（非圖表）
        elif hasattr(item, 'text') and item.text.strip():
            lc_doc = Document(
                page_content=item.text,
                metadata={
                    "source": input_file,
                    "is_visual": False,
                    "page_no": item.prov[0].page_no if item.prov else 0
                }
            )
            final_langchain_docs.append(lc_doc)

    # 儲存 JSON 偵錯檔讓你確認 metadata
    debug_output = [{"content": d.page_content, "meta": d.metadata} for d in final_langchain_docs]
    with open(output_dir / "check_metadata.json", "w", encoding="utf-8") as f:
        json.dump(debug_output, f, ensure_ascii=False, indent=4)

    print(f"\n✨ 完工！共產生 {len(final_langchain_docs)} 個物件。")
    print(f"🔍 請開啟 {output_dir / 'check_metadata.json'} 檢查 Metadata！")

if __name__ == "__main__":
    main()