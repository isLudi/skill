# 飞书表格命令与诊断索引

仅在需要选择命令、定位参数或排查能力差异时读取对应部分；不要全量展开所有 references。文中脚本路径相对 Skill 根目录。编辑准则见 [编辑约束](lark-sheets-editing-principles.md)。

## 场景 → 命令速查（拿不准命令名先查这里，别按直觉拼）

> **若本次读取被截断在本表中段**：下列能力**都原生存在**，
> 详细用法（flag、payload 形状、易错点）在本表后半部分与其后的「执行要点」「公共 flag」章节：
>
> `+styles-put` 美化收尾（样式 / 边框 / 合并 / 行高列宽 / **冻结** 一次交付）·
> `+chart-create` 原生图表 · `+pivot-create` 透视表 · `+filter-create` 筛选 ·
> `+cond-format-create` 条件格式 · `+range-sort` 排序 · `+dim-insert` 插入行列 ·
> `+cells-search` / `+cells-replace` 查找替换 · `+workbook-import` 本地文件转在线表
>
> 要用其中任一能力而对应行未读到时，**用文件读取工具的偏移参数（`offset` / 起始行）把后半段再读一次**，
> 取全对应行再动手。不要因为没读到展开就判定命令不存在，更不要改用本地脚本绕路——
> 本地生成的透视表 / 图表导入后会退化成死表、静态图。

把高频意图映射到**真实存在**的 shortcut / flag（agent 常从 Excel / Google Sheets / OpenAPI 误迁移命令名）。**选定命令后先读「动手前读」列指向的 reference 再动手**——命令名对得上不代表用法对。

