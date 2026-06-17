# service_dw.dwd_crm_assign_private_detail_hf

## 1. 中文名称

crm分配私海记录表

## 2. 表用途

记录 CRM 线索分配到私海后的阶段、顾问、部门和跟进状态。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

## 3. 数据粒度

用户/线索-顾问-小时粒度，待确认

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |
| hour | string | 小时级分区 HH | 是 |
## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 | 来源 |
|---|---|---|---|---|---|
| assign_employee_top_level_department_name | string | '<待填写>' | 是 | 顾问最新部门信息，topname | 待人工确认 |
| assign_employee_first_level_department_name | string | 'H业务线' | 是 | 顾问最新部门信息，1级name | 按 row_permissions 同层级历史取值补充 |
| assign_employee_second_level_department_name | string | '精品班学部' | 是 | 顾问最新部门信息，2级name | 按 row_permissions 同层级历史取值补充 |
| assign_employee_third_level_department_name | string | '学习顾问部' | 是 | 顾问最新部门信息，3级name | 按 row_permissions 同层级历史取值补充 |

说明：
- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。
- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 分区过滤 | 是 |
| hour | string | 小时级分区 HH | 分区过滤 | 是 |
| private_sea_id | bigint | 主键id | 待按需求确认 | 否 |
| user_number | bigint | 用户id | 主键/关联键 | 是 |
| employee_id | int | 顾问id | 主键/关联键 | 是 |
| team_id | bigint | 团队id | 待按需求确认 | 否 |
| stage | int | 线索状态 我的线索(4) 我的客户(5) 我的成单(6) | 待按需求确认 | 否 |
| stage_name | string | 线索状态 我的线索(4) 我的客户(5) 我的成单(6) | 待按需求确认 | 否 |
| other_customer | int | 是否属于其他人的客户 | 待按需求确认 | 否 |
| source | int | 来源，1公开课报名 2手动录入 3公海领取 4主管分配 | 待按需求确认 | 否 |
| source_name | string | 来源，1公开课报名 2手动录入 3公海领取 4主管分配 | 待按需求确认 | 否 |
| last_follow_time | string | 跟进时间 | 时间分析 | 否 |
| last_follow_content | string | 最后一次跟进内容 | 待按需求确认 | 否 |
| intention_level | int | 意向度 | 待按需求确认 | 否 |
| assign_time | string | 线索分配时间 | 时间分析 | 否 |
| fall_sea_time | string | 线索掉海时间 | 时间分析 | 否 |
| is_del | int | 是否删除 | 待按需求确认 | 否 |
| private_sea_create_time | string | 创建时间 | 时间分析 | 否 |
| private_sea_update_time | string | 更新时间 | 时间分析 | 否 |
| version | int | 版本号 | 待按需求确认 | 否 |
| intention_level_time | string | 首次记录意向度时间 | 时间分析 | 否 |
| assign_customer_time | string | 转客户时间 | 时间分析 | 否 |
| is_union_id_lead_show | int | 如果这条私海上只有微信线索且没有收到u群的加好友消息该字段一直为1不展示 0展示 | 待按需求确认 | 否 |
| union_id | string | 微信unionId | 待按需求确认 | 否 |
| next_follow_time | string | 下次跟进时间 | 时间分析 | 否 |
| lead_id | bigint | 线索id | 主键/关联键 | 是 |
| account_id | int | 顾问accountId | 指标聚合 | 是 |
| sale_flow_snapshot_id | bigint | 销售流程快照 | 待按需求确认 | 否 |
| sale_flow_stage | bigint | 销售阶段id | 待按需求确认 | 否 |
| active_time | string | 激活时间 | 时间分析 | 否 |
| b_client | int | 1线上 2线下 | 待按需求确认 | 否 |
| order_time | string | 成单时间 | 时间分析 | 否 |
| sale_flow_stage_sequence | int | 销售阶段顺序 | 待按需求确认 | 否 |
| model_type | bigint | 销售阶段顺序 | 待按需求确认 | 否 |
| model_type_desc | string | 模型类型 0:线索 1:潜客 | 待按需求确认 | 否 |
| close_time | string | 私海关闭时间 | 时间分析 | 否 |
| close_reason | bigint | 私海关闭原因：0-无效 \| 1-掉海 \| 2-转移 \| 3-订单留痕全部退费 \| 4-微信线索合并 \| 5-虚拟手机号绑定手机号 \| 6-归因修正 \| 7-无服务能力 | 待按需求确认 | 否 |
| close_reason_desc | string | 私海关闭原因： 0-无效 \| 1-掉海 \| 2-转移 \| 3-订单留痕全部退费 \| 4-微信线索合并 \| 5-虚拟手机号绑定手机号 \| 6-归因修正 \| 7-无服务能力 | 待按需求确认 | 否 |
| employee_email_name | string | 带数字的员工名称 | 常用维度 | 是 |
| employee_email_prefix | string | 邮箱前缀 | 常用维度 | 是 |
| department_code | bigint | 部门编号 | 常用维度 | 是 |
| department_path_json | string | 部门信息，json字符串 | 常用维度 | 是 |
| assign_employee_top_level_department_code | string | 顾问最新部门信息，topcode | 常用维度 | 是 |
| assign_employee_first_level_department_code | string | 顾问最新部门信息，1级code | 常用维度 | 是 |
| assign_employee_second_level_department_code | string | 顾问最新部门信息，2级code | 常用维度 | 是 |
| assign_employee_third_level_department_code | string | 顾问最新部门信息，3级code | 常用维度 | 是 |
| assign_employee_top_level_department_name | string | 顾问最新部门信息，topname | 权限/业务范围限定 | 是 |
| assign_employee_first_level_department_name | string | 顾问最新部门信息，1级name | 权限/业务范围限定 | 是 |
| assign_employee_second_level_department_name | string | 顾问最新部门信息，2级name | 权限/业务范围限定 | 是 |
| assign_employee_third_level_department_name | string | 顾问最新部门信息，3级name | 权限/业务范围限定 | 是 |
| intention_level_desc | string | 顾问填写的意向度 | 待按需求确认 | 否 |
## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.hour = 'HH'`
- `t.assign_employee_top_level_department_name = '<待填写>'`
- `t.assign_employee_first_level_department_name = 'H业务线'`
- `t.assign_employee_second_level_department_name = '精品班学部'`
- `t.assign_employee_third_level_department_name = '学习顾问部'`

