# gaotu_hl.dim_mkt_h_lead_channel_df

## 1. 中文名称

市销线索渠道映射表

## 2. 表用途

来自天工数据地图的表说明：记录市销线索的系统期、标准期、部门、年级、渠道归因和成本字段。

## 3. 数据粒度

日快照内一条 `lead_id` 一行。`dt='20260812'` 实测 3,305,571 行、3,305,571 个非空去重 `lead_id`，因此该分区内 `lead_id` 唯一；跨 `dt` 不是唯一键。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 计算日期 yyyyMMdd | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| dt | string | 最新已完成分区 | 是 | 不得跨分区直接按 `lead_id` Join，否则同一线索会随快照数放大 |

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|

### 7.1 数据地图字段补充（2026-08-13）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| lead_id | string | 线索ID（主键） | 数据地图补充 | 否 |
| source_period_name | string | 系统期名 group_period_year+group_period_term | 数据地图补充 | 否 |
| stat_period_name | string | 标准期名（来自期名对照表，本表不推导） | 数据地图补充 | 否 |
| department | string | 顾问二级学部（精品班中价单列为 精品中价） | 数据地图补充 | 否 |
| stat_grade | string | 归一后年级（初级/预科→初级，初三→初级），成本关联键 | 数据地图补充 | 否 |
| channel_map | string | 渠道名，未命中规则时为 其他未知流量 | 数据地图补充 | 否 |
| channel_group | string | 渠道大类，如 KOC/ip/信息流/本地化图书 | 数据地图补充 | 否 |
| has_rule_config | int | 1=该标准期飞书已配规则 0=无规则可用（未参与归因） | 数据地图补充 | 否 |
| lead_count | int | 线索数，本表恒为 1（粒度口径） | 数据地图补充 | 否 |
| valid_lead_count | int | 有效线索数 0/1 | 数据地图补充 | 否 |
| cost_lead_basis | string | 成本口径：ip 用 lead_count，其他用 valid_lead_count | 数据地图补充 | 否 |
| cb_of_lead | double | 投放成本单价（元/线索），来自飞书表③ | 数据地图补充 | 否 |
| has_cost_config | int | 1=成本配置命中 0=该(期×渠道×年级)未配成本 | 数据地图补充 | 否 |
| invest_cost | double | 投放成本 = cb_of_lead × 成本口径线索数 | 数据地图补充 | 否 |
| lead_cost | double | 底表原始线索成本（平台回传，与 invest_cost 口径不同） | 数据地图补充 | 否 |

## 8. 常用过滤条件

- 查询必须限定单个 `dt` 分区；2026-08-13 16:00 探查时最新可用分区为 `20260812`，相对宽表 `20260813/hour=13` 存在 D-1 延迟。
- `has_rule_config=0` 代表该标准期没有可用规则配置，不能把非空 `channel_map` 自动理解为已按当前共享 CASE 完整归因。

## 9. 常用 join key

- 与 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 的物理候选键为 `lead_id`，两边类型均为 string。
- 必须先把本表限定到单个 `dt`，再按 `wide.lead_id = dim.lead_id` 关联。最新分区 `lead_id` 唯一，因此不会由维表侧制造 1:N 放大；宽表自身同一 `lead_id` 可有多行，不能反向宣称整体一对一。
- 该候选 Join 当前只通过了基数门禁，没有通过替换覆盖门禁：宽表 `dt='20260813', hour='13'` 的市场顾问范围有 1,497,182 个去重线索，仅 364,326 个命中，覆盖率 24.3341%。
- `20260815期` 仍有 265 个线索未命中，且承载 251 个 `lead_count` 和 227 个 `valid_lead_count`；因此不得用本表直接替换共享渠道 CASE，也不得用 inner join 丢弃未命中线索。
- 与 `gaotu_hl.dim_mkt_h_period_map_df` 可按 `department + source_period_name` 对齐期次；与 `gaotu_hl.ods_mkt_h_channel_group_df` 可在后者限定 `department_name='all'` 后按 `channel_map = channel` 补充渠道组。两条路径都必须各自限定单个分区并复核唯一性。
- 排除 `lead_id` 后，最细的可共享维度键 `source_period_name + stat_period_name + department + stat_grade` 仍有 1,136 个键中的 760 个对应多个 `channel_map`，单键最多 43 个渠道；3,305,571 行中 3,230,041 行落在歧义键上。该组合不是函数依赖，禁止直接 Join。
- 用宽表语义最接近的 `concat(group_period_year, group_period_term) + section_assign_employee_second_level_department_name + lead_purchase_intention_level2_category_name` 回连时，仅 233/1,587,930 行落入唯一渠道键，安全覆盖 `lead_count=96`、`valid_lead_count=87`；若直接连接原始维表，理论输出约 1,844,968,031 行，存在严重 1:N 放大。
- `rule_name + flow_pool_name` 及 15 个原始归因字段签名只能通过 `lead_id` 命中样本反向学习映射，不是本表自带 Join key。15 字段签名映射全宽表仅覆盖 394,836 行，并只为原未命中部分新增 `lead_count=454`、`valid_lead_count=409`，不能解决全量替换。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from gaotu_hl.dim_mkt_h_lead_channel_df t
where t.dt = 'YYYYMMDD'
limit 20;
```

## 11. 注意事项

- 字段、类型和分区信息来源于天工数据地图；唯一性、覆盖和指标影响来自 2026-08-13 Presto 探针。
- `channel_map` 在最新分区无空值，但仍有 180,466 行为 `其他未知流量`，且 1,674,850 行 `has_rule_config=0`；非空不等于与市场顾问共享 CASE 等价。
- 命中行中存在 `source_period_name` 和 `department` 与宽表对应字段不一致的记录，业务替换前仍须完成逐渠道值、期次和部门语义对照。
- 两条 Data Center 专属退款复用规则在本轮最新宽表快照中均为 0 条，不能据此证明维表已吸收这些规则；有可用样本后需单独复验。
- 证据 Query ID：`1545770550`、`1545772344`、`1545778770`、`1545781728`、`1545783720`、`1545794539`、`1545799826`。
- 当前结论：可作为按线索补充属性的受控候选维表，但不可作为全部市场顾问渠道 CASE 的直接替代源。
- 非 `lead_id` 结论的证据 Query ID：`1545827397`、`1545833782`、`1545836172`、`1545839822`、`1545843263`。
