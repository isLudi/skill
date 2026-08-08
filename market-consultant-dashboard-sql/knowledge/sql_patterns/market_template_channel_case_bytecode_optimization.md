# 市场顾问部模板渠道 CASE 编译性能优化

## 适用范围

- 业务域：\`market_consultant\`
- 平台来源：模板取数
- 共享规则基线：\`resources/raw_sql/market_channel_case_when_0808.sql\`
- 规则基线：175 条 \`WHEN\`、118 个去重渠道值；完整 CASE 文本 SHA-256 为 \`136accb16cf81580f2a2f97198a91225c174a5ee01b27ca6b9327ceac45df7e5\`
- 适用模板：\`AI分析市场顾问部_宽表\`（id \`9002\`）、\`AI分析市场顾问部多科用户成单数据\`（id \`8882\`）

本文件记录两个已发布模板的同类编译故障修复模式。它只描述模板取数口径，不替代数据中心 canonical SQL，也不改变 0808 CASE 的业务顺序。

## 线上版本登记

| 模板 | 发布后 SQL | 参数 | 输出字段 | 发布后真实查询 |
|---|---|---|---:|---|
| \`AI分析市场顾问部_宽表\`（9002） | [\`template_query_market_wide.sql\`](../../resources/raw_sql/template_query_market_wide.sql)，SHA-256 \`71274379824c29b4216041b0841a3696a41525589d80075fd3ca536941356138\` | \`\${qici:1}\`, \`\${qici:2}\` | 122 | query \`386622\`，540 行，130 秒，\`SUCCESS\` |
| \`AI分析市场顾问部多科用户成单数据\`（8882） | [\`template_query_market_multi_subject_order_user.sql\`](../../resources/raw_sql/template_query_market_multi_subject_order_user.sql)，SHA-256 \`0a410a877c5895dae41f3bd46241a6fe003f2a20d7c2bf77f0e72fa87aa811ff\` | \`\${qici:1}\`, \`\${qici:2}\` | 22 | query \`386604\`，102 行，19 秒，\`SUCCESS\` |

两个模板均保持原模板 id、名称、owner \`lvshuai01\`、数据源实例 \`dlc_presto\` 和已有申请/权限关系，均按 Apply、独立 Publish、线上 SQL 回读、发布后真实查询完成闭环。8882 原线上版本没有 SQL 参数；因永久模板发布门禁要求至少一个参数，本次将固定的 \`period_name >= '20260403期'\` 改为 \`\${qici:1}\`/\`\${qici:2}\` 同名半开区间过滤，输出字段和渠道口径不变，并减少无关期次扫描。

## 故障特征

同类失败通常表现为 \`PRESTO_EXECUTE_DQL_ERROR(code=3021)\`、\`Compiler failed\`、\`Query results in large bytecode exceeding JVM\` 或平台 504。根因是 175 条渠道规则被编译为一个超长 CASE，叠加模板自身多层 CTE 后超过 Presto 编译器的字节码/stage 或查询时限；不是渠道规则顺序错误，也不是结果为空。

不要用以下方式绕过：

- 删除或机械截断 0808 分支；
- 重排更具体或更宽泛规则；
- 用 \`UNNEST\` 数组或未经验证的行类型比较替换规则；
- 仅把固定期次改宽，或删除业务过滤来“避开”超时；
- 用 UI 面板超时代替 Result API 的最终状态。

## 已验证的 SQL 结构

### 1. 规则级审计

从线上已发布 SQL 和 0808 canonical SQL 分别提取 active \`WHEN\` 分支，必须同时满足：

1. 分支数均为 175；
2. 条件文本和输出文本逐条、逐序一致；
3. canonical CASE 文本 SHA-256 为 \`136accb16cf81580f2a2f97198a91225c174a5ee01b27ca6b9327ceac45df7e5\`；
4. \`其他未知流量\` fallback 保留；
5. 期次、部门、流量池、source 负责人、SKU 等精确覆盖仍处在原优先级位置。

性能拆分只能改变编译形态，不能把相邻规则按输出值合并或改变顺序。

### 2. 五组连续 CASE + 最小规则组

将 175 条分成五个连续组，每组 35 条：1-35、36-70、71-105、106-140、141-175。每组使用独立 CASE：命中返回渠道值，未命中返回 \`cast(null as varchar)\`；五组通过 \`UNION ALL\` 产出 \`(mapping_key, channel, rule_group)\`，再按 \`mapping_key\` 使用 \`min_by(channel, rule_group)\` 选择最早非空规则组。

\`min_by\` 选择最早非空规则组，因此等价于原始 175 条 CASE 的 first-match 语义。0808 版本采用五组×35，既保持完整规则顺序，又把单个编译单元控制在已验证范围内。

### 3. 无碰撞键和回连

在渠道 CASE 依赖的全部字段上生成长度前缀键：NULL 编码为 \`N\`，非 NULL 值编码为 \`V<varchar_length>:<varchar_value>\`，字段之间用 \`|\` 连接。两个模板使用的 28 个映射字段为：

\`period_name\`、\`rule_name\`、\`flow_pool_name\`、\`sku_id_name\`、\`ad_account_name\`、\`source_manager_name\`、\`channel_name_1\`、\`channel_name_2\`、\`channel_name_3\`、\`put_plan_name\`、\`flow_original_order_activity_price\`、\`flow_orders_income_amount\`、\`flow_order_price\`、\`channel_provider_name\`、\`channel_second_provider_name\`、\`page_id_name\`、\`source_put_plan_name\`、\`get_customer_way_name\`、\`first_department_name\`、\`second_department_name\`、\`third_department_name\`、\`virtual_second_department_name\`、\`virtual_fourth_department_name\`、\`virtual_fifth_department_name\`、\`trace_type_name\`、\`lead_purchase_intention_level1_category_name\`、\`lead_purchase_intention_level2_category_name\`、\`lead_create_time\`。

先对源 CTE 计算 \`mapping_key\`，对五组结果按键取最早渠道，再左连接回源行，并使用 \`coalesce(channel, '其他未知流量')\`。键不包含线索量、金额、用户或订单统计字段，所以相同映射条件的重复源行会共享归因结果但不会被去重；\`N\` 标记和长度前缀避免 NULL/空串以及拼接边界碰撞。回连后再进入原有聚合，保留模板原始粒度、金额、计数和 NULL/fallback 行为。

### 4. 期次范围下推

对有模板参数的查询保留同名字段参数的左闭右开形式：\`where period_name >= \${qici:1} and period_name < \${qici:2}\`。参数不要包裹 \`cast\`、\`date\`、\`substr\`，也不要改名为 \`begin_period\`/\`end_period\`。生成实际探针时才替换为具体期次；沉淀到模板 raw SQL 时保留参数形态。

## 验证门禁

每次维护两个模板或其他共享 CASE 模板时，必须留下以下证据：

1. 从线上 published 版本读取 baseline，确认唯一模板 id、owner、实例、参数和输出字段；
2. 对候选 SQL 做 canonical 175 分支逐序比对，检查 fallback、关键字段覆盖和参数计数；
3. 通过 \`text2sql.py validate-sql\` 的 concrete SQL 检查；\`validate_sql_rules.py\` 若命中旧模板 \`src\` 投影的已知解析器误报，必须同时保存未修改 baseline 对照，不能把误报写成 Presto 失败；
4. 使用 Presto 实际运行候选 SQL，执行时间必须小于 300 秒且 Result API 为 \`success_with_rows\`；
5. 按精确计划 hash 原位 Apply，回读未发布版本 SQL/metadata hash；
6. 单独 Publish，回读 \`status=2\` 和线上 SQL hash；
7. 必须用发布后回读 SQL 生成具体参数探针并再次实际查询；UI 结果面板缺失时以同一 query id 的 Result API、HTTP 200、error code 0 和字段元数据为准；
8. 对有效模板不创建新模板、不重置权限；远端已经删除的模板不恢复、不同步，并从当前 canonical 路由移除。

后续如规则源发生变化，先按 [\`channel_mapping_case_when.md\`](channel_mapping_case_when.md) 完成当前版本之后的逐分支新增/删除/顺序审计，再分别从两个模板的线上 SQL 生成候选；不得把本文件中的五组切分当作可独立维护的渠道规则副本。
