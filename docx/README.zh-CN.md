# DOCX Skill 中文使用说明

## 这个 skill 是做什么的

`docx` skill 用于处理 Microsoft Word `.docx` 文档。它适合创建正式文档、读取和整理 Word 内容、编辑已有文档、插入或替换图片、处理批注和修订痕迹，以及把文本内容排版成报告、备忘录、信函、模板等 Word 文件。

这个文件是中文上手说明，实际执行规则仍以同目录下的 `SKILL.md` 和 `LICENSE.txt` 为准。

## 适合使用的场景

- 从需求、会议纪要、Markdown 或结构化内容生成 `.docx` 报告。
- 读取 `.docx` 内容，提取正文、标题、表格、批注或修订痕迹。
- 修改已有 Word 文档，同时尽量保留原始结构和格式。
- 对合同、方案、制度文档做带修订痕迹的修改。
- 将旧版 `.doc` 转换为 `.docx` 后继续处理。
- 将 Word 文档转换为 PDF 或图片，用于版式检查。

## 基本使用方法

在 Codex 中直接描述你的 Word 文档任务即可。只要请求中出现 Word、`.docx`、报告、信函、模板、批注、修订痕迹等上下文，Codex 会根据 skill 描述自动选择是否加载 `docx` skill。

推荐把任务说清楚：

- 输入文件路径，例如 `C:\Users\...\contract.docx`。
- 目标输出文件名，例如 `reviewed-contract.docx`。
- 是否需要保留格式、批注、修订痕迹。
- 文档语言、受众、正式程度。
- 是否要生成目录、页眉页脚、页码、表格或图片。

## 常用 Prompt 模板

### 读取和总结 Word 文档

```text
请使用 docx skill 读取这个 Word 文件：<文件路径>。
输出一份中文摘要，包括：文档主题、主要章节、关键结论、待办事项和潜在风险。
如果文档里有批注或修订痕迹，也请单独列出。
```

### 生成正式 Word 报告

```text
请使用 docx skill 生成一份正式的 Word 报告，输出为 <输出文件名>.docx。
报告主题是：<主题>。
内容结构包括：封面、目录、背景、分析、结论、建议、附录。
要求使用清晰标题层级、页码、表格和适合商务汇报的排版。
```

### 修改已有 Word 文档

```text
请使用 docx skill 修改 <输入文件.docx>，并输出为 <输出文件.docx>。
修改要求：
1. 将所有“甲方”替换为“委托方”。
2. 在第 3 节后新增一段风险提示。
3. 保留原文档格式和标题结构。
4. 不要改动未提及的段落。
```

### 以修订痕迹方式审阅合同

```text
请使用 docx skill 审阅 <合同文件.docx>。
以修订痕迹方式输出修改建议，重点关注付款条款、交付期限、违约责任和保密条款。
请只标记实际变化的文字，不要重写整段无变化内容。
输出文件名为 <reviewed.docx>。
```

### 接受全部修订并输出清洁版

```text
请使用 docx skill 将 <带修订文件.docx> 中的修订全部接受，输出一份清洁版 <clean.docx>。
同时告诉我是否发现无法自动处理的批注或异常格式。
```

## 常见工作流

### 读取内容

优先使用文本抽取；如果需要批注、修订、图片、元数据或复杂格式，再解包查看 OOXML。

```bash
pandoc --track-changes=all document.docx -o output.md
python scripts/office/unpack.py document.docx unpacked/
```

### 创建新文档

通常使用 Node.js 的 `docx` 包生成 `.docx`，然后运行校验。

```bash
npm install -g docx
python scripts/office/validate.py output.docx
```

### 编辑已有文档

典型流程是解包、修改 XML、重新打包并校验。

```bash
python scripts/office/unpack.py input.docx unpacked/
python scripts/office/pack.py unpacked/ output.docx --original input.docx
```

## 依赖和环境

根据任务不同，可能需要：

- `pandoc`：抽取 Word 文本和修订信息。
- `LibreOffice`：转换 `.doc`、导出 PDF、接受修订。
- `Poppler`：把 PDF 渲染为图片用于视觉检查。
- `docx` npm 包：从代码生成 Word 文档。

## 使用注意

- 处理重要合同或正式文档时，建议输出到新文件，不覆盖原文件。
- 如果需要可审阅的修改，明确说“保留修订痕迹”。
- 如果只要最终版本，明确说“接受修订并输出清洁版”。
- 对法律、财务、政府或学术文档，优先使用精确的小范围修改，避免整段重写。
- 该 skill 的许可证不是开源许可证，集成、分发或二次改造前请先阅读 `LICENSE.txt`。
