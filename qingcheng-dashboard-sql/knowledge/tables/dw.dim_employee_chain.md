# dw.dim_employee_chain

## 1. 中文名称

员工组织链维表

## 2. 表用途

在青橙年季月营收 SQL 中用于确认员工在青橙项目部路径下的任职起止时间，从而只保留交易发生在员工属于青橙期间的财务业绩。

## 3. 数据粒度

待人工确认。当前 SQL 按 `email_prefix + dep_path + name` 聚合，取最早 `begin_time` 和最晚 `end_time`。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | string | 日期分区 |
## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `path_name` | `'高途-H业务线-青橙项目部'` 的前三层路径 | 青橙组织路径 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `email_prefix` | string | 员工邮箱前缀 | 当前 SQL 取出但 join 使用 `name` |
| `path_name` | string | 组织路径 | 取前三层作为 `dep_path` |
| `name` | string | 员工姓名/邮箱名 | join 财务表 `employee_email_name` |
| `talent_type_name` | string | 人才类型 | 当前 SQL 取出 |
| `position_name` | string | 岗位名称 | 当前 SQL 取出 |
| `source_hr_status` | int | HR 状态 | 当前 SQL 取出 |
| `leave_time` | string | 离职时间 | 当前 SQL 取出 |
| `execute_time` | string | 执行时间 | 当前 SQL 取出 |
| `begin_time` | string | 组织关系开始时间 | 用于交易时间过滤 |
| `end_time` | string | 组织关系结束时间 | 用于交易时间过滤 |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `biz_type` | int | 业务线类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_id` | string | 员工id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `role_id` | int | cas账号角色，1主讲老师，2辅导老师，3销售老师 其他详见wiki枚举 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `department` | string | 部门 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `phase` | string | 学部 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `parent_department_number` | string | ehr父部门number | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `cas_uid` | string | cas_uid | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `law_name` | string | 法律名 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `job_number` | string | 员工编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `begin_work_time` | string | 入职时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `talent_type` | int | 人才类型 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `position` | string | 职位名称id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `structure_fnc` | string | 组织架构 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `leader` | string | 直属上级（邮箱前缀） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `leader_name` | string | 直属上级名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `display_number` | string | 新员工编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_department` | string | 新部门 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_status` | int | 新员工状态码 1-已入职，8-待离职，4-已离职 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_type` | int | 新员工类型 1-正式，2-实习，3-劳务 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_city` | int | 工作城市编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_city_name` | string | 工作城市名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `resign_reason` | string | 员工离职原因 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `resign_reason_name` | string | 员工离职原因名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and array_join(slice(split(path_name, '-'), 1, 3), '-') = '高途-H业务线-青橙项目部'
```

## 9. 常用 join key

- `name = finance_dw.app_finance_performance_extend_details_hf.employee_email_name`
- `trade_time >= begin_time and trade_time <= end_time`

## 10. 常用 SQL 片段

```sql
array_join(slice(split(path_name, '-'), 1, 3), '-') as dep_path
```

## 11. 注意事项

- 当前 SQL 使用 `name` join 财务表，若存在重名可能误匹配；更稳妥的标准 key 待确认。
- 使用当前 `dt = now() - interval '24' hour` 的组织链快照读取历史 `begin_time/end_time`，需确认是否覆盖历史组织变更。
