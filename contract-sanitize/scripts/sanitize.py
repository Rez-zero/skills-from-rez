"""
合同脱敏脚本 - 识别并脱敏合同中的敏感信息
支持：docx / pdf / txt
"""

import sys
import os
import re
from pathlib import Path

try:
    from docx import Document
    import fitz
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


# 敏感信息识别模式
PATTERNS = {
    # 企业名称 - 常见后缀
    '企业全称': [
        r'[^\s，。、：；""''（）【】]{2,}(?:有限公司|有限责任公司|集团有限公司|集团|股份有限公司|股份公司)',
        r'[^\s，。、：；""''（）【】]{2,}(?:合伙企业|合作社|事务所)',
    ],
    # 统一社会信用代码 - 18位
    '信用代码': r'[1-9]\d{15,18}',
    # 手机号 - 11位
    '手机号': r'1[3-9]\d{9}',
    # 固定电话
    '固定电话': r'\d{3,4}[-\s]?\d{7,8}',
    # 邮箱
    '邮箱': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    # 银行卡
    '银行卡': r'\b\d{16,19}\b',
    # IP地址
    'IP地址': r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b',
}


def load_file_content(file_path):
    """读取文件内容"""
    ext = Path(file_path).suffix.lower()

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    elif ext in ['.docx']:
        doc = Document(file_path)
        return '\n'.join([p.text for p in doc.paragraphs])

    elif ext == '.doc':
        # doc 需要转换，这里暂时不支持
        print("暂不支持 .doc 格式，请另存为 .docx")
        return None

    elif ext == '.pdf':
        doc = fitz.open(file_path)
        text = ''
        for page in doc:
            text += page.get_text()
        return text

    else:
        print(f"不支持的格式: {ext}")
        return None


def find_all_entities(text):
    """从文本中识别所有企业实体（用于后续简称匹配）"""
    entities = []

    # 匹配企业全称
    for pattern in PATTERNS['企业全称']:
        matches = re.findall(pattern, text)
        entities.extend(matches)

    return list(set(entities))


def mask_text(text, mode='mask'):
    """脱敏主函数"""

    # 第一步：识别所有企业全称
    all_companies = find_all_entities(text)

    # 构建简称映射（全称的前2-4个字可能是简称）
    company_mapping = {}
    for company in all_companies:
        if len(company) >= 4:
            short = company[:4]
            if short not in company_mapping:
                company_mapping[short] = company

    # 脱敏替换
    result = text

    # 1. 脱敏企业全称
    for company in all_companies:
        if mode == 'mask':
            result = result.replace(company, '█' * len(company))
        elif mode == 'remove':
            result = result.replace(company, '[企业名称]')
        elif mode == 'replace':
            result = result.replace(company, '<企业>')

    # 2. 脱敏简称（但避免把无关词也脱敏了，需要上下文确认）
    # 简化处理：只脱敏在企业名称附近出现过的简称
    for short, full in company_mapping.items():
        if len(short) >= 3:
            # 在可能构成简称的语境中替换
            result = re.sub(rf'\b{re.escape(short)}\b', '█' * len(short), result)

    # 3. 脱敏其他敏感信息
    sensitive_patterns = [
        ('手机号', PATTERNS['手机号'], '█' * 11),
        ('固定电话', PATTERNS['固定电话'], '[电话]'),
        ('邮箱', PATTERNS['邮箱'], '[邮箱]'),
        ('银行卡', PATTERNS['银行卡'], '****'),
        ('信用代码', PATTERNS['信用代码'], '[信用代码]'),
        ('IP地址', PATTERNS['IP地址'], '[IP]'),
    ]

    for name, pattern, replacement in sensitive_patterns:
        result = re.sub(pattern, replacement, result)

    return result


def save_sanitized(content, original_path, output_dir=None):
    """保存脱敏后的文件"""

    if output_dir is None:
        output_dir = Path(original_path).parent

    original_name = Path(original_path).stem
    ext = Path(original_path).suffix.lower()
    output_path = Path(output_dir) / f"{original_name}_sanitized{ext}"

    if ext == '.txt':
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    elif ext == '.docx':
        doc = Document()
        for line in content.split('\n'):
            doc.add_paragraph(line)
        doc.save(output_path)

    elif ext == '.pdf':
        # 创建新的PDF
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4
        page.insert_text((50, 50), content, fontsize=11)
        doc.save(output_path)

    print(f"脱敏完成: {output_path}")
    return str(output_path)


def main():
    if not HAS_DEPENDENCIES:
        print("缺少依赖库，请安装:")
        print("pip install python-docx pymupdf")
        return

    if len(sys.argv) < 3:
        print("用法: python sanitize.py <文件路径> <脱敏方式> [输出目录]")
        print("脱敏方式: mask | remove | replace")
        return

    file_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'mask'
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None

    print(f"正在读取文件: {file_path}")
    content = load_file_content(file_path)

    if content is None:
        return

    print("正在脱敏...")
    sanitized = mask_text(content, mode=mode)

    output_path = save_sanitized(sanitized, file_path, output_dir)
    print(f"完成！输出文件: {output_path}")


if __name__ == '__main__':
    main()