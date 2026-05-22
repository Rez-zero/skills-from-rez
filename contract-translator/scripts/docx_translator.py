"""
Docx 文档翻译器 v3 — 通用版（支持批注/修订原文保留+翻译）

功能：
1. 读取英文 .docx 文档
2. 按段落级别收集文本，保持结构完整
3. 识别并处理带批注/修订的原文：
   - 保留英文原文
   - 同时翻译为中文
4. 翻译批注内容
5. 提取并翻译修订内容（删除/插入）
6. 使用 AI 批量翻译（支持自定义术语表）
7. 按原始 run 长度比例切分回写
8. 统一字体为宋体，保留原文格式

使用方式：
    python docx_translator.py <input.docx> [output.docx] [--terms <terms.json>]

依赖：
    pip install python-docx lxml
"""

import sys
import os
import json
import re
import argparse
import zipfile
from pathlib import Path
from lxml import etree
from docx import Document

W_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def _tag(element):
    """获取 XML 元素本地标签名"""
    t = element.tag
    return t.split('}')[-1] if '}' in t else t


# ========== 默认术语表 ==========

DEFAULT_TERMS = {
    # ========== 合同基本术语 ==========
    "Agreement": "协议", "Contract": "合同", "Party": "方", "Parties": "各方",
    "Service Provider": "服务提供方", "Provider": "提供方",
    "Subscriber": "订阅方", "Customer": "客户", "Client": "客户",
    "Data": "数据", "Order": "订单", "Subscription": "订阅",
    "License": "许可", "Licensor": "许可方", "Licensee": "被许可方",
    "Platform": "平台", "System": "系统",
    "Terms and Conditions": "条款和条件", "T&C": "条款和条件",
    "Governing Law": "适用法律", "Applicable Law": "适用法律",
    "Party A": "甲方", "Party B": "乙方",
    "Client": "客户", "Contractor": "承包商",
    "Vendor": "供应商", "Purchaser": "采购方",

    # ========== 权利义务 ==========
    "Termination": "终止", "Terminate": "终止", "terminated": "已终止",
    "Confidential": "保密", "Confidentiality": "保密性",
    "Indemnification": "赔偿", "Indemnify": "赔偿", "Indemnity": "赔偿",
    "Liability": "责任", "Liable": "承担责任",
    "Intellectual Property": "知识产权", "IP": "知识产权",
    "Representations and Warranties": "声明和保证", "Representations": "声明", "Warranties": "保证",
    "Force Majeure": "不可抗力",
    "Breach": "违约", "breach of": "违反",
    "Remedy": "救济", "Remedies": "救济措施",
    "Effective Date": "生效日期", "Commencement Date": "开始日期",
    "Expiration Date": "到期日", "Expiry": "到期",
    "Renewal": "续期", "Renew": "续期", "renewed": "已续期",
    "Notice": "通知", "Notification": "通知",
    "Amendment": "修订", "amend": "修订", "amended": "已修订",
    "Severability": "可分割性",
    "Entire Agreement": "完整协议",
    "Waiver": "放弃", "waive": "放弃",
    "Assignment": "转让", "assign": "转让", "assigned": "已转让",
    "Binding": "有约束力", "binding": "有约束力的",
    "Jurisdiction": "管辖权",
    "Arbitration": "仲裁", "arbitrate": "仲裁",
    "Confidential Information": "保密信息",
    "Proprietary": "专有", "Proprietary Information": "专有信息",
    "DAMAGES": "损害赔偿", "damages": "损害赔偿",
    "WARRANTIES": "保证", "warranty": "保证",
    "NEGLIGENCE": "过失",
    "INFRINGEMENT": "侵权",
    "Limitation of Liability": "责任限制",
    "Obligations": "义务", "obligation": "义务",
    "Rights": "权利", "right": "权利",
    "Covenants": "契约条款", "covenant": "契约",
    "Indemnify and Hold Harmless": "赔偿并使其免受损害",

    # ========== 人员与公司 ==========
    "Employee": "员工", "Employees": "员工",
    "Representatives": "代表", "representative": "代表",
    "Affiliate": "关联方", "Affiliates": "关联方",
    "affiliates": "关联公司", "Successors": "继承人", "successors": "继承人",
    "assigns": "受让人", "Contractors": "承包人", "contractor": "承包人",
    "officers": "高级管理人员", "directors": "董事",
    "Shareholders": "股东", "shareholder": "股东",

    # ========== 付款与财务 ==========
    "fees": "费用", "Fee": "费用", "Payment": "付款", "pay": "付款",
    "Invoice": "发票", "Invoicing": "开票",
    "refund": "退款", "Refund": "退款",
    "Purchase Price": "购买价格", "Price": "价格",
    "Commission": "佣金", "Royalty": "特许权使用费",
    "Advance Payment": "预付款", "Prepayment": "预付款",
    "Late Payment": "逾期付款",
    "Consideration": "对价",
    "Payment Terms": "付款条款",
    "non-exclusive": "非排他性", "non-exclusive": "非排他性",
    "non-transferable": "不可转让",
    "royalty-free": "免费", "royalty free": "免特许权使用费",
    "sub-licensable": "可再许可",
    "irrevocable": "不可撤销",
    "perpetual": "永久", "perpetually": "永久地",
    "commercially reasonable": "商业合理",

    # ========== 法律程序 ==========
    "arbitration": "仲裁", "litigation": "诉讼", "dispute": "争议",
    "court": "法院", "lawsuit": "诉讼", "injunction": "禁令",
    "equitable relief": "衡平法救济",
    "attorney fees": "律师费", "legal fees": "律师费",
    "arbitration rules": "仲裁规则",
    "arbitral tribunal": "仲裁庭",
    "award": "裁决", "Mediation": "调解",
    "Dispute Resolution": "争议解决",
    "Venue": "审判地",

    # ========== 期限与终止 ==========
    "Term": "期限", "Duration": "期限", "Initial Term": "初始期限",
    "Renewal Term": "续期期限", "Extended Term": "延长期限",
    "Termination for Cause": "因故终止",
    "Termination for Convenience": "因方便终止",
    "Notice of Termination": "终止通知",
    "Cure Period": "补救期",
    "Survival": "存续", "survive": "继续有效",

    # ========== 违约与救济 ==========
    "Default": "违约", "Material Breach": "重大违约",
    "Minor Breach": "轻微违约",
    "Specific Performance": "实际履行",
    "Liquidated Damages": "约定赔偿金",
    "Consequential Damages": "间接损失",
    "Indirect Damages": "间接损害",
    "Incidental Damages": "附带损害",
    "Direct Damages": "直接损害",

    # ========== 知识产权 ==========
    "Copyright": "著作权", "Trademark": "商标",
    "Patent": "专利", "Trade Secret": "商业秘密",
    "Work Product": "工作成果", "Deliverables": "交付物",
    "License Grant": "许可授予", "Ownership": "所有权",
    "License Grant": "许可授予",

    # ========== 保密义务 ==========
    "Non-Disclosure Agreement": "保密协议", "NDA": "保密协议",
    "Non-Disclosure": "保密", "non-disclosure": "保密",
    "Return of Information": "信息返还",
    "Exclusions from Confidentiality": "保密例外",

    # ========== 其他法律术语 ==========
    "hereunder": "据此", "thereof": "其", "whereas": "鉴于",
    "IN WITNESS WHEREOF": "兹证明",
    "hereinafter": "以下", "herein": "其中",
    "hereby": "兹", "thereby": "因此",
    "hereto": "与此", "thereto": "据此",
    "shall": "应", "may": "可", "must": "必须", "will": "将",
    "including but not limited to": "包括但不限于",
    "Subject to": "受...约束", "Notwithstanding": "尽管",
    "Pursuant to": "依据", "In accordance with": "按照",
    "Entire Agreement": "完整协议", "Counterparts": "副本",
    "Severability": "可分割性", "Integration": "完整协议条款",
    "Headings": "标题",
    "interpretation": "解释", "Interpretation": "解释",
    "Further Assurances": "进一步保证",
    "Independent Contractor": "独立承包商",
    "Net 30": "30天付款", "Net 60": "60天付款", "Net 90": "90天付款",
    "Interest Rate": "利率",
}


