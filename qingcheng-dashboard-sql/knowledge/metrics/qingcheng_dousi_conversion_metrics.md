# 青橙渠道分周期转化指标

## 1. 来源与粒度

- SQL：`resources/raw_sql/data_center_qingcheng_2740.sql`
- 看板说明：`knowledge/dashboards/qingcheng_dousi_conversion_raw_20260729.md`
- 看板：`青橙渠道分周期转化`，`dashboard_3884629814875697153`；底层数据集 `抖私-转化`，model `2740`。
- 基础金额：`service_gmv union all course_transfer_gmv`；保留 2740 自身的课程部门白名单、2026-06-01 起交易范围、两小时前快照、内部转移归零及保护期补数规则。虽然组件名与 2460 相近，不能据此宣称两者订单集合完全相同或直接整段覆盖。
- 最终粒度：`qici + channel_1 + channel_2 + dazu + leader_employee_email_name + grade_list + name`
- 最终 SELECT 固定 19 列，现有字段名、退款符号和看板公式均不变。

## 2. 时间分层

交易归期优先使用已验证的青橙实际运营窗口；从 `2026-09-07` 起使用周一至周日，周内周五为期次标签，如 `20261016期 = 10-12 至 10-18`。历史特殊窗口及别名见[数据集说明](../dashboards/qingcheng_dousi_conversion_raw_20260729.md)。不得借用市场顾问部的暑期日历。

线索期次保留完整年份，优先级如下：

1. 经 SEC 来源组织和同一期次架构双重限域确认的潜客原期次。
2. 财务业绩事实的完整 `lead_period_name`；旧 `20260814期` 同时对应两个实际窗口，不能单凭该标签选择 0808 或 0815，继续寻找可验证上下文。
3. `full_link_valid_lead_count > 0` 的真实线索 cohort 期次。
4. 规则短期次与 full_link 期次相同，取 full_link 年份；或规则自身有可解析完整年份。

full_link 中无有效线索、无分配信息的财务骨架行不能直接当作获客期次；不能用交易年份猜线索年份，也不能按交易所属期次强行拆分歧义 0814。先做经验证的期次别名归一，再计算实际运营周期序号。特殊期内未识别标签、空期次及仍无法核实的线索（含 `lead_id=0`）均归入非30天，不单设“未归期”渠道或新增展示标注。

以 `trade_period_index - lead_period_index` 的序号差分桶，所有行只进入一个桶：

| `week_diff` | 条件 | 净营收字段 | 退款字段 |
|---:|---|---|---|
| `0` | 序号差 = 0，当期线索当期交易 | `gmv_7` | `refund_7` |
| `1` | 序号差 = 1，上一运营期线索本期交易 | `gmv_14` | `refund_14` |
| `2` | 序号差 = 2 或 3，更早两至三运营期线索 | `gmv_30` | `refund_30` |
| `4` | 序号差 = -1，下期线索提前交易 | `gmv_7_h` | `refund_7_p` |
| `3` | 其他差值或无法核实线索期次 | `gmv_n30` | `refund_n30` |

字段名保留看板现有命名。“8-14天”“15-30天”是运营期差桶，不是严格滚动自然日账龄；暑期短周期尤其不能按列名反推天数。常规周序号使用对齐周起点后的 `cast(floor(date_diff('day', anchor, week_start) / 7.0) as bigint)`，不使用 `date_diff('week', ...)`。后者在 2026-10-22 的 SQL 复算与 Data Center 抽数链路产生跨期桶差异；显式日差除7已通过相同期次/渠道逐项回读。

## 3. 净营收指标

| 指标 | SQL 口径 |
|---|---|
| `gmv_7` | `sum(case when week_diff = 0 then promit_amount else 0 end)` |
| `gmv_14` | `sum(case when week_diff = 1 then promit_amount else 0 end)` |
| `gmv_30` | `sum(case when week_diff = 2 then promit_amount else 0 end)` |
| `gmv_n30` | `sum(case when week_diff = 3 then promit_amount else 0 end)` |
| `gmv_7_h` | `sum(case when week_diff = 4 then promit_amount else 0 end)` |
| `gmv_total` | `sum(promit_amount)` |

闭合式：

```text
gmv_total = gmv_7 + gmv_14 + gmv_30 + gmv_n30 + gmv_7_h
```

## 4. 退款指标

来源订单集中的 `refund_amount` 为正数退款。2740 为保持看板展示口径，对各退款输出统一取负：

