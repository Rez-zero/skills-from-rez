# Contract Translator Skill

将英文合同文档翻译为中文，支持对批注和修订内容的特殊处理。

---

## 功能说明

### 核心能力

1. **按段落级别翻译** - 避免 run 级别碎片化翻译
2. **内置法律术语表** - 50+ 核心法律术语自动一致翻译
3. **修订气泡完整保留** - 原有的 track changes（侧边栏修订气泡、作者、日期、删除线/下划线）完全保留
4. **修订段落译文插入** - 含修订的段落，英文原文完整保留，在段落后插入【中文译文】行
5. **批注内容直接翻译** - 批注内容直接翻译为中文，不保留英文原文
6. **字体统一为宋体** - 中文使用宋体，西文使用 Times New Roman
7. **不产生新修订** - 翻译行为本身不修改修订 XML 结构

---

## 核心概念：批注/修订内容的处理规则

### 核心原则

| 情况 | 英文原文 | 中文翻译 |
|------|---------|---------|
| **有修订的段落** | ✅ 完整保留（含修订样式） | ✅ 在段落后插入【中文译文】行 |
| **有批注的段落** | ❌ 不保留 | ✅ 直接翻译 |
| **批注内容** | ❌ 不保留 | ✅ 直接翻译 |
| **普通段落** | ❌ 不保留 | ✅ 直接翻译 |

| 类别 | 定义 | 处理方式 |
|------|------|----------|
| **修订内容** | 原文档中的 track changes（插入/删除） | 英文原文完整保留 + 在段落后插入【中文译文】行 |
| **批注内容** | 用户添加的评论文字 | 直接翻译为中文（不保留英文原文） |
| **有批注的正文** | 段落中包含批注（comment）标记的文本 | 直接翻译为中文（不保留英文原文） |

### 2. 处理规则详解

#### 2.1 修订内容（保留原文 + 插入【中文译文】行）

**规则**：
- 该段落的**英文原文完整保留**（包括修订标记样式：删除线/下划线）
- 原 XML 结构完整保留（包括 `w:ins`/`w:del` 元素）
- 侧边栏修订气泡（含作者、日期）**完整保留**
- 修订标记（删除线/下划线）**完整保留**
- 在段落后插入**【中文译文】**行，包含完整翻译
- 字体统一为宋体（中文）/ Times New Roman（西文）

**输出效果示例**（Word 中）：
```
┌─────────────────────────────────────────────────────────────────────┐
│ The Subscriber shall ~~not~~ _immediately_ pay...                   │  ← 英文原文（含修订样式）
│ 【中文译文】订阅方应立即支付...                                       │  ← 中文翻译行
│      John | 2024-01-15                                             │
└─────────────────────────────────────────────────────────────────────┘
```

**翻译策略**：
- 提取修订后的完整语义（删除内容移除，插入内容保留）
- 将整个段落翻译成流畅的中文
- 【中文译文】行单独显示，不含修订标记

#### 2.2 批注内容（直接翻译）

**规则**：
- 提取批注文字（英文）
- **直接翻译为中文，不保留英文原文**
- 以结构化方式输出

**输出格式示例**：
```
【批注译文】需要与法务团队确认罚则条款。
```

#### 2.3 有批注的正文段落

**规则**：
- 正文段落内容**直接翻译为中文，不保留英文原文**
- 批注内容单独翻译并附加在正文翻译后

**输出格式示例**：
```
[正文中文翻译]
【批注译文】xxx
```

#### 2.4 修订内容的语义理解

**规则**：
- 提取 `w:ins`（插入）和 `w:del`（删除）的文本内容
- **翻译修订后的完整语义**（删除内容移除，插入内容保留）
- **英文原文完整保留**在段落中
- 【中文译文】行单独显示翻译后的中文

**示例**：
| 原修订 | 英文原文（保留修订样式） | 中文译文 |
|--------|------------------------|--------|
| 删除 "not" | The Subscriber shall ~~not~~ pay... | 订阅方应支付... |
| 增加 "immediately" | The Subscriber shall _immediately_ pay... | 订阅方应立即支付... |
| 同时有删除和增加 | The Subscriber shall ~~not~~ _immediately_ pay... | 订阅方应立即支付... |

