# 范围限定规则

## 必读核心规则

- 字段名包含 `department_name`，或业务语义为部门、业务线、学部、小组、架构、虚拟架构、期次归属时，必须加过滤条件。
- 选表和选字段阶段就要检查范围限定，不能等 SQL 写完后再补。
- 用户未提供部门或架构取值时，SQL 中使用占位符，例如 `'<一级部门名称>'`、`'<二级部门名称>'`、`'<三级部门名称>'`，不得编造业务范围。
- 必须重点检查下方“必须重点检查的字段”表；表级历史取值和看板范围补充只作为按需参考，不代表可以省略用户确认。
- 临时架构表即使不含 `department_name`，只要字段表达部门、架构、小组或经理范围，也必须控制范围。
- 平台模板取数的日期/时间区间参数必须写成 `字段名 >= ${字段名:1} and 字段名 < ${字段名:2}`。参数名必须和过滤列名一致，不得用 `begin_xxx` / `end_xxx`，也不得对模板参数或过滤列添加 `cast()`、`date()`、`substr()` 等函数。

## department_name 字段

字段名包含 `department_name`，或业务语义为部门、业务线、学部、小组、架构时，必须加过滤条件。

## 历史真实取值

> 来源：`baijia-data-map/row_permissions.json`，由百家平台历史 SQL 提取。取值是生成 SQL 的默认参考，不代表所有场景都可省略用户确认。

