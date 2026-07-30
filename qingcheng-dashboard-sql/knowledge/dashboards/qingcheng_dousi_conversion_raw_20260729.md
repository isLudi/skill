# 青橙抖私转化 raw

## 1. 来源

- canonical SQL：`resources/raw_sql/data_center_qingcheng_2740.sql`
- 数据集：`抖私-转化`
- model：`2740`
- 适用看板：`青-抖私-转化`
- 当前版本：2026-07-29

## 2. 口径边界

`2740` 不再维护独立订单归因口径。它完整复用 `2460` 的标准订单集：

```text
service_gmv
union all
course_transfer_gmv
```

在该订单集上仅增加规则期次与交易期次的时间分层。渠道、暑期期次、内部调课调班剔除、保护期课程转移补数和课程部门范围必须与 `2460` 同步。

## 3. 暑期期次

| 期次 | 起止日期 |
|---|---|
| `20260710期` | 2026-07-07 至 2026-07-13 |
| `20260716期` | 2026-07-14 至 2026-07-19 |
| `20260722期` | 2026-07-20 至 2026-07-25 |
| `20260728期` | 2026-07-26 至 2026-07-31 |
| `20260803期` | 2026-08-01 至 2026-08-06 |
| `20260809期` | 2026-08-07 至 2026-08-12 |

订单交易时间先匹配 `biz_qici_calendar`，未命中时才回退历史周五期次逻辑。规则名中的旧短期次通过 `legacy_short_qici -> short_qici` 归一。

## 4. 渠道归因

- 一级输出 `channel_1`，二级输出 `channel_2`。
- 复用 `2460.lead_map`，包含 `IP退费 / 春春、朱博士、郭艺`、`抖音复用 / 抖音正价退费` 及图片标准渠道命名。
- `IP退费` 规则先去除普通空格，精确匹配不含期次前缀的 `%青橙IP-招生退费-春春%`、`%青橙IP-招生退费-朱博士%`、`%青橙IP-招生退费-郭艺%`。
- 精确规则必须位于宽泛 `%青橙IP%` 和 `%招生退费%` 之前。

完整渠道契约见 `knowledge/sql_patterns/qingcheng_channel_grade_mapping.md`。

## 5. 标准订单集

### 5.1 service 主订单

`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 是标准订单主表。若 service 行的 `transfer_in_amount` 或 `transfer_out_amount` 大于 0，则该行的收入、退款、净营收和 `refund_4` 全部归零，避免内部调课调班重复计入。

### 5.2 保护期课程转移

从 2026-07-20 起，仅补回同时满足以下条件的课程转移：

- `order_change_type = 1` 的有效最新子订单。
- 青橙财务正向支付，且支付金额大于 0。
- B 用户在交易时点处于同一青橙顾问的有效私海保护期。
- 私海线索能够命中当前 `lead_map`，复用相同渠道、年级和主管。

补数独立生成 `course_transfer_gmv`，不改变 service 主订单的内部转移归零规则。

## 6. 团队架构

最终结果按以下条件关联 `temp_table.dingxi01_qing_team_jg`：

```text
name = employee_email_name
and qici = qici
```

不能只按员工关联。2026-07-29 验证中，架构表有 155 名员工、1,729 行，其中 152 名员工跨期重复，单人最多 14 行；`employee_email_name + qici` 为 1,729 个唯一键且无重复。

## 7. 输出粒度和字段

输出粒度：

```text
qici + channel_1 + channel_2 + dazu + leader_employee_email_name + grade_list + name
```

共 19 个字段：

- 7 个维度：`qici`、`channel_1`、`channel_2`、`dazu`、`leader_employee_email_name`、`grade_list`、`name`。
- 6 个净营收指标：`gmv_7`、`gmv_14`、`gmv_30`、`gmv_n30`、`gmv_7_h`、`gmv_total`。
- 6 个退款指标：`refund_7`、`refund_14`、`refund_30`、`refund_n30`、`refund_7_p`、`refund_total`。

详细公式见 `knowledge/metrics/qingcheng_dousi_conversion_metrics.md`。

## 8. 验证与生产状态

- 标准订单结果和 2740 均为 46 个 `qici + channel_1 + channel_2` 组合；逐组合净营收最大差额 `0.00`，退款最大差额 `0.00`。
- 每行 `gmv_total` 与五个净营收桶闭合差为 `0.00`；`refund_total` 与五个退款桶闭合差为 `0.00`。
- 生产 SQL SHA-256：`d85b1f745c20935a9a29046655a05b48174b9a351bda93af4b0c5b3995f225c0`。
- Preview task：`1507319914`；新抽数记录：`161603511`，状态 `SUCCESS`。

## 9. 维护规则

- 2460 标准订单集、渠道 CASE、暑期日历或课程转移规则变化后，必须同步重建 2740，不能局部复制手改。
- 回归必须按 `qici + channel_1 + channel_2` 比较净营收和退款，而不是只比较无筛选的原始 value/unit。
- 必须验证两个闭合式：`gmv_total = 五个 gmv 桶之和`、`refund_total = 五个 refund 桶之和`。
- 2740 的退款字段为负数展示；与标准订单正数退款比较时先统一符号。
