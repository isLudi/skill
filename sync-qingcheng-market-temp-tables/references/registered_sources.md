# 已登记来源、目标与质量门禁

本页是人工可读索引；`workflow_registry.json` 是机器执行真源。历史消息 ID 和行数只是设计证据，运行时必须重新检索对应精确群聊中的最新匹配消息。

## 固定身份与群聊

| 领域 | 群聊 | 精确 chat_id | 默认来源人 | open_id |
|---|---|---|---|---|
| 青橙项目部 | 青橙数据对接 | `oc_e604e064976c022ab4289fc2fb979332` | 郅玲玉 | `ou_bf111effd2d71a52ee40c58c7cb4d105` |
| 市场顾问部 | 市场顾问部临时表上传 | `oc_7b9873ee89b18d11cf60c8768c6eba9e` | 张君言 | `ou_04f543bec3cdd195bbdd53a582f68443` |
| 青橙行课例外来源 | 青橙数据对接 | 同上 | 李怡青 | `ou_3168c83ffe93b49a192755c8e31e2bc5` |

来源人、文件名和内容同时匹配，但群 ID 不匹配时必须拒绝。历史私聊仅用于建立市场映射和阈值，不是生产取件源；市场生产附件只能来自新群。

## 青橙六类表

| family_id | 登记源 | 本地累计工作簿 | 平台临时表 | 合并作用域 |
|---|---|---|---|---|
| `personal_period_goal` | `个人期度目标表.xlsx` / `个人期次目标表.xlsx` | `E:\1900_work\GAOTU\19003_青橙项目部看板维护表格\qing_goal.xlsx` | `dingxi01_qing_goal` | 源 `qici` 切片 |
| `team_period_goal` | `团队期度目标表.xlsx` / `团队期次目标表.xlsx` | `...\qing_team_goal_qi.xlsx` | `dingxi01_qing_team_g_qi` | 源 `qici` 切片 |
| `team_month_goal` | `团队月度目标表.xlsx` / `月度目标表.xlsx` | `...\qing_team_goal_moth.xlsx` | `dingxi01_qing_team_goal` | 源 `month` 切片 |
| `result_architecture` | `全员结果数据架构.xlsx` | `...\qing_team_jg.xlsx` | `dingxi01_qing_team_jg` | 源 `qici` 切片 |
| `period_architecture` | 青橙带班架构文件 | `E:\1900_work\GAOTU\19002_市场顾问部看板维护表格\jiagou_db.xlsx` | `dingxi01_jiagou_db` | `dept_1=青橙项目部` 且源 `qici` |
| `course_schedule` | 李怡青发布的登记文档链接 | `E:\1900_work\GAOTU\19003_青橙项目部看板维护表格\qing_daoke.xlsx` | `dingxi01_qing_daoke` | 活动页对应 `qici` |

前三类目标表允许在登记文件名前增加一个严格的数字月份前缀：`1月`–`12月`，并兼容 `01月`–`09月`。月份以外的文本前缀、`0月`、`13月`、中文数字月份和其他扩展名仍不匹配。

2026-07 历史证据包括：个人目标 445 行、团队期度 88 行、团队月度 22 行、全员架构 461 行、青橙带班架构 140 行、行课表 90 行。对应消息和线上探针留在原审计记录中；它们不得替代运行时新鲜度检查。

## 市场本地工作簿与平台临时表全量映射

2026-07-29 对 `E:\1900_work\GAOTU\19002_市场顾问部看板维护表格` 直属文件完成盘点：排除两个凭据环境文件后，共有 9 个 `.xlsx`。以下本地文件名和平台表名各自唯一，组成严格一一映射：

