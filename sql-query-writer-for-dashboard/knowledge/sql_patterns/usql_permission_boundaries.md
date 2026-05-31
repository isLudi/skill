# USQL RestAPI 权限边界探查记录

本文记录通过 USQL RestAPI 对知识库高频表的最小安全探查结果，用于判断当前账号能否通过 API 查询相关表，以及哪些部门、期次或字段范围需要额外申请权限。

安全约束：
- 不记录 `USQL_TOKEN`、`USQL_APP_ID`、env 原文、cookie、账号凭据或完整 DAS 申请 URL。
- 只测试知识库和历史 SQL 已出现的表、字段、部门和期次范围。
- 大表只执行带 `dt/hour`、部门或期次限定的 `limit 1` / 小范围聚合查询，不做无范围扫表。
- 表可读不等于业务范围完整可见；后续生成 SQL 时仍需保留部门、期次、分区和 `limit` 规则。

## 2026-05-31 首轮探查

- API 环境：online
- 连通性：`select 1 as smoke_test` 成功，返回 `code=0`
- 候选表来源：`knowledge/**/*.md` 与 `resources/raw_sql/*.sql` 中出现的完整表名
- 分层规则：高频为出现次数 `>= 10`，中频为 `4-8`，低频为 `<= 3`
- 探查范围：27 张表
- 汇总结果：13 张最小读成功，13 张明确提示当前账号无表权限，1 张触发权限校验器 SQL 解析错误

### 高频表

| 表 | 调用次数 | 探查条件 | 结果 | 权限边界和建议 |
| --- | ---: | --- | --- | --- |
| `finance_dw.app_finance_performance_extend_details_hf` | 19 | `dt/hour` 最近 2 小时 + `employee_first_level_department_name='H业务线'` + `employee_second_level_department_name='市场部'` + `employee_third_level_department_name='市场顾问部'` | 无表权限 | 当前账号无法通过 USQL RestAPI 查询该财务业绩明细表；错误提示为账号无表权限并包含 DAS 申请入口。若继续维护 GMV、退费、财务业绩类看板，应优先申请该表权限。 |
| `temp_table.dingxi01_jiagou_zx` | 16 | `cast(zaizhi as varchar)='1'` + `department in ('郑州顾问部','西安一部','西安二部')` | 可读 | 当前在职架构口径可用。已验证可见部门为 `郑州顾问部`、`西安二部`、`西安一部`，分别约 139、75、47 行。后续作为在职顾问名单时必须保留 `zaizhi` 和部门限定，并按 `employee_email_name` 去重。 |
| `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` | 13 | 最近 `dt/hour`、字面量 `dt/hour`、仅 `dt`、部门字段拆分测试、`where 1=0`、`desc/show columns`、alias/双引号标识符 | 权限校验器解析错误 | 所有真实引用该表的写法均返回“权限校验时遇到错误 SQL”。对照无权限财务表会返回标准“账号没权限/申请权限”错误，因此该表当前更像 USQL 权限校验器或 DAS 资源映射异常，而不是普通 SQL 语法错误或已确认的标准无表权限。该表是全链路主表且高频使用，建议作为最高优先级向平台确认权限校验器/资源配置；平台确认资源正常后再按需申请表权限。 |
| `temp_table.dingxi01_jiagou_db` | 10 | `qici='20260522期'` | 可读 | 期次架构表可用。可见期次包含 `20260605期`、`20260529期`、`20260522期`、`20260515期`、`20260508期` 等；可见部门包含郑州市场顾问、西安学习顾问、青橙项目等。市场顾问场景必须同时限定 `qici` 和目标部门，避免混入青橙或其他架构。 |
| `temp_table.dingxi01_pingyou_jg` | 10 | `qici >= '20260320期'` | 可读 | 评优名单表可用。可见最新期次到 `20260522期`，历史期次约 10 个。仅在评优/参评名单口径中使用，不应默认作为最新在职顾问名单。 |

### 中频表

