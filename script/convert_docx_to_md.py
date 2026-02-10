import os
import zipfile
import xml.etree.ElementTree as ET
import re

def docx_to_md(docx_path, md_path):
    try:
        with zipfile.ZipFile(docx_path) as z:
            xml_content = z.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        md_lines = []
        for p in tree.findall('.//w:p', namespace):
            line_parts = []
            pStyle = p.find('.//w:pStyle', namespace)
            style = pStyle.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if pStyle is not None else ""
            for r in p.findall('.//w:r', namespace):
                is_bold = r.find('.//w:b', namespace) is not None
                text_elements = r.findall('.//w:t', namespace)
                text = "".join([t.text for t in text_elements if t.text])
                if text.strip():
                    if is_bold: text = f"**{text}**"
                    line_parts.append(text)
            paragraph_text = "".join(line_parts).strip()
            if paragraph_text:
                if style.startswith('Heading') or re.match(r'^[一二三四五六七八九十]、', paragraph_text) or re.match(r'^\d+\.', paragraph_text):
                    md_lines.append(f"## {paragraph_text}")
                else:
                    md_lines.append(paragraph_text)
                md_lines.append("")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_lines))
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    source_dir = "File"
    files = [f for f in os.listdir(source_dir) if f.endswith(".docx") and not f.startswith("~$")]
    for filename in files:
        md_name = filename.replace(".docx", ".md")
        if docx_to_md(os.path.join(source_dir, filename), os.path.join(source_dir, md_name)):
            print(f"Converted: {filename}")

if __name__ == "__main__":
    main()