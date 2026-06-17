# service_dw.app_h_crm_lead_employee_workload_detail_hf

## 1. 中文名称

CRM 线索员工工作量明细小时表

## 2. 表用途

在青橙过程数据 SQL 中作为外呼明细来源，计算通时、外呼次数、接通次数和长通话标记。

## 3. 数据粒度

待人工确认。当前 SQL 先 `select distinct` 外呼明细，再按 `user_number + lead_id + section_assign_employee_email_prefix` 聚合。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | string | 日期分区 |
| `hour` | string | 小时分区 |
## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| 无直接青橙字段 | 通过青橙主表 join 限定 | 单独查询本表时必须补充员工/部门范围或从青橙主表驱动 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `user_number` | bigint | 用户编号 | join `data.user_id` |
| `lead_id` | bigint | 线索 ID | 外呼聚合粒度 |
| `section_assign_employee_email_prefix` | string | 截面分配员工邮箱前缀 | join `data.employee_email_prefix` |
| `call_duration` | string | 通话时长，疑似秒 | 大于 480 秒为长通话 |
| `call_status` | int | 呼叫状态 | `'1'` 为接通，`'1','0'` 计入外呼次数 |
| `call_time` | string | 呼叫时间 | 当前 SQL 取出用于 distinct |
| `call_type_name` | string | 呼叫类型 | 当前 SQL 取出用于 distinct |
| `data_source` | string | 数据来源 | 当前 SQL 取出用于 distinct |
| `msg_type_name` | string | 消息类型 | 当前 SQL 取出用于 distinct |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_period_name` | string | 线索归属期name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_valid_lead` | bigint | 是否计算有效线索数。同时满足以下条件：1.排除黑名单用户；2.如果主留痕类型为 微信私域，限制入群成功；3.截面分配顾问不为空；4.线索是否有效为是。 eg: Y-算 \| N-不算 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_group_period_year` | string | 分组期年 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_group_period_term` | string | 分组期次 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `section_assign_employee_email_name` | string | 截面分配-分配顾问员工带数字名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_role` | bigint | 员工角色，eg：0-普通组员｜1-虚线管辖｜2-实线汇报 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_code_0` | string | 虚拟组织架构零级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_code_1` | string | 虚拟组织架构一级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_code_2` | string | 虚拟组织架构二级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_code_3` | string | 虚拟组织架构三级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_name_0` | string | 虚拟组织架构零级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_name_1` | string | 虚拟组织架构一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_name_2` | string | 虚拟组织架构二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_name_3` | string | 虚拟组织架构三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `owner_account_id` | bigint | 实线汇报account_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `owner_name` | string | 实线汇报员工名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `owner_email_name` | string | 实线汇报员工带数字名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `owner_email_prefix` | string | 实线汇报邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_date` | string | 通话开始日期 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_type` | int | 1呼入、2呼出 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_phone_number` | string | 手机号****分割 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_url` | string | 录音 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_id` | string | 通话记录id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `from_username` | string | 发送人hookid | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `to_username` | string | 接收人hookid | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `unique_key` | string | 唯一键 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `phone_call_count` | string | 通话记录id（手机电话拨打） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `phone_call_answer_count` | string | 通话记录id（手机电话接通） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `phone_duration_total` | bigint | 手机电话通话时长 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `wechat_call_count` | string | 通话记录id（微信电话拨打） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `wechat_call_answer_count` | string | 通话记录id（微信电话接通） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `wechat_call_duration_total` | bigint | 微信通话时长 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_count` | string | 通话记录id（电话拨打） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_answer_count` | string | 通话记录id（电话接通） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_duration_total` | bigint | 电话通话时长 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 8. 常用过滤条件

```sql
where wf.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and wf.hour = format_datetime(now() - interval '2' hour, 'HH')
```

## 9. 常用 join key

- `user_number = data.user_id`
- `section_assign_employee_email_prefix = data.employee_email_prefix`

## 10. 常用 SQL 片段

```sql
sum(case when call_status in ('1','0') then 1 else 0 end) as zong_call_ci_1,
sum(case when call_status = '1' then 1 else 0 end) as call_status_1
```

## 11. 注意事项

- 本表当前 SQL 未直接过滤青橙部门，必须通过青橙主表 join 后限定范围。
