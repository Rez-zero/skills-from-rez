"""
合同比对脚本 - 对 docx/pdf 文件进行差异标注
- docx: 添加批注
- pdf: 添加高亮
"""

import sys
import os
import subprocess
from pathlib import Path

# 尝试导入依赖库
try:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    import fitz  # pymupdf
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


def convert_doc_to_docx(doc_path):
    """将 .doc 文件转换为 .docx"""
    try:
        import comtypes.client
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False
        doc = word.Documents.Open(str(doc_path))
        docx_path = str(doc_path) + 'x'
        doc.SaveAs(docx_path, FileFormat=16)  # 16 = wdFormatXMLDocument
        doc.Close()
        word.Quit()
        return docx_path
    except Exception as e:
        print(f"doc 转 docx 失败: {e}")
        print("请手动将 .doc 文件另存为 .docx 格式")
        return None


def extract_text_from_docx(docx_path):
    """从 docx 文件提取纯文本"""
    doc = Document(docx_path)
    paragraphs = []
    for para in doc.paragraphs:
        paragraphs.append(para.text)
    return '\n'.join(paragraphs)


def extract_text_from_pdf(pdf_path):
    """从 PDF 文件提取文本和布局信息"""
    doc = fitz.open(pdf_path)
    pages = []
    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        pages.append({
            'page_num': page_num + 1,
            'text': text,
            'blocks': page.get_text("blocks")
        })
    return pages


def split_into_sentences(text):
    """将文本分割为句子"""
    import re
    # 按中英文标点分割
    sentences = re.split(r'([。！？；\n])', text)
    result = []
    current = ''
    for i, part in enumerate(sentences):
        if i % 2 == 0:
            current += part
        else:
            current += part
            if current.strip():
                result.append(current)
            current = ''
    if current.strip():
        result.append(current)
    return result


def compare_texts(base_text, compare_text):
    """比对两份文本，返回差异列表"""
    base_sentences = split_into_sentences(base_text)
    compare_sentences = split_into_sentences(compare_text)

    diffs = []

    # 简单的行顺序比对
    i, j = 0, 0
    while i < len(base_sentences) or j < len(compare_sentences):
        if i >= len(base_sentences):
            diffs.append(('新增', compare_sentences[j]))
            j += 1
        elif j >= len(compare_sentences):
            diffs.append(('删除', base_sentences[i]))
            i += 1
        elif base_sentences[i] == compare_sentences[j]:
            i += 1
            j += 1
        else:
            # 找最近匹配
            match_found = False
            for k in range(j, min(j + 3, len(compare_sentences))):
                if base_sentences[i] == compare_sentences[k]:
                    for m in range(j, k):
                        diffs.append(('新增', compare_sentences[m]))
                    diffs.append(('修改', base_sentences[i], compare_sentences[k]))
                    i += 1
                    j = k + 1
                    match_found = True
                    break
            if not match_found:
                diffs.append(('删除', base_sentences[i]))
                i += 1

    return diffs


def annotate_docx(docx_path, diffs, output_path):
    """为 docx 文件添加批注"""
    doc = Document(docx_path)

    # 获取所有段落文本的索引
    para_list = []
    for para in doc.paragraphs:
        para_list.append(para.text)

    # 创建批注
    for diff in diffs:
        diff_type = diff[0]
        if diff_type == '删除':
            content = diff[1]
            # 在段落中查找并添加批注
            for para in doc.paragraphs:
                if content in para.text:
                    # 添加删除线样式
                    for run in para.runs:
                        if content in run.text:
                            run.font.strike = True
                            run.font.color.rgb = None
        elif diff_type == '新增':
            content = diff[1]
            for para in doc.paragraphs:
                if content in para.text:
                    for run in para.runs:
                        if content in run.text:
                            run.font.highlight_color = 0x2E75B6  # 蓝色

    doc.save(output_path)
    print(f"批注文件已保存: {output_path}")


def annotate_pdf(pdf_path, diffs, output_path):
    """为 PDF 文件添加高亮"""
    doc = fitz.open(pdf_path)

    for diff in diffs:
        diff_type = diff[0]
        if diff_type == '删除':
            content = diff[1]
            for page in doc:
                text_instances = page.search_for(content)
                for inst in text_instances:
                    # 红色高亮
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=(1, 0, 0))

        elif diff_type == '新增':
            content = diff[1]
            for page in doc:
                text_instances = page.search_for(content)
                for inst in text_instances:
                    # 蓝色高亮
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=(0, 0, 1))

        elif diff_type == '修改':
            old_content = diff[1]
            new_content = diff[2]
            for page in doc:
                # 旧内容红色
                old_instances = page.search_for(old_content)
                for inst in old_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=(1, 0, 0))
                # 新内容蓝色
                new_instances = page.search_for(new_content)
                for inst in new_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=(0, 0, 1))

    doc.save(output_path)
    print(f"高亮文件已保存: {output_path}")


def main():
    if not HAS_DEPENDENCIES:
        print("缺少依赖库，请安装:")
        print("pip install python-docx pymupdf")
        return

    if len(sys.argv) < 3:
        print("用法: python compare_docs.py <原文件> <待标文件> [输出目录]")
        return

    base_file = sys.argv[1]
    compare_file = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(compare_file)

    base_ext = Path(base_file).suffix.lower()
    compare_ext = Path(compare_file).suffix.lower()

    # 转换 doc 为 docx
    if base_ext == '.doc':
        base_file = convert_doc_to_docx(base_file)
        if not base_file:
            return
        base_ext = '.docx'

    if compare_ext == '.doc':
        compare_file = convert_doc_to_docx(compare_file)
        if not compare_file:
            return
        compare_ext = '.docx'

    # 提取文本
    if base_ext in ['.docx']:
        base_text = extract_text_from_docx(base_file)
    elif base_ext == '.pdf':
        base_pages = extract_text_from_pdf(base_file)
        base_text = '\n'.join([p['text'] for p in base_pages])
    else:
        print(f"不支持的原文件格式: {base_ext}")
        return

    if compare_ext in ['.docx']:
        compare_text = extract_text_from_docx(compare_file)
    elif compare_ext == '.pdf':
        compare_pages = extract_text_from_pdf(compare_file)
        compare_text = '\n'.join([p['text'] for p in compare_pages])
    else:
        print(f"不支持的比对文件格式: {compare_ext}")
        return

    # 比对
    print("正在比对文本...")
    diffs = compare_texts(base_text, compare_text)

    if not diffs:
        print("两份文件没有发现差异")
        return

    print(f"发现 {len(diffs)} 处差异")

    # 生成标注文件
    compare_name = Path(compare_file).stem
    output_ext = compare_ext

    if compare_ext == '.docx':
        output_path = os.path.join(output_dir, f"{compare_name}_compared.docx")
        annotate_docx(compare_file, diffs, output_path)
    elif compare_ext == '.pdf':
        output_path = os.path.join(output_dir, f"{compare_name}_compared.pdf")
        annotate_pdf(compare_file, diffs, output_path)


if __name__ == '__main__':
    main()