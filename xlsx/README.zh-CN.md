# XLSX / Excel Skill 中文使用说明

## 这个 skill 是做什么的

`xlsx` skill 用于处理 Excel 和表格文件。它适合读取、清洗、分析、创建或修改 `.xlsx`、`.xlsm`、`.csv`、`.tsv` 文件，支持公式、格式、图表、工作表结构、模板保留，以及通过平台原生后端重算公式并检查错误：Windows 使用 Microsoft Excel COM，Linux/macOS 使用 LibreOffice。

用户口中的 “Excel skill” 在本地目录名是 `xlsx`。这个文件是中文上手说明，实际执行规则仍以同目录下的 `SKILL.md` 和 `LICENSE.txt` 为准。

## 适合使用的场景

- 读取和分析 Excel、CSV、TSV 数据。
- 清洗脏数据，修复错位表头、空行、异常列。
- 生成新的 Excel 报表、预算表、台账或数据透视汇总。
- 修改已有模板，同时保留原格式、公式和工作表结构。
- 创建带动态公式的财务模型或运营分析模型。
- 将 PDF 或其他来源抽取的表格整理为 Excel。
- 检查公式错误，例如 `#REF!`、`#DIV/0!`、`#VALUE!`。
- 自动美化表格：深蓝表头、交替行着色、数据条、色阶、分类色块、KPI 卡片、透视表专项美化。

## 基本使用方法

在 Codex 中直接描述表格任务即可。只要请求中包含 `.xlsx`、`.xlsm`、`.csv`、`.tsv`、Excel、表格、工作簿、公式、数据清洗等上下文，Codex 会根据 skill 描述自动选择是否加载 `xlsx` skill。

推荐提供这些信息：

- 输入文件路径和目标输出文件名。
- 需要处理的工作表名称。
- 数据列含义、指标口径和期望计算逻辑。
- 是否要保留已有模板格式。
- 是否需要新增公式、图表、数据透视或多个工作表。
- 数字格式、币种、百分比、小数位、日期格式。
- 是否需要重算公式并检查错误。

## 常用 Prompt 模板

### 分析 Excel 数据

```text
请使用 xlsx skill 分析 <文件路径.xlsx>。
请读取所有工作表，识别每张表的字段含义和数据质量问题。
输出中文分析摘要，并列出可疑值、缺失值、重复记录和建议修复方式。
```

### 清洗 CSV 并导出 Excel

```text
请使用 xlsx skill 清洗 <输入文件.csv>，输出为 <输出文件.xlsx>。
要求：
1. 自动识别并修复错位表头；
2. 删除完全空白行；
3. 标准化日期和金额格式；
4. 新增一个“数据质量问题”工作表记录清洗日志。
```

### 生成 Excel 报表（带自动美化）

```text
请使用 xlsx skill 根据以下数据生成 Excel 报表，输出为 <报表.xlsx>。
报表需要包含：
1. 原始数据表；
2. 汇总分析表；
3. 趋势图或柱状图；
4. 关键指标说明。
请使用 quick_style() 自动美化所有数据表。
```

### 生成透视表（带美化）

```text
请使用 xlsx skill 创建透视表，输出为 <透视表.xlsx>。
要求：
1. 对数值列自动应用数据条和色阶；
2. 按渠道/分类字段设置分类色块；
3. 汇总行使用特殊样式；
4. 降序排列的指标列表头添加排序箭头。
```

### 修改已有模板

```text
请使用 xlsx skill 修改 <模板.xlsx>，输出为 <输出文件.xlsx>。
请保留模板原有格式、列宽、颜色、公式和工作表结构。
只更新 <工作表名> 中的指定数据区域，并新增必要公式。
完成后请运行 `scripts/recalc.py`，由脚本自动选择当前平台的重算后端并检查公式错误。
```

### 构建财务模型

```text
请使用 xlsx skill 创建一个动态财务模型，输出为 <模型.xlsx>。
模型包含：假设区、收入预测、成本预测、利润表、现金流摘要和敏感性分析。
请所有计算使用 Excel 公式，不要把 Python 计算结果硬编码进单元格。
输入假设用蓝色字体，公式用黑色字体，并检查所有公式错误。
```

## 常见工作流

### 读取和分析数据

```python
import pandas as pd
df = pd.read_excel("file.xlsx")
all_sheets = pd.read_excel("file.xlsx", sheet_name=None)
```

### 写入 Excel

```python
df.to_excel("output.xlsx", index=False)
```

### 需要保留样式或写公式

