# bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf

## 1. 中文名称

潜客转线索指标统计表

## 2. 表用途

用于青橙 TMK / 规划系统潜客侧过程数据和潜客转正常线索链路排查。相比 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df`，本表显式提供 `lead_model_type`：

- `lead_model_type = 1`：潜客。
- `lead_model_type = 0`：线索，但当前验证中不适合作为 TMK 转移后承接顾问来源。

本表适合提供潜客阶段的 TMK 顾问、用户 ID、分配规则、渠道、年级、期次、有效线索数、加微数、等待时长、外呼次数和通时等字段。

## 3. 数据粒度

待业务侧完全确认。按数据地图 DDL 和当前 SQL 使用方式，核心粒度接近“线索/潜客 ID + 员工截面 + 期次/渠道”。生产查询中应按 `lead_id` 去重或先窗口取一条后再 join，避免同一潜客多行放大。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | string | 日期分区，格式 `yyyyMMdd` |
| `hour` | string | 小时分区，格式 `HH` |

当前过程数据探索使用：

```sql
where dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
```

## 6. 强制范围限定字段

| 字段名 | 推荐取值 | 说明 |
|---|---|---|
| `section_assign_employee_first_level_department_name` | `'H业务线'` | 截面分配员工一级部门 |
| `section_assign_employee_second_level_department_name` | `'青橙项目部'` | 截面分配员工二级部门 |
| `period_mapping_first_level_department_name` | `'H业务线'` | 期次映射一级部门 |
| `period_mapping_second_level_department_name` | `('精品班学部','青橙项目部')` | 期次映射二级部门 |

如果查询是从 `data_lake_fuwu.dwd_crm_leads_rt` 已确认的 TMK 潜客转移明细回补字段，可把 `dwd` 的 `purchase_intention_name` 与 `previous_model_id` 链路作为主过滤，再按 `lead_id` 回连本表补充 TMK 顾问和渠道；此时是否继续强加青橙截面范围会影响历史潜客覆盖率，需在输出中说明。

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_id` | bigint | 线索/潜客 ID | 当 `lead_model_type=1` 时可理解为潜客 ID，可与 `data_lake_fuwu.dwd_crm_leads_rt.crm_leads_id` 的潜客记录匹配 |
| `lead_model_type` | bigint | 线索模型类型 | `0`=线索，`1`=潜客 |
| `lead_model_type_name` | string | 线索模型类型名称 | 数据地图说明同上 |
| `user_id` | bigint | 用户 ID | 用户级补充字段 |
| `employee_email_prefix` | string | 员工邮箱前缀 | 潜客阶段 TMK 顾问账号 |
| `employee_email_name` | string | 员工姓名数字 | 潜客阶段 TMK 顾问姓名 |
| `virtual_first_department_name` | string | 员工最新虚拟架构一级部门 | 数据地图确认；2026-07-11 TMK 样本主要为 `H业务线` |
| `virtual_second_department_name` | string | 员工最新虚拟架构二级部门 | 数据地图确认；TMK 样本可见 `市场部`、`青橙项目部` |
| `virtual_third_department_name` | string | 员工最新虚拟架构三级部门 | 数据地图确认；TMK 过程数据可作为 `department` 的临时架构兜底来源 |
| `virtual_fourth_department_name` | string | 员工最新虚拟架构四级部门 | 数据地图确认；TMK 过程数据可作为 `dept_2` 的临时架构兜底来源 |
| `virtual_leader_email_name` | string | 员工最新虚拟架构大组长 | 数据地图确认；直属主管为空时的上级兜底 |
| `virtual_direct_leader_email_name` | string | 员工最新虚拟架构小组长 | 数据地图确认；TMK 过程数据可作为 `xiaozu` 的临时架构兜底来源 |
| `lead_purchase_intention_name` | string | 购买意向名称 | 青橙 TMK/规划系统筛选核心字段 |
| `lead_purchase_intention_level2_category_name` | string | 购买意向二级分类 | 年级兜底字段 |
| `stats_grade_name` | string | 统计口径线索年级 | 可作为年级优先补充 |
| `rule_name` | string | 分配规则 | 可按青橙过程数据 CASE 生成渠道大类/细分 |
| `group_period_year` | string | 期分组年 | 潜客期次拼接字段 |
| `group_period_term` | string | 期分组期次 | 潜客期次拼接字段 |
| `group_period_name` | string | 期分组名称 | 当前验证中更贴近潜客体验课期次 |
| `period_name` | string | 期名称 | 当前验证中更贴近公开课期次 |
| `valid_lead_count` | bigint | 有效线索数 | 过程数据分母 |
| `friend_lead_count` | bigint | 加微数 | 好友率分子 |
| `section_assign_time` | string | 截面分配时间 | 等待时长、首 call 时效计算 |
| `first_call_time` | string | 分配后首 call 时间 | 首 call 时效计算 |
| `section_assign_first_call_connected_time` | string | 分配后首次接通时间 | 沟通率时效计算 |
| `section_assign_call_connected_count` | bigint | 分配后接通次数 | 外呼频次 |
| `section_assign_call_missed_count` | bigint | 分配后未接通次数 | 外呼频次 |
| `section_assign_all_call_duration` | bigint | 分配后总通话时长，秒 | 总通时/外呼时长 |