# ========== 修订处理 ==========

def collect_revisions(container):
    """
    从容器（段落）中收集所有修订内容。
    返回: list of {"type": "ins"|"del", "text": str, "element": xml_element}
    """
    revisions = []
    for child in list(container):
        tag = _tag(child)
        if tag == 'ins':
            # 插入内容
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 't' and rc.text is not None:
                        revisions.append({
                            "type": "ins",
                            "text": rc.text,
                            "element": rc
                        })
        elif tag == 'del':
            # 删除内容
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 'delText' and rc.text is not None:
                        revisions.append({
                            "type": "del",
                            "text": rc.text,
                            "element": rc
                        })
    return revisions


def has_revisions_in_paragraph(para_elem):
    """
    检查段落是否包含修订。
    """
    for child in list(para_elem):
        tag = _tag(child)
        if tag == 'ins' or tag == 'del':
            return True
    return False


def get_revision_items_for_paragraph(para_elem):
    """
    获取段落中所有修订项目。
    """
    revisions = []
    for child in list(para_elem):
        tag = _tag(child)
        if tag == 'ins':
            # 收集插入内容
            texts = []
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 't' and rc.text is not None:
                        texts.append(rc.text)
            if texts:
                revisions.append({
                    "type": "insertion",
                    "text": ''.join(texts)
                })
        elif tag == 'del':
            # 收集删除内容
            texts = []
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 'delText' and rc.text is not None:
                        texts.append(rc.text)
            if texts:
                revisions.append({
                    "type": "deletion",
                    "text": ''.join(texts)
                })
    return revisions


def get_text_with_revision_markers(container):
    """
    获取带修订标记的文本（用于显示给用户）。
    格式：
    - 正常文本：原样保留
    - 删除内容：~~deleted~~（双波浪号）
    - 插入内容：_inserted_（下划线）
    返回: {"full_text": str, "has_revisions": bool, "revision_count": int}
    """
    parts = []
    deletion_count = 0
    insertion_count = 0

    for child in list(container):
        tag = _tag(child)
        if tag == 'r':
            # 正常文本
            for rc in child:
                rt = _tag(rc)
                if rt == 't' and rc.text is not None:
                    parts.append(rc.text)
        elif tag == 'ins':
            # 插入内容 - 加下划线标记
            text_parts = []
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 't' and rc.text is not None:
                        text_parts.append(rc.text)
            if text_parts:
                text = ''.join(text_parts)
                parts.append(f'_{text}_')
                insertion_count += 1
        elif tag == 'del':
            # 删除内容 - 加删除线标记
            text_parts = []
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 'delText' and rc.text is not None:
                        text_parts.append(rc.text)
            if text_parts:
                text = ''.join(text_parts)
                parts.append(f'~~{text}~~')
                deletion_count += 1

    full_text = ''.join(parts)
    return {
        "full_text": full_text,
        "has_revisions": deletion_count > 0 or insertion_count > 0,
        "revision_count": deletion_count + insertion_count
    }


def get_clean_text_for_translation(container):
    """
    获取用于翻译的"干净"文本（移除修订标记，代表修订后的最终语义）。
    删除内容被移除，插入内容被保留。
    返回: str
    """
    parts = []

    for child in list(container):
        tag = _tag(child)
        if tag == 'r':
            # 正常文本
            for rc in child:
                rt = _tag(rc)
                if rt == 't' and rc.text is not None:
                    parts.append(rc.text)
        elif tag == 'ins':
            # 插入内容 - 保留（代表修订后的内容）
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 't' and rc.text is not None:
                        parts.append(rc.text)
        elif tag == 'del':
            # 删除内容 - 移除（不代表最终语义）
            pass

    return ''.join(parts)


# ========== 批注处理 ==========