通常使用 `openpyxl` 做单元格级别处理，保留模板时必须先研究原文件格式，再做局部修改。

### 自动美化表格（新增）

skill 内置了完整的表格美化模块（`scripts/style_apply.py` + `scripts/style_palette.py`），**所有新建 Excel 文件都应自动调用**，无需用户每次手动声明。

**最简调用：**

```python
from style_apply import quick_style

# 一个函数覆盖标题、表头、交替行、数字格式、列宽、边框
quick_style(ws, title='报表标题', value_cols=[3, 4, 5], category_col='A')
```

**一键全表美化（更细粒度控制）：**

```python
from style_apply import auto_style_sheet

auto_style_sheet(
    ws,
    title='市场顾问部 退费分析',
    subtitle='Period: 2026-05 ~ 2026-07 | Source: CRM',
    value_cols=[4, 5, 6],
    category_col='A',
    category_map={'KOC': 'E3F2FD', '抖音': 'FFF3E0'},
    add_color_scale=True,
    add_data_bars=True,
)
```

**单功能函数（按需使用）：**

| 函数 | 用途 |
|------|------|
| `apply_title_banner(ws, title, ...)` | 深蓝标题横幅 |
| `apply_header_style(ws, row, ...)` | 表头样式 + 冻结窗格 |
| `apply_banded_rows(ws, ...)` | 交替行着色 |
| `apply_number_format(ws, ...)` | 中文关键词自动识别数字格式 |
| `apply_auto_fit_columns(ws)` | 中文感知自动列宽 |
| `apply_border_grid(ws, ...)` | 数据区网格边框 |
| `apply_data_bars(ws, col_range)` | 单元格内数据条 |
| `apply_color_scale(ws, col_range)` | 红-白-绿 色阶 |
| `apply_pivot_style(ws, ...)` | 透视表专项美化 |
| `apply_sort_indicator(ws, col)` | 排序箭头指示器 |
| `apply_category_colors(ws, col, mapping)` | 分类色块 |
| `apply_kpi_card(ws, ...)` | KPI 指标卡片 |
| `apply_section_header(ws, ...)` | 分段标题 |
| `apply_subtotal_row(ws, ...)` / `apply_grand_total_row(ws, ...)` | 汇总行样式 |
| `detect_existing_template(ws)` | 检测已有模板（避免覆盖） |

**模板保护：** 修改已有模板时，`detect_existing_template()` 会自动检测已有样式，`quick_style()` 遇到模板时会跳过破坏性修改，仅执行非破坏性操作（如自动列宽）。

### 重算和检查公式

官方 skill 提供 `scripts/recalc.py`，用于重算公式值并检查错误。Windows 自动使用 Excel COM，Linux/macOS 自动使用 LibreOffice。

```bash
# Windows（本机）
D:\anaconda3\python.exe scripts/recalc.py workbook.xlsx

# Linux/macOS
python3 scripts/recalc.py workbook.xlsx
```

## 依赖和环境

根据任务不同，可能需要：

- `pandas`：数据读取、清洗、聚合和分析。
- `openpyxl`：读写 `.xlsx`、样式、公式、工作表结构。
- Windows：桌面版 Microsoft Excel 与 `pywin32`；本机默认使用 `D:\anaconda3\python.exe`。
- Linux/macOS：LibreOffice，且 `soffice` 需要位于 `PATH`。
- `scripts/recalc.py`：官方 skill 中的公式重算辅助脚本。

## 使用注意

- 生成 Excel 模型时优先使用 Excel 公式，不要把计算结果硬编码。
- 新建文件必须调用美化函数：每次生成新的 xlsx 文件，默认使用 `quick_style()` 或 `auto_style_sheet()` 自动美化，确保输出风格统一稳定。
- 修改模板时必须保留已有格式和约定，`detect_existing_template()` 会自动检测已有样式并跳过覆盖。
- 财务模型中输入、公式、跨表链接和外部链接应使用不同颜色区分。
- 输出前应检查公式错误、循环引用、范围偏移和除零问题。
- 不要对 Excel Table 已覆盖的同一区域再设置工作表级 `auto_filter`，重叠筛选器可能导致 Excel COM 无法打开工作簿。
- 如果 Excel COM 能启动但无法打开某个文件，应优先检查工作簿结构、筛选器重叠、文件锁定或文件损坏，而不是判断本机缺少 COM。
- 重要工作簿请输出到新文件，不要覆盖原件。
- 该 skill 的许可证不是开源许可证，集成、分发或二次改造前请先阅读 `LICENSE.txt`。