| 表 | 调用次数 | 探查条件 | 结果 | 权限边界和建议 |
| --- | ---: | --- | --- | --- |
| `temp_table.dingxi01_cost` | 8 | `qici > '20260424期'` | 可读 | 成本维护表可用。可见期次为 `20260529期`、`20260522期`、`20260508期`。后续必须按期次限定，避免误取缺失期次。 |
| `dw.dim_employee_chain` | 8 | `dt` 最近 24 小时 + `path_name like '%市场顾问部%'` | 无表权限 | 当前账号无法查询员工链路维表。涉及员工架构、员工 ID 或部门路径补充时，需要申请该表权限，或改用已可读的临时架构表。 |
| `temp_table.dingxi01_daoke_1_6_t` | 7 | `qici='20260403期'` | 可读 | 到课维护表可用。可见期次包含 `20260529期`、`20260522期`、`20260515期`、`20260508期`、`20260501期` 等。后续按期次使用。 |
| `service_dw.dim_crm_assign_rule_lead_detail_hf` | 7 | 最近 `dt/hour` | 可读 | 规则明细表可读，但测试 `first_level_department_name/second_level_department_name` 字段失败，字段不存在。该表不宜按部门字段直接限权，应通过 `dt/hour`、`rule_id + plan_id`、`group_id`、`rule_name` 以及 `temp_table.dingxi01_plan_id` 收窄。 |
| `temp_table.dingxi01_plan_id` | 7 | `qici is not null` | 可读 | 计划组维护表可用。`qici` 格式为 `MMDD期`，可见 `0605期`、`0529期`、`0522期`、`0515期`、`0508期` 等。与规则表 join 时不能只用 `group_id`，需要保留期次或规则名前缀约束。 |
| `temp_table.shenbaoxin_channel_group` | 6 | 先测 `qici is not null`，再回退 `limit 1` | 可读，但无 `qici` 字段 | 表可读；`qici` 字段不存在。后续不能按期次过滤该表，应先确认其维护粒度和更新时间。 |
| `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf` | 5 | 最近 `dt/hour` + H 业务线相关二级部门 | 无表权限 | 当前账号无法查询首呼任务表。涉及首呼任务链路时需申请该表权限。 |
| `finance_dw.dim_finance_employee_df` | 5 | 最近 24 小时 `dt` + H 业务线相关二级部门 | 无表权限 | 当前账号无法查询财务员工维表。财务员工架构补充需申请权限或改用可读临时架构表。 |
| `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` | 5 | 最近 `dt/hour` + `performance_first_level_department_name='H业务线'` | 无表权限 | 当前账号无法查询订单线索收入退费明细表。涉及收入/退费闭环时需申请权限。 |
| `dw.dim_cstm_active_user_c_appliction_mb_df` | 4 | 最近 24 小时 `dt` | 无表权限 | 当前账号无法查询 APP 日级活跃表。APP 登录日级补充需申请权限或改用小时级可读表。 |
| `service_dw.dwd_crm_assign_private_detail_hf` | 4 | 最近 `dt/hour` + `assign_employee_first_level_department_name='H业务线'` + 二级部门 `市场部/精品班学部` | 可读 | 私海阶段表可读。按 `assign_employee_first_level_department_name='H业务线'` 聚合可见范围较宽，包含一对一学部、精品班学部、菁英班学部、市场部等；市场顾问场景必须继续限定 `assign_employee_second_level_department_name='市场部'` 和 `assign_employee_third_level_department_name='市场顾问部'`。 |
| `service_dw.dws_service_user_learn_detail_hf` | 4 | 最近 `dt/hour` + H 业务线课程二级部门 | 无表权限 | 当前账号无法查询用户学习明细表。涉及学习过程或到课事实表时需申请权限，或先使用已可读的临时到课表。 |
| `temp_table.dingxi01_channel_group` | 4 | 先测 `qici is not null`，再回退 `limit 1` | 可读，但无 `qici` 字段 | 表可读；`qici` 字段不存在。后续不能按期次过滤该表，应先确认渠道维护粒度。 |

### 低频表