def load_comments(docx_path):
    """
    从 docx 文件中加载批注内容。
    返回: dict {comment_id: {"author": str, "date": str, "text": str}}
    """
    comments = {}
    try:
        with zipfile.ZipFile(docx_path, 'r') as zf:
            if 'word/comments.xml' in zf.namelist():
                with zf.open('word/comments.xml') as f:
                    tree = etree.parse(f)
                    root = tree.getroot()
                    for comment in root.findall(f'.//{W_NS}comment'):
                        cid = comment.get(f'{W_NS}id')
                        author = comment.get(f'{W_NS}author', '')
                        date = comment.get(f'{W_NS}date', '')
                        # 收集批注文本
                        texts = []
                        for t in comment.findall(f'.//{W_NS}t'):
                            if t.text:
                                texts.append(t.text)
                        text = ''.join(texts)
                        comments[cid] = {
                            'author': author,
                            'date': date,
                            'text': text
                        }
    except Exception as e:
        print(f"警告：加载批注时出错: {e}")
    return comments


def get_comment_ids_for_paragraph(para_elem):
    """
    获取段落中所有批注的 ID。
    """
    comment_ids = set()
    # 查找 commentRangeStart 和 commentRangeEnd 标记
    for elem in para_elem.iter():
        tag = _tag(elem)
        if tag == 'commentRangeStart' or tag == 'commentRangeEnd' or tag == 'commentReference':
            cid = elem.get(f'{W_NS}id')
            if cid:
                comment_ids.add(cid)
    return list(comment_ids)


def has_comment_on_paragraph(para_elem, comments):
    """
    检查段落是否包含批注。
    """
    return len(get_comment_ids_for_paragraph(para_elem)) > 0


def get_comment_texts_for_paragraph(comment_ids, comments):
    """
    获取段落关联的所有批注内容。
    """
    result = []
    for cid in comment_ids:
        if cid in comments:
            result.append(comments[cid])
    return result


# ========== 段落级文本收集 ==========

def _get_text_elements(container):
    """
    按顺序收集容器中所有可翻译的文本元素。
    返回: [(xml_element, text_type, original_text), ...]
        text_type: 'text' | 'ins_text' | 'del_text'
    """
    items = []
    for child in list(container):
        tag = _tag(child)
        if tag == 'r':
            for rc in child:
                rt = _tag(rc)
                if rt == 't' and rc.text is not None:
                    items.append((rc, 'text', rc.text))
        elif tag == 'ins':
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 't' and rc.text is not None:
                        items.append((rc, 'ins_text', rc.text))
        elif tag == 'del':
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 'delText' and rc.text is not None:
                        items.append((rc, 'del_text', rc.text))
    return items


def collect_paragraphs(doc, comments=None):
    """
    按段落级别收集所有待翻译文本。
    返回 list of dict
    """
    paragraphs = []
    idx = 0
    seen_cells = set()

    def _add(source, info, container):
        nonlocal idx
        elems = _get_text_elements(container)
        if not elems:
            return
        full = ''.join(e[2] for e in elems).strip()
        if not full:
            return

        # 检查是否有批注
        para_has_comments = has_comment_on_paragraph(container, comments or {})
        comment_ids = get_comment_ids_for_paragraph(container)

        # 检查是否有修订，并获取带修订标记的原文和干净文本
        para_has_revisions = has_revisions_in_paragraph(container)
        revision_info = get_text_with_revision_markers(container)
        clean_text = get_clean_text_for_translation(container)

        # 标记是否有批注或修订
        has_special = para_has_comments or para_has_revisions

        lengths = [len(e[2]) for e in elems]
        paragraphs.append({
            "idx": idx, "source": source, "source_info": info,
            "elements": elems, "full_text": full, "run_lengths": lengths,
            "has_comments": para_has_comments,
            "has_revisions": para_has_revisions,
            "has_special": has_special,  # 是否有批注或修订
            "comment_ids": comment_ids,
            "revision_items": get_revision_items_for_paragraph(container),  # 修订项目列表
            "original_with_markers": revision_info["full_text"],  # 带修订标记的原文
            "clean_text": clean_text,  # 干净文本（用于翻译）
            "_para_elem": container,  # 保存段落 XML 元素引用，用于插入新段落
        })
        idx += 1

    for i, para in enumerate(doc.paragraphs):
        _add("para", {"para_idx": i}, para._p)

    for ti, table in enumerate(doc.tables):
        for ri, row in enumerate(table.rows):
            for ci, cell in enumerate(row.cells):
                cid = (ti, ri, ci)
                if cid in seen_cells:
                    continue
                seen_cells.add(cid)
                for pi, para in enumerate(cell.paragraphs):
                    _add("table", {"ti": ti, "ri": ri, "ci": ci, "pi": pi}, para._p)

    for section in doc.sections:
        for hf_type in ('header', 'footer'):
            hf = getattr(section, hf_type, None)
            if hf and hf.is_linked_to_previous is False:
                for pi, para in enumerate(hf.paragraphs):
                    _add(hf_type, {"pi": pi}, para._p)

    return paragraphs


# ========== 按比例切分 ==========

def split_by_ratio(translated, run_lengths):
    """
    按原始 run 字符长度比例切分译文。
    最后一个 run 取剩余全部文本。
    """
    if not run_lengths:
        return []
    if len(run_lengths) == 1:
        return [translated]

    total = sum(run_lengths)
    if total == 0:
        return [''] * len(run_lengths)

    result = []
    remaining = translated
    trans_len = len(translated)

    for i, length in enumerate(run_lengths):
        if i == len(run_lengths) - 1:
            result.append(remaining)
            break
        ratio = length / total
        alloc = max(1, round(trans_len * ratio))
        if alloc >= len(remaining):
            result.append(remaining)
            for _ in range(i + 1, len(run_lengths)):
                result.append('')
            break
        result.append(remaining[:alloc])
        remaining = remaining[alloc:]

    return result


# ========== 字体设置 ==========

def set_font_songti(text_element):
    """设置文本元素所属 run 的字体为宋体"""
    r_elem = text_element.getparent()
    if r_elem is None:
        return
    rPr = r_elem.find(f'{W_NS}rPr')
    if rPr is None:
        rPr = etree.SubElement(r_elem, f'{W_NS}rPr')
    rFonts = rPr.find(f'{W_NS}rFonts')
    if rFonts is None:
        rFonts = etree.SubElement(rPr, f'{W_NS}rFonts')
    rFonts.set(f'{W_NS}eastAsia', '宋体')
    rFonts.set(f'{W_NS}ascii', 'Times New Roman')
    rFonts.set(f'{W_NS}hAnsi', 'Times New Roman')


# 向后兼容：保留旧函数名但指向新函数
set_font_times = set_font_songti


