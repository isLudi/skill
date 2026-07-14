# service_dw.dwd_crm_assign_private_detail_hf

## 1. 中文名称

CRM 线索分配私海记录小时表。

## 2. 表用途

用于追溯正常线索分配到顾问私海后的历史记录，包括首次承接顾问、后续转手顾问、分配时间、私海关闭时间和关闭原因。

本表用于解释“TMK 潜客转为正常线索后流向了谁”。当前截面承接顾问仍以 `service_dw.dm_crm_lead_stats_detail_hf.section_assign_employee_email_name` 为主，本表不替代当前截面。

## 3. 数据粒度

- 当前 `dt + hour` 快照内，物理记录键为 `private_sea_id`。
- 2026-07-13 live 探查中，H 业务线允许学部、`model_type=0`、`assign_time >= '2026-07-01'` 共 509829 行和 509829 个 `private_sea_id`，未发现重复键、跨线索、跨用户或跨顾问复用。
- 同一 `lead_id` 可以对应多个 `private_sea_id` 和多个顾问。上述范围内 478339 个 `lead_id` 中，29208 个有多个私海记录，28798 个对应多个顾问。
- 因此 `lead_id` 是历史链路关联键，不是本表唯一键；直接按 `lead_id` join 会放大线索明细。

## 4. 查询引擎

Presto。

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | string | 天分区，必须限定 |
| `hour` | string | 小时分区，必须限定 |

当前快照通常使用 `current_timestamp - interval '2' hour`；TMK 正常线索还必须限定 `model_type = 0`。

## 6. 强制范围限定字段

```sql
and assign_employee_first_level_department_name = 'H业务线'
and assign_employee_second_level_department_name in (
    '精品班学部',
    '菁英班学部',
    '市场部',
    '本地化大班学部',
    '青橙项目部'
)
```

该范围表示青橙 TMK 转移后允许承接的 H 业务线学部，不得缩窄为仅 `青橙项目部`，否则会漏掉分配到精品班等学部的正常线索；也不得在没有独立域证据时扩大到其他业务线。

## 7. 字段清单

| 字段 | 语义 | 用法 |
|---|---|---|
| `private_sea_id` | 私海记录 ID | 当前小时快照内的物理唯一键 |
| `lead_id` | 正常线索 ID | 关联 TMK 转移后的 `crm_leads_id` |
| `user_number` | 正常线索侧用户 ID | 与潜客用户 ID 分列保留，不直接 `coalesce` |
| `employee_email_name` | 该私海记录对应的顾问 | 首次/历史承接顾问来源 |
| `employee_email_prefix` | 顾问邮箱前缀 | 稳定员工关联候选键 |
| `assign_time` | 该私海记录的分配时间 | 排序历史承接顺序 |
| `private_sea_update_time` | 私海记录更新时间 | 同分配时间时的排序兜底 |
| `close_time` | 私海关闭时间 | `1970-01-01 08:00:00` 为未关闭默认值的 live 证据 |
| `close_reason`, `close_reason_desc` | 关闭原因 | `2/转移` 可识别转手关闭 |
| `is_del` | 私海记录是否删除/失效 | 与关闭时间联合判断活跃状态 |
| `assign_employee_*_department_name` | 顾问当前组织字段 | 范围限定和承接学部输出 |

## 8. 常用过滤条件

```sql
where p.dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
  and p.hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
  and p.model_type = 0
  and p.assign_employee_first_level_department_name = 'H业务线'
  and p.assign_employee_second_level_department_name in (
      '精品班学部', '菁英班学部', '市场部', '本地化大班学部', '青橙项目部'
  )
```

## 9. 常用 join key

- `private_sea_id`：当前小时快照内的私海记录键。
- `lead_id`：关联转移后正常线索；一对多，必须先去重或保留历史粒度。
- `user_number`：正常线索侧用户 ID，不能替代 `lead_id`。
- `employee_email_prefix`：关联员工维度的候选稳定键。

## 10. 常用 SQL 片段

首次承接顾问：

```sql
row_number() over (
    partition by lead_id
    order by assign_time, private_sea_id
) as first_rn
```

完整的当前私海候选排序见“去重契约”；当前截面顾问仍应关联 `service_dw.dm_crm_lead_stats_detail_hf`。

## 11. 注意事项

- `private_sea_id` 是记录键，`lead_id` 不是唯一键。
- 小时分区表示查询快照，不是分配事件发生时间。
- 私海历史用于首次承接和转手解释；当前顾问由截面表最终确认。
- H 范围内未命中不能解释为没有分配或没有发生潜客转正常线索。
- 顾问组织字段是当前组织截面，不能直接承担历史组织归属。

## 12. 关联契约

### 7.1 TMK 转移线索关联私海历史

```sql
dwd_transfer.transfer_lead_id = assign_private.lead_id
```

- 左侧必须是 `data_lake_fuwu.dwd_crm_leads_rt` 中 `model_type=0` 的转移后正常线索 ID，不能使用潜客 ID。
- 关系为一对多；生产 join 前必须先按业务目的排序或聚合私海记录。
- 2026-07-13 当前 144 条 TMK/规划系统转移线索中，H 范围私海历史命中 123 条；未命中的 21 条只能解释为“当前 H 范围内无私海历史”，不能直接解释为未分配。

### 7.2 当前截面校验

```sql
assign_private.lead_id = lead_stats.lead_id
```