| 你要做的事 | ✅ 正确写法 | 动手前读 | ❌ 不存在（会被 cobra 拒） |
| --- | --- | --- | --- |
| 读数据（纯值 / CSV） | `+csv-get`（`--range` 可省略 = 读整个子表，无需先探行列；限定范围才传） | `lark-sheets-read-data` | `+read-data`、`+get-range`、`+range-get`、`+cells-read` |
| 读值 + 公式 / 样式 / 批注 | `+cells-get --include value,formula,style,comment,data_validation` | `lark-sheets-read-data` | `+get-cell`、`+cell-get`、`--sheet`（定位只有 `--sheet-id` / `--sheet-name`）、`--value-only`、`--include-style`、`--value-render-option`、`--with-styles`、`--with-merges`、`--include-merged-cells` |
| 写纯文本值（整块 CSV 平铺；列里**没有**需字面保真的数值 / 日期标签 / 编号——点分日期 `12.10`、编号 `001` 会被 csv-put 数值化，不算纯文本） | `+csv-put`（定位用 `--start-cell`，单个左上角锚点格；也接受 `--range` 别名，区间自动取左上角） | `lark-sheets-write-cells` | 把含点分日期(`12.10`)/编号(`001`)的列裸灌 `+csv-put`——会被数值化（`12.10`→`12.1`、`001`→`1`，尾零/前导零丢失），改用 `+table-put` 声明 `dtypes:object` |
| 写带类型的数据到**已有**表（列里有数字 / 金额 / 百分比 / 日期 / 计数等**本质是量值**的数据——不看当下要不要排序 / 求和，量值一律走这里） | `+table-put --sheets` 完整 payload `{"sheets":[{...}]}`（列名走 `columns`、二维数据走 `data`、列 pandas dtype 走 `dtypes`、列展示格式走 `formats`；来源不限 DataFrame——Counter / dict / list 同理；要同时美化加 `--styles` 一步带样式（区域底色 / 边框 / 列宽 / 行高 / 合并），不必事后再刷；payload 里不存在的 sheet 名会自动建子表，详见 write-cells） | `lark-sheets-write-cells` | 在本地把数字拼成 `"$1,234"` / `"30.5%"` 字符串再 `+csv-put`（会落成文本、丢失计算能力；常见借口见下方 ⚠️） |
| **新建**电子表格并写带类型的数据（类型保真需求同上，但目标表还不存在） | `+workbook-create --sheets`（协议与 `+table-put` 同构、一步建表 + typed 写入，无需先建空表再 `+table-put`；date / number 不丢；`--styles` 同样可在建表同一步带全套样式，详见 workbook） | `lark-sheets-workbook` | 用 `--values` 灌日期 / 数字（会落成文本、丢类型） |
| 写公式 / 富写入（样式 · 批注 · 图片 · 富文本），或需精确矩形定位的值 | `+cells-set`（单区域 `--range`+`--cells`；**散布多处 / 跨表用 `--writes` 一次批量交付**，每项自带 sheet_name；批注 / 图片 / 富文本只能用它；公式落表后可用 `+formula-verify` 诊断） | `lark-sheets-write-cells` | — |
| 只改样式、值 / 公式不动 | `+cells-set-style`（单区域小改）；多区域 / 整表美化收尾一次 `+styles-put` 交付（见 `lark-sheets-styles-put`） | `lark-sheets-write-cells` | `+cells-set --copy-to-range` 刷样式——它连**值**一起复制，会把整个区域的值覆盖成锚点格的值；拼 `+batch-update` 的 `--operations` 做美化 |
| **已有**表美化收尾（样式 / 边框 / 合并 / 行高列宽 / 冻结的任意组合，单表或多表） | `+styles-put --styles '{"styles":[{"name":…,"cell_styles":[…],"cell_merges":[…],"row_sizes":[…],"col_sizes":[…],"freeze":{…}}]}'`（一份规格一次交付，词汇同 `+table-put --styles`） | `lark-sheets-styles-put` | 拼 `+batch-update` 的 `--operations` 子操作数组做美化、逐区域多次 `+cells-set-style` |
| 画图表 / 可视化（柱 / 折线 / 饼 / 条 / 散点 / 组合…） | 普通单图用 `+chart-create-basic`，多图用扁平输入的 `+batch-chart-create`；已有图的数据源用 `+chart-data-update`、常用配置用 `+chart-config-update`；只有语义 shortcut 无法表达的单系列 / 单数据点 / 高级字段才用 `+chart-create` / `+chart-update`，并只提交必要的局部 properties。多图先断言目标数量，图片迁移成真图表后必须删除并复查原浮动图片 | `lark-sheets-chart` | matplotlib / 本地画图再贴图（原生图表可交互、随数据更新） |
| 分组汇总 / 透视 | `+pivot-create`（默认不传落点 flag → 自动新建子表，零覆盖） | `lark-sheets-pivot-table` | 用 SUMIF / 本地脚本拼一张假透视表 |
| 排序（按列升 / 降序） | `+range-sort`（原生整行原子移动，值 / 样式 / 空值随行走） | `lark-sheets-range-operations` | 本地排完再整块 `+cells-set` 回写——`cells-set` 写空值**不覆盖**目标格（保留原值），会残留旧值，且样式不随行移动 |
| 筛选 / 只看符合条件的行（仅行级不裁列；"只保留某几列 / 筛出来另存一张表"→ 不走这里，另建结果 sheet 物化行与列、原表原样保留） | `+filter-create` | `lark-sheets-filter` | pandas filter 后覆盖写回（会毁原数据；要保存多份筛选状态用 `+filter-view-create`） |
| 查找 / 替换文本 | `+cells-search`（找，关键字用 `--find`）、`+cells-replace`（替换） | `lark-sheets-search-replace` | `+cells-find`、`+find`、`--query` |
| 条件格式 / 条件高亮 / 数据条 / 色阶 / 重复值标记 | `+cond-format-create` | `lark-sheets-conditional-format` | `+highlight`、`+conditional-format`、逐格 `+cells-set-style` 硬凑 |
| 看子表结构（合并 / 行高列宽 / 冻结 / 隐藏） | `+sheet-info` | `lark-sheets-sheet-structure` | `+sheet-get`、`+structure-get`、`+sheet-structure-get` |
| 插图：图片**绑定到某条记录**、随行走（凭证 / 证件照 / 商品图 / 头像 / 二维码 / 每行配图） | `+cells-set-image`（单格 `--range`，嵌入单元格内） | `lark-sheets-write-cells` | — |
| 插图：**自由摆放、不绑数据**的装饰 / 标识（logo / 水印 / 封面大图 / banner） | `+float-image-create`（浮动图片，自由定位 + 尺寸 + 层级） | `lark-sheets-float-image` | — |
| 迷你图 / 单元格内趋势线 / 胜负图 | `+sparkline-create` 等 `+sparkline-*` | `lark-sheets-sparkline` | 文本字符（▁▂▃）拼接、matplotlib 贴图（不随数据更新） |
| 清除内容 / 格式 | `+cells-clear`（high-risk-write 需用户确认后带 `--yes`；范围维度用 `--scope`，取值 content / formats / all） | `lark-sheets-range-operations` | `--type` |
| 批量清除多区域 | `+cells-batch-clear`（high-risk-write 需用户确认后带 `--yes`；`--scope`） | `lark-sheets-batch-update` | `--target` |
| 调整列宽 / 行高 | `+cols-resize` / `+rows-resize`（行、列是两个独立命令；连同样式一起调时并入 `+styles-put` 的 `row_sizes` / `col_sizes`） | `lark-sheets-range-operations` | `--dimension`（无此 flag） |
| 看工作簿 / 子表清单 | `+workbook-info` | `lark-sheets-workbook` | `+sheet-list`、`+workbook-get`、`+workbook-list` |
| 导入本地 xlsx/xls/csv 文件为飞书电子表格 | `+workbook-import --file ./x.xlsx`（本地表格文件 → 飞书电子表格的正解；仅要导成多维表格 bitable 时才用 `drive +import --type bitable`） | `lark-sheets-workbook` | `drive +import`（绕路且要多给 `--type`）、本地读出数据再 `+workbook-create` 重灌（多此一举）；要给**已有工作簿**加子表别用它（只会新建独立表，走 `+sheet-copy` / `+sheet-create`） |
| 参考某个**已有在线表**、把多个本地文件 / 数据各作为一张子表**追加**进去（不另起独立表） | 先 `+workbook-info` 拿模板子表 `sheet_id` → `+sheet-copy` 逐张复制模板子表（公式 / 合并 / 分组底色 / 列宽 / 条件格式全继承）再用 `+cells-*` 只改数据；无模板可继承时 `+sheet-create` 建空子表 + `+table-put --sheets/--styles` 写入 | `lark-sheets-workbook` | 把文件 `+workbook-import` / `+workbook-create` 另起一张**独立新表**（目标是并入已有工作簿时就跑偏了；这两条只产新表、不接受已有表定位） |
| 复核某次（AI）编辑改了什么 / 取两个版本间的变更 | `+changeset-get --start-revision <编辑前版本>`（省略 `--end-revision` 取到最新；版本差 ≤ 20） | `lark-sheets-changeset` | — |
| 取当前文档 revision（版本号） | `+revision-get` | `lark-sheets-workbook` | — |
| 导出 xlsx / 单表 csv | `+workbook-export` | `lark-sheets-workbook` | — |

