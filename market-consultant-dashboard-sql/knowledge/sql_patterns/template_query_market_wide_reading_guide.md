# AI分析市场顾问部_宽表：SQL 阅读指南

## 权威入口与版本

- 领域：`market_consultant`，使用口径为模板取数。
- 线上模板：`AI分析市场顾问部_宽表`，template id `9002`。
- 当前状态：`published`；线上发布时间与更新时间为 `2026-10-29 17:49:57`。
- 完整 SQL 唯一入口：[template_query_market_wide.sql](../../resources/raw_sql/template_query_market_wide.sql)。
- 当前 SQL SHA-256：`d255963cf8baf4ac9f704b9a10256709dbd61ef14dd09962c2d1e1c4581bce04`；canonical UTF-8 文件为 13 行、49,917 字节。
- 模板参数：`${qici:1}` 为包含的起始期次，`${qici:2}` 为不包含的结束期次；主链使用半开区间 `qici >= ${qici:1} AND qici < ${qici:2}`。

canonical 文件逐字保存平台当前已发布 SQL，以便后续按模板身份和文本哈希审计。线上原文存在较长的单行 CTE；本指南通过分层导航提高可读性，不生成第二份可能与线上漂移的“格式化 SQL”，也不改变参数、字段、过滤、关联、聚合或输出。后续修改前仍须重新读取线上模板，不能把本指南或历史版本当作编辑基线。

## 查询结构总览

SQL 共 42 个 CTE，最终执行 `SELECT * FROM joined`。建议按以下八段阅读：

| 阶段 | CTE | 主要职责 |
|---|---|---|
| 1. 时间与公共维表 | `runtime_clock`, `biz_qici_calendar`, `market_employee_dim` | 定义运行时分区参考、暑期特殊期次日历和市场顾问员工维度。`runtime_clock` 当前未被后续 CTE 引用，不应仅凭此事实删除。 |
| 2. 过程辅助事实 | `private_stage_latest`, `lead_stats`, `abnormal_label`, `double_table`, `call_c`, `f_call0`, `d_ap`, `h_ap`, `denglu_app` | 分别准备私海阶段、首通时差、异常流量标签、双表、通话、首呼、日/小时 APP 登录信息；在 `lead_enriched` 汇合。 |
| 3. 线索主链与渠道 | `lead_raw0`, `lead_raw`, `lead_channel_dim`, `lead_raw_mapped`, `lead_base_all`, `lead_base` | 从全链路宽表抽取市场顾问线索并限制期次；`lead_raw_mapped` 按 `lead_id` 左连接市销渠道日快照，整理年级/人员/金额字段，再在 `qici + lead_id + employee` 粒度稳定组织维度。 |
| 4. 到课链路 | `learn_date_map`, `learn_selected_bounds`, `learn_raw_all`, `learn_raw`, `learn_rank_base`, `learn_ranked`, `attendance_by_lead` | 将课程日期映射到运营期次，按参数反推有界学习日期，识别第 1～6 讲到课及有效到课，再按 `qici + user_id` 聚合。 |
| 5. 顾问过程与转化 | `lead_enriched`, `consultant_metric` | 把线索主链与辅助事实合并，派生首呼、长通、通话时长、深沟/双沟、APP 登录、异常和到课指标；再按期次、渠道、年级及顾问组织维度聚合。 |
| 6. 多科用户 | `multi_user_consultant_raw`, `multi_user_base`, `multi` | 先聚合到用户与顾问，再为同一业务键选择一条稳定顾问记录，最终计算多科人数、科次、收入和净收入。 |
| 7. 财务分周期 | `period_trade_dd_raw`, `period_trade_dd`, `period_trade_keys`, `period_trade_prepared`, `period_trade_union`, `period_n_uid`, `lead_dim_period`, `period_trade`, `period_conv`, `period_consultant` | 读取市场顾问财务业绩流水，处理正常订单/调课调班，关联线索维度，计算线索期与交易期的相对桶并聚合 GMV、退款。 |
| 8. 组织拼接与输出 | `org_raw`, `joined` | 补员工姓名、在职状态，将顾问过程/转化、财务分周期和多科指标按共同维度左连接，形成最终宽表。 |

## CTE 依赖顺序

以下顺序与当前 SQL 一致，排查时从同组上游向下追踪：

1. 公共基础：`runtime_clock` → `biz_qici_calendar` → `market_employee_dim`。
2. 辅助事实：`private_stage_latest`、`lead_stats`、`abnormal_label`、`double_table`、`call_c`、`f_call0`、`d_ap`、`h_ap` → `denglu_app`。
3. 线索与渠道：`lead_raw0` → `lead_raw`；`lead_channel_dim` 与 `lead_raw` 一同进入 `lead_raw_mapped` → `lead_base_all` → `lead_base`。
4. 到课：`learn_date_map` → `learn_selected_bounds` → `learn_raw_all` → `learn_raw` → `learn_rank_base` → `learn_ranked` → `attendance_by_lead`。
5. 顾问指标：`lead_base` + 全部辅助事实 + `attendance_by_lead` → `lead_enriched` → `consultant_metric`。
6. 多科：`lead_base` → `multi_user_consultant_raw` → `multi_user_base` → `multi`。
7. 财务：`period_trade_dd_raw` → `period_trade_dd` → `period_trade_keys` → `period_trade_prepared` → `period_trade_union`；同时由 `period_trade_keys` 生成 `period_n_uid`，由 `lead_base` 生成 `lead_dim_period`；三者汇入 `period_trade` → `period_conv` → `period_consultant`。
8. 输出：`market_employee_dim` → `org_raw`；`consultant_metric` + `period_consultant` + `multi` + `org_raw` → `joined`。