| 本地文件 | 大航海完整表名 | 当前用途 |
|---|---|---|
| `ceshiqudao_pingyou.xlsx` | `temp_table.dingxi01_ceshiqudao_pingyou` | 仅登记映射 |
| `cost.xlsx` | `temp_table.dingxi01_cost` | 自动维护文件族 `market_cost` |
| `daoke_1_6_t.xlsx` | `temp_table.dingxi01_daoke_1_6_t` | 自动维护文件族 `market_attendance_schedule` |
| `jiagou_db.xlsx` | `temp_table.dingxi01_jiagou_db` | 自动维护文件族 `market_period_architecture`；与青橙按 `dept_1` 共享 |
| `jiagou_xinren.xlsx` | `temp_table.dingxi01_jiagou_xinren` | 仅登记映射 |
| `jiagou_zx.xlsx` | `temp_table.dingxi01_jiagou_zx` | 仅登记映射 |
| `jinliang_goal.xlsx` | `temp_table.dingxi01_jinliang_goal` | 自动维护文件族 `market_lead_goal` |
| `pingyou_jg.xlsx` | `temp_table.dingxi01_pingyou_jg` | 自动维护文件族 `market_evaluation_architecture` |
| `plan_id.xlsx` | `temp_table.dingxi01_plan_id` | 自动维护文件族 `market_plan_id` |

平台核验使用九张表的 `WHERE 1=0` 零行解析探针，不读取业务行；查询 ID `1506786567`，状态 `Success`。其中 `jiagou_xinren.xlsx` 当前为 160 行、字段为 `employee_email_prefix`、`employee_email_name`、`new_qici`，与既有线上核验记录一致。

机器真源是 `workflow_registry.json.local_temp_table_inventories.market_consultant`。加载注册表时必须同时验证：

- 本地文件名不重复；
- 平台 `dingxi01_*` 名称不重复；
- 6 个 `managed` 映射与对应文件族的本地路径和平台目标完全一致；
- 3 个 `mapping_only` 映射没有 `workflow_family_id`，且继续处于延迟自动化列表。

`mapping_only` 只解决身份映射，不构成自动同步或上传授权。若以后要让张君言维护这 3 张表，必须先补齐精确来源文件规则、来源质量阈值、合并策略、验证规则和测试，再把范围改为 `managed`。

## 市场六类自动维护表

2026-07-29 对张君言历史私聊完成了 240 条消息盘点，其中 94 条为文件消息，识别出以下六个稳定文件族。最新历史附件只用于初始化规则和来源切片哈希。

| family_id | 最新历史证据 | 本地累计工作簿 | 平台临时表 | 合并模式 |
|---|---|---|---|---|
| `market_cost` | `cost.xlsx`，2026-07-26，29 行 | `E:\1900_work\GAOTU\19002_市场顾问部看板维护表格\cost.xlsx` | `dingxi01_cost` | 源 `qici` 切片 upsert |
| `market_period_architecture` | `daiban_jg_db.xlsx`，2026-07-28，8602 行 | `...\jiagou_db.xlsx` | `dingxi01_jiagou_db` | 只处理新增/变更源切片；目标限定 `dept_1=市场顾问部` |
| `market_attendance_schedule` | `daoke_1_6_t.xlsx`，2026-07-27，6881 行 | `...\daoke_1_6_t.xlsx` | `dingxi01_daoke_1_6_t` | 只处理新增/变更源切片 |
| `market_lead_goal` | `leads_goal.xlsx`，2026-07-28，19 行 | `...\jinliang_goal.xlsx` | `dingxi01_jinliang_goal` | 源 `qici` 切片 upsert |
| `market_evaluation_architecture` | `pingyou_jg.xlsx`，2026-07-21，5921 行 | `...\pingyou_jg.xlsx` | `dingxi01_pingyou_jg` | 确定性修订后完整替换 |
| `market_plan_id` | `plan_id.xlsx`，2026-07-28，96 行 | `...\plan_id.xlsx` | `dingxi01_plan_id` | 只处理新增/变更源切片 |

历史样本数量分别为：架构 24、到课 7、成本 14、评优 14、进量目标 13、计划 ID 14。历史消息中存在“年级错了”“渠道改了”“ID 错了”等同文件修订，因此选择必须以消息时间和位置确定最新版，不能按文件名首次命中。

