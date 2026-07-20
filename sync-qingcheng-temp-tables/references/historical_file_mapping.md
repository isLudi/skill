# 青橙群文件与临时表映射

证据快照日期：2026-07-20。群聊为 `青橙数据对接`，发布人为郅玲玉。历史检索返回 93 条该发布人的 Excel 附件消息；运行时必须重新检索，不得把本快照当成“当前最新”。

## 当前自动化范围

| 文件族 | 最新消息证据 | 源切片与行数 | 本地累计工作簿 | 线上临时表 |
|---|---|---|---|---|
| 个人期度目标表 | `om_x100b6a81a78690a8c4c04921d74b4f7`，2026-07-18 19:08 | `20260626期` 至 `20260716期`，445 行 | `E:\1900_work\GAOTU\19003_青橙项目部看板维护表格\qing_goal.xlsx` | `temp_table.dingxi01_qing_goal` |
| 团队期度目标表 | `om_x100b6a81a700b0a0c072551f4a0965d`，2026-07-18 19:08 | 同上，88 行 | `...\qing_team_goal_qi.xlsx` | `temp_table.dingxi01_qing_team_g_qi` |
| 团队月度目标表 | `om_x100b6a4c225ae0a4def65b85fcefd79`，2026-07-15 21:10 | `202607`，22 行 | `...\qing_team_goal_moth.xlsx` | `temp_table.dingxi01_qing_team_goal` |
| 全员结果数据架构 | `om_x100b6a4ce4c9eca0df9524c9eddd444`，2026-07-15 21:26 | `20260626期` 至 `20260716期`，461 行 | `...\qing_team_jg.xlsx` | `temp_table.dingxi01_qing_team_jg` |
| 期次带班架构 | `om_x100b6a4280e92ca8c020397a005c5fd`，2026-07-15 19:20 | `20260722期`，140 行 | `E:\1900_work\GAOTU\19002_市场顾问部看板维护表格\jiagou_db.xlsx` | `temp_table.dingxi01_jiagou_db` |

线上聚合探针 `query_id=1488060600` 验证四张青橙表的对应切片分别为 445/88/22/461 行，唯一键数与行数相等；`query_id=1488063518` 验证 `dingxi01_jiagou_db` 中 `20260722期 + dept_1=青橙项目部 + zaizhi=1` 为 140 行、140 个员工键。上述结果与群文件和本地累计工作簿一致。

## 字段与业务键对应

| 文件族 | 源字段到临时表字段 | 切片 | 唯一业务键 |
|---|---|---|---|
| 个人期度目标表 | `month,qici,xuebu,jingli,dazu,xiaozu,guwen,goal` → `month,qici,xuebu,jingli,dazu,xiaozu,name,qudao,goal`；其中 `guwen→name`、`qudao='-'` | `qici` | `qici + name` |
| 团队期度目标表 | `month,qici,xuebu,jingli,dazu,xiaozu,emye_c,goal` 原名对应 | `qici` | `qici + xuebu + jingli + dazu + xiaozu` |
| 团队月度目标表 | `month,xuebu,jingli,dazu,xiaozu,emye_c,goal` 原名对应 | `month` | `month + xuebu + jingli + dazu + xiaozu` |
| 全员结果数据架构 | `employee_name,employee_email_name,email_prefix,leader_employee_email_name,leader_email_prefix,dazu,jingli,xuebu,qici` 原名对应 | `qici` | `qici + employee_email_name` |
| 期次带班架构 | `xiaozu_z,employee_email_prefix,xiaozu,employee_email_name,department,zaizhi,qici,dept_1,dept_2,jingli` 原名对应 | `qici`，且目标作用域限定 `dept_1='青橙项目部'` | `qici + employee_email_name` |

## 合并规则

- “追加”统一实现为 slice upsert：先删除目标中与源文件重叠的 `qici` 或 `month` 切片，再插入源切片；历史非重叠切片必须保留。
- 个人期度目标把源列 `guwen` 重命名为目标列 `name`，并补 `qudao='-'`。2026-07-18 样本的 445 行在本地表中全部对应 `qudao='-'`。
- 青橙四张累计工作簿按切片升序保存。
- `jiagou_db.xlsx` 是跨部门累计载体，按切片降序保存。只替换 `dept_1='青橙项目部'` 的源期次行；同一期 `市场顾问部` 行以及其他历史期次必须原样保留。
- 每个源文件先按登记键做严格唯一性检查。目标表的旧问题只允许保持不变，不允许新增或扩大。
- Excel 中的公式按有效缓存值判断幂等；真正发生切片变化时才重建该切片，并通过 Excel COM 重算后再允许本地 Apply。
- 平台上传使用完整本地累计工作簿、`target-mode=reuse`、`import-mode=overwrite`；禁止把单次群文件直接以平台 `append` 模式上传。

## 历史演变与识别边界

- 2026-01 至 2026-04 的带班架构经历 9 列（含 `daibanqudao/nianji`）、7 列、当前 10 列三种结构。旧结构只用于历史分析，不自动写入当前 10 列累计表。
- 2026-05-08 的通用 `期度目标表.xlsx` 是团队期度结构；从 2026-05-29 起稳定拆为个人期度、团队期度、团队月度三类。通用旧期度文件不得自动识别为个人目标。
- 2026-05-29 的首版 `全员结果数据架构.xlsx` 缺少 `qici`，不能安全追加；2026-06-13 的 `qing_team_moth_jg.xlsx` 已成为带 `qici` 的历史累计快照，之后群内 `全员结果数据架构.xlsx` 稳定带 `qici`。
- 同一期文件会被修订。`0716期带班架构.xlsx` 从 2026-07-08 的 147 行修订为 2026-07-15 的 140 行，所以必须按消息时间选择最新版并替换整期，不能简单追加。
- `qi*daibanguocheng.xlsx` 是带班过程文件，`task_*.xlsx` 与 `CRM线索数据*.xlsx` 是查询或分析制品，均不属于自动上传源。

## 治理边界

- `plan` 只读群消息、下载附件到 runtime、生成本地 staged 副本和 Hash 绑定计划；不改 E 盘维护表，不上传平台。
- `apply-local` 必须消费精确计划 Hash，并在改写前为每个变化工作簿创建时间戳备份；失败时恢复本轮已写文件。
- `upload` 必须消费成功的本地 ApplyReceipt、重新检查群内最新消息没有漂移，并带显式生产上传确认。平台多表覆盖不是原子事务；失败 receipt 必须列出已成功、失败和未执行表。