**关键理解**：
- 修订样式（删除线/下划线）保留在英文原文中
- 【中文译文】行显示翻译后的完整中文意思
- 修订标记展示原始修改过程

### 3. 明确不做的事情

| ❌ 禁止项 | 说明 |
|----------|------|
| 批注段落保留英文原文 | 有批注的正文段落直接翻译为中文，不显示英文原文 |
| 批注内容保留英文原文 | 批注内容直接翻译为中文，不显示英文原文 |

### 4. 模糊点处理

| 问题 | 处理方式 |
|------|----------|
| 一段文字既有批注又有修订 | 分别提取批注和修订操作，各自翻译后以不同标识输出 |
| 被批注/修订段落 + 正常段落混合 | 正常段落只翻译不加英文；特殊段落按上述规则处理 |
| 批注中涉及修订 | 批注翻译时一并处理修订内容 |

---

## 快速开始（Agent 使用方式）

### 命令格式

```
/contract-translator @"<文件路径>"
```

示例：
```
/contract-translator @"C:/Users/xxx/Downloads/Contract.docx"
/contract-translator @"E:/E/VsCode/tonghua/Data Subscription Agreement.docx"
```

### Agent 内部工作流程

当收到翻译请求时，Agent 执行以下步骤：

#### 方式一：使用预存翻译数据（推荐，已有翻译结果时）

当存在预存的 `_translations.json` 或 `_full_translations.json` 文件时，直接加载并应用：

```python
import sys
import json
import os
sys.path.append('C:/Users/Jxz/.workbuddy/skills/contract-translator/scripts')
from docx_translator import collect_paragraphs, apply_translations_with_markup
from docx import Document

input_path = "<用户提供的文件路径>"
output_path = input_path.replace(".docx", "（中文翻译版）.docx")

# 1. 查找预存翻译数据（优先精确匹配，其次模糊匹配）
translations_path = None
input_name = os.path.basename(input_path)

# 优先在工作目录查找同名翻译文件
for candidate in ["_full_translations.json", "_translations.json"]:
    candidate_path = os.path.join(os.path.dirname(input_path), candidate)
    if os.path.exists(candidate_path):
        translations_path = candidate_path
        break

# 如果没找到，在当前工作目录查找
if translations_path is None:
    for candidate in ["_full_translations.json", "_translations.json"]:
        if os.path.exists(candidate):
            translations_path = candidate
            break

# 2. 加载翻译数据
with open(translations_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 转换为 dict 格式：{idx: translated_text}
if isinstance(data, list):
    translations = {item['idx']: item['translated_text'] for item in data}
else:
    translations = data

print(f"加载了 {len(translations)} 条翻译")

# 3. 读取文档
doc = Document(input_path)
paragraphs = collect_paragraphs(doc)

# 4. 应用翻译
count = apply_translations_with_markup(paragraphs, translations)
print(f"已应用 {count} 条翻译")

# 5. 保存
doc.save(output_path)
print(f"已保存至: {output_path}")
print(f"输出文件大小: {os.path.getsize(output_path)} bytes")
```

#### 方式二：调用 AI 实时翻译（无预存数据时）

```python
import sys
import json
sys.path.append('C:/Users/Jxz/.workbuddy/skills/contract-translator/scripts')
from docx_translator import (
    collect_paragraphs, batch_translate, apply_translations_with_markup,
    translate_comments, load_comments, DEFAULT_TERMS
)
from docx import Document

input_path = "<用户提供的文件路径>"
output_path = input_path.replace(".docx", "（中文翻译版）.docx")

# 1. 读取文档并收集段落
doc = Document(input_path)
comments = load_comments(input_path)
paragraphs = collect_paragraphs(doc, comments)

print(f"共 {len(paragraphs)} 个段落")

# 2. 定义 AI 翻译函数（需要用户提供或使用内置翻译服务）
def ai_translate_func(prompt):
    """调用 AI 模型进行翻译"""
    response = your_ai_model.translate(prompt)
    return response

# 3. 翻译
translations = batch_translate(paragraphs, ai_translate_func, DEFAULT_TERMS)

# 4. 应用翻译
count = apply_translations_with_markup(paragraphs, translations)

# 5. 保存
doc.save(output_path)
```

### 翻译数据文件格式

预存翻译数据支持两种格式：

