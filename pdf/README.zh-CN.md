# PDF Skill 中文使用说明

## 这个 skill 是做什么的

`pdf` skill 用于处理 PDF 文件。它适合读取 PDF 文本和表格、合并和拆分 PDF、旋转页面、添加水印、生成新 PDF、填写 PDF 表单、加密或解密、提取图片，以及对扫描版 PDF 做 OCR。

这个文件是中文上手说明，实际执行规则仍以同目录下的 `SKILL.md`、`forms.md`、`reference.md` 和 `LICENSE.txt` 为准。

## 适合使用的场景

- 从 PDF 中抽取正文、表格、元数据或图片。
- 合并多个 PDF，或按页拆分一个 PDF。
- 将扫描件转换为可搜索文本。
- 批量填写可编辑 PDF 表单。
- 在 PDF 上加水印、旋转页面、调整页面顺序。
- 从数据生成发票、证明、报告等 PDF 文件。
- 将 PDF 页面转成图片，用于人工或视觉检查。

## 基本使用方法

在 Codex 中直接描述 PDF 任务即可。只要请求中包含 `.pdf`、PDF、表单、扫描件、合并、拆分、OCR、抽表等上下文，Codex 会根据 skill 描述自动选择是否加载 `pdf` skill。

推荐提供这些信息：

- 输入 PDF 文件路径，多个文件时给出顺序。
- 输出文件名和输出格式。
- 需要处理的页码范围。
- 是否要保留原页面布局。
- 表格是否要导出为 Excel、CSV 或 Markdown。
- 表单字段和填充值。
- 是否涉及密码、加密或敏感信息。

## 常用 Prompt 模板

### 提取 PDF 摘要

```text
请使用 pdf skill 读取 <文件路径.pdf>。
输出中文摘要，包括文档主题、章节结构、关键数据、重要结论和可能需要人工复核的页面。
```

### 抽取 PDF 表格为 Excel

```text
请使用 pdf skill 从 <文件路径.pdf> 中抽取所有表格。
将结果整理为 Excel 文件 <输出文件.xlsx>，每个主要表格放在独立工作表。
如果某些表格识别不稳定，请列出页码和问题。
```

### 合并 PDF

```text
请使用 pdf skill 按以下顺序合并 PDF：
1. <封面.pdf>
2. <正文.pdf>
3. <附件.pdf>
输出为 <合并后.pdf>。
请保留所有页面，不要压缩画质。
```

### 拆分 PDF

```text
请使用 pdf skill 将 <文件路径.pdf> 拆分：
第 1-3 页输出为 <part-1.pdf>；
第 4-10 页输出为 <part-2.pdf>；
剩余页面输出为 <appendix.pdf>。
```

### 填写 PDF 表单

```text
请使用 pdf skill 检查 <表单.pdf> 的可填写字段。
先列出字段名和当前值，等我确认后再填写。
需要填写的数据如下：
<字段和值>
```

### OCR 扫描件

```text
请使用 pdf skill 对 <扫描件.pdf> 做 OCR。
输出一个可搜索文本版本 <ocr.pdf>，并额外导出纯文本 <ocr.txt>。
如果有低置信度或无法识别的页面，请列出页码。
```

## 常见工作流

### 读取 PDF 基本信息

```python
from pypdf import PdfReader
reader = PdfReader("document.pdf")
print(len(reader.pages))
```

### 抽取文本或表格

```python
import pdfplumber
with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        tables = page.extract_tables()
```

### 合并或拆分

```python
from pypdf import PdfReader, PdfWriter
```

### 表单处理

处理可填写表单前，先阅读 `forms.md`，并先列出字段再填值，避免字段名不匹配导致误填。

## 依赖和环境

根据任务不同，可能需要：

- `pypdf`：基础读写、合并、拆分、旋转、加密。
- `pdfplumber`：文本和表格抽取。
- `reportlab`：生成新的 PDF。
- `pytesseract`、`pdf2image`：扫描件 OCR。
- `poppler-utils`：PDF 转图片、文本抽取等命令行工具。
- `qpdf` 或 `pdftk`：部分 PDF 页面和密码处理任务。

## 使用注意

- 先判断 PDF 是文本型还是扫描型；扫描型通常需要 OCR。
- PDF 表格抽取可能不稳定，复杂表格需要人工复核。
- 填写表单前先检查字段名，避免把值写到错误字段。
- 处理加密 PDF 前，需要确认你有权限和密码。
- 重要文件请输出到新文件，不要覆盖原件。
- 该 skill 的许可证不是开源许可证，集成、分发或二次改造前请先阅读 `LICENSE.txt`。
