---
name: lark-sheets
version: 3.1.8
description: "读取或编辑飞书电子表格的单元格、公式、样式、图表和原生透视表。适用于已有 Sheets/wiki 表格链接及创建在线表格；按名称找文件先用 lark-drive，本地 Excel 用 xlsx。"
metadata:
  requires:
    bins: ["lark-cli"]
    siblings: ["lark-shared"]
  cliHelp: "lark-cli sheets --help"
---

# 飞书电子表格

首次使用时读取 [lark-shared](../lark-shared/SKILL.md) 的身份、授权和输出契约；已读且未变化时复用。工作簿用 URL/token，子表用真实 sheet_id/name；不猜 Sheet1，也不把表内对象 reference_id 与图片上传句柄混用。

## 按操作读取

| 任务 | Reference |
|---|---|
| 读取数据、定位真实范围 | [读取](references/lark-sheets-read-data.md) |
| 工作簿/子表创建、复制、命名 | [工作簿](references/lark-sheets-workbook.md) |
| 写值、公式、附件或单元格样式 | [写单元格](references/lark-sheets-write-cells.md) |
| 插入行列、冻结、隐藏、调整结构 | [结构](references/lark-sheets-sheet-structure.md) |
| 搜索/替换或范围操作 | [搜索替换](references/lark-sheets-search-replace.md)、[范围操作](references/lark-sheets-range-operations.md) |
| 写公式 / 迁移 Excel 公式 | [公式生成](references/lark-sheets-formula-translation.md)；写后做 [公式验证](references/lark-sheets-formula-verify.md) |
| 样式、美化 | [视觉规范](references/lark-sheets-visual-standards.md)、[批量样式](references/lark-sheets-styles-put.md) |
| 分组汇总/原生透视、图表 | [透视](references/lark-sheets-pivot-table.md)、[图表](references/lark-sheets-chart.md) |
| 跨类型且有顺序依赖的写操作链 | [batch-update](references/lark-sheets-batch-update.md)；授权规则来自 lark-shared |
| 其他对象、命令参数或能力排错 | [命令索引](references/lark-sheets-command-guide.md) 中的对应行 |

## 编辑与交付

编辑前读取 [编辑约束](references/lark-sheets-editing-principles.md) 的适用部分。保留未授权修改的值、表结构和格式，补齐任务只写空格；批量任务确认真实末行，避免遗漏表尾。标识符用文本，金额/计数/百分比/日期用正确类型。动态派生结果使用公式；原生透视/图表要求不得以静态结果冒充。

写后验证真实落格、相关范围和受影响公式依赖，返回成功不替代最终结果。已有无关错误予以披露，不扩展修改范围；全本修复需在任务范围内。当前文档/schema/能力声明或已有错误足以说明不支持时可据此判断；不确定性用只读或 dry-run 澄清，不为能力探查做多余生产写入。

语义、范围和风格选择由当前任务决定。命令用法已确认且版本未变时可复用；发现新错误或冲突再读取对应 reference。只报告产物中确实存在且已核实的结果。
