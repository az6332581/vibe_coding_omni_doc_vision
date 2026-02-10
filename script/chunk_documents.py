import zipfile
import xml.etree.ElementTree as ET
import os
import re
import json

def get_docx_text_xml(path):
    if not os.path.exists(path):
        return ""
    try:
        with zipfile.ZipFile(path) as z:
            xml_content = z.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        paragraphs = []
        for p in tree.findall('.//w:p', namespace):
            texts = [t.text for t in p.findall('.//w:t', namespace) if t.text]
            if texts:
                paragraphs.append(''.join(texts))
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return ""

def split_by_chapters(text, doc_id):
    chapter_pattern = re.compile(r'^(\d+\.\d+(\.\d+)?|[\u4e00-\u9fa5]+[、])')
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_header = "前言/標題"
    for line in lines:
        line = line.strip()
        if not line: continue
        if chapter_pattern.match(line):
            if current_chunk:
                chunks.append({"doc_id": doc_id, "header": current_header, "content": "\n".join(current_chunk)})
            current_header = line
            current_chunk = [line]
        else:
            current_chunk.append(line)
    if current_chunk:
        chunks.append({"doc_id": doc_id, "header": current_header, "content": "\n".join(current_chunk)})
    return chunks

def process_all_files():
    file_configs = [
        {"path": "File/IC02_A_存取控制作業規範.docx", "id": "IC02"},
        {"path": "File/IP14_A_帳號與存取控制程序.docx", "id": "IP14"},
        {"path": "File/IC0201_A_帳號權限申請表.docx", "id": "IC0201"},
        {"path": "File/IC0202_A_存取權限審查表.docx", "id": "IC0202"},
    ]
    all_chunks = []
    for config in file_configs:
        raw_text = get_docx_text_xml(config['path'])
        if not raw_text: continue
        if config['id'] in ["IC02", "IP14"]:
            doc_chunks = split_by_chapters(raw_text, config['id'])
        else:
            doc_chunks = [{"doc_id": config['id'], "header": "表單欄位定義", "content": raw_text}]
        all_chunks.extend(doc_chunks)
    for chunk in all_chunks:
        if chunk['doc_id'] == "IP14":
            if "申請" in chunk['content']:
                chunk['content'] += "\n[關聯表單]: 本步驟需填寫 IC0201 帳號權限申請表。"
            if "審查" in chunk['content'] or "稽核" in chunk['content']:
                chunk['content'] += "\n[關聯表單]: 本步驟需參考 IC0202 存取權限審查表。"
        if chunk['doc_id'] in ["IC0201", "IC0202"]:
            chunk['content'] = f"[程序依據]: 本表單作業依據 IP14 帳號與存取控制程序辦理。\n{chunk['content']}"
    output_path = "File/chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"Generated {len(all_chunks)} chunks in {output_path}")

if __name__ == "__main__":
    process_all_files()