| 指标 | SQL 口径 |
|---|---|
| `refund_7` | `-sum(case when week_diff = 0 then refund_amount else 0 end)` |
| `refund_14` | `-sum(case when week_diff = 1 then refund_amount else 0 end)` |
| `refund_30` | `-sum(case when week_diff = 2 then refund_amount else 0 end)` |
| `refund_n30` | `-sum(case when week_diff = 3 then refund_amount else 0 end)` |
| `refund_7_p` | `-sum(case when week_diff = 4 then refund_amount else 0 end)` |
| `refund_total` | `-sum(refund_amount)` |

闭合式：

```text
refund_total = refund_7 + refund_14 + refund_30 + refund_n30 + refund_7_p
```

与 2460 或订单明细的正数退款比较时，应使用 `-refund_total`，或先把两边统一为相同符号。

## 5. 占比集合关系

对相同筛选和聚合层级，使用各桶金额之和除以该层级总额，不平均明细占比：

- 净收款：当期占比 + 8-14天收款占比 + 15-30天净收款占比 + 非30天净收款占比 + 下期线索当期占比 = 100%。
- 退款：当期退款占比 + 8-14天退款占比 + 15-30天退款占比 + 非30天退款占比 + 下期线索当期退款占比 = 100%。

退款分子与分母均为负数，保持相同符号。分母为0时现有 `ifnull(sum(bucket)/sum(total),0)` 显示0，此时不要求五项等于100%；净收款含退款冲销，单项可能小于0或大于100%。显示保留一位小数，五个已四舍五入的百分数可能合计99.9%或100.1%，应以未舍入金额闭合校验。

## 6. 行保留条件与渠道

最终只保留：

```sql
coalesce(promit_amount, 0) <> 0
or coalesce(refund_amount, 0) <> 0
```

因此 2740 是有净营收或退款的标准订单结果，不输出金额全部为 0 的组合。

渠道先应用当前青橙具名规则（含 IP 退费优先、本地化河南、表单浙江/江苏、私域裂变、公域自然流、内部图书和 SEC 内部未加好友）；未命中时保留真实来源：一级取非空 `channel_name_1`，二级依次取 `channel_name_3 / channel_name_2 / channel_name_1`。真正无来源才使用既有 `未知`，不虚构渠道。该兜底只属于 2740，不自动改写 2064 过程维度契约或 2460 口径。

## 7. 2026-10-22 上线验收

- 当前生产 SQL SHA-256：c94974bdf7e3fe5aba809e4a565a064214e245acae1ad648cd2f6251bb21db48；通过 operator 回读保存 SQL 后同步，当前源仅保留稳定 canonical 路径。
- 同一 `dt=20261022 / hour=18`，原金额口径与修复结果逐交易日核对 144 天，行数和收入/退款/净收款差额均为0；23个期次的两套五桶金额均闭合。
- Query `1650777519` 验证416个期次/二级渠道组合、12个金额字段；常规周序号修正前后在 SQL 复算中一致。
- Data Center preview `1650780657` 返回19列；新抽数 `177874097` 于20:53:25开始、20:53:29结束，4秒，状态 `SUCCESS`。
- 已发布主透视表全期、当前期、暑期历史期、边界期及渠道共11个切片，逐渠道金额与10项占比均匹配复算；副透视表当前期净收款和总退款一致；显示字段及10个公式不变。
- CTE由26减至22、JOIN由17减至12，移除与最终结果无关的完课/退4/订单变更链路；没有靠删财务记录提速。

## 8. 历史验证记录（非当前结果）

下表仅保留 2026-07-29 当时快照的验证记录，不作为现行归期或金额基线。

| 期次 | 净营收 | 正数退款 |
|---|---:|---:|
| `20260710期` | 3,704,157.93 | 418,871.57 |
| `20260716期` | 2,362,957.14 | 323,155.67 |
| `20260722期` | 2,316,801.90 | 200,325.09 |
| `20260728期` | 938,218.35 | 205,411.65 |

- 共 46 个 `qici + channel_1 + channel_2` 组合。
- 与同版标准订单集逐组合比较，净营收和退款最大差额均为 `0.00`。
- 所有组合的净营收桶与退款桶闭合差均为 `0.00`。
- `20260803期`、`20260808期` 在该历史验证时尚无非零标准订单金额行，不能据此推断当前仍无数据。