| 表 | 调用次数 | 探查条件 | 结果 | 权限边界和建议 |
| --- | ---: | --- | --- | --- |
| `finance_dw.dwd_finance_order_refund_df` | 3 | 最近 24 小时 `dt` | 无表权限 | 当前账号无法查询订单退费明细表。退费分析需申请财务退费表权限。 |
| `service_dw.app_h_crm_lead_employee_workload_detail_hf` | 3 | 最近 `dt/hour` + `virtual_department_name_2='H业务线'` | 无表权限 | 当前账号无法查询顾问工作量明细表。 |
| `service_dw.app_h_crm_lead_task_process_info_detail_hf` | 3 | 最近 `dt/hour` + `virtual_department_name_2='H业务线'` + `virtual_department_name_3='市场部'` | 无表权限 | 当前账号无法查询线索任务过程明细表。 |
| `service_dw.dim_crm_assign_rule_plan_item_info_hf` | 3 | 最近 `dt/hour` | 可读 | 计划 item 表可读，但无部门字段。可读字段包含顾问配置类字段；知识库不记录员工姓名样例。使用时需通过 `rule_id + plan_id` 关联规则表，并用 `temp_table.dingxi01_plan_id` 或规则名收窄。 |
| `dw.dws_user_active_user_c_appliction_hf` | 2 | 最近 `dt/hour` | 可读 | APP 小时级活跃表可读。该表不承担部门限权，使用时应从主线索/用户集合先限定部门后再 join。 |
| `service_dw.app_user_attribute_label_gaia_wide_df` | 2 | 最近 24 小时 `dt` | 无表权限 | 当前账号无法查询用户标签宽表。 |
| `service_dw.dm_crm_lead_stats_detail_hf` | 2 | 最近 `dt/hour` + `mapping_first_level_department_name='H业务线'` | 可读 | 线索统计公共明细表可读。`mapping_second_level_department_name` 可见范围较宽，包含精品班学部、菁英班学部、一对一学部、青橙项目部、升学规划中心等；市场顾问分析需继续限定到目标二级/三级部门。`section_assign_employee_*` 分组测试触发权限校验器解析错误，优先使用 `mapping_*` 或其他已验证字段。 |
| `service_dw.dm_crm_trace_lead_full_link_data_hf` | 1 | 最近 `dt/hour` + `last_assign_employee_first_level_department_name='H业务线'` | 无表权限 | 当前账号无法查询留痕全链路表。 |
| `service_dw.dws_service_wechat_call_detail_df` | 1 | 最近 24 小时 `dt` + `employee_first_level_department_name='H业务线'` | 无表权限 | 当前账号无法查询微信通话明细表。 |

## 当前可用表清单

优先用于后续 USQL RestAPI 探索和看板 SQL 校验：

- 临时维护/架构表：`temp_table.dingxi01_jiagou_zx`、`temp_table.dingxi01_jiagou_db`、`temp_table.dingxi01_pingyou_jg`、`temp_table.dingxi01_cost`、`temp_table.dingxi01_daoke_1_6_t`、`temp_table.dingxi01_plan_id`、`temp_table.shenbaoxin_channel_group`、`temp_table.dingxi01_channel_group`
- CRM 分配/线索表：`service_dw.dim_crm_assign_rule_lead_detail_hf`、`service_dw.dwd_crm_assign_private_detail_hf`、`service_dw.dim_crm_assign_rule_plan_item_info_hf`、`service_dw.dm_crm_lead_stats_detail_hf`
- APP 小时活跃表：`dw.dws_user_active_user_c_appliction_hf`

## 当前需优先申请或排查的权限

按知识库调用频率和业务依赖优先级排序：

1. `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`：高频全链路主表；当前为权限校验器解析错误，需要平台确认或补齐权限。
2. `finance_dw.app_finance_performance_extend_details_hf`：最高频财务业绩明细表；当前明确无表权限。
3. `dw.dim_employee_chain`：员工组织链路维表；当前明确无表权限，影响员工/部门路径校验。
4. `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`：首呼任务链路；当前明确无表权限。
5. `finance_dw.dim_finance_employee_df`、`finance_dw.dwd_finance_order_refund_df`、`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`：财务员工、退费、收入闭环；当前明确无表权限。
6. `service_dw.dws_service_user_learn_detail_hf`、`service_dw.app_h_crm_lead_employee_workload_detail_hf`、`service_dw.app_h_crm_lead_task_process_info_detail_hf`、`service_dw.dm_crm_trace_lead_full_link_data_hf`、`service_dw.dws_service_wechat_call_detail_df`：过程、学习、留痕、通话链路；按具体看板需求申请。

## 后续使用规则

- 若需要快速验证 SQL，可优先选用“当前可用表清单”中的表。
- 若看板 SQL 依赖无权限表，不要直接把失败归因为 SQL 语法；应先标注“USQL 当前账号无表权限”。
- 对 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`，后续需单独跟进平台权限校验器或 DAS 资源映射问题；当前不建议基于该表做 API 自动验证。该表的失败特征不同于标准“账号无表权限”报错。
- 对可读但范围较宽的表，如 `service_dw.dwd_crm_assign_private_detail_hf`、`service_dw.dm_crm_lead_stats_detail_hf`，生成探索 SQL 时必须继续保留 H 业务线、市场部、市场顾问部等目标范围限定。
- 对临时表，优先使用已验证的 `qici`、`department` 或维护名单字段；不要假设所有临时表都有 `qici` 字段。
