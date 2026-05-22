# 虚拟架构（virtual_*）与截面架构（section_assign_*）的区别

## 字段含义

| 字段族 | 含义 | 时点 | 来源表字段示例 |
|--------|------|------|---------|
| `section_assign_employee_*` | 期次截面时间点的顾问组织归属 | 截面时点（历史快照） | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.section_assign_employee_third_level_department_name` |
| `virtual_*` | 员工最新虚拟架构 | 当前最新快照 | `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.virtual_leader_email_name`、`virtual_third_department_name` |
| 临时表架构 | 按期次维护的架构映射 | 期次粒度 | `temp_table.dingxi01_jiagou_db`（按期次）、`temp_table.dingxi01_jiagou_zx`（在职，无期次） |

## 常见问题

### 1. WHERE 用截面字段过滤，SELECT 用虚拟字段展示

转换看板典型模式：
```sql
-- WHERE: 截面字段限定范围（正确）
where section_assign_employee_third_level_department_name = '市场顾问部'

-- SELECT: 虚拟字段作为展示维度（风险）
select virtual_leader_email_name as jingli
```

**后果**：顾问从青橙项目部转入市场顾问部后，WHERE 能筛入他的 0522 期线索，但 `virtual_leader_email_name` 可能仍显示旧主管，导致数据归入错误主管名下。

### 2. 虚拟架构更新滞后于截面分配

截面分配字段随期次创建更新，虚拟架构字段依赖架构维护流程，二者存在时间差。

## 排查方法

```sql
-- 对比同一顾问在特定期的截面 vs 虚拟架构
select
    concat(group_period_year, group_period_term) as period,
    section_assign_employee_second_level_department_name as section_dept2,
    section_assign_employee_third_level_department_name  as section_dept3,
    virtual_third_department_name    as virtual_dept3,
    virtual_fourth_department_name   as virtual_dept4,
    virtual_leader_email_name        as virtual_leader,
    virtual_direct_leader_email_name as virtual_direct,
    count(*) as row_cnt
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
where employee_email_name = '<顾问名>'
  and dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and section_assign_employee_first_level_department_name = 'H业务线'
group by 1,2,3,4,5,6,7
order by 1 desc
limit 20;
```

## 修复方向

| 场景 | 推荐方案 | 推荐来源 |
|------|---------|---------|
| 展示主管/经理维度 | 用 `jiagou_db`（按期次）替代 `virtual_*` | `temp_table.dingxi01_jiagou_db.jingli` |
| 展示小组长维度 | 用 `jiagou_db`（按期次）或 `jiagou_zx`（在职） | `temp_table.dingxi01_jiagou_db.xiaozu` |
| 展示在职架构 | 用 `jiagou_zx`（在职专项架构） | `temp_table.dingxi01_jiagou_zx` |
| 仅做范围过滤 | 用 `section_assign_*`（截面时点） | 主表 section_assign_* 字段 |