> ⚠️ **动手前的触发式必读（按动作判定，不看主场景）**：本次操作只要**涉及样式 / 美化**（底色 / 边框 / 字号 / 对齐 / 数字格式 / 汇总行 / 配色 / 列宽行高），动手前先读 `lark-sheets-visual-standards`；只要**要写飞书公式**，动手前先读 `lark-sheets-formula-translation`（飞书函数与 Excel 有差异，凭直觉迁移易错），写完后可读 `lark-sheets-formula-verify` 并执行 `+formula-verify` 做一次诊断。哪怕主任务是"建表 / 展开数据 / 录入"，只要动作里含美化或写公式就适用——别因"这不算专门的美化 / 公式任务"而跳过。
> ⚠️ **两种图片别选错**：图若**绑定某条记录、要随行排序 / 筛选 / 增删**（凭证 / 证件照 / 每行配图，话里带「对应 / 每行 / 这列」等绑定词）→ 单元格图片 `+cells-set-image`；只是自由摆放的装饰（logo / 水印 / 封面）→ 浮动图片 `+float-image-create`。别因「浮动图更好控制 / 更熟」默认选浮动图。
> ⚠️ **纯文本还是数值语义（看数据本质，不看当下用途）**：金额 / 百分比 / 比率 / 计数 / 日期等**本质是量值**的数据 → 一律数值写入，常规二维表用 `+table-put`（`dtypes` 声明类型 + `formats` 设展示格式），版式装不下（多级 / 合并表头的宽表 leaderboard 等）改用 `+cells-set` 传数字（百分比传小数 `0.4`）+ `number_format`，照样显示 `40%` 且数值无损。只有编号 / 身份证 / 单据号这类**本质是标识符**、要字面保真的才用 `+csv-put` 平铺。**几个常见借口都不成立**——"只是 leaderboard / 报表展示不用算""版式复杂""样式以后再刷、先铺文本"都不是把百分比写成 `"40%"` 字符串灌 `+csv-put` 的理由（展示不改变它是数值；类型不能后补，落成文本就回不来）。判据与操作展开见 `lark-sheets-write-cells`「数字还是文本」。
> ⚠️ **要新建子表 / 整表美化 → 别默认「`+csv-put` 写值再事后刷样式」**：`+table-put` / `+workbook-create` 的 `--styles` 能在写数据的**同一步**带全套样式（区域底色 / 边框 / 列宽 / 行高 / 合并），且 `+table-put` 的 payload 里若 sheet 名不在工作簿中会自动新建子表——**纯文本表要新建子表 + 美化时同样走这里**（`--styles` 与列是否 typed 无关），比「`+csv-put` 写值 + 多次 `+cells-batch-set-style` / `+*-resize` 刷样式」少好几次调用（冻结行列等 sheet 级属性仍需 `+dim-freeze` 单独一步）。存量表事后美化则一次 `+styles-put` 交付（同一份 `--styles` 词汇）。
> ⚠️ **定位 flag**：`+cells-get` / `+cells-set` / `+csv-get` 用 `--range`；`+csv-put` 规范用 `--start-cell`（单个左上角锚点格），也接受 `--range` 别名（区间自动取左上角），二者择一即可。**`--range` 只写 `A1:B2` 纯区间——不接受 OpenAPI 的 `sheetId!A1:B2` 前缀写法**，子表定位必须单独传 `--sheet-id` / `--sheet-name`（从 OpenAPI 迁移习惯最易踩）。
> ⚠️ **读取附加信息**一律走 `+cells-get --include …`，**没有** `--with-styles` 这类 flag；**看合并单元格**用 `+sheet-info` 的 `merged_cells`，不要在 `+cells-get` 里找 merge flag。