## 8. 常用过滤条件

青橙 TMK / 规划系统潜客过程数据常用意向：

```sql
lead_model_type = 1
and lead_purchase_intention_name in (
    '高中预科青橙TMK',
    '高一青橙TMK',
    '高二青橙TMK',
    '高三青橙TMK',
    '规划系统高一',
    '规划系统高二',
    '规划系统高三'
)
```

## 9. 常用 join key

- `lead_id = data_lake_fuwu.dwd_crm_leads_rt.crm_leads_id`
  - 当本表 `lead_model_type=1` 时，`lead_id` 可作为潜客 ID。
  - 可继续通过 `data_lake_fuwu.dwd_crm_leads_rt` 中正常线索的 `previous_model_id = 潜客 crm_leads_id` 找到转移后的正常线索 ID。
- `lead_id = service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.lead_id`
  - 仅适用于转移后的正常线索 ID，不适用于潜客 ID 直接找成交。

## 10. 常用 SQL 片段

```sql
with dwd_prelead as (
    select
        cast(crm_leads_id as bigint) as prelead_id,
        cast(user_id as bigint) as prelead_user_id,
        purchase_intention_name
    from data_lake_fuwu.dwd_crm_leads_rt
    where model_type = 1
      and purchase_intention_name in (
          '高中预科青橙TMK',
          '高一青橙TMK',
          '高二青橙TMK',
          '高三青橙TMK',
          '规划系统高一',
          '规划系统高二',
          '规划系统高三'
      )
),
dwd_transfer as (
    select
        p.prelead_id,
        cast(l.crm_leads_id as bigint) as transfer_lead_id
    from dwd_prelead p
    join data_lake_fuwu.dwd_crm_leads_rt l
      on cast(l.previous_model_id as bigint) = p.prelead_id
    where l.model_type = 0
      and l.previous_model_id > 0
)
select
    t.prelead_id,
    t.transfer_lead_id,
    p.employee_email_name as tmk_employee_name,
    p.rule_name
from dwd_transfer t
left join bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf p
  on cast(p.lead_id as bigint) = t.prelead_id
 and p.lead_model_type = 1
where p.dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
  and p.hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
limit 1000
```

## 12. 当前 live 验证记录

- `desc bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf` 成功，query id `1456918587`。
- `data_lake_fuwu.dwd_crm_leads_rt` 自关联验证 TMK/规划系统潜客转正常线索链路成功，query id `1456961079`：当前可见意向为 `规划系统高一/高二/高三`，去重转移线索约百条量级。
- 用 `dwd` 转移链路回补本表潜客字段时，当前最新小时可补到大部分 TMK 顾问；若额外加严格青橙截面范围，历史覆盖率明显下降。诊断 query id `1456978632`。

## 11. 注意事项

- 本表字段名使用 `lead_id`，没有 `crm_leads_id` 字段；与 `data_lake_fuwu.dwd_crm_leads_rt.crm_leads_id` 关联时需显式说明两侧语义。
- 用本表直接取 `lead_model_type=0` 作为转移后承接顾问来源，在 2026-07-09 最新小时验证未命中这些转移线索，query id `1456984198`。
- 若目标是历史转移漏斗，建议以 `data_lake_fuwu.dwd_crm_leads_rt` 的 `previous_model_id` 链路为主，再回补本表字段；不要从本表 `lead_model_type=0` 单独推断转移结果。
- 2026-07-11 TMK 过程数据探查中，132 条转移线索有 102 个潜客 ID 命中本表，100 条过程字段完整；按 `qici + employee_email_name` 匹配 `temp_table.dingxi01_jiagou_db` 仅 8 条。若过程数据必须保留 TMK 行，可先用临时架构表，未命中时再用 `virtual_third_department_name / virtual_fourth_department_name / virtual_direct_leader_email_name` 兜底，并保留其原始组织名称，不得伪装为青橙一部/三部等既有团队。
