import os
import re
import logging
import traceback
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, PictureDescriptionApiOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import PictureItem

# --- 基礎配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 1. 設定
file_path = "File/SAL-03.docx" 
output_dir = Path("File/SAL-03_output")
assets_dir = output_dir / "assets"
assets_dir.mkdir(parents=True, exist_ok=True)

try:
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True # 保持表格結構化以輸出 Markdown Table
    pipeline_options.enable_remote_services = True 
    pipeline_options.do_picture_description = True
    pipeline_options.picture_description_options = PictureDescriptionApiOptions(
        url="http://localhost:11434/v1/chat/completions",
        params={"model": "granite3.2-vision:latest"}, 
        prompt="請用中文簡潔地描述這張圖片的內容與關鍵數據，約三句話。",
        timeout=300
    )
    pipeline_options.images_scale = 2.0
    pipeline_options.generate_picture_images = True
    pipeline_options.generate_table_images = False # 關閉表格圖片輸出

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )
    
    print(f"🚀 正在開始解析 {file_path} (僅描述圖片)...")
    result = converter.convert(file_path)
    doc = result.document
    
    # 2. 導出 Markdown (表格會自動轉為 Markdown Table)
    md_text = doc.export_to_markdown()

    # 3. 收集圖片資產
    visual_assets = []
    
    print("\n--- 📝 圖片描述結果 ---")
    
    for item, _ in doc.iterate_items():
        # 僅針對 PictureItem 進行處理
        if isinstance(item, PictureItem) and hasattr(item, 'image') and item.image:
            img_id = item.self_ref.split('/')[-1]
            page_no = item.prov[0].page_no if (item.prov) else 0
            img_filename = f"page_{page_no}_img_{img_id}.png"
            
            # 儲存圖片
            item.image.pil_image.save(assets_dir / img_filename)
            
            # 取得 AI 描述
            ai_desc_text = "無描述 (VLM 可能未回傳)"
            if item.meta and item.meta.description:
                ai_desc_text = item.meta.description.text
            
            print(f"📷 檔案: {img_filename}")
            print(f"📄 描述: {ai_desc_text}")
            print("-" * 30)
            
            rel_path = f"assets/{img_filename}"
            injection = f"\n\n![img]({rel_path})\n\n> **AI 描述:** {ai_desc_text}\n\n"
            
            visual_assets.append(injection)

    # 4. 手動替換 Markdown 內容中的圖片佔位符
    final_md = md_text
    for injection in visual_assets:
        # 按順序替換 <!-- image -->
        final_md = final_md.replace("<!-- image -->", injection, 1)

    # 5. 存檔
    output_file = output_dir / "output.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_md)

    print(f"\n✨ 任務完成！表格已轉 Markdown，圖片描述已存入 {output_file}")

except Exception as e:
    print(f"❌ 發生錯誤: {str(e)}")
    traceback.print_exc()