💡 **高频写命令签名（照抄改参即可；各命令 `--help` 的 Tips 段有同款示例）**：

```bash
lark-cli sheets +cells-set --url <U> --sheet-name S1 --range A1:B1 --cells '[[{"value":"名称"},{"formula":"=SUM(B2:B9)"}]]'  # --cells 恒为二维数组 [[…]]，单格也是 [[{…}]]
lark-cli sheets +cells-set-style --url <U> --sheet-name S1 --range A1:D1 --font-weight bold --background-color "#F0F0F0" --horizontal-alignment center
lark-cli sheets +styles-put --url <U> --styles - <<'JSON'
{"styles":[{"name":"S1","cell_styles":[{"range":"A1:D1","font_weight":"bold","background_color":"#F0F0F0"}],"col_sizes":[{"range":"A:D","type":"pixel","size":120}],"freeze":{"rows":1}}]}
JSON
lark-cli sheets +batch-update --url <U> --dry-run --operations - <<'JSON'   # high-risk：先 --dry-run 给用户看，同意后原样重发并追加 --yes
[{"shortcut":"+cells-set","input":{"sheet_name":"S1","range":"A1","cells":[[{"value":"x"}]]}}]
JSON
lark-cli sheets +dim-freeze --url <U> --sheet-name S1 --rows 1 --cols 2  # 一次给全；冻结是整份状态覆盖，没写的轴即为不冻结
lark-cli sheets +dim-insert --url <U> --sheet-name S1 --position 3 --count 2 --inherit-style before  # 行/列由 --position 决定：数字=行、字母=列，无 --dimension
lark-cli sheets +cols-resize --url <U> --sheet-name S1 --range A:C --width 120  # 像素；分列不同宽用 --widths '{"A":80,"C:E":120}'
lark-cli sheets +sheet-copy --url <U> --sheet-name 源表名 --title 副本名  # --sheet-name=源表、--title=新表名
```

## 执行要点（读取 / 原生工具 / 陷阱）

### 读取：按需求选路径（细则见 `lark-sheets-read-data`）

| 用户需求 | 读取路径 |
|---|---|
| "完善 / 补齐 / 修正所有 XX"、分析 / 清洗 / 大数据 | 先 `scripts/lark_profile_table.py` 确认目标区域与字段画像，再原生优先（公式 / 透视表 / 筛选等原生对象，命令见速查表）；表达不了再分批 `+csv-get` 导出 + 脚本处理 + 分批回写（默认覆盖所有对应数据行） |
| "查一下 / 统计 / 汇总"等只读 | 小表 `+csv-get` 读到上下文；大表先 `+workbook-info` + 小窗口 `+csv-get` 定边界，再对未截断窗口跑 `scripts/lark_detect_subtables.py` / `scripts/lark_profile_table.py` |
| 需要公式 / 样式 / 批注 | `+cells-get` |
| 续写 / 扩展已有内容 | `+csv-get` 看结构 + `+cells-get` 读源区样式 + `+sheet-info --include row_heights,merges`（见准则 5） |

> "补齐 / 填空"类只探前 10 行就写会漏写表尾——先按 `lark-sheets-read-data` 确认真实数据末行（准则 3）。

### 用脚本配合 CLI 时

- **只读 stdout**：CLI 数据走 stdout、诊断走 stderr；解析 JSON 别 `2>&1`（警告混入会解析失败），用管道或单独重定向 stdout。
- **读表理解优先用 `scripts/lark_*.py`（若可用）**：`lark_inspect_workbook.py` / `lark_detect_subtables.py` / `lark_profile_table.py` 是只读脚本，用来把在线表格整理成结构摘要。**可选增强，不是必经步骤**——`scripts/` 只随仓库版 skill 分发，二进制内嵌版没有这些文件；本地不存在时直接用 CLI 等价路径（对照表见 `lark-sheets-read-data`：`+workbook-info` / `+sheet-info` / 小窗口 `+csv-get`）。它们不替代写入类 shortcut；确认目标区域后，写入仍按对应 reference 执行。
- **喂 CLI 的 CSV / JSON 用 UTF-8 无 BOM**；临时文件**不要落进用户项目目录**——宿主若声明过 workspace 落点纪律（如禁用 `/tmp`）就照它放，没有则用系统临时目录。
- **命令失败先读 stderr 再调整**，别原样重发。
- **回写纯单元格值**：值(样式)注记剥离规则见准则 2（SoT）；补充：残留引号一并剥离；排序优先 `+range-sort` 原生工具，别"读出本地排完再整列写回"。

### 易漏陷阱