| 字段名 | 历史取值 | 使用建议 |
|---|---|---|
| course_first_level_department_name | `'H业务线'` (8次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| course_second_level_department_name | `'精品班学部'` (1次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| employee_first_level_department_name | `'H业务线'` (4次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| employee_second_level_department_name | `'精品班学部'` (2次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| first_level_department_name | `'H业务线'` (29次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| goods_first_level_department_name | `'H业务线'` (2次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| mapping_first_level_department_name | `'H业务线'` (1次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| mapping_second_level_department_name | `'精品班学部'` (1次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| performance_second_level_department_name | `'精品班学部'` (1次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| performance_third_level_department_name | `'学习顾问部'` (5次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| pre_employee_path_department2 | `'市场二部'` (1次), `'青橙项目部'` (1次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| second_level_department_name | `'精品班学部'` (9次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |
| third_level_department_name | `'学习顾问部'` (5次) | 用户未明确时优先用占位符；探索验证可参考最高频取值 |

## 表级权限切分

| 表名 | 字段 | 历史取值 | 出现次数 |
|---|---|---|---|
| bdg_ba.dwd_finance_acc_control_mbr_cashflow_df | course_first_level_department_name | `'H业务线'` | 8 |
| bdg_ba.dwd_finance_acc_control_mbr_cashflow_df | first_level_department_name | `'H业务线'` | 8 |
| bdg_ba.dwd_finance_acc_control_mbr_cashflow_df | course_second_level_department_name | `'精品班学部'` | 1 |
| bdg_ba.dwd_finance_acc_control_mbr_cashflow_df | second_level_department_name | `'精品班学部'` | 1 |
| finance_dw.dim_finance_employee_df | first_level_department_name | `'H业务线'` | 14 |
| finance_dw.dim_finance_employee_df | second_level_department_name | `'精品班学部'` | 4 |
| finance_dw.app_finance_performance_extend_details_hf | employee_first_level_department_name | `'H业务线'` | 1 |
| finance_dw.app_finance_performance_extend_details_hf | employee_second_level_department_name | `'市场部'` | 1 |
| finance_dw.app_finance_performance_extend_details_hf | employee_third_level_department_name | `'市场顾问部'` | 1 |
| service_dw.dim_crm_assign_rule_lead_detail_hf | first_level_department_name | `'H业务线'` | 1 |
| service_dw.dim_crm_assign_rule_lead_detail_hf | second_level_department_name | `'精品班学部'` | 1 |
| service_dw.dm_crm_trace_lead_full_link_data_hf | first_level_department_name | `'H业务线'` | 1 |
| service_dw.dm_crm_trace_lead_full_link_data_hf | second_level_department_name | `'精品班学部'` | 1 |
| service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf | performance_third_level_department_name | `'学习顾问部'` | 5 |
| service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf | third_level_department_name | `'学习顾问部'` | 5 |
| service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf | second_level_department_name | `'精品班学部'` | 2 |
| service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf | first_level_department_name | `'H业务线'` | 1 |
| service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf | performance_second_level_department_name | `'精品班学部'` | 1 |
| service_dw.dws_service_wechat_call_detail_df | employee_first_level_department_name | `'H业务线'` | 4 |
| service_dw.dws_service_wechat_call_detail_df | first_level_department_name | `'H业务线'` | 4 |
| service_dw.dws_service_wechat_call_detail_df | employee_second_level_department_name | `'精品班学部'` | 2 |
| service_dw.dws_service_wechat_call_detail_df | second_level_department_name | `'精品班学部'` | 2 |

## 必须重点检查的字段

| 字段名 | 默认占位符 | 说明 |
|---|---|---|
| assign_employee_first_level_department_name | '<一级部门名称>' | 分配顾问一级部门 |
| assign_employee_second_level_department_name | '<二级部门名称>' | 分配顾问二级部门 |
| assign_employee_third_level_department_name | '<三级部门名称>' | 分配顾问三级部门 |
| section_assign_employee_first_level_department_name | '<一级部门名称>' | 截面分配顾问一级部门 |
| section_assign_employee_second_level_department_name | '<二级部门名称>' | 截面分配顾问二级部门 |
| section_assign_employee_third_level_department_name | '<三级部门名称>' | 截面分配顾问三级部门 |
| performance_first_level_department_name | '<一级部门名称>' | 业绩归属一级部门 |
| performance_second_level_department_name | '<二级部门名称>' | 业绩归属二级部门 |
| performance_third_level_department_name | '<三级部门名称>' | 业绩归属三级部门 |
| employee_first_level_department_name | '<一级部门名称>' | 员工一级部门 |
| employee_second_level_department_name | '<二级部门名称>' | 员工二级部门 |
| course_first_level_department_name | '<一级部门名称>' | 课程一级部门 |
| course_second_level_department_name | '<二级部门名称>' | 课程二级部门 |
| goods_first_level_department_name | '<一级部门名称>' | 商品一级部门 |
| mapping_first_level_department_name | '<一级部门名称>' | 映射一级部门 |
| mapping_second_level_department_name | '<二级部门名称>' | 映射二级部门 |
| period_mapping_first_level_department_name | '<一级部门名称>' | 期次映射一级部门 |
| period_mapping_second_level_department_name | '<二级部门名称>' | 期次映射二级部门 |
| virtual_first_department_name | '<一级部门名称>' | 虚拟一级部门 |
| virtual_second_department_name | '<二级部门名称>' | 虚拟二级部门 |
| virtual_third_department_name | '<三级部门名称>' | 虚拟三级部门 |
| virtual_fourth_department_name | '<四级部门名称>' | 虚拟四级部门 |
| virtual_fifth_department_name | '<五级部门名称>' | 虚拟五级部门/团队 |
| first_department_name | '<一级部门名称>' | 一级部门 |
| second_department_name | '<二级部门名称>' | 二级部门 |
| third_department_name | '<三级部门名称>' | 三级部门 |
| first_level_department_name | '<一级部门名称>' | 一级部门 |
| second_level_department_name | '<二级部门名称>' | 二级部门 |
| third_level_department_name | '<三级部门名称>' | 三级部门 |

## 输出要求

如果用户没有提供部门取值，SQL 中使用占位符，并在解释里明确“需要替换后执行”。

## 历史看板范围补充：流量画像

来源：`resources/raw_sql/data_center_market_2683_20260705.sql`。2026-05-15 已按 `D:\Feishu\city_channel.txt` 更新为省份/城市维度版本。

该 SQL 涉及市场顾问流量画像，复用时应优先保持以下范围限制，除非用户明确要求改业务范围：

| 表/CTE | 范围字段 | 历史取值 |
|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `section_assign_employee_first_level_department_name` | `'H业务线'` |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `section_assign_employee_second_level_department_name` | `'市场部'` |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `section_assign_employee_third_level_department_name` | `'市场顾问部'` |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `period_mapping_first_level_department_name` | `'H业务线'` |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `period_mapping_second_level_department_name` | `'精品班学部','青橙项目部','一对一学部','本地化大班学部','市场部','菁英班学部'` |
| `service_dw.dwd_crm_assign_private_detail_hf` | `assign_employee_first_level_department_name` | `'H业务线'` |
| `service_dw.dwd_crm_assign_private_detail_hf` | `assign_employee_second_level_department_name` | `'市场部'` |
| `service_dw.dwd_crm_assign_private_detail_hf` | `assign_employee_third_level_department_name` | `'市场顾问部'` |
| `service_dw.dws_service_user_learn_detail_hf` | `course_first_level_department_name` | `'H业务线'` |
| `service_dw.dws_service_user_learn_detail_hf` | `course_second_level_department_name` | `'精品班学部','市场部','青橙项目部'` |
| `finance_dw.app_finance_performance_extend_details_hf` | `employee_first_level_department_name` | `'H业务线'` |
| `finance_dw.app_finance_performance_extend_details_hf` | `employee_second_level_department_name` | `'市场部'` |
| `finance_dw.app_finance_performance_extend_details_hf` | `employee_third_level_department_name` | `'市场顾问部'` |

注意：

- `data_center_market_2683_20260705.sql` 中外呼工作量表 `service_dw.app_h_crm_lead_employee_workload_detail_hf` 只限定 `dt/hour`，未单独限定部门。若后续脱离主表生成外呼明细或外呼聚合 SQL，应补充可用的员工/虚拟部门范围字段或通过主表范围内 join 限定。
- 当前 `city_channel.txt` 版本在 `base` CTE 使用 `period_name >= ${period_name1}` 且 `period_name < ${period_name2}` 的半开区间过滤；生成可执行 SQL 前必须替换期次参数，不能保留占位符直接提交。

## 历史看板范围补充：退费分析

来源：`resources/raw_sql/data_center_market_2350_20260705.sql`、`resources/raw_sql/data_center_market_2349_20260705.sql`、`resources/raw_sql/data_center_market_2353_20260705.sql`。

| 表/CTE | 范围字段 | 历史取值 |
|---|---|---|
| `finance_dw.app_finance_performance_extend_details_hf` | `employee_first_level_department_name` | `'H业务线'` |
| `finance_dw.app_finance_performance_extend_details_hf` | `employee_second_level_department_name` | `'市场部'` |
| `finance_dw.app_finance_performance_extend_details_hf` | `employee_third_level_department_name` | `'市场顾问部'` |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | `course_first_level_department_name` | 多科用户退费占比/退费原因分析使用 `'H业务线'`；退费科目产品使用多业务线白名单 |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | `course_second_level_department_name` | 多科用户退费占比/退费原因分析使用 `'精品班学部','菁英班学部','市场部','本地化大班学部','一对一学部','青橙项目部'`；退费科目产品使用长白名单 |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | `performance_third_level_department_name` | `'市场顾问部'` |

注意：当前 2349 科目/产品/年级退款金额占比 SQL 已作为最新入口，仍沿用财务主表员工部门范围和归因流水课程部门长白名单。历史三份退费分析 SQL 的财务主表选出了课程部门字段，但主表层只过滤员工部门；生成新 SQL 时如果以课程维度分析，需要确认是否补充 `course_*_department_name` 范围。

## 历史看板范围补充：H业务线二级部门转化看板

来源：`resources/raw_sql/h_biz_line_department_conversion.sql`。

该 SQL 覆盖 H业务线下四个二级部门的全量转化数据，部门范围比市场顾问转化看板更宽：

| 表/CTE | 范围字段 | 历史取值 |
|---|---|---|
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `section_assign_employee_first_level_department_name` | `'H业务线'` |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `section_assign_employee_second_level_department_name` | `'市场部','精品班学部','青橙项目部','菁英班学部'` |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `virtual_third_department_name` | `'学习顾问部','市场顾问部','中价产品项目部'` |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | `period_mapping_first_level_department_name` | `'H业务线'` 或 `null`（放宽条件） |
| `finance_dw.dim_finance_employee_df` | `first_level_department_name` | `'H业务线'` |
| `finance_dw.dim_finance_employee_df` | `second_level_department_name` | `'市场部','精品班学部','青橙项目部','菁英班学部'` |

注意：
- `period_mapping_first_level_department_name is null` 的放宽条件可能导致期次映射缺失的线索也被纳入；生成类似跨部门 SQL 时需确认是否同样放宽或还原为严格匹配。
- 首 call 任务表 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` 只通过 `account_id` 桥接到员工维表间接获取部门范围，未直接在首 call 表上限定部门字段。