**格式一：JSON 列表（每项含 idx）**
```json
[
  {"idx": 0, "translated_text": "数据订阅协议"},
  {"idx": 1, "translated_text": "本协议由...签订。"}
]
```

**格式二：JSON 字典（idx 为键）**
```json
{
  "0": "数据订阅协议",
  "1": "本协议由...签订。"
}
```

### 输出文件命名

- 默认：`原文件名（中文翻译版）.docx`
- 与输入文件保存在同一目录

---

## 核心功能详解

### 1. 批注/修订原文的处理机制

**规则**：
- 段落中的文本如果有批注或修订，该段落的英文原文**完整保留**
- 修订样式（删除线/下划线）**完整保留**
- 批注内容翻译为中文
- 字体统一为宋体（中文）/ Times New Roman（西文）

**实现逻辑**：
```
if 段落有修订:
    英文原文完整保留（含修订样式）
    在段落后插入【中文译文】行
elif 段落有批注:
    直接翻译为中文
else:
    正常翻译为中文（单行显示）
```

### 2. 文本元素类型

| XML 元素 | 类型 | 说明 |
|---------|------|------|
| `<w:r><w:t>` | text | 正常文本 |
| `<w:ins><w:r><w:t>` | ins_text | 插入内容（翻译后保留下划线样式） |
| `<w:del><w:r><w:delText>` | del_text | 删除内容（翻译后保留删除线样式） |
| `<w:commentRangeStart>` | comment_start | 批注范围起点 |
| `<w:commentRangeEnd>` | comment_end | 批注范围终点 |
| `<w:commentReference>` | comment_ref | 批注引用 |

### 3. 修订内容的提取与翻译

**修订类型**：
- **插入 (ins)**：新增的文本内容 → 保留英文原文，含下划线样式
- **删除 (del)**：被删除的文本内容 → 保留英文原文，含删除线样式

**处理方式**：
1. 从 XML 中提取修订内容及其类型
2. 将整个段落翻译为中文
3. **英文原文完整保留**（含修订样式）
4. **在段落后插入【中文译文】行**

**输出效果**：
- 修订段落显示英文原文（含删除线/下划线）
- 段落后插入【中文译文】行，显示翻译后的中文
- 修订气泡（含作者、日期）完整保留

### 4. 内置法律术语表

`DEFAULT_TERMS` 包含 50+ 核心法律术语：

| 英文 | 中文 |
|------|------|
| Service Provider | 服务提供方 |
| Subscriber | 订阅方 |
| Termination | 终止 |
| Intellectual Property | 知识产权 |
| Confidential Information | 保密信息 |
| Limitation of Liability | 责任限制 |
| Governing Law | 适用法律 |
| Force Majeure | 不可抗力 |
| ... | ... |

### 5. 字体统一为宋体/Times New Roman

- 中文文本（eastAsia）：宋体
- 西文文本（ascii/hAnsi）：Times New Roman
- 保留原文 `w:sz`/`w:szCs` 字号不变

---

## 关键技术细节

### 按比例切分回写

```python
# 示例
# 原始 run_lengths = [6, 5, 3]（共14字符）
# 译文："本协议由甲方与乙方签订" (12字)
# 按比例切分：
#   run1: 12 * 6/14 ≈ 5字 → "本协议由甲"
#   run2: 12 * 5/14 ≈ 4字 → "方与乙方"
#   run3: 剩余 → "签订"
```

### 批量翻译策略

- 单次批量限制：4000 字符
- 超出时分批处理，每批独立翻译
- **特殊段落（有批注/修订）单独翻译**：保留英文 + 翻译中文

### 批注识别流程

1. 从 `word/comments.xml` 加载所有批注
2. 在段落中查找 `commentRangeStart`/`commentRangeEnd` 标记
3. 如果段落包含批注范围标记，标记为"有批注"
4. 翻译时根据 `has_comments` 标志决定处理方式

### 修订识别流程

1. 在段落中查找 `w:ins` 和 `w:del` 元素
2. 提取插入/删除的文本内容
3. 标记段落为"有修订"
4. 翻译时英文原文完整保留，在段落后插入【中文译文】行

### 翻译输出格式（批注/修订段落）

对于有批注或修订的段落，翻译输出格式为：