- **`+dim-insert` 不继承行高**：只继承值 / 公式 / 边框，新行回落默认高度截断长文本；插行填长文本前读相邻行 `row_height`，用 `+batch-update` 合 `+rows-resize` 补齐。
- **公式容错**：日期 / 查找 / 数值转换公式用 `IFERROR` 包裹；写完读结果列首末各 5 行查 `#VALUE!` / `#REF!` / `#DIV/0!`，必要时再跑 `+formula-verify` 定位问题；只有新证据或方案变化才重试；不确定的写入先回读，避免重复写。
- **循环引用**：聚合公式引用范围不能含目标 cell 自身或其传递依赖。
- **隐藏行列**：`+csv-get` 默认含隐藏行列；设 `--skip-hidden=true` 只看可见，返回的真实行号可能跳空。禁止按返回数组下标推导行号，必须使用 `annotated_csv` 的 `[row=N]` 或 `row_indices`。
- **跨 sheet 对象**：图表 / 条件格式 / 透视表 / 浮动图片可能分布在多个子表，操作前先 `+workbook-info` 掌握全局。
- **按证据判断能力**：当前文档、schema、明确的能力声明或已取得的错误可用于判断不支持；证据冲突时优先只读 / dry-run 探查。不得为证明“不支持”而执行多余生产写入，也不凭猜测宣称能力缺失。
- **NLP 任务分批**：语义理解 / 翻译 / 改写 / 分类等用 NLP 处理（代码只做分批 / 行号映射 / 写回）；数据量大必须分批（通常 30 行 / 批），每批处理完即时写回，单批生成通常 ≤ 300 行，多批用 `+batch-update`。

## References

按当前操作读取对应工具 reference；只有涉及样式或公式时，才读取对应通用规范。编辑约束见 [编辑准则](lark-sheets-editing-principles.md)，已读内容可复用。

### 通用方法与规范（先读，横切所有任务，不含具体 shortcut）

| Reference | 描述 |
| --- | --- |
| [飞书表格样式与配色规范](lark-sheets-visual-standards.md) | 飞书表格样式与配色规范：表头/数据区/汇总行的颜色、字号、对齐、边框、数字格式等取值标准，以及从零新建表格的版式美化、新增汇总行、追加行列继承原表风格、已有区域美化等典型场景的决策流程与样式要点。工具调用参数细节请参考对应的 lark-sheets-write-cells / lark-sheets-range-operations / lark-sheets-batch-update。条件格式（高亮、标红、数据条、色阶）请使用 lark-sheets-conditional-format。 |
| [飞书表格公式生成规则](lark-sheets-formula-translation.md) | Excel 公式到飞书表格公式的迁移与生成规则。核心目标不是保留 Excel 原语法，而是按飞书表格可执行规则重写公式，并在结果上尽量对齐 Excel。当用户要求把 Excel 公式改写成飞书表格公式，或需要生成飞书公式（尤其涉及 ARRAYFORMULA、数组语义与逐行填充、原生数组函数、INDEX/OFFSET、MAP/LAMBDA、日期差、多层范围结果与二次展开）时使用。本文只负责把公式写对，落表后可接 `lark-sheets-formula-verify` 做诊断。 |

### 按对象的工具参考（含 shortcut）