现有共享 `jiagou_db.xlsx` 的 operator 基线包含 1 个大写邮箱前缀错误和 231 个 `qici+employee_email_name` 重复键组；评优表另有 2 个一对多映射警告。这些是已记录的目标基线，不得新增或扩大。架构候选采用前后错误签名和数量回归比较；若无法证明未回归则阻断，不得把基线问题解释为来源正常。

## 字段、键与共享表保护

完整字段顺序、别名、常量列和校验规则见注册表。关键保护如下：

- 所有文件族先校验登记业务键唯一；任何新增重复键阻断。
- `jiagou_db.xlsx` 是跨部门共享载体。青橙和市场分别按 `dept_1` 作用域替换，另一领域所有行必须字节语义等价地保留。
- 市场带班架构源缺少 `dept_1`，仅允许 `dept_2` 属于已登记市场组织集合的行进入候选，再补 `dept_1=市场顾问部`。
- 市场到课键为 `qici+qudao+grade+begin_time+dow+ke_1+channel`。
- 市场评优键为 `qici+employee_email_name`；分配计划键为 `year+qici+group_id`。
- 平台上传总是使用验证后的完整本地累计工作簿、`target-mode=reuse`、`import-mode=overwrite`，禁止把单次附件直接按平台 append 上传。

## 四类来源质量门禁

| 文件族 | 最大年龄 | 总行数下界–上界 | 最大逐切片相对变化 |
|---|---:|---:|---:|
| 青橙个人期度目标 | 360 小时 | 50–2000 | 50% |
| 青橙团队期度目标 | 360 小时 | 10–500 | 50% |
| 青橙团队月度目标 | 840 小时 | 5–200 | 50% |
| 青橙全员结果架构 | 360 小时 | 50–2000 | 35% |
| 青橙带班架构 | 360 小时 | 20–800 | 35% |
| 青橙行课 | 240 小时 | 20–500 | 50% |
| 市场成本 | 360 小时 | 10–200 | 60% |
| 市场带班架构 | 360 小时 | 4000–9000 | 35% |
| 市场到课 | 360 小时 | 5000–8000 | 35% |
| 市场进量目标 | 360 小时 | 5–100 | 50% |
| 市场评优架构 | 480 小时 | 4500–7500 | 25% |
| 市场计划 ID | 360 小时 | 50–200 | 50% |

相对变化优先使用目标同一切片；新切片使用目标最新切片。必要列空值阈值按文件族登记在注册表，大多数关键字段为 0；青橙个人目标的少数组织层级列允许 2%。任何阈值缺失、来源过期、行数越界、变化超限、必要列空值超限或无可用基线都阻断。

这些阈值是异常阻断线，不是业务目标。已确认的组织扩张或课程规模变化必须先评审并修改注册表和测试，再生成新 Plan；运行时不得临时放宽。

## 来源切片基线

`source_slice_baselines.json` 保存市场带班架构、到课和计划 ID 的初始来源切片行数与 SHA-256，不保存业务行内容。只有成功完成生产上传后，运行时基线才能原子更新。

- 来源删除任一登记历史切片：阻断。
- 单次变更切片数超过登记上限：阻断。
- 非最近窗口的历史切片发生变化且不在审查白名单：阻断。
- `market_plan_id` 的 0529/0605 两期有一次性 `bootstrap_pending`，用于修复现有目标中 6 条期次前缀错误；只有成功上传后该标记才消失。

## 阶段边界

- `plan`：读飞书、下载到 runtime、读目标、生成 staged 候选与哈希；不改 E 盘、不上传。
- `apply-local`：精确 Plan 哈希、来源/目标/基线无漂移、质量门禁仍有效，才可备份并原子替换。
- `upload`：精确本地回执哈希、目标读回一致、群内无更新，才可逐表上传。
- 多表平台覆盖不是原子事务。失败回执必须明确已成功、失败和未执行列表。
