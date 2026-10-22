# 市场顾问部模板渠道 CASE 编译性能优化

## 适用范围

- 业务域：`market_consultant`
- 平台来源：模板取数
- 当前共享规则入口：`resources/raw_sql/market_channel_case_when_1016.sql`；以下五路 UNION 记录属于 0925 历史版本
- 规则基线：183 条 `WHEN`、127 个分支输出值（含 ELSE 共 128，2026-10-09 AST 重算，旧 129 已撤销）；融合 CASE 文件 SHA-256 为 `d882a5a82562ed698961cb28e0846a0825f494d868c37e693b4970d2b79ddb8a`
- 适用模板：`AI分析市场顾问部_宽表`（id `9002`）、`AI分析市场顾问部多科用户成单数据`（id `8882`）

本文件记录超长模板的同类编译故障修复模式。它只描述模板取数口径，不替代数据中心 canonical SQL，也不改变 0925 CASE 的业务顺序。

## 0925历史线上版本登记（仅作历史参考）

| 模板 | 发布后 SQL | 参数 | 输出字段 | 发布后真实查询 |
|---|---|---|---:|---|
| `AI分析市场顾问部_宽表`（9002） | [`template_query_market_wide.sql`](../../resources/raw_sql/template_query_market_wide.sql)，SHA-256 `274d12a9b47e83d944c7ce5c0cda546e0b7d2f74eb0541dfb0d79edb90137591` | `\${qici:1}`, `\${qici:2}` | 122 | query `405866`，513 行，182 秒，`SUCCESS` |
| `AI分析市场顾问部多科用户成单数据`（8882） | [`template_query_market_multi_subject_order_user.sql`](../../resources/raw_sql/template_query_market_multi_subject_order_user.sql)，SHA-256 `c4a66422fccedc99113a9c15bc65dc161ebd2203e2de85e20b338542cccd2d0e` | `\${qici:1}`, `\${qici:2}` | 22 | query `405864`，130 行，36 秒，`SUCCESS` |

0925 历史发布时两个模板均保持原模板 id、名称、owner `lvshuai01`、数据源实例 `dlc_presto` 和已有申请/权限关系，均按 Apply、独立 Publish、线上 SQL 回读、发布后真实查询完成闭环。8882 原线上版本没有 SQL 参数；因永久模板发布门禁要求至少一个参数，本次将固定的 `period_name >= '20260403期'` 改为 `\${qici:1}`/`\${qici:2}` 同名半开区间过滤，输出字段和渠道口径不变，并减少无关期次扫描。

## 故障特征

同类失败通常表现为 `PRESTO_EXECUTE_DQL_ERROR(code=3021)`、`Compiler failed`、`Query results in large bytecode exceeding JVM` 。这类编译报错的根因是 183 条渠道规则被编译为一个超长 CASE，叠加模板自身多层 CTE 后超过 Presto 编译器的字节码/stage 或查询时限；不是渠道规则顺序错误，也不是结果为空。

不要用以下方式绕过：

- 删除或机械截断 0925 分支；
- 重排更具体或更宽泛规则；
- 用 `UNNEST` 数组或未经验证的行类型比较替换规则；
- 仅把固定期次改宽，或删除业务过滤来“避开”超时；
- 用 UI 面板超时代替 Result API 的最终状态。

## 已验证的 SQL 结构

### 1. 规则级审计

从线上已发布 SQL 和 0925 canonical SQL 分别提取 active `WHEN` 分支，必须同时满足：

1. 分支数均为 183；
2. 条件文本和输出文本逐条、逐序一致；
3. canonical CASE 文件 SHA-256 为 `d882a5a82562ed698961cb28e0846a0825f494d868c37e693b4970d2b79ddb8a`；
4. `其他未知流量` fallback 保留；
5. 期次、部门、流量池、source 负责人、SKU 等精确覆盖仍处在原优先级位置。

性能拆分只能改变编译形态，不能把相邻规则按输出值合并或改变顺序。

### 2. 五组连续 CASE + 最小规则组

将 183 条分成五个连续组：1-37、38-74、75-111、112-147、148-183（37/37/37/36/36）。每组使用独立 CASE：命中返回渠道值，未命中返回 `cast(null as varchar)`；五组通过 `UNION ALL` 产出 `(mapping_key, channel, rule_group)`，再按 `mapping_key` 使用 `min_by(channel, rule_group)` 选择最早非空规则组。

