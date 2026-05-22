# 更新日志

## 2026-05-22

- 初始化 `qingcheng-dashboard-sql` Skill，用于隔离维护青橙项目部看板 SQL、指标、临时表和字段匹配规则。
- 创建空知识库目录和模板文件，等待后续青橙看板 SQL 入库。

## 2026-05-22 16:53:55

- 入库青橙看板 SQL `qingcheng_process_data_raw_20260522.sql`，生成 `qingcheng_process_data_raw_20260522` 初始看板知识文档和指标/临时表待确认项。

## 2026-05-22 16:54:58

- 人工整理青橙过程数据 raw SQL：补充看板结构、指标集合、渠道/年级映射、物理表文档、临时表文档、join 关系和表索引。
- 将自动生成的 `metric_1` 至 `metric_22` 占位文档合并为 `knowledge/metrics/qingcheng_process_data_metrics.md`。

## 2026-05-22 18:19:42

- 入库青橙到课 SQL `qingcheng_daoke_raw_20260522.sql`，新增到课看板文档和第 1 至第 6 讲到课/有效到课指标文档。
- 更新 `temp_table.dingxi01_qing_daoke` 语义：`ke_1` 字段在到课 SQL 中承载课次编号 `'1'` 至 `'6'`，不再只按首节课理解。
- 更新 `temp_table.dingxi01_jiagou_db` 语义：到课 SQL 使用 `employee_email_prefix + qici` join 架构，和过程数据 raw 的 `employee_email_name + qici` join key 差异需确认。

## 2026-05-22 18:20:57

- 修正 `scripts/validate_sql_rules.py` 读取 Markdown 字段清单时未剥离反引号导致的字段误报问题。

## 2026-05-22 18:28:41

- 入库青橙转化 SQL `qingcheng_conversion_raw_20260522.sql`，新增转化看板文档和转化指标文档。
- 新增订单业绩表文档 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.md`，记录青橙转化的收入、退款、净营收和业绩归属范围。
- 新增临时表文档 `temp_table.dingxi01_qing_team_jg.md`，记录青橙最新团队架构 join 逻辑。
- 更新青橙渠道/年级映射、成本硬编码、转化 join 关系、范围限定规则、表索引和业务域档案。

## 2026-05-22 20:50:31

- 入库青橙年季月营收 SQL `qingcheng_revenue_year_quarter_month_raw_20260522.sql`，新增营收看板文档和年/季/月营收指标文档。
- 新增财务业绩表 `finance_dw.app_finance_performance_extend_details_hf.md`、员工组织链表 `dw.dim_employee_chain.md` 和青橙组织临时表 `temp_table.dingxi01_qing_zz.md`。
- 更新营收范围口径、join 关系、表索引和业务域档案，明确该 SQL 使用交易发生时员工属于青橙的组织时间窗口过滤。

## 2026-05-22 22:26:16

- 入库青橙团队完成度【月】SQL `qingcheng_team_completion_month_raw_20260522.sql`，新增月度完成度看板文档和指标文档。
- 新增退款明细表 `finance_dw.dm_finance_order_refund_detail_df.md`、订单调课调班维表 `finance_dw.dim_finance_order_change_df.md`、期次月份映射表 `temp_table.dingxi01_qing_qi_moth.md` 和团队月目标表 `temp_table.dingxi01_qing_team_goal.md`。
- 更新团队架构表 `temp_table.dingxi01_qing_team_jg.md` 的适用场景，并补充团队完成度【月】的 join、范围、索引和业务域档案。

## 2026-05-22 22:31:54

- 入库青橙团队完成度【期】SQL `qingcheng_team_completion_period_raw_20260522.sql`，新增期次完成度看板文档和指标文档。
- 新增期次团队目标表 `temp_table.dingxi01_qing_team_g_qi.md`，并更新 `temp_table.dingxi01_qing_qi_moth.md`、`temp_table.dingxi01_qing_team_jg.md`、`temp_table.dingxi01_qing_team_goal.md` 的适用边界。
- 更新团队完成度【期】的 join、范围、索引和业务域档案。

## 2026-05-22 22:39:00

- 入库青橙个人转化 SQL `qingcheng_personal_conversion_raw_20260522.sql`，新增个人转化看板文档和指标文档。
- 更新 `temp_table.dingxi01_qing_team_jg.md` 和 `temp_table.dingxi01_qing_qi_moth.md`，记录个人转化以团队架构表为人员期次骨架并按期次补充月份。
- 更新个人转化的 join、范围、索引和业务域档案，明确该 SQL 不接团队目标表。