```json
{
  "idx": 5,
  "has_comments_or_revisions": true,
  "original_text": "The liquidated damages shall be 5% of the contract price.",
  "translated_text": "违约金应为合同价格的5%。",
  "comments": [
    {
      "id": "1",
      "original": "Need to confirm penalty clause with legal team.",
      "translated": "需要与法务团队确认罚则条款。"
    }
  ],
  "revisions": [
    {
      "type": "deletion",
      "original": "not",
      "translated": "不"
    },
    {
      "type": "insertion",
      "original": "immediately",
      "translated": "立即"
    }
  ]
}
```

---

## ⚠️ 重要：JSON 解析问题处理

### 问题描述

翻译后的中文文本可能包含**中文引号** `"` 和 `"`（curly quotes），这与 JSON 的双引号分隔符冲突，导致解析失败。

### 解决方案

**方案 A：在提示词中约束 AI（推荐）**

在 `build_translate_prompt()` 中已添加：
> "如需使用引号，请使用单引号「」或直引号 '，避免使用与 JSON 分隔符冲突的双引号。"

**方案 B：回写时处理特殊字符**

如果 AI 仍输出了中文引号，在写入 JSON 前替换：
```python
# 将中文引号替换为 Unicode 转义
fixed_text = text.replace('\u201c', '\\u201c').replace('\u201d', '\\u201d')
```

---

## 常见工作流程

### 场景一：批量翻译多个文档

```python
import os
import sys
sys.path.append('C:/Users/Jxz/.workbuddy/skills/contract-translator/scripts')
from docx_translator import collect_paragraphs, apply_translations_with_markup
from docx import Document
import json

input_dir = "E:/E/VsCode/tonghua/"
translations_path = "_full_translations.json"  # 预存翻译

# 加载翻译数据
with open(translations_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
translations = {item['idx']: item['translated_text'] for item in data}

# 遍历目录下的所有 docx 文件
for filename in os.listdir(input_dir):
    if filename.endswith('.docx') and '中文翻译版' not in filename:
        input_path = os.path.join(input_dir, filename)
        output_path = input_path.replace('.docx', '（中文翻译版）.docx')

        doc = Document(input_path)
        paragraphs = collect_paragraphs(doc)
        count = apply_translations_with_markup(paragraphs, translations)
        doc.save(output_path)
        print(f"{filename}: {count} 段已翻译")
```

### 场景二：处理不同目录的文档

翻译数据文件与文档在同一目录时：
```python
# 翻译数据自动在同一目录查找
input_path = "E:/E/VsCode/tonghua/Data Subscription Agreement.docx"
# 系统会查找 E:/E/VsCode/tonghua/_full_translations.json
```

### 场景三：保存翻译结果供后续使用

```python
# 将 AI 翻译结果保存为 JSON 文件
with open('_full_translations.json', 'w', encoding='utf-8') as f:
    json.dump([{"idx": k, "translated_text": v} for k, v in translations.items()], f, ensure_ascii=False, indent=2)
```

---

## 调用方式

### 方式一：使用预存翻译数据（快速回写）

当已有翻译结果时，直接加载并回写到文档：

```python
from scripts.docx_translator import collect_paragraphs, apply_translations_with_markup
from docx import Document
import json

def translate_with_preloaded_data(input_path, translations_path, output_path=None):
    """使用预存翻译数据快速生成中文版文档

    参数：
        input_path: 输入的 .docx 文件路径
        translations_path: 翻译数据 JSON 文件路径
        output_path: 输出的 .docx 文件路径（默认：原文件名+中文翻译版）
    """
    if output_path is None:
        output_path = input_path.replace(".docx", "（中文翻译版）.docx")

    # 加载翻译数据
    with open(translations_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 转换为 dict 格式
    if isinstance(data, list):
        translations = {item['idx']: item['translated_text'] for item in data}
    else:
        translations = data

    # 读取文档并收集段落
    doc = Document(input_path)
    paragraphs = collect_paragraphs(doc)

    # 应用翻译
    count = apply_translations_with_markup(paragraphs, translations)
    print(f"已应用 {count} 条翻译")

    # 保存
    doc.save(output_path)
    return output_path

# 使用示例
translate_with_preloaded_data(
    input_path="合同.docx",
    translations_path="_full_translations.json"
)
```