当前承接顾问使用 `lead_stats.section_assign_employee_email_name`。在当前 TMK 样本中，私海去重候选命中 123 条，截面顾问命中 115 条；双方同时命中的 115 条全部一致，0 条冲突。

### 7.3 数据地图字段补充（2026-07-13）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `dt` | string | 天级别分区 yyyyMMdd | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `hour` | string | 小时级分区 HH | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_id` | int | 顾问id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `team_id` | bigint | 团队id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stage` | int | 线索状态 我的线索(4) 我的客户(5) 我的成单(6) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stage_name` | string | 线索状态 我的线索(4) 我的客户(5) 我的成单(6) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `other_customer` | int | 是否属于其他人的客户 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source` | int | 来源，1公开课报名 2手动录入 3公海领取 4主管分配 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source_name` | string | 来源，1公开课报名 2手动录入 3公海领取 4主管分配 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_follow_time` | string | 跟进时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_follow_content` | string | 最后一次跟进内容 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `intention_level` | int | 意向度 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fall_sea_time` | string | 线索掉海时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `private_sea_create_time` | string | 创建时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `version` | int | 版本号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `intention_level_time` | string | 首次记录意向度时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_customer_time` | string | 转客户时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_union_id_lead_show` | int | 如果这条私海上只有微信线索且没有收到u群的加好友消息该字段一直为1不展示 0展示 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `union_id` | string | 微信unionId | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `next_follow_time` | string | 下次跟进时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `account_id` | int | 顾问accountId | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `sale_flow_snapshot_id` | bigint | 销售流程快照 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `sale_flow_stage` | bigint | 销售阶段id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `active_time` | string | 激活时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `b_client` | int | 1线上 2线下 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_time` | string | 成单时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `sale_flow_stage_sequence` | int | 销售阶段顺序 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `model_type` | bigint | 销售阶段顺序 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `model_type_desc` | string | 模型类型 0:线索 1:潜客 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `close_reason` | bigint | 私海关闭原因：0-无效 \| 1-掉海 \| 2-转移 \| 3-订单留痕全部退费 \| 4-微信线索合并 \| 5-虚拟手机号绑定手机号 \| 6-归因修正 \| 7-无服务能力 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `close_reason_desc` | string | 私海关闭原因： 0-无效 \| 1-掉海 \| 2-转移 \| 3-订单留痕全部退费 \| 4-微信线索合并 \| 5-虚拟手机号绑定手机号 \| 6-归因修正 \| 7-无服务能力 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `department_code` | bigint | 部门编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `department_path_json` | string | 部门信息，json字符串 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_employee_top_level_department_code` | string | 顾问最新部门信息，topcode | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_employee_first_level_department_code` | string | 顾问最新部门信息，1级code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_employee_second_level_department_code` | string | 顾问最新部门信息，2级code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_employee_third_level_department_code` | string | 顾问最新部门信息，3级code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_employee_top_level_department_name` | string | 顾问最新部门信息，topname | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_employee_first_level_department_name` | string | 顾问最新部门信息，1级name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_employee_second_level_department_name` | string | 顾问最新部门信息，2级name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_employee_third_level_department_name` | string | 顾问最新部门信息，3级name | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `intention_level_desc` | string | 顾问填写的意向度 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 13. 去重契约

### 历史明细

保留每个 `private_sea_id` 一行，不按 `lead_id` 去重。若未来分区出现同一 `private_sea_id` 多行，先按 `private_sea_update_time desc, version desc` 保留最新版本。

### 首次承接顾问

```sql
row_number() over (
    partition by lead_id
    order by assign_time, private_sea_id
)
```

取 `rn = 1`。必须用 `private_sea_id` 处理分配时间并列；全量探查发现 27 个 `lead_id` 首次分配时间并列。

### 当前私海候选顾问

```sql
row_number() over (
    partition by lead_id
    order by
        case
            when is_del = 0
             and (close_time is null or close_time <= '1970-01-02 00:00:00')
            then 1 else 0
        end desc,
        assign_time desc,
        private_sea_update_time desc,
        private_sea_id desc
)
```

该排序只生成“当前私海候选”，最终当前承接顾问仍以截面表为准。不能只按活跃标记取一行：全量探查发现 11393 个 `lead_id` 同时存在多个活跃私海，25 个 `lead_id` 末次分配时间并列。

### 转手链路

按 `lead_id, assign_time, private_sea_id` 排序并保留全部记录。TMK 当前样本 144 条中有 3 条多次分配，且首次顾问与当前顾问不同；其中 `315424857` 明确表现为关闭原因“转移”后从李洁96转给吴家富。

## 14. 已验证限制

- 小时表是当前快照中保留的私海历史集合，不应把 `dt/hour` 当事件发生时间。
- `employee_email_name` 是私海记录顾问，不是订单业绩归属顾问。
- `assign_employee_*_department_name` 是顾问组织截面字段，可能随组织变化；历史组织归属分析需另接员工任职区间表。
- 当前 TMK 覆盖不是 100%，不得用私海表缺失行反向否定 `previous_model_id` 转移关系。

## 15. Live 证据

- 粒度与唯一性：query id `1466169274`。
- 活跃状态与排序边界：query id `1466174917`。
- TMK 覆盖与截面一致性：query id `1466178403`。
- 多次分配和未命中边界明细：query id `1466187134`。