| Reference | 描述 |
| --- | --- |
| [Lark Sheet Formula Verify](lark-sheets-formula-verify.md) | 公式写入 / 批量填充 / `--copy-to-range` 扩展 / 导入含公式工作簿后的诊断入口。对指定子表（或整本工作簿）扫描公式与单元格值，聚合所有 Excel 错误（#REF! / #DIV/0! / #VALUE! / #NAME? / #NULL! / #NUM! / #N/A），同时合并最近一次写入留下的编译失败（formula_errors），输出统一 JSON 让 AI 一次拿到完整健康度报告。任务涉及公式时可调用 +formula-verify 定位问题；`status='errors_found'` 或 `status='partial'` 时记录诊断结果并按任务风险决定是否修复。 |
| [Lark Sheet Workbook](lark-sheets-workbook.md) | 管理飞书表格的工作簿结构（子表列表及元数据）。当用户提到"看看这个表格有什么"、"表格结构"、"有哪些 sheet"、"新建一个 sheet"、"删除这个工作表"、"重命名"、"复制一份"、"移动到前面"时使用。 |
| [Lark Sheet Sheet Structure](lark-sheets-sheet-structure.md) | 管理飞书表格的子表结构与布局。适用场景：查看行高、列宽、隐藏行列、合并单元格等布局信息，以及"插入一行"、"删除这列"、"隐藏行"、"冻结表头"、行列分组（大纲折叠/展开）等操作。行列大纲仅在用户明确提到"行分组"、"列分组"、"大纲"、"outline"时才触发，"按XXX分组"等数据分组场景请使用 lark-sheets-pivot-table。如需在表尾追加数据，应先通过此 skill 插入行，再通过 lark-sheets-write-cells 写入。 |
| [Lark Sheet Read Data](lark-sheets-read-data.md) | 读取飞书表格中的单元格数据。当用户需要"看看数据"、"分析数据"、"统计/汇总"时使用；也适用于需要查看公式、样式、批注等详细信息的场景。 |
| [Lark Sheet Search & Replace](lark-sheets-search-replace.md) | 在飞书表格中搜索和替换文本，支持限定范围、大小写匹配、精确匹配、正则表达式。当用户需要"查找"、"搜索"、"定位"某个值，或"替换"、"批量修改文本"、"把 A 改成 B"时使用。不要用于理解表格结构（应读取数据）、不要用于数据分析（应读取数据后计算）、不要把用户操作动作中的关键词（如"汇总金额""统计数量"）当作搜索词。 |
| [Lark Sheet Write Cells](lark-sheets-write-cells.md) | 向飞书表格的指定区域批量写入值、公式、样式、批注或单元格图片。适用场景：填写数据、设置公式、修改格式、添加批注、嵌入单元格图片（如需操作浮动图片，请使用 lark-sheets-float-image）；若只需把一块 CSV 批量铺到表格上（值或公式，不带样式/批注），直接使用 `+csv-put` 更短更快。追加数据需先通过 lark-sheets-sheet-structure 插入行列。写入公式后可使用 `lark-sheets-formula-verify` 做诊断。 |
| [Lark Sheet Range Operations](lark-sheets-range-operations.md) | 对飞书表格中指定区域执行结构性操作（不涉及写入单元格数据值）。适用场景：清除内容或格式（"清空"、"删除内容"、"去掉格式"）、合并/取消合并单元格、调整行高列宽（"加宽列"、"自适应列宽"）、移动/复制/填充/排序数据（"移动数据"、"复制到"、"自动填充"、"按某列排序"）。写入单元格数据请使用 lark-sheets-write-cells。 |
| [Lark Sheet Styles Put](lark-sheets-styles-put.md) | 把一份声明式视觉规格（样式/边框/合并/行高列宽/冻结）一次性应用到已有飞书表格的多个子表，整份规格一次提交。当任务是对存量表做美化收尾、批量刷样式、统一版式时使用。样式取值标准见 lark-sheets-visual-standards；建新表带样式走 lark-sheets-workbook（+workbook-create --styles）、写数据同步带样式走 lark-sheets-write-cells（+table-put --styles），三者共用同一份 --styles 词汇。仅针对飞书表格。 |
| [Lark Sheet Batch Update](lark-sheets-batch-update.md) | 将多个飞书表格写入操作合并为一次批量执行，按顺序依次完成。适合需要连续执行多个写入操作的场景（如先修改结构再写入数据）。 |
| [Lark Sheet Chart](lark-sheets-chart.md) | 管理飞书表格中的图表（柱形图、折线图、饼图、条形图、面积图、散点图、组合图、雷达图等）。当用户需要创建图表、修改图表样式或数据源、查看已有图表配置、删除图表时使用。也适用于用户提到"数据可视化"、"画个图"、"趋势分析"、"对比图"、"占比分析"、"做个图表"等数据可视化相关场景。 |
| [Lark Sheet Pivot Table](lark-sheets-pivot-table.md) | 管理飞书表格中的数据透视表。当用户需要创建透视表、修改透视表的行列字段/聚合方式/筛选条件、查看已有透视表配置、删除透视表时使用。也适用于用户提到"分组汇总"、"交叉分析"、"按XXX统计"、"按字段分组"、"再分下组"、"多维分析"、"数据透视"等场景。 |
| [Lark Sheet Conditional Format](lark-sheets-conditional-format.md) | 管理飞书表格中的条件格式规则（重复值高亮、单元格值比较、数据条、色阶、排名、自定义公式等）。当用户需要创建条件格式、修改已有规则的范围或样式、查看当前条件格式配置、删除规则时使用。也适用于用户提到"高亮"、"标红"、"颜色标记"、"数据条"、"色阶"、"条件样式"等场景。 |
| [Lark Sheet Filter](lark-sheets-filter.md) | 管理飞书表格中的筛选器（filter）。当用户需要筛选数据（按文本/数值/颜色/日期条件过滤行）、查看已有筛选配置、修改或删除筛选器时使用。也适用于"只看"、"筛选出"、"仅保留符合条件的"等场景。 |
| [Lark Sheet Filter View](lark-sheets-filter-view.md) | 管理飞书表格中的筛选视图（filter view）。当用户需要"建一个 XX 视图"、"保存这个筛选状态"、"切换不同筛选"、维护一个 sheet 上多份独立筛选配置时使用。视图与筛选器（filter）相互独立，可在同一 sheet 共存；视图的隐藏行仅在用户进入该视图时本地生效，不影响其他协作者。 |
| [Lark Sheet Sparkline](lark-sheets-sparkline.md) | 管理飞书表格中的迷你图（折线迷你图、柱形迷你图、胜负迷你图）。当用户需要在单元格内嵌入小型图表来展示数据趋势时使用。也适用于"趋势线"、"单元格内图表"、"迷你图"等场景。注意：不等同于被禁用的 SPARKLINE() 公式函数。 |
| [Lark Sheet Float Image](lark-sheets-float-image.md) | 管理飞书表格中的浮动图片。当用户需要在表格中插入浮动图片、调整图片位置和大小、查看已有浮动图片、删除图片时使用。也适用于"插入图片"、"添加 logo"、"放一张图"等场景。注意：如果用户需要将图片嵌入到某个单元格内部（单元格图片），请阅读 lark-sheets-write-cells。 |
| [Lark Sheet History](lark-sheets-history.md) | 查询飞书表格的历史版本并回滚到指定版本。当用户需要查看一张表的编辑历史版本列表、回滚到某个历史版本、或查询回滚的异步状态（进行中/成功/失败）时使用。回滚为异步操作，发起后通过状态查询轮询结果。仅针对飞书表格。 |
| [Lark Sheet Changeset](lark-sheets-changeset.md) | 读取两个版本（CS revision）之间的 changeset（原始变更操作清单），用于复核某次编辑——尤其是 AI 编辑——是否真实满足用户诉求。传入起始版本（编辑前基线），可选结束版本（省略取最新），版本差上限 20；返回里最外层带当前表格最新版本号。当用户需要"看看这次改了什么"、"核对 AI 改动"、"对比两个版本的变更"时使用。 |
| [Lark Sheet 旧命令迁移指南](lark-sheets-legacy-command-migration.md) | 重构前的 42 个 sheets 旧命令（`+create`、`+read`、`+write`、`+create-sheet`、`+media-upload` 等）已删除，调用会直接报 `unknown subcommand`。当手上的脚本或 skill 早于本次重构、或收到该报错时，用本文查替代命令，以及那些不只是改名的差异：单元格 payload 词汇（`{"type":"formula","text":…}` 已被拒绝）、响应字段路径、`+update-sheet` / `+update-dimension` 拆成多个命令。 |