`min_by` 选择最早非空规则组，因此等价于原始 183 条 CASE 的 first-match 语义。0925 版本采用 37/37/37/36/36 五组，既保持完整规则顺序，又把单个编译单元控制在已验证范围内。

### 3. 无碰撞键和回连

在渠道 CASE 依赖的全部字段上生成长度前缀键：NULL 编码为 `N`，非 NULL 值编码为 `V<varchar_length>:<varchar_value>`，字段之间用 `|` 连接。两个模板使用的 28 个映射字段为：

`period_name`、`rule_name`、`flow_pool_name`、`sku_id_name`、`ad_account_name`、`source_manager_name`、`channel_name_1`、`channel_name_2`、`channel_name_3`、`put_plan_name`、`flow_original_order_activity_price`、`flow_orders_income_amount`、`flow_order_price`、`channel_provider_name`、`channel_second_provider_name`、`page_id_name`、`source_put_plan_name`、`get_customer_way_name`、`first_department_name`、`second_department_name`、`third_department_name`、`virtual_second_department_name`、`virtual_fourth_department_name`、`virtual_fifth_department_name`、`trace_type_name`、`lead_purchase_intention_level1_category_name`、`lead_purchase_intention_level2_category_name`、`lead_create_time`。

先对源 CTE 计算 `mapping_key`，对五组结果按键取最早渠道，再左连接回源行，并使用 `coalesce(channel, '其他未知流量')`。键不包含线索量、金额、用户或订单统计字段，所以相同映射条件的重复源行会共享归因结果但不会被去重；`N` 标记和长度前缀避免 NULL/空串以及拼接边界碰撞。回连后再进入原有聚合，保留模板原始粒度、金额、计数和 NULL/fallback 行为。

### 4. 期次范围下推

对有模板参数的查询保留同名字段参数的左闭右开形式：`where period_name >= \${qici:1} and period_name < \${qici:2}`。参数不要包裹 `cast`、`date`、`substr`，也不要改名为 `begin_period`/`end_period`。生成实际探针时才替换为具体期次；沉淀到模板 raw SQL 时保留参数形态。

## 验证门禁

每次维护两个模板或其他共享 CASE 模板时，必须留下以下证据：

1. 从线上 published 版本读取 baseline，确认唯一模板 id、owner、实例、参数和输出字段；
2. 对候选 SQL 按当前共享源逐分支、逐序比对（1016与1009均193条，历史1002为188条、0925为183条），检查 fallback、关键字段覆盖和参数计数；
3. 通过 `text2sql.py validate-sql` 的 concrete SQL 检查；`validate_sql_rules.py` 若命中旧模板 `src` 投影的已知解析器误报，必须同时保存未修改 baseline 对照，不能把误报写成 Presto 失败；
4. 使用目标模板实际引擎运行候选 SQL，执行时间必须小于 300 秒且 Result API 为 `success_with_rows`；
5. 按精确计划 hash 原位 Apply，回读未发布版本 SQL/metadata hash；
6. 单独 Publish，回读 `status=2` 和线上 SQL hash；
7. 必须用发布后回读 SQL 生成具体参数探针并再次实际查询；UI 结果面板缺失时以同一 query id 的 Result API、HTTP 200、error code 0 和字段元数据为准；
8. 对有效模板不创建新模板、不重置权限；远端已经删除的模板不恢复、不同步，并从当前 canonical 路由移除。

后续如规则源发生变化，先按 [`channel_mapping_case_when.md`](channel_mapping_case_when.md) 完成当前版本之后的逐分支新增/删除/顺序审计，再分别从两个模板的线上 SQL 生成候选；不得把本文件中的五组切分当作可独立维护的渠道规则副本。


## 1002 业财模板单扫描优化（2026-10-09 已验证）

模板 `7689` 的1002当轮线上版本使用五组188条规则（38/38/38/37/37）。原结构需要映射键、DISTINCT 映射维度、五路 UNION、`min_by` 和回连；源事实有七条有效引用路径。模板 query `407928` 在目标实例运行 900 秒后由引擎取消，最终状态为失败。504 或 UI 超时须按同一 Query ID 的终态及日志诊断为查询超时，不能直接等同于字节码故障。

