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

## 3. 修复优先级

1. 优先在 CASE 中添加 `rule_name` 提取分支（字段本身已含年级关键词）
2. 如 `rule_name` 不含年级且 ELSE 值不匹配，在 ELSE 后加一层映射
3. 尽量避免直接用 `lead_purchase_intention_level2_category_name` 而不做映射
