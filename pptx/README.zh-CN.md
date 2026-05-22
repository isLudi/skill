# PPTX Skill 中文使用说明

## 这个 skill 是做什么的

`pptx` skill 用于处理 PowerPoint `.pptx` 文件。它适合创建演示文稿、读取和分析已有幻灯片、基于模板生成新内容、编辑文字和版式、处理 speaker notes、批注、母版和底层 OOXML，并通过缩略图进行视觉质量检查。

这个文件是中文上手说明，实际执行规则仍以同目录下的 `SKILL.md`、`editing.md`、`pptxgenjs.md` 和 `LICENSE.txt` 为准。

## 适合使用的场景

- 根据大纲、文档或数据生成一份 `.pptx`。
- 总结或审阅已有 PPT，提取主要观点和页结构。
- 基于公司模板替换内容、更新图表、调整页顺序。
- 批量修改演示文稿中的标题、脚注、品牌文案或备注。
- 从 PPT 中抽取 speaker notes、批注、隐藏内容或元数据。
- 将 PPT 渲染为图片，检查文字重叠、越界和版式问题。

## 基本使用方法

在 Codex 中直接描述演示文稿任务即可。只要请求中包含 `.pptx`、PPT、slides、deck、presentation、幻灯片、演示文稿等上下文，Codex 会根据 skill 描述自动选择是否加载 `pptx` skill。

推荐提供这些信息：

- 输入文件路径或模板路径。
- 目标输出文件名。
- 受众、用途和语言。
- 页数范围或期望页数。
- 是否必须沿用模板、品牌色、字体或母版。
- 是否需要图表、图片、流程图、时间线或关键数据页。
- 是否需要渲染成图片做视觉检查。

## 常用 Prompt 模板

### 从大纲生成 PPT

```text
请使用 pptx skill 生成一份中文演示文稿，输出为 <输出文件.pptx>。
主题：<主题>。
受众：<受众>。
页数：约 <页数> 页。
请包含封面、目录、背景、核心内容、数据页、结论和行动建议。
要求每页都有明确视觉元素，不要做纯文字堆叠。
```

### 基于模板生成 PPT

```text
请使用 pptx skill 基于模板 <模板.pptx> 生成新演示文稿。
内容来自：<内容或文件路径>。
请尽量保留模板的母版、字体、颜色、页眉页脚和版式风格。
输出为 <输出文件.pptx>。
生成后请渲染缩略图检查是否有文字重叠或越界。
```

### 分析已有 PPT

```text
请使用 pptx skill 分析 <文件路径.pptx>。
输出：
1. 每页标题和核心内容；
2. 整体叙事结构；
3. 设计和版式问题；
4. 可以改进的页面清单。
```

### 修改已有 PPT

```text
请使用 pptx skill 修改 <输入文件.pptx>，输出为 <输出文件.pptx>。
修改要求：
1. 将所有旧品牌名替换为新品牌名；
2. 删除第 5 页；
3. 将第 8 页移动到第 3 页后；
4. 保留原模板风格；
5. 生成后做缩略图检查。
```

### 提取演讲者备注

```text
请使用 pptx skill 从 <文件路径.pptx> 中提取所有 speaker notes。
按页码整理成 Markdown，保留每页标题和备注内容。
如果某页没有备注，请标注“无备注”。
```

## 常见工作流

### 读取和分析内容

```bash
python -m markitdown presentation.pptx
python scripts/thumbnail.py presentation.pptx
python scripts/office/unpack.py presentation.pptx unpacked/
```

### 基于模板编辑

先阅读 `editing.md`，一般流程是生成缩略图、解包、修改内容、清理、重新打包和验证。

```bash
python scripts/thumbnail.py template.pptx
python scripts/office/unpack.py template.pptx unpacked/
```

### 从零创建

先阅读 `pptxgenjs.md`，通常使用 `pptxgenjs` 生成文件。

```bash
npm install -g pptxgenjs
```

### 视觉检查

生成后建议转为图片检查，重点看文字是否重叠、元素是否越界、边距是否足够、模板占位符是否残留。

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

## 依赖和环境

根据任务不同，可能需要：

- `markitdown[pptx]`：读取和抽取 PPT 内容。
- `Pillow`：生成缩略图或图片辅助检查。
- `pptxgenjs`：从代码生成 PPT。
- `LibreOffice`：PPT 转 PDF。
- `Poppler`：PDF 转图片。

## 使用注意

- PPT 生成后必须做视觉检查，尤其是文字换行、重叠、越界和低对比度。
- 如果有模板，优先保留模板的母版、字体和品牌规范。
- 不要只生成白底项目符号页；每页应有图表、图片、图标、流程或关键数字等视觉元素。
- 修改已有 PPT 时请输出到新文件，避免覆盖原件。
- 该 skill 的许可证不是开源许可证，集成、分发或二次改造前请先阅读 `LICENSE.txt`。