### 方式二：调用 AI 实时翻译

```python
from scripts.docx_translator import translate_document

def my_translate(prompt):
    """你的 AI 翻译函数"""
    response = ai_model.translate(prompt)
    return response

translate_document(
    input_path="合同.docx",
    output_path="合同_翻译.docx",
    ai_translate_func=my_translate,
    terms=None,  # 使用默认术语表
    custom_instructions=None
)
```

### 翻译数据文件格式

预存翻译数据支持两种格式：

**格式一：JSON 列表**
```json
[
  {"idx": 0, "translated_text": "第一段中文翻译"},
  {"idx": 1, "translated_text": "第二段中文翻译"}
]
```

**格式二：JSON 字典**
```json
{
  "0": "第一段中文翻译",
  "1": "第二段中文翻译"
}
```

---

## 文件结构

```
contract-translator/
├── SKILL.md                          # 本文档（使用说明）
├── scripts/
│   ├── docx_translator.py            # 核心翻译脚本
│   └── translate_contract.py         # 旧版脚本（兼容）
└── references/
    ├── docx_xml_structure.md         # Word XML 结构参考
    └── legal_terms_cn.md             # 法律术语对照表（中英）
```

## 脚本使用（命令行）

### 基本用法

```bash
python scripts/docx_translator.py contract.docx
# 输出：contract（中文翻译版）.docx
```

### 指定输出文件

```bash
python scripts/docx_translator.py contract.docx translated_contract.docx
```

### 使用自定义术语表

```bash
python scripts/docx_translator.py contract.docx --terms my_terms.json
```

### 使用自定义翻译指令

```bash
python scripts/docx_translator.py contract.docx --instructions custom_rules.txt
```

---

## 注意事项

1. **翻译单位是完整段落**，不是碎片化的 run
2. **修订段落保留原文**，英文原文（含修订样式）完整保留，在段落后插入【中文译文】行
3. **批注段落直接翻译**，不保留英文原文，批注内容单独翻译
4. **按比例切分回写**，确保中文字符合理分配
5. **字号保持**，不修改 `w:sz`/`w:szCs`
6. **字体统一宋体/Times New Roman**，中文用宋体，西文用 Times New Roman
7. **术语一致性**，术语表中的术语翻译在全文中保持一致
8. **修订结构不动**，翻译行为不修改修订 XML 结构
9. **处理中文引号**，避免 JSON 解析失败
10. **修订样式保留**，英文原文中的删除线/下划线样式完整保留在 Word 中显示

---

## 常见问题

### Q: 翻译结果中出现乱码怎么办？
A: 检查源文档编码，确保是 UTF-8 或 Unicode 编码的 docx 文件。

### Q: 部分段落没有翻译？
A: 检查 `translations` 字典中是否包含该段落的 idx，可能 AI 响应解析失败。

### Q: 如何添加自定义术语？
A: 创建 JSON 文件（如 `my_terms.json`），格式为 `{"英文": "中文"}`，使用 `--terms` 参数加载。

### Q: 翻译后的文档在哪里？
A: 默认保存在原文件同目录，文件名添加"（中文翻译版）"后缀。

### Q: 修订段落如何翻译？
A: 修订段落的英文原文完整保留（含删除线/下划线），在段落后插入【中文译文】行。例如原文 `The Subscriber shall ~~not~~ _immediately_ pay` 后会插入 `【中文译文】订阅方应立即支付...`。

### Q: 带批注的原文为什么不保留英文原文？
A: 批注段落直接翻译为中文，批注内容单独翻译。不需要同时显示英文原文和中文翻译，避免冗余。

### Q: 修订的删除线/下划线去哪了？
A: **修订样式完整保留在英文原文中**。删除内容和插入内容在英文原文中的删除线/下划线保持不变。修订气泡（含作者、日期）也完整保留。

### Q: 如何识别哪些段落有批注或修订？
A: 检查段落的 `has_comments` 和 `has_revisions` 属性。在翻译提示词中，有批注/修订的段落会单独处理。

### Q: 字体可以修改吗？
A: 当前默认中文字体为宋体，西文字体为 Times New Roman。如需修改，可在代码中修改 `set_font_songti` 函数中的字体设置。