## 9. 常用 join key

- `lead_id`：线索关联/去重
- `user_number`：用户关联
- `private_sea_id`：私海记录关联
- `employee_id`：员工关联
- `employee_email_prefix`：员工邮箱前缀关联
- `employee_email_name`：员工姓名关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.hour,
    t.lead_id,
    t.user_number,
    t.employee_email_prefix,
    t.employee_email_name,
    t.assign_employee_top_level_department_name,
    t.assign_employee_first_level_department_name,
    t.assign_employee_third_level_department_name,
    t.assign_employee_second_level_department_name,
    t.private_sea_id,
    t.employee_id,
    t.team_id,
    t.stage,
    t.stage_name,
    t.other_customer
from service_dw.dwd_crm_assign_private_detail_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.assign_employee_top_level_department_name = '<待填写>'
  and t.assign_employee_first_level_department_name = 'H业务线'
  and t.assign_employee_second_level_department_name = '精品班学部'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 51。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 51。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 分区限制：查询分区表必须带分区条件。
- department_name 范围限定：涉及部门字段必须过滤；未给取值时使用占位符。
- 字段类型注意事项：PDF 图片 OCR 低置信度字段必须先人工确认。
- 常见报错：字段不存在、库名前缀不正确、小时表遗漏 hour、group by 不完整。
- 待人工确认问题：
- PDF 第 4-5 页可读字段已录入，页面底部截断字段需人工复核。

### 流量画像 SQL 使用备注

- `traffic_profile.sql` 通过 `user_id = user_number` 关联该表，并按 `private_sea_update_time desc` 取每个用户最新私海阶段。
- 阶段映射在 SQL 内硬编码：`450 = 深沟`、`470 = 已双沟`，其他阶段归为 `其他`，同时保留了完整 `sale_flow_stage_sequence` 到阶段名映射。
- 范围限定为 `assign_employee_first_level_department_name = 'H业务线'`、`assign_employee_second_level_department_name = '市场部'`、`assign_employee_third_level_department_name = '市场顾问部'`。

## 12. 反向联动速查

被以下看板高频使用：

- `../dashboards/traffic_profile.md`：最新私海阶段、深沟、已双沟。
- `../dashboards/outbound_call_process_dashboard.md`：外呼过程中的深沟、双沟和阶段补充。

已知风险：

- Web 查询环境正常可用。市场顾问场景必须继续限定部门范围。
- 与主线索表常用 `user_id = user_number` 关联，使用前确认类型和去重粒度。
