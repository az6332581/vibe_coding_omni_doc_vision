import os
import sys
import argparse
import logging

# 1. 執行環境設定 (必須在 import paddle 之前)
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_use_onednn'] = '0'

from paddleocr import PaddleOCR

# 2. 屏蔽冗餘日誌
logging.getLogger("ppocr").setLevel(logging.ERROR)

_ocr_instance = None

def get_ocr_engine():
    global _ocr_instance
    if _ocr_instance is None:
        # 徹底移除 use_gpu, ocr_version, show_log 等參數
        # 讓 PaddleOCR 根據你的環境自動決定最適合的預設值
        try:
            _ocr_instance = PaddleOCR(lang="ch") 
        except Exception as e:
            # 如果連最簡單的初始化都失敗，通常是安裝沒裝好
            return None
    return _ocr_instance

def ocr_image_to_text(image_path):
    if not os.path.exists(image_path):
        return f"找不到檔案: {image_path}"

    try:
        ocr = get_ocr_engine()
        if ocr is None:
            return "OCR 引擎初始化失敗，請檢查環境。"
            
        # 執行識別：不要傳入 cls=True
        result = ocr.ocr(image_path)

        if not result or result[0] is None:
            return ""

        # 提取文字
        return " ".join([line[1][0] for res in result for line in res])

    except Exception as e:
        return f"OCR 執行錯誤: {str(e)}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path")
    parser.add_argument("-q", "--query", default="")
    args = parser.parse_args()

    text = ocr_image_to_text(args.image_path)
    print("-" * 30)
    print(f"最終檢索字串: {args.query} (Context: {text})")
    print("-" * 30)