# ========== 翻译 ==========

def build_translate_prompt(items, terms, custom_instructions=None, translate_comments=True):
    """
    构建翻译提示词

    重要提示：
    1. 确保 AI 生成的 JSON 不含中文引号（或将其转义），以避免 JSON 解析错误。
    2. 对于有批注或修订的段落（has_special=True）：
       - 英文原文保留修订标记（~~deleted~~、_inserted_）
       - 中文翻译修订后的完整语义（不是分别翻译删除和增加）
    3. 翻译批注内容。
    """
    items_json = json.dumps(items, ensure_ascii=False, indent=2)
    terms_json = json.dumps(terms, ensure_ascii=False, indent=2)

    # 检查是否有特殊段落（有批注或修订）
    has_special_items = any(item.get('has_special', False) for item in items)
    has_revision_items = any(item.get('has_revisions', False) for item in items)

    instructions = """
翻译要求：
1. 使用自然流畅的中文翻译风格，符合法律合同用语规范
2. 以下术语表中的英文必须使用对应中文翻译，确保全文一致：
{terms}
3. 保持条款编号（如 1.1, 2.3.a, Section 3）和文档结构完整
4. 公司名称、产品名称可保留英文原名
5. **重要**：在 translated_text 字段中，如需使用引号，请使用单引号「」或直引号 ' ，避免使用与 JSON 分隔符冲突的双引号。或者直接不使用引号。
6. 返回 JSON 数组，每项包含 idx（数字）和 translated_text（字符串）
7. **只返回纯 JSON 数组，不要添加任何解释、代码块标记或其他文字**
8. JSON 数组格式示例：
[
  {{"idx": 0, "translated_text": "这是第一条翻译内容"}},
  {{"idx": 1, "translated_text": "这是第二条翻译内容「引用文本」"}}
]
""".format(terms=terms_json)

    # 如果有带修订的段落，添加额外说明
    if has_revision_items:
        instructions += """
\n\n**【修订内容翻译规则】（重要）**

对于标注了 "has_revisions": true 的段落，请注意以下规则：

1. **翻译的是什么**：
   - 使用 "clean_text" 字段进行翻译（这是移除删除内容、保留插入内容后的文本，代表修订后的最终语义）
   - **不要**分别翻译"删除内容"和"插入内容"

2. **输出格式**（必须严格遵守）：
   - translated_text 只包含【中文译文】，格式为：
     【中文译文】<翻译修订后完整语义的中文>

   例如：
   {{
     "idx": 5,
     "translated_text": "【中文译文】买方应立即支付发票。"
   }}

   注意：英文原文会被自动保留在原段落中（包括修订气泡和标记），
   你只需提供中文译文，系统会在段落后插入译文行。

3. **修订标记说明**：
   - ~~deleted~~ 表示被删除的内容（显示为删除线）
   - _inserted_ 表示新增的内容（显示为下划线）
   - original_with_markers 字段显示原文（含修订标记）

4. **翻译策略**：
   - 理解修订后的完整语义
   - 翻译成流畅的中文
   - 中文译文**不加任何修订标记**
"""

    # 如果有带批注的段落，添加额外说明
    if has_special_items and not has_revision_items:
        instructions += """
\n\n**【批注内容翻译规则】**

对于标注了 "has_comments": true 的段落：
- 英文原文保留不翻译
- 批注内容翻译为中文（在 comment_translations 字段中返回）
"""

    if custom_instructions:
        instructions += f"\n\n自定义要求：\n{custom_instructions}"

    prompt = f"""你是一个专业的法律合同翻译器。请将以下英文合同段落翻译为中文。

{instructions}

待翻译段落：
{items_json}"""

    return prompt


def build_comment_translate_prompt(comments_dict, terms):
    """
    构建批注翻译提示词。
    comments_dict: {comment_id: {"author": str, "date": str, "text": str}}
    """
    if not comments_dict:
        return None

    items = []
    for cid, info in comments_dict.items():
        items.append({
            "id": cid,
            "text": info["text"],
            "author": info.get("author", "")
        })

    items_json = json.dumps(items, ensure_ascii=False, indent=2)
    terms_json = json.dumps(terms, ensure_ascii=False, indent=2)

    prompt = f"""你是一个专业的法律合同翻译器。请将以下英文批注（comments）翻译为中文。

翻译要求：
1. 使用自然流畅的中文翻译风格
2. 以下术语表中的英文必须使用对应中文翻译：
{terms_json}
3. **重要**：如需使用引号，请使用单引号「」或直引号 '，避免使用与 JSON 分隔符冲突的双引号。
4. 返回 JSON 数组，每项包含 id（批注ID）和 translated_text（翻译后的批注内容）
5. **只返回纯 JSON 数组，不要添加任何解释、代码块标记或其他文字**

待翻译批注：
{items_json}"""

    return prompt


def parse_translation_response(response_text):
    """从 AI 响应中解析 JSON 翻译结果

    重要：处理以下特殊字符问题：
    1. 中文引号 " " 与 JSON 双引号冲突
    2. Unicode 转义序列 \u201c \u201d
    3. 其他可能导致 JSON 解析失败的特殊字符
    """
    import html

    # 预处理：处理常见编码问题
    cleaned = response_text.strip()

    # 如果包含 markdown 代码块标记，去除它们
    if cleaned.startswith('```'):
        # 找到第一个 { 或 [
        for i, c in enumerate(cleaned):
            if c in '{[':
                cleaned = cleaned[i:]
                break
        # 去除结尾的 ```
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3].strip()

    # 尝试直接解析
    try:
        data = json.loads(cleaned)
        return normalize_translations(data)
    except json.JSONDecodeError:
        pass

    # 尝试提取 JSON 数组
    patterns = [
        r'\[\s*\{[\s\S]*\}\s*\]',  # 数组
        r'\{[\s\S]*"translated_text"[\s\S]*\}',  # 对象
    ]
    for pattern in patterns:
        matches = re.findall(pattern, cleaned)
        for match in matches:
            try:
                data = json.loads(match)
                return normalize_translations(data)
            except json.JSONDecodeError:
                # 如果失败，尝试替换中文引号后再解析
                fixed = match.replace('\u201c', '\u201c').replace('\u201d', '\u201d')
                # 使用 html.parser 解码 HTML 实体
                try:
                    data = json.loads(fixed)
                    return normalize_translations(data)
                except:
                    continue
    return None


def normalize_translations(data):
    """规范化翻译结果，处理特殊字符"""
    if isinstance(data, list):
        result = []
        for item in data:
            if isinstance(item, dict) and "translated_text" in item:
                # 处理中文引号等特殊字符
                text = item["translated_text"]
                if isinstance(text, str):
                    # 确保文本中的引号不会干扰 JSON 序列化
                    # 但在最终结果中保留它们供显示
                    item["translated_text"] = text
                result.append(item)
        return result
    return data


def batch_translate(paragraphs, ai_translate_func, terms, custom_instructions=None,
                    comment_translations=None):
    """
    按段落批量翻译
    paragraphs: 段落列表
    ai_translate_func: 接受 prompt，返回翻译结果文本
    返回: {
        idx: translated_text,
        ...
    }
    """
    if not paragraphs:
        return {}

    BATCH_SIZE = 4000

    # 分离普通段落和特殊段落（有批注或修订）
    normal_paragraphs = [p for p in paragraphs if not p.get('has_special', False)]
    special_paragraphs = [p for p in paragraphs if p.get('has_special', False)]

    # 分离修订段落（有修订的段落需要特殊处理）
    revision_paragraphs = [p for p in special_paragraphs if p.get('has_revisions', False)]
    comment_only_paragraphs = [p for p in special_paragraphs if p.get('has_comments', False) and not p.get('has_revisions', False)]

    all_results = {}

    # ========== 1. 翻译修订段落（需要特殊格式）==========
    if revision_paragraphs:
        # 构建包含完整信息的翻译项
        items = []
        for p in revision_paragraphs:
            items.append({
                "idx": p["idx"],
                "original_with_markers": p.get("original_with_markers", p["full_text"]),
                "clean_text": p.get("clean_text", p["full_text"]),  # 用于翻译的干净文本
                "has_revisions": True,
                "has_comments": p.get("has_comments", False),
                "comment_ids": p.get("comment_ids", [])
            })

        prompt = build_translate_prompt(items, terms, custom_instructions)
        response = ai_translate_func(prompt)
        results = parse_translation_response(response)
        if results:
            for r in results:
                all_results[r["idx"]] = r["translated_text"]

    # ========== 2. 翻译普通段落 + 只有批注的段落 ==========
    # 只有批注的段落也按普通方式翻译（直接翻译成中文，不保留英文原文）
    normal_and_comment_only = normal_paragraphs + comment_only_paragraphs
    if normal_and_comment_only:
        total = sum(len(p["full_text"]) for p in normal_and_comment_only)

        if total <= BATCH_SIZE:
            items = [{"idx": p["idx"], "text": p["full_text"]} for p in normal_and_comment_only]
            prompt = build_translate_prompt(items, terms, custom_instructions)
            response = ai_translate_func(prompt)
            results = parse_translation_response(response)
            if results:
                for r in results:
                    all_results[r["idx"]] = r["translated_text"]
        else:
            # 分批处理
            batches = []
            cur_batch = []
            cur_chars = 0
            for p in normal_and_comment_only:
                if cur_chars + len(p["full_text"]) > BATCH_SIZE and cur_batch:
                    batches.append(cur_batch)
                    cur_batch = []
                    cur_chars = 0
                cur_batch.append(p)
                cur_chars += len(p["full_text"])
            if cur_batch:
                batches.append(cur_batch)

            for batch in batches:
                items = [{"idx": p["idx"], "text": p["full_text"]} for p in batch]
                prompt = build_translate_prompt(items, terms, custom_instructions)
                response = ai_translate_func(prompt)
                results = parse_translation_response(response)
                if results:
                    for r in results:
                        all_results[r["idx"]] = r["translated_text"]

    return all_results


def translate_comments(comments, ai_translate_func, terms):
    """
    翻译批注内容。
    返回: {comment_id: translated_text}
    """
    if not comments:
        return {}

    prompt = build_comment_translate_prompt(comments, terms)
    if not prompt:
        return {}

    response = ai_translate_func(prompt)
    results = parse_translation_response(response)

    if results:
        return {r["id"]: r["translated_text"] for r in results}
    return {}


def translate_revisions(revisions, ai_translate_func, terms):
    """
    翻译修订内容（删除/插入的文本）。
    revisions: list of {"type": "deletion"|"insertion", "text": str}
    返回: list of {"type": ..., "original": ..., "translated": ...}
    """
    if not revisions:
        return []

    items = []
    for i, rev in enumerate(revisions):
        items.append({
            "idx": i,
            "type": rev["type"],
            "text": rev["text"]
        })

    items_json = json.dumps(items, ensure_ascii=False, indent=2)
    terms_json = json.dumps(terms, ensure_ascii=False, indent=2)

    prompt = f"""你是一个专业的法律合同翻译器。请将以下修订内容（删除或插入的英文文本）翻译为中文。

翻译要求：
1. 简洁准确地翻译每个修订项
2. 以下术语表中的英文必须使用对应中文翻译：
{terms_json}
3. 返回 JSON 数组，每项包含 idx、type、original、translated
4. **只返回纯 JSON 数组，不要添加任何解释、代码块标记或其他文字**
5. JSON 数组格式示例：
[
  {{"idx": 0, "type": "deletion", "original": "not", "translated": "不"}},
  {{"idx": 1, "type": "insertion", "original": "immediately", "translated": "立即"}}
]

待翻译修订内容：
{items_json}"""

    response = ai_translate_func(prompt)
    results = parse_translation_response(response)

    if results:
        return results
    return []


# ========== 文本替换 ==========

def apply_translations(paragraphs, translations):
    """将翻译结果按比例切分回写到各 XML 元素（普通段落）"""
    count = 0
    for p in paragraphs:
        if p.get('has_special', False):
            continue  # 跳过特殊段落，由 apply_translations_with_markup 处理
        translated = translations.get(p["idx"])
        if translated is None:
            continue
        if isinstance(translated, dict):
            translated = translated.get("text", "")
        parts = split_by_ratio(translated, p["run_lengths"])
        for i, (elem, _type, _orig) in enumerate(p["elements"]):
            if i < len(parts):
                elem.text = parts[i]
            else:
                elem.text = ''
            set_font_songti(elem)
        count += 1
    return count


def apply_translations_with_markup(paragraphs, translations, revision_translations=None):
    """
    将翻译结果回写到各 XML 元素。

    处理逻辑：
    1. **有修订的段落**：保留英文原文，在段落后插入【中文译文】行
       - 删除内容（w:del）：保留英文原文，保持删除线
       - 插入内容（w:ins）：保留英文原文，保持下划线
       - 正常内容（w:r）：保留英文原文
       - 字体统一为宋体
    2. **有批注的段落**：直接翻译中文，英文原文保留，
       批注内容单独翻译
    3. **普通段落**：直接翻译为中文

    revision_translations: 修订内容的翻译字典（可选，用于细粒度控制）
        格式：{para_idx: {"del_items": [...], "ins_items": [...]}}

    返回：处理的段落数量
    """
    from docx.oxml import OxmlElement
    from docx.shared import Pt
    from docx.oxml.ns import qn

    count = 0

    # 构建修订翻译查找表
    rev_trans = {}
    if revision_translations:
        for para_idx, rev_data in revision_translations.items():
            rev_trans[para_idx] = rev_data

    for p in paragraphs:
        translated = translations.get(p["idx"])
        if translated is None:
            continue

        # 获取段落 XML 元素
        para_elem = p.get("_para_elem")

        # ========== 有修订的段落 ==========
        if p.get("has_revisions", False) and para_elem is not None:
            # 修订段落：保留英文原文，在段落后插入【中文译文】行
            if p["idx"] in rev_trans:
                # 使用细粒度修订翻译
                _translate_revision_content(para_elem, rev_trans[p["idx"]], qn)
            else:
                # 保留原文 + 插入【中文译文】行
                _translate_revision_paragraph_old(para_elem, translated, qn)
            count += 1

        # ========== 有批注但无修订的段落 ==========
        elif p.get("has_comments", False):
            full_translated = translated
            parts = split_by_ratio(full_translated, p["run_lengths"])
            for i, (elem, _type, _orig) in enumerate(p["elements"]):
                if i < len(parts):
                    elem.text = parts[i]
                else:
                    elem.text = ''
                set_font_songti(elem)
            count += 1

        # ========== 普通段落 ==========
        else:
            full_translated = translated
            parts = split_by_ratio(full_translated, p["run_lengths"])
            for i, (elem, _type, _orig) in enumerate(p["elements"]):
                if i < len(parts):
                    elem.text = parts[i]
                else:
                    elem.text = ''
                set_font_songti(elem)
            count += 1

    return count


def _translate_revision_paragraph_old(para_elem, translated_text, qn):
    """
    翻译修订段落：在段落后插入【中文译文】行，同时保留英文原文及修订标记样式。

    策略：
    - 英文原文段落保留不变（修订结构 del/ins 保持）
    - 在段落后插入新段落，包含【中文译文】<翻译文本>
    - 字体统一为宋体
    """
    # 在段落后插入【中文译文】行
    _insert_translation_paragraph(para_elem, translated_text, qn)


def _translate_revision_paragraph(para_elem, translated_text, qn):
    """
    翻译修订段落中的英文内容为中文，同时保留修订标记样式。

    策略：
    - 将翻译文本填入第一个正常文本元素
    - 清空所有其他文本元素的内容
    - 修订结构（del/ins）保留在XML中用于显示修订标记
    - 字体统一为宋体（中文）/ Times New Roman（西文）
    """
    from docx.oxml import OxmlElement

    # 收集所有文本元素
    text_elements = []  # [(xml_element, text_type)]
    first_normal_elem = None

    for child in list(para_elem):
        tag = _tag(child)
        if tag == 'r':
            for rc in child:
                rt = _tag(rc)
                if rt == 't' and rc.text is not None:
                    text_elements.append((rc, 'text'))
                    if first_normal_elem is None:
                        first_normal_elem = (rc, 'text')
        elif tag == 'ins':
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 't' and rc.text is not None:
                        text_elements.append((rc, 'ins_text'))
        elif tag == 'del':
            for r in child.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 'delText' and rc.text is not None:
                        text_elements.append((rc, 'del_text'))

    if not text_elements:
        return

    # 策略：将完整翻译填入第一个正常文本元素
    # 修订结构保留（用于Word中显示修订标记）
    if first_normal_elem:
        elem, elem_type = first_normal_elem
        elem.text = translated_text
        _set_font_on_element(elem, elem_type, para_elem, qn)

    # 清空其他所有元素的内容
    for elem, elem_type in text_elements:
        if (elem, elem_type) != first_normal_elem:
            elem.text = ''
            # 修订元素也需要清空文本（保留结构）
            _set_font_on_element(elem, elem_type, para_elem, qn)


def _split_translation_by_ratio(translated_text, text_elements, total_chars):
    """
    按原始字符长度比例切分翻译文本。
    返回: [(element, text_type, translated_text), ...]
    """
    if not text_elements:
        return []

    trans_len = len(translated_text)
    result = []
    remaining = translated_text

    for i, (elem, text_type, orig_text) in enumerate(text_elements):
        if i == len(text_elements) - 1:
            # 最后一个元素获取剩余全部
            result.append((elem, text_type, remaining))
            break

        # 按比例计算应分配的字符数
        ratio = len(orig_text) / total_chars
        alloc = max(1, round(trans_len * ratio))

        if alloc >= len(remaining):
            result.append((elem, text_type, remaining))
            remaining = ""
        else:
            result.append((elem, text_type, remaining[:alloc]))
            remaining = remaining[alloc:]

        total_chars -= len(orig_text)

    return result