## 公共 flag 速查

各 reference 的 shortcut 标题下用一行徽章标注支持的公共 / 系统 flag（如 `_公共四件套 · 系统：--dry-run_`；`_公共：URL/token（无 sheet 定位）…_` 表示只接 URL/token）。type / 必填 / 描述在本段统一声明：

### 公共 flag（定位资源）

**公共四件套** = `--url` / `--spreadsheet-token` / `--sheet-id` / `--sheet-name`，分成两组 XOR，**每组都必须给且只能给一个**（XOR = 二选一必填，不是"可选"）：

1. **spreadsheet 定位（必填）**：`--url`（解析 `/sheets/`、`/spreadsheets/`、`/wiki/` 三种链接；wiki 链接自动定位背后的电子表格）与 `--spreadsheet-token`（裸 token）二选一。**例外**：`+workbook-create` / `+workbook-import` 产出**还不存在**的表，不接受任何定位 flag。
2. **sheet 定位（公共四件套 shortcut 必填）**：`--sheet-id` 与 `--sheet-name` 二选一。
   - ⚠️ **不确定 sheet 名时禁止猜 `Sheet1`**：除非对话或上下文已出现具体值，第一步先 `+workbook-info` 拿 `sheets[].sheet_id/title` 再选——中文表的子表常叫"数据"/"工作表 1"/业务名，猜名大概率撞 `sheet not found`。
   - ⚠️ **`--range` 里的 `Sheet1!` 前缀不能替代 sheet 定位**：仍必须传 `--sheet-id` / `--sheet-name`。
   - ⚠️ **A1 引用含 `!` 时整段用单引号包裹**（`--range 'Sheet1!A1:B2'`，挡 bash history expansion；别用 `set +H`，sh/dash 下非法）。sheet 名含 `-`/空格需内层再包单引号时用 `'\''` 转义：`--source ''\''Sales-2025'\''!A1:D100'`。
   - **例外**：徽章标 `_公共：URL/token（无 sheet 定位）…_` 的 shortcut（`+workbook-info` / `+workbook-export` / `+batch-update` / `+styles-put` / `+dropdown-update|delete` / `+cells-batch-clear` / `+sheet-create`）不接受 sheet 定位。`+pivot-create` 用 `--target-sheet-id/name`（XOR，可都不传）。

```bash
# 统一调用范式：两组定位缺一不可（占位符别原样填；表名先 +workbook-info 查）
lark-cli sheets +csv-get --url "https://.../sheets/shtXXX" --sheet-name "<真实表名>" --range "A1:F30"
```

### 系统 flag

