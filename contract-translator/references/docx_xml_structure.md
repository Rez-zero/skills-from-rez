# Word DOCX XML 结构参考

## 文件结构

一个 .docx 文件本质上是一个 ZIP 包，包含以下主要文件：

```
document.docx
├── [Content_Types].xml
├── _rels/
│   └── document.xml.rels
├── word/
│   ├── document.xml       # 主文档内容
│   ├── styles.xml         # 样式定义
│   ├── settings.xml       # 文档设置
│   ├── header*.xml        # 页眉
│   ├── footer*.xml        # 页脚
│   └── _rels/
│       └── document.xml.rels
└── _rels/.rels
```

## 命名空间

```xml
xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
```

## 核心元素

### 段落结构（含修订痕迹）

```xml
<w:p>
  <w:pPr>                           <!-- 段落属性 -->
    <w:pStyle w:val="Normal"/>
    <w:jc w:val="both"/>
  </w:pPr>

  <!-- 普通文本 run -->
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体"/>
      <w:sz w:val="24"/>
      <w:b/>
    </w:rPr>
    <w:t>Hello </w:t>               <!-- 翻译时替换此文本 -->
  </w:r>

  <!-- 插入修订 -->
  <w:ins w:id="2" w:author="John" w:date="2026-01-15T10:00:00Z">
    <w:r>
      <w:rPr><w:b/></w:rPr>
      <w:t>world</w:t>              <!-- 只替换文本，保留 w:ins 结构 -->
    </w:r>
  </w:ins>

  <!-- 删除修订 -->
  <w:del w:id="3" w:author="John" w:date="2026-01-15T10:00:00Z">
    <w:r>
      <w:rPr><w:strike/></w:rPr>
      <w:delText>old</w:delText>    <!-- 只替换文本，保留 w:del 结构 -->
    </w:r>
  </w:del>
</w:p>
```

### 文本元素位置

| 文本来源 | XML 路径 | 元素标签 |
|----------|----------|----------|
| 普通文本 | `<w:p>` → `<w:r>` → | `<w:t>` |
| 新增修订 | `<w:p>` → `<w:ins>` → `<w:r>` → | `<w:t>` |
| 删除修订 | `<w:p>` → `<w:del>` → `<w:r>` → | `<w:delText>` |

### 字体设置

```xml
<w:rFonts
  w:ascii="宋体"           <!-- 西文字符 -->
  w:eastAsia="宋体"         <!-- 东亚字符（中文） -->
  w:hAnsi="宋体"           <!-- 高位 ANSI 字符 -->
/>
```

### 字号

- `w:sz` 和 `w:szCs` 以**半磅**为单位：`24` = 12pt，`21` = 10.5pt（五号），`28` = 14pt（四号）
- 翻译时**不修改**

### 格式属性（必须保留）

`w:b` 粗体 | `w:i` 斜体 | `w:u` 下划线 | `w:pStyle` 段落样式 | `w:jc` 对齐 | `w:strike` 删除线

## 按比例切分策略

Word 修订追踪会将文本拆成极碎的 run（甚至逐字母），因此必须按段落级别翻译后切分回写：

```
原文段落完整文本:  "The Service Provider shall not unilaterally..."
                    |-- run1(20) --|-- run2(15) --|-- run3(10) --|

中文译文:          "服务提供方不得单方面..."
                    |-- 切分1(20/45) --|-- 切分2(15/45) --|-- 切分3(10/45) --|
```

切分比例 = run_length / total_length，最后一个 run 取剩余全部。