def _set_font_on_element(text_elem, text_type, para_elem, qn):
    """
    设置文本元素所属 run 的字体为宋体。
    需要根据元素类型找到对应的 run 元素。
    """
    # text_elem 可能是 w:t 或 w:delText，需要找到父级 run
    parent = text_elem.getparent()

    # 如果父级是 run（对于 w:t）或 del（对于 w:delText）
    if parent is None:
        return

    parent_tag = _tag(parent)

    if parent_tag == 'r':
        # 正常文本或 ins 内的文本
        run_elem = parent
    elif parent_tag == 'del':
        # delText 的父级是 del，del 的父级是 run
        run_elem = parent.getparent()
    else:
        # 尝试向上查找 run
        run_elem = parent
        while run_elem is not None and _tag(run_elem) != 'r':
            run_elem = run_elem.getparent()

    if run_elem is None:
        return

    rPr = run_elem.find(f'{W_NS}rPr')
    if rPr is None:
        rPr = etree.SubElement(run_elem, f'{W_NS}rPr')

    rFonts = rPr.find(f'{W_NS}rFonts')
    if rFonts is None:
        rFonts = etree.SubElement(rPr, f'{W_NS}rFonts')

    rFonts.set(qn('w:eastAsia'), '宋体')
    rFonts.set(qn('w:ascii'), 'Times New Roman')
    rFonts.set(qn('w:hAnsi'), 'Times New Roman')


def _translate_revision_content(para_elem, rev_data, qn):
    """
    翻译修订段落中的英文内容为中文，同时保留修订标记样式。

    - w:del 元素内的文本：翻译成中文，保持删除线样式
    - w:ins 元素内的文本：翻译成中文，保持下划线样式
    - w:r 元素内的文本：翻译成中文
    """
    del_items = rev_data.get("del_items", [])
    ins_items = rev_data.get("ins_items", [])

    # 构建翻译查找表
    del_map = {item["original"]: item["translated"] for item in del_items}
    ins_map = {item["original"]: item["translated"] for item in ins_items}

    def _process_element(elem):
        """递归处理元素"""
        tag = _tag(elem)

        if tag == 'del':
            # 删除内容：翻译并保持删除线
            for r in elem.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 'delText' and rc.text:
                        # 翻译删除内容
                        translated = del_map.get(rc.text, rc.text)
                        rc.text = translated
                        # 确保字体为宋体（中文）/ Times New Roman（西文）
                        _set_font_on_run(r, qn)
            return

        elif tag == 'ins':
            # 插入内容：翻译并保持下划线
            for r in elem.findall(f'{W_NS}r'):
                for rc in r:
                    rt = _tag(rc)
                    if rt == 't' and rc.text:
                        # 翻译插入内容
                        translated = ins_map.get(rc.text, rc.text)
                        rc.text = translated
                        # 确保字体为宋体（中文）/ Times New Roman（西文）
                        _set_font_on_run(r, qn)
            return

        elif tag == 'r':
            # 正常文本：直接翻译
            for rc in elem:
                rt = _tag(rc)
                if rt == 't' and rc.text:
                    # 这里rc.text需要在后续被翻译替换
                    # 但由于我们已经有了完整翻译，这里不做处理
                    pass
            return

        # 递归处理子元素
        for child in list(elem):
            _process_element(child)

    def _set_font_on_run(r_elem, qn):
        """设置 run 的字体为宋体"""
        rPr = r_elem.find(f'{W_NS}rPr')
        if rPr is None:
            rPr = etree.SubElement(r_elem, f'{W_NS}rPr')
        rFonts = rPr.find(f'{W_NS}rFonts')
        if rFonts is None:
            rFonts = etree.SubElement(rPr, f'{W_NS}rFonts')
        rFonts.set(qn('w:eastAsia'), '宋体')
        rFonts.set(qn('w:ascii'), 'Times New Roman')
        rFonts.set(qn('w:hAnsi'), 'Times New Roman')

    # 处理段落中的所有修订元素
    for child in list(para_elem):
        _process_element(child)


def _insert_translation_paragraph(para_elem, translation_text, qn):
    """
    在段落元素后插入一个包含翻译文本的新段落。

    参数：
        para_elem: 段落 XML 元素
        translation_text: 翻译文本（如 "【中文译文】订阅方应立即支付服务费用。"）
        qn: docx 命名空间函数
    """
    from docx.oxml import OxmlElement

    # 创建新段落
    new_para = OxmlElement('w:p')

    # 创建新 run
    new_run = OxmlElement('w:r')

    # 添加 run 属性（字体：宋体）
    rPr = OxmlElement('w:rPr')
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:eastAsia'), '宋体')
    rFonts.set(qn('w:ascii'), 'Times New Roman')
    rFonts.set(qn('w:hAnsi'), 'Times New Roman')
    rPr.append(rFonts)
    new_run.append(rPr)

    # 添加文本
    t = OxmlElement('w:t')
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = translation_text
    new_run.append(t)

    new_para.append(new_run)

    # 在段落后插入
    para_elem.addnext(new_para)


# ========== 两阶段工作流（导出 → 外部翻译 → 回写）==========

def export_paragraphs(input_path, output_json_path, terms=None):
    """
    阶段1：从文档收集段落并导出为 JSON，供外部 AI 翻译。
    产出 JSON 中包含：段落文本、修订标记、批注信息、run_lengths 等完整上下文。
    """
    if terms is None:
        terms = DEFAULT_TERMS

    doc = Document(input_path)
    comments = load_comments(input_path)
    paragraphs = collect_paragraphs(doc, comments)

    export_data = {
        "terms": terms,
        "comments": comments,
        "paragraphs": [
            {
                "idx": p["idx"],
                "full_text": p["full_text"],
                "run_lengths": p["run_lengths"],
                "has_revisions": p.get("has_revisions", False),
                "has_comments": p.get("has_comments", False),
                "has_special": p.get("has_special", False),
                "original_with_markers": p.get("original_with_markers", p["full_text"]),
                "clean_text": p.get("clean_text", p["full_text"]),
            }
            for p in paragraphs
        ],
        "stats": {
            "total": len(paragraphs),
            "revision_count": sum(1 for p in paragraphs if p.get("has_revisions")),
            "comment_count": sum(1 for p in paragraphs if p.get("has_comments")),
            "total_chars": sum(len(p["full_text"]) for p in paragraphs),
        }
    }

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"已导出 {len(paragraphs)} 个段落到 {output_json_path}")
    print(f"  修订段落: {export_data['stats']['revision_count']}")
    print(f"  含批注段落: {export_data['stats']['comment_count']}")
    print(f"  总字符数: {export_data['stats']['total_chars']}")
    return export_data