## 物理来源表

当前 SQL 直接扫描 14 张物理表：

| 业务用途 | 物理表 |
|---|---|
| 线索、成本、转化和沟通学习宽表 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` |
| 员工维度 | `finance_dw.dim_finance_employee_df` |
| 私海阶段 | `service_dw.dwd_crm_assign_private_detail_hf` |
| 线索首通统计 | `service_dw.dm_crm_lead_stats_detail_hf` |
| 异常流量标签 | `service_dw.app_user_attribute_label_gaia_wide_df` |
| 线索任务过程 | `service_dw.app_h_crm_lead_task_process_info_detail_hf` |
| 顾问工作量/通话 | `service_dw.app_h_crm_lead_employee_workload_detail_hf` |
| 首呼任务 | `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` |
| 市销线索渠道日快照 | `gaotu_hl.dim_mkt_h_lead_channel_df` |
| APP 最近活跃（日） | `dw.dim_cstm_active_user_c_appliction_mb_df` |
| APP 活跃（小时） | `dw.dws_user_active_user_c_appliction_hf` |
| 学习明细 | `service_dw.dws_service_user_learn_detail_hf` |
| 财务业绩流水 | `finance_dw.app_finance_performance_extend_details_hf` |
| 订单线索归因 | `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` |

## 关键范围与粒度

- 线索主体固定为截面分配员工 `H业务线 / 市场部 / 市场顾问部`，期次映射学部保留线上当前名单；不能用课程学部或虚拟组织字段替代这一员工范围。
- 多处小时表使用 `CURRENT_TIMESTAMP - INTERVAL '2' HOUR` 的日期分区和 `-3 HOUR` 或 `-2 HOUR` 的小时分区。各 CTE 的偏移并不完全相同，排查快照差异时必须逐表核对。
- 当前 `lead_raw_mapped` 从 `gaotu_hl.dim_mkt_h_lead_channel_df` 读取 `dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '24' HOUR, 'YYYYMMdd')` 的 `lead_id/channel_map`，以 `CAST(r.lid AS VARCHAR) = d.lead_id` 左连接，空映射回填为 `未知`。这与本 Skill 的历史证据存在未解决差异：2026-08-13 对 `20260813/hour=13` 市场顾问宽表的覆盖率为 24.3341%，且 `20260815期` 有未命中有效线索。模板于 2026-10-29 发布的版本已使用该维表，但本次仅回读并同步 SQL，未重新执行覆盖探针或模板查询；不能把“已发布”解释为新旧渠道口径准确性已验证。详见 [维表历史 Join 证据](../joins/table_relationships.md#市销线索渠道维表与市场顾问全链路宽表2026-08-13) 与 [维表字段和范围](../tables/gaotu_hl.dim_mkt_h_lead_channel_df.md)。
- 历史唯一性检查只证明 `dt='20260812'` 快照内 `lead_id` 唯一；该表跨 `dt` 重复，未来改动须限定单个已完成分区并重验当前分区唯一性、覆盖、未命中线索和指标守恒。不得沿用 2026-08 的探针结果声称当前覆盖充分。
- `lead_base` 使用窗口排序为同一 `qici + lead_id + employee_email_name + employee_email_prefix` 选取稳定组织、渠道和年级；修改投影或排序会影响后续过程、财务和多科三条链。
- 到课先按课程日期映射期次，再按用户、班级和讲次排序，最终聚合到 `qici + user_id`。不要把课程行粒度直接连接到线索行，否则会放大顾问指标。
- 财务链先在流水层处理正常订单与调课调班，再用用户与顾问寻找线索维度。相对期次桶包含暑期特殊邻接规则，不能只用自然日差替换。
- `joined` 以 `consultant_metric` 为主表，财务、多科和员工组织均为左连接；改为内连接会丢失主链记录。连接键中的 `xiaozu`、员工名/前缀使用 `COALESCE(..., '')` 处理空值，不能静默改成普通等值。
- 最终 `SELECT * FROM joined` 使输出契约依赖 `joined` 的列顺序。新增、删除或重排任何上游列都可能改变模板字段身份，必须结合线上 parser 元数据和发布回读审查。

## 阅读与维护规则

1. 只需理解某一指标时，先在本指南定位阶段，再打开 canonical SQL 搜索对应 CTE；不要从 42 个 CTE 全量反推。
2. 需要修改模板时，先用 operator 重新抓取 template id `9002` 的完整线上 SQL，保存到 runtime，并校验名称、状态、更新时间和 SQL SHA-256。
3. 排版、注释或格式变化也属于文本变化；若不能用同方言解析结果证明等价，按逻辑变化执行准确性、性能和参数/输出回归。
4. 本次维护仅同步已发布 SQL 与知识导航，没有执行模板查询，也没有修改、下线或重新发布线上模板。
