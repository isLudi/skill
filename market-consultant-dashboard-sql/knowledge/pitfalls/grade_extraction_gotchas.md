# grade_1 年级提取常见坑

## 1. CASE 分支不完整

`grade_1` 从 `rule_name` 提取年级时，容易遗漏某些年级。

**当前需覆盖**：高一、高二、高三、初一、初二、初三。

**完整 CASE 模板**：

```sql
case
    when f.rule_name like '%高一%' then '高一'
    when f.rule_name like '%高二%' then '高二'
    when f.rule_name like '%高三%' then '高三'
    when f.rule_name like '%初一%' then '初一'
    when f.rule_name like '%初二%' then '初二'
    when f.rule_name like '%初三%' then '初三'
    else f.lead_purchase_intention_level2_category_name
end as grade_1
```

**注意**："初一"易被遗漏（只写了初二/初三，漏掉初一）。如后续新增"小六"等年级，需同步补充。

## 2. ELSE 分支与临时表命名不一致

`lead_purchase_intention_level2_category_name` 的取值（如"初级"、"七年级"、"八年级"）
与 daoke 表 `grade`（"初一"、"初二"）和 cost 表 `grade`（"初三"、"初二"、"高中"）命名规范不同，导致 JOIN 断裂。

**已知的不一致**：

| 主表 `lead_purchase_intention_level2_category_name` | 临时表 `grade` |
|---|---|
| `'初级'` | `'初一'` |
| `'七年级'` | `'初一'` |
| `'八年级'` | `'初二'` |

**排查方法**：

```sql
with data_grades as (
    select distinct
        case when rule_name like '%初一%' then '初一' ... end as grade_1
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
    where ...
),
temp_grades as (
    select distinct grade from temp_table.dingxi01_daoke_1_6_t where ...
)
select d.grade_1 as data_grade, k.grade as temp_grade,
       case when d.grade_1 = k.grade then 'MATCH' else 'MISMATCH' end
from data_grades d
full outer join temp_grades k on d.grade_1 = k.grade;
```

## 3. 业财宽表 `rule_name` 只记录主留痕分配规则

`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.rule_name` 不是 CRM 当前页面展示的所有分配规则全集。该字段只记录主留痕上的分配规则。

如果线索进量时分配错了，或主留痕上没有命中分配规则，后续再通过调课调班、线索流转等方式进入正确班级，CRM 页面可能已经能看到分配规则，但业财宽表的 `rule_name` 仍可能为空。此时看板中从 `rule_name` 提取年级的 CASE 会落到 ELSE，使用 `lead_purchase_intention_level2_category_name`，从而出现 CRM 有规则但看板年级仍为购买意向年级的情况。

**典型现象**：

- CRM 页面分配规则存在，例如 `0626期-koc自孵化5元-koc自孵化5元-初二`。
- 业财宽表 `bdg_ba...rule_name` 为空。
- `service_dw.dim_crm_assign_rule_lead_detail_hf.rule_name` 或 `service_dw.dm_crm_lead_stats_detail_hf.trace_rule_name` 能查到分配规则。
- 看板年级取值不是规则中的年级，而是购买意向二级品类映射后的年级。

**排查时需同时对比**：

```sql
select
    f.lead_id,
    f.user_id,
    f.rule_name as bdg_main_trace_rule_name,
    s.trace_rule_name as stats_trace_rule_name,
    r.rule_name as assign_rule_detail_rule_name,
    f.lead_purchase_intention_level2_category_name
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
left join service_dw.dm_crm_lead_stats_detail_hf s
    on f.lead_id = s.lead_id
   and f.user_id = s.user_id
left join service_dw.dim_crm_assign_rule_lead_detail_hf r
    on f.lead_id = r.lead_id
   and f.user_id = r.user_id
where ...
```

复现看板口径时，应优先使用业财宽表 `rule_name`，并保留缺失时回退到购买意向年级的逻辑。若业务目标是按 CRM 当前可见规则或后续调课调班后的规则修正年级，需要额外 join 规则明细或线索统计留痕表，并明确优先级，不能把业财宽表 `rule_name` 缺失直接解释为 CRM 没有分配规则。

## 4. 修复优先级

1. 先确认业务目标：是复现当前看板口径，还是按 CRM 当前/后续规则修正年级。
2. 复现看板口径时，优先在 CASE 中添加 `rule_name` 提取分支（字段本身已含年级关键词）。
3. 如 `rule_name` 不含年级且 ELSE 值不匹配，在 ELSE 后加一层映射。
4. 如 CRM 有分配规则但业财宽表 `rule_name` 为空，优先排查主留痕缺失、进量后调课调班或后续流转场景，不要直接判断为 CRM 无规则。
5. 尽量避免直接用 `lead_purchase_intention_level2_category_name` 而不做映射。