| Flag | Type | 必填 | 说明 |
| --- | --- | --- | --- |
| `--dry-run` | bool | 否 | 零副作用：仅打印请求路径与参数模板，不发起调用；多步操作会输出每个子操作的请求模板 |
| `--yes` | bool | 是（仅 `high-risk-write`） | 二次确认；不带时退出码 10。详见 [`../../lark-shared/SKILL.md`](../../lark-shared/SKILL.md) 高风险审批协议 |
| `--print-schema` | bool | 否 | 本地打印复合 JSON flag 的 JSON Schema 并退出，不发起调用、不需要其它 required flag。搭配 `--flag-name` 指定查哪个 flag；省略时列出该 shortcut 可查询的 flag。仅对含复合 JSON flag 的 shortcut 有效。 |
| `--flag-name` | string | 否 | 配合 `--print-schema`：flag 名不带 `--` 前缀（`cells` / `properties`）。**支持点分路径切片**：`--flag-name properties.snapshot.plotArea.axes` 只打印该子树，大 schema（chart 的 properties 约 1700 行）按需取，别整篇翻页。 |

> ⚠️ **high-risk-write 命令清单（exit 10 强确认门禁）**：`+batch-update`、`+cells-clear`、`+cells-batch-clear`、`+sheet-delete`、`+dim-delete`、`+dropdown-delete`，以及各对象删除 `+chart-delete` / `+pivot-delete` / `+cond-format-delete` / `+filter-delete` / `+filter-view-delete` / `+sparkline-delete` / `+float-image-delete`。
>
> **审批协议**：按 [lark-shared](../../lark-shared/SKILL.md) 核对精确目标、操作、影响与已有授权。缺少授权时先准备 dry-run 预览再询问；同一范围已有明确授权时可沿用。exit 10 本身不是授权。

**Agent 使用提示**：写复合 JSON flag 前对结构不确定时，先 `--print-schema --flag-name <name>`（深层字段用点分路径切片）再构造 payload；图表直接 `+chart-create --print-example <type>` 拿最小可用模板改参。reference 的 `## Schemas` 段只给一层结构。

### flag 内容类型与输出约定（术语速记）

- JSON 类入参分三类：**复合 JSON** = 深层嵌套对象（`--print-schema` 可查）；**简单 JSON** = 一二维标量数组；**非 JSON 文本** = 原样文本（如 CSV）。`--print-schema` 只对复合 JSON flag 有效。
- **envelope**：所有 shortcut 返回统一外层 `{ok, identity, data, ...}`；写操作不会自动回读，校验自行调用 `+*-list` / `+*-get` / `+cells-get`。

## 复合 JSON / 大入参：优先 stdin

flag 帮助里标注支持 **Stdin** 的入参，当 payload 较大、含换行 / 引号等特殊字符，或已经落在某个文件里时，优先用 stdin（`-`）传入，避免命令行超长与 shell 转义问题。

推荐写法：payload 写到用户项目目录之外的临时文件（落点同上：宿主声明过禁用 `/tmp` 就放 workspace 内相对路径，否则系统临时目录），再用 stdin 喂进去：

```bash
# TMPFILE 指向 payload 文件（落点按上文纪律选：workspace 内相对路径，或系统临时目录）
lark-cli sheets +cells-set --url "..." --sheet-name "Sheet1" --range "A1:B2" --cells - < "$TMPFILE"
lark-cli sheets +batch-update --url "..." --dry-run --operations - <<'JSON'   # high-risk：先 --dry-run，用户同意后再追加 --yes 重发
[{"shortcut":"+cells-set","input":{...}}]
JSON
```

- **stdin 每次调用只能给一个 flag**：`+table-put` 同时传 `--sheets` 与 `--styles` 两个大 JSON 时，一个走 `-`、另一个走 `@./styles.json`（`@file` 只接受 cwd 下相对路径，**绝对路径会被拒**；正解是 stdin，别 cd、别把临时文件写进用户项目目录）。
- **参数含特殊字符时用单引号包裹即可，不要 `set +H`**（sh/dash 下非法直接报错）；参数本身含单引号或 payload 大时走 stdin。
- **非 POSIX shell（PowerShell / cmd.exe）适配**：本 skill 全部 `bash` 代码块（heredoc `<<'JSON'`、单引号转义 `'\''`）只适用于 bash / zsh，动手前先判断当前 shell，非 POSIX 环境按下表改写，**不要试错式改引号**——`@file`（cwd 相对路径）是全平台无引号问题的兜底形态：

| 形态 | bash / zsh | PowerShell | cmd.exe |
| --- | --- | --- | --- |
| 大 / 多行 JSON | `--flag - <<'JSON' … JSON` | 先写 UTF-8 无 BOM 文件再 `--flag '@./x.json'`，或 `Get-Content -Raw ./x.json \| lark-cli … --flag -` | 先写文件再 `--flag @./x.json`（cmd 无 heredoc / 管道读文件不可靠） |
| 单行 inline JSON | `--flag '{"a":1}'` | `--flag '{"a":1}'`（PS 单引号同为字面量） | 不要 inline——cmd 会吃掉内层双引号，一律走 `@file` |
