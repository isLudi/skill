# 渠道 CASE 映射口径

## 1. 口径名称

市场顾问渠道 CASE 映射口径

## 2. 最新来源

- 原始文件：`D:\Feishu\0524.txt`
- Skill 归档：`resources/raw_sql/market_channel_case_when_0524.sql`
- 来源文件最后修改时间：2026-05-24
- 入库日期：2026-05-09
- 最近更新日期：2026-05-24
- 代码规模：201 行，200 个 `then` 分支，132 个去重后的渠道输出值
- 输出字段：`qudao`

### 0522 → 0524 增量变更

- **新增** `周帅-百度数字人`：`when third_department_name = '直播部' and sku_id_name like '%周帅%' and channel_name_2 in ('百度','B站') then '周帅-百度数字人'`（1 条）
- **新增** `途途私域`：`when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') then '途途私域'`（1 条）
- **修改** `B站信息流-亚飞`：条件追加 `or rule_name like '%亚飞%' or page_id_name like '%初中-0元%'`

## 3. 适用范围

用于市场顾问相关看板中的渠道归因 CASE 映射。现有历史 SQL 中同类字段包括：

- `channel_map`
- `channel_map_1`
- `qudao`

生成或改写市场顾问转化、线索转化到课、外呼过程、分配计划实际有效量等看板 SQL 时，如果需要“最新渠道 CASE”，优先引用 `resources/raw_sql/market_channel_case_when_0524.sql`，不要直接照抄旧看板中的长 CASE。

## 4. 主要依赖字段

该 CASE 片段依赖主线索/全链路宽表中的渠道、投放、流量池、规则和部门字段。常见字段包括：

| 字段 | 用途 |
|---|---|
| flow_pool_name | 流量池识别，覆盖直播、图书、私域、自然流、商务等大量规则 |
| rule_name | 规则名识别，覆盖期次、训练营、私域、IP、老师名、价格等规则 |
| put_plan_name | 投放计划识别，覆盖抖音私信、进校、KOC、商务、私域等规则 |
| sku_id_name | 商品/落地页 SKU 识别，覆盖老师 IP、价格、图书、纯课等规则 |
| source_manager_name | source 负责人识别，覆盖抖音私信、进校、KOC、创新、图书等规则 |
| channel_name_1 / channel_name_2 / channel_name_3 | 渠道树识别，覆盖信息流、B站、小红书、商务、公众号、APP 等规则 |
| ad_account_name | 广告账户识别，覆盖信息流老师 IP 和科目规则 |
| page_id_name | 页面名称识别，覆盖 B站信息流、TMK、书商、进校等规则 |
| source_put_plan_name | source 侧投放计划识别，常用于 B站信息流等规则 |
| first_department_name / second_department_name / third_department_name | 部门范围和渠道归属识别 |
| virtual_second_department_name / virtual_fourth_department_name / virtual_fifth_department_name | 虚拟架构识别，常用于私域、菁英、团队规则 |
| channel_provider_name / channel_second_provider_name | 渠道商识别，覆盖小程序、TMK、图书、商务等规则 |
| get_customer_way_name | 获客方式识别，覆盖短视频信息流、KOL 直播等规则 |
| period_name | 期次/多学科拓展排除条件 |
| lead_purchase_intention_name / lead_purchase_intention_level1_category_name / lead_purchase_intention_level2_category_name | 购买意向和品类条件 |
| flow_original_order_activity_price / flow_order_price / flow_orders_income_amount | 价格条件 |
| lead_create_time | 特定时间后规则 |

## 5. 关键渠道规则提示

该 CASE 顺序敏感，前面的规则会覆盖后面的规则。改写时必须整体保留顺序，除非用户明确要求局部调整。

与近期排查相关的抖音私信规则：

```sql
when source_manager_name in ('韩正卿') then '抖音私信'
when channel_name_1 = '信息流'
  and (
      put_plan_name like '%抖音私信%'
      or put_plan_name like '%初三0元%'
      or put_plan_name like '%高中0元%'
  )
then '信息流-抖音私信'
```

因此排查“抖音私信”进量时不能只查 `rule_name like '%抖音私信%'`，还应检查：

- `source_manager_name = '韩正卿'`
- `channel_name_1 = '信息流'`
- `put_plan_name like '%抖音私信%'`
- `put_plan_name like '%初三0元%'`
- `put_plan_name like '%高中0元%'`

## 6. 复用模板

建议在主数据 CTE 中直接派生渠道字段：

```sql
with base as (
    select
        t.lead_id,
        t.user_id,
        t.employee_email_name,
        t.rule_name,
        -- 粘贴 resources/raw_sql/market_channel_case_when_0524.sql
        -- 并按需要将输出别名 qudao 改为 channel_map
        <latest_channel_case_when>
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t
    where t.dt = 'YYYYMMDD'
      and t.hour = 'HH'
      and t.section_assign_employee_first_level_department_name = 'H业务线'
      and t.section_assign_employee_second_level_department_name = '市场部'
)
select *
from base
limit 100;
```

如果目标看板历史字段名为 `channel_map` 或 `channel_map_1`，应只改最终别名：

```sql
else '其他未知流量' end as channel_map
```

不要改 CASE 分支顺序。

## 7. 定期更新流程

当渠道 CASE 来源文件更新后：

1. 从来源文件名提取日期后缀；例如来源为 `D:\Feishu\0515.txt`，归档路径必须为 `resources/raw_sql/market_channel_case_when_0515.sql`。后续若来源为 `D:\Feishu\MMDD.txt`，最新归档必须同步改为 `market_channel_case_when_MMDD.sql`。
2. 将来源文件同步覆盖到对应日期后缀的归档 SQL；如果已有旧日期后缀文件作为最新入口，应重命名或替换为新后缀，并同步更新所有知识库引用。
3. 重新统计行数、`then` 分支数、去重渠道数和关键字段变化。
4. 更新本文件的原始文件、Skill 归档、来源文件最后修改时间、代码规模、关键渠道规则和待确认事项。
5. 更新 `knowledge/update_log/changelog.md`，按时间正序追加到文件末尾。
6. 运行 `python scripts/check_skill_integrity.py`。

该文件是 CASE 片段，不是完整 SQL；通常不直接运行 `scripts/validate_sql_rules.py`，除非先包成完整可执行查询。

## 8. 待确认事项

- 渠道 CASE 来源文件是否仍按 `D:\Feishu\MMDD.txt` 命名；如果命名规则变化，应同步更新本知识文档和归档文件命名规则。
- `qudao`、`channel_map`、`channel_map_1` 是否完全等价需按具体看板确认。
- CASE 依赖的部分字段来自宽表，若用于规则表或其他表，需要先确认字段是否存在。
- 部分条件把价格字段当字符串做 `like` 或 `in ('100.0', ...)`，字段真实类型需按目标表确认。