def apply_translations_from_file(input_path, translations_json_path, output_path):
    """
    阶段2：从 JSON 加载翻译结果，回写到文档。
    翻译 JSON 格式：[{"idx": 0, "translated_text": "..."}, ...] 或 {"0": "...", "1": "..."}
    """
    with open(translations_json_path, 'r', encoding='utf-8') as f:
        translations_raw = json.load(f)

    # 支持两种格式：list 或 dict
    if isinstance(translations_raw, list):
        translations = {item["idx"]: item["translated_text"] for item in translations_raw}
    elif isinstance(translations_raw, dict):
        translations = {int(k): v for k, v in translations_raw.items()}
    else:
        raise ValueError(f"不支持的翻译数据格式: {type(translations_raw)}")

    doc = Document(input_path)
    comments = load_comments(input_path)
    paragraphs = collect_paragraphs(doc, comments)

    applied = apply_translations_with_markup(paragraphs, translations)
    doc.save(output_path)

    print(f"已回写 {applied} 个段落到 {output_path}")
    return applied


# ========== 主流程 ==========

def translate_document(input_path, output_path, ai_translate_func,
                      terms=None, custom_instructions=None):
    """
    翻译整个文档。

    参数：
        input_path: 输入的 .docx 文件路径
        output_path: 输出的 .docx 文件路径
        ai_translate_func: 接受 prompt 字符串，返回翻译结果文本
        terms: 术语表字典，可选
        custom_instructions: 自定义翻译指令，可选
    """
    if terms is None:
        terms = DEFAULT_TERMS

    doc = Document(input_path)

    # 加载批注
    comments = load_comments(input_path)
    print(f"加载了 {len(comments)} 条批注")

    # 1. 按段落收集
    paragraphs = collect_paragraphs(doc, comments)
    if not paragraphs:
        print("文档中没有可翻译的文本。")
        doc.save(output_path)
        return

    # 统计
    revision_count = sum(1 for p in paragraphs if p.get('has_revisions', False))
    comment_count = sum(1 for p in paragraphs if p.get('has_comments', False))
    total_chars = sum(len(p["full_text"]) for p in paragraphs)
    print(f"共 {len(paragraphs)} 个段落，{total_chars} 字符待翻译。")
    print(f"其中 {revision_count} 个段落包含修订，{comment_count} 个段落包含批注。")

    # 2. 翻译批注内容
    comment_translations = translate_comments(comments, ai_translate_func, terms)
    if comment_translations:
        print(f"翻译了 {len(comment_translations)} 条批注")

    # 3. 批量翻译段落（修订段落已包含在 batch_translate 中）
    translations = batch_translate(paragraphs, ai_translate_func, terms,
                                   custom_instructions, comment_translations)
    print(f"翻译完成，{len(translations)} 个段落。")

    # 4. 处理批注翻译（为有批注的段落添加批注翻译）
    for p in paragraphs:
        if p.get('has_comments', False) and p['idx'] in translations:
            comment_ids = p.get('comment_ids', [])
            for cid in comment_ids:
                if cid in comment_translations:
                    translations[p['idx']] += f"\n【批注 {cid} 译文】{comment_translations[cid]}"

    # 5. 切分回写 + 统一宋体
    applied = apply_translations_with_markup(paragraphs, translations)
    print(f"已替换 {applied} 个段落。")

    # 6. 保存
    doc.save(output_path)
    print(f"翻译完成：{output_path}")


def main():
    parser = argparse.ArgumentParser(description='Docx 文档翻译器')
    parser.add_argument('input', help='输入 .docx 文件')
    parser.add_argument('output', nargs='?', help='输出 .docx 文件（默认：原文件名+中文翻译版）')
    parser.add_argument('--terms', '-t', help='术语表 JSON 文件路径')
    parser.add_argument('--instructions', '-i', help='自定义翻译指令文件路径')
    parser.add_argument('--export', '-e', metavar='JSON', help='导出段落到 JSON 文件（两阶段模式-阶段1）')
    parser.add_argument('--apply', '-a', metavar='JSON', help='从 JSON 加载翻译并回写（两阶段模式-阶段2）')

    args = parser.parse_args()

    input_file = Path(args.input)

    # 两阶段模式：导出
    if args.export:
        if not input_file.exists():
            print(f"错误：文件不存在 {input_file}")
            sys.exit(1)
        terms = DEFAULT_TERMS.copy()
        if args.terms:
            with open(args.terms, 'r', encoding='utf-8') as f:
                terms.update(json.load(f))
        export_paragraphs(str(input_file), args.export, terms)
        print("\n请将导出的 JSON 中的 paragraphs 翻译后，以如下格式保存：")
        print('  [{"idx": 0, "translated_text": "中文翻译"}, ...]')
        print(f"然后运行: python {sys.argv[0]} {args.input} <输出> --apply <翻译JSON>")
        return

    # 两阶段模式：回写
    if args.apply:
        if not input_file.exists():
            print(f"错误：文件不存在 {input_file}")
            sys.exit(1)
        output_file = Path(args.output) if args.output else input_file.parent / f"{input_file.stem}（中文翻译版）{input_file.suffix}"
        apply_translations_from_file(str(input_file), args.apply, str(output_file))
        return

    # 单阶段模式：需要 AI 翻译函数（由 Agent 提供）
    if not input_file.exists():
        print(f"错误：文件不存在 {input_file}")
        sys.exit(1)

    if args.output:
        output_file = Path(args.output)
    else:
        output_file = input_file.parent / f"{input_file.stem}（中文翻译版）{input_file.suffix}"

    terms = DEFAULT_TERMS.copy()
    if args.terms:
        with open(args.terms, 'r', encoding='utf-8') as f:
            terms.update(json.load(f))

    custom_instructions = None
    if args.instructions:
        with open(args.instructions, 'r', encoding='utf-8') as f:
            custom_instructions = f.read()

    def mock_translate(prompt):
        match = re.search(r'\[[\s\S]*\]', prompt)
        if match:
            data = json.loads(match.group())
            return '[{"idx": ' + str(data[0]["idx"]) + ', "translated_text": "[请使用 AI 翻译"]}]'
        return '[]'

    translate_document(str(input_file), str(output_file), mock_translate, terms, custom_instructions)


if __name__ == '__main__':
    main()
