# service_dw.app_h_crm_lead_employee_workload_detail_hf

## 1. 中文名称

高中顾问工作量看板

## 2. 表用途

高中顾问工作量看板明细。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

## 3. 数据粒度

顾问-小时粒度，待确认

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
| virtual_department_name_0 | string | '<待填写>' | 是 | 虚拟组织架构零级部门名称 | 待人工确认 |
| virtual_department_name_1 | string | '<待填写>' | 是 | 虚拟组织架构一级部门名称 | 待人工确认 |
| virtual_department_name_2 | string | '<待填写>' | 是 | 虚拟组织架构二级部门名称 | 待人工确认 |
| virtual_department_name_3 | string | '<待填写>' | 是 | 虚拟组织架构三级部门名称 | 待人工确认 |

说明：
- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。
- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 分区过滤 | 是 |
| hour | string | 小时级分区 HH | 分区过滤 | 是 |
| lead_id | bigint | 线索id | 主键/关联键 | 是 |
| lead_period_name | string | 线索归属期name | 常用维度 | 是 |
| is_valid_lead | bigint | 是否计算有效线索数。同时满足以下条件：1.排除黑名单用户；2.如果主留痕类型为 微信私域，限制入群成功；3.截面分配顾问不为空；4.线索是否有效为是。 eg: Y-算 \| N-不算 | 待按需求确认 | 否 |
| lead_group_period_year | string | 分组期年 | 常用维度 | 是 |
| lead_group_period_term | string | 分组期次 | 常用维度 | 是 |
| section_assign_employee_email_name | string | 截面分配-分配顾问员工带数字名称 | 常用维度 | 是 |
| section_assign_employee_email_prefix | string | 截面分配-分配顾问邮箱前缀 | 常用维度 | 是 |
| employee_role | bigint | 员工角色，eg：0-普通组员｜1-虚线管辖｜2-实线汇报 | 常用维度 | 是 |
| virtual_department_code_0 | string | 虚拟组织架构零级部门code | 常用维度 | 是 |
| virtual_department_code_1 | string | 虚拟组织架构一级部门code | 常用维度 | 是 |
| virtual_department_code_2 | string | 虚拟组织架构二级部门code | 常用维度 | 是 |
| virtual_department_code_3 | string | 虚拟组织架构三级部门code | 常用维度 | 是 |
| virtual_department_name_0 | string | 虚拟组织架构零级部门名称 | 权限/业务范围限定 | 是 |
| virtual_department_name_1 | string | 虚拟组织架构一级部门名称 | 权限/业务范围限定 | 是 |
| virtual_department_name_2 | string | 虚拟组织架构二级部门名称 | 权限/业务范围限定 | 是 |
| virtual_department_name_3 | string | 虚拟组织架构三级部门名称 | 权限/业务范围限定 | 是 |
| owner_account_id | bigint | 实线汇报account_id | 指标聚合 | 是 |
| owner_name | string | 实线汇报员工名称 | 待按需求确认 | 否 |
| owner_email_name | string | 实线汇报员工带数字名称 | 待按需求确认 | 否 |
| owner_email_prefix | string | 实线汇报邮箱前缀 | 待按需求确认 | 否 |
| user_number | bigint | 用户id | 主键/关联键 | 是 |
| call_time | string | 通话开始时间 | 时间分析 | 否 |
| call_date | string | 通话开始日期 | 时间分析 | 否 |
| call_duration | string | 通话时长(s) | 指标聚合 | 是 |
| call_status | int | 通话状态：1-接通 \| 0-未接通 | 待按需求确认 | 否 |
| call_type | int | 1呼入、2呼出 | 待按需求确认 | 否 |
| call_type_name | string | 1呼入、2呼出 | 待按需求确认 | 否 |
| call_phone_number | string | 手机号****分割 | 待按需求确认 | 否 |
| call_url | string | 录音 | 待按需求确认 | 否 |
| call_id | string | 通话记录id | 待按需求确认 | 否 |
| data_source | string | 上报来源: 先驱 \| 工作机 \| 微信-工作机 \| 微信-PC | 待按需求确认 | 否 |
| msg_type_name | string | 消息类型: 微信-语音通话 \| 微信-视频通话 \| 电话 | 待按需求确认 | 否 |
| from_username | string | 发送人hookid | 待按需求确认 | 否 |
| to_username | string | 接收人hookid | 待按需求确认 | 否 |
| unique_key | string | 唯一键 | 待按需求确认 | 否 |
| phone_call_count | string | 通话记录id（手机电话拨打） | 指标聚合 | 是 |
| phone_call_answer_count | string | 通话记录id（手机电话接通） | 指标聚合 | 是 |
| phone_duration_total | bigint | 手机电话通话时长 | 指标聚合 | 是 |
| wechat_call_count | string | 通话记录id（微信电话拨打） | 指标聚合 | 是 |
| wechat_call_answer_count | string | 通话记录id（微信电话接通） | 指标聚合 | 是 |
| wechat_call_duration_total | bigint | 微信通话时长 | 指标聚合 | 是 |
| call_count | string | 通话记录id（电话拨打） | 指标聚合 | 是 |
| call_answer_count | string | 通话记录id（电话接通） | 指标聚合 | 是 |
| call_duration_total | bigint | 电话通话时长 | 指标聚合 | 是 |
## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.hour = 'HH'`
- `t.virtual_department_name_0 = '<待填写>'`
- `t.virtual_department_name_1 = '<待填写>'`
- `t.virtual_department_name_2 = '<待填写>'`
- `t.virtual_department_name_3 = '<待填写>'`

## 9. 常用 join key

- `lead_id`：线索关联/去重
- `user_number`：用户关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.hour,
    t.lead_id,
    t.user_number,
    t.virtual_department_name_3,
    t.virtual_department_name_2,
    t.virtual_department_name_0,
    t.virtual_department_name_1,
    t.lead_period_name,
    t.is_valid_lead,
    t.lead_group_period_year,
    t.lead_group_period_term,
    t.section_assign_employee_email_name,
    t.section_assign_employee_email_prefix,
    t.employee_role,
    t.virtual_department_code_0
from service_dw.app_h_crm_lead_employee_workload_detail_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.virtual_department_name_0 = '<待填写>'
  and t.virtual_department_name_1 = '<待填写>'
  and t.virtual_department_name_2 = '<待填写>'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 46。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 46。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 46。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 分区限制：查询分区表必须带分区条件。
- department_name 范围限定：涉及部门字段必须过滤；未给取值时使用占位符。
- 字段类型注意事项：PDF 图片 OCR 低置信度字段必须先人工确认。
- 常见报错：字段不存在、库名前缀不正确、小时表遗漏 hour、group by 不完整。
- 待人工确认问题：
- PDF 第 26-27 页字段表为图片型，需人工校验。

### 流量画像 SQL 使用备注

- `data_center_market_2683_20260705.sql` 的 `call_c` CTE 使用该表统计外呼过程指标：`call_duration > 300` 作为 5 分钟长通话，`call_status in ('1','0')` 统计总外呼次数，`call_status = '1'` 统计接通次数。
- `call_c` 先按 `user_number + lead_id + section_assign_employee_email_prefix` 聚合，但后续 join 主线索时只使用 `user_number + section_assign_employee_email_prefix`，未使用 `lead_id`；多线索用户需确认是否会重复匹配。
- 该 CTE 只加 `dt/hour` 分区条件，未单独加部门范围；复用时如查询范围扩大，应结合主表或本表可用部门字段补充限制。