从实时 published SQL 新取 immutable baseline 后，将这些相同的五个 CASE 按原顺序放入同一个源行投影：

```sql
src_mapped AS (
    SELECT s.*,
           COALESCE(<case_group_1>, <case_group_2>, <case_group_3>,
                    <case_group_4>, <case_group_5>, '其他未知流量') AS channel_map
    FROM src s
)
```

每组未命中仍返回 NULL，故 `COALESCE` 的首个非空组与 `min_by(channel, rule_group)` 选择最小非空组等价。原 28 字段键覆盖全部 CASE 输入，同键归因结果确定，因此无需先按键去重/回连；重复源行仍保留到原有最终 DISTINCT。审计覆盖全部 243 种三值/NULL 组合；188 条分支及注释/顺序、源过滤、期次映射、最终 27 个字段和 DISTINCT 均未改变。1002当轮归档含131个WHEN输出值，包含ELSE共132。

单事实扫描替代七条引用路径，移除长度前缀拼接、维度去重、重复扫描、分组和回连；不使用数组 UNNEST。保持原模板 ID、参数及申请关系，Apply/Publish 后 SQL SHA-256 为 `f5b5a0bc63f21e9e45e7abcffcb4832654a7d8db145842c8fc3f5cb2d093e216`，真实 query `407937`（`${dt}='20261002期'`）7 秒返回 7,381 行 SUCCESS。线上源二级部门原本缺失，本次按用户授权补充 `市场部` 并保留三级 `市场顾问部`；性能优化的 fresh baseline 已包含该条件。

上述运行证据只适用于1002当轮7689版本。其他超长模板须从实时SQL分析字段、参数、重复扫描与粒度；范围变更需依据用户授权，不能借性能优化擅自收窄部门或NULL范围。最新消费者状态见当前渠道维护入口。


## 1009运行复核（2026-10-12）

193条共享规则分为39/39/39/38/38，保留既有COALESCE单扫描或min_by组序选择。7689与9002没有恢复重复源扫描、序列化键或映射回连；本轮只更新CASE内容，性能结构与源过滤保持实时生产原状。

| 模板ID | 发布后Query ID | 行数 | 秒 | 终态 |
|---:|---:|---:|---:|---|
| 7689 | 408704 | 3707 | 22 | SUCCESS |
| 7808 | 408705 | 6594 | 267 | SUCCESS |
| 8735 | 408711 | 519 | 150 | SUCCESS |
| 8866 | 408743 | 8525 | 28 | SUCCESS |
| 8882 | 408721 | 103 | 147 | SUCCESS |
| 8948 | 408716 | 578 | 95 | SUCCESS |
| 9002 | 408722 | 508 | 230 | SUCCESS |

本轮未发生SQL504。三次45000ms模板解析接口请求超时采用相同候选的只读重新解析，不能据此判断查询SQL超时；所有已发布模板的真实查询已成功。不同查询使用不同期次/日期与更新截面，耗时和行数不能直接作为与历史版本的等量性能对比。


## 1016运行复核（2026-10-19）

四处条件扩展保留193条共享规则及原顺序。原7模板保持39/39/39/38/38连续组，10477保持40/40/40/40/33；同源COALESCE与min_by组序结构、分区/期次/部门下推和输出粒度保持。10477仅改4处谓词正文，_map_输入映射、键和35个输出字段保留。没有为提速删行或修改范围。

| 模板ID | 发布后Query ID | 行数 | 秒 | 终态 |
|---:|---:|---:|---:|---|
| 7689 | 411355 | 8472 | 17 | SUCCESS |
| 7808 | 411356 | 1857 | 268 | SUCCESS |
| 8735 | 411362 | 1256 | 60 | SUCCESS |
| 8866 | 411367 | 8867 | 50 | SUCCESS |
| 8882 | 411368 | 129 | 97 | SUCCESS |
| 8948 | 411365 | 1447 | 80 | SUCCESS |
| 9002 | 411370 | 569 | 234 | SUCCESS |
| 10477 | 411408 | 777 | 113 | SUCCESS |

不同期次、日期及源截面的结果与耗时不能直接当作历史版本的等量性能对比。SQL执行超时与解析/请求超时分别依据同一Query ID和日志诊断。
