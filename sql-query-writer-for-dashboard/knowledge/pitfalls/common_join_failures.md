# 常见 JOIN 断裂排查速查表

## 1. cost 表 → GMV 目标全为 0

**症状**：`gl_gl` / `cb_cb` 始终为 0，GMV 目标 = 0。

**根因**：`temp_table.dingxi01_cost.grade = '0'` 为全年级通配标记，不等于看板 `grade_1` 的具体年级值（'高一'、'初二'等）。

**排查**：
1. `select distinct grade from temp_table.dingxi01_cost where qici > '<期次>'` → 观察是否大量 `grade = '0'`
2. FULL OUTER JOIN 对比 cost 表 key 与看板 zhuanhua key → 定位断裂字段

**修复**：JOIN 条件加 `or ct.grade = '0'`

```sql
left join temp_table.dingxi01_cost ct
  on ct.channel = zz.channel_map
  and (ct.grade = zz.grade_1 or ct.grade = '0')
  and zz.period_name = ct.qici
```

**安全性**：已验证同一 `(channel, qici)` 不会同时存在 `grade='0'` 和具体年级值，不会产生行膨胀。

---

## 2. 到课表 / 自动课次 → 到课率全为 0

**症状**：应出勤人数 > 0（`lead > 0`），但 `ke_1`~`ke_6`、`v_ke_1`~`v_ke_6` 全为 0。

**优先根因**：

- 最新 `market_consultant_lead_conversion_attendance.sql` 的主课次不再由 `temp_table.dingxi01_daoke_1_6_t` 决定，而是按 `qici + channel_map_1 + grade_1` 下实际 `begin_time` 自动排序；主到课全 0 时，先检查 `learn_candidates` 是否圈到行课、`lesson_slots` 是否被低覆盖过滤、`lesson_ranked_1_6` 是否生成课 1-课 6。
- 如果只是 `manual_*` 或自动/手工对照字段异常，再检查 `temp_table.dingxi01_daoke_1_6_t` 是否覆盖特定的 `(qudao, grade, begin_time)` 组合。

**排查**：
1. 按 `qici + channel_map_1 + grade_1` 检查 `lead_user_period` 的用户数。
2. 检查 `learn_candidates` 是否有对应用户行课，时间窗口为 `qici_date - 3 day` 到 `qici_date + 4 day`。
3. 检查 `lesson_slots` 中是否有 `lesson_user_cnt` 达到阈值的开课槽位，并确认 `begin_time_slot` 是否被规范到分钟粒度。
4. 仅排查 `manual_*` 时，按 `(channel_map_1, grade_1)` LEFT JOIN daoke 手工表，查 `ke_qici_cnt = 0` 的组合，并对比看板 `begin_time` 与 daoke 表 `begin_time` 格式。

**修复**：主口径异常时优先修自动课次候选窗口、槽位过滤阈值或渠道/年级归因；manual 诊断异常时才在 daoke Excel 中补充缺失的 `(qudao, grade, begin_time)` 映射记录并重新导入 temp table。

---

## 2.1 daoke 表有渠道，但看板渠道消失

**症状**：`temp_table.dingxi01_daoke_1_6_t` 中目标期次已经维护了某个渠道，例如 `孟亚飞IP99元`，但到课看板从某期开始不再出现该渠道，或该渠道 manual 诊断字段全为 0。

**优先根因**：超长渠道 CASE 顺序问题。目标 `rule_name` 仍存在，但先被前面的宽泛分支命中，导致 `channel_map_1` 输出成别的渠道。最新主课次会按错误渠道分组排序，manual 诊断也会因 `channel_map_1 = ke.qudao` 断裂。

**已验证案例**：

- 事实表 `rule_name`：`0529期-孟亚飞ip99元-孟亚飞ip99元-初一/初二`、`0605期-孟亚飞ip99元-孟亚飞ip99元-初二/初三`
- 临时表 `qudao`：`孟亚飞IP99元` / `孟亚飞ip99元`
- 原 CASE 结果：先命中 `孟亚飞9元`
- 修复结果：将 `when lower(f.rule_name) like '%孟亚飞ip99%' then '孟亚飞IP99元'` 放到 `孟亚飞9元` 宽泛规则之前

**排查**：

1. 查 daoke 表目标期次是否维护目标 `qudao`：

```sql
select
    t.qici,
    t.qudao,
    t.grade,
    t.begin_time,
    t.ke_1,
    count(*) as cnt
from temp_table.dingxi01_daoke_1_6_t t
where t.qici in ('<目标期次>')
  and t.qudao like '%<渠道关键词>%'
group by
    t.qici,
    t.qudao,
    t.grade,
    t.begin_time,
    t.ke_1
limit 1000;
```

2. 查事实表同期期次的 `rule_name` 与渠道画像字段，并模拟现有 CASE 的输出。
3. 如果目标记录被归到相邻渠道，优先调整 CASE 顺序；不要只在 CASE 末尾追加新分支。

---

## 3. grade_1 导致 JOIN 断裂

**症状**：某年级数据在到课/成本看板中完全缺失。

**根因**：
- `grade_1` CASE 遗漏年级分支（如缺失"初一"分支）
- ELSE 分支的 `lead_purchase_intention_level2_category_name` 取值与临时表 grade 命名不一致（如"初级" vs "初一"、"七年级" vs "初一"）

**排查**：FULL OUTER JOIN 对比 `data.grade_1` 与 `temp_table.grade`。

**修复**：
1. 优先在 CASE 中补充 `rule_name` 提取分支
2. 如仍有断裂，加命名映射兼容

---

## 4. 架构归属错位（截面 vs 虚拟）

**症状**：顾问数据不出现在预期主管/部门下，但 `lead > 0`。

**根因**：主表 `virtual_*` 字段（最新虚拟架构）与 `section_assign_*` 字段（截面时点架构）归属于不同时点，转岗顾问出现不一致。

**排查**：对比顾问的 `virtual_leader_email_name` vs `section_assign_employee_third_level_department_name`。

**修复**：展示主管/经理 → 优先用 `dingxi01_jiagou_db`（按期次维护），`dingxi01_jiagou_zx`（在职架构），替代主表 `virtual_*` 字段。

---

## 4.1 运营侧个人数据 2293 透视表绑定事实宽表旧架构

**症状**：运营侧个人数据看板中，顾问出现在错误经理/主管下。例如期次架构表和员工维表均显示顾问应归属 `吴志强03`，但看板透视表仍展示在 `薛源02` 下。

**根因**：数据集最终层如果使用 `select zz.*`，会把中间层事实宽表字段 `zz.jingli`、`zz.zhuguan` 原样输出。BI 透视表字段配置通常绑定输出字段名 `jingli` / `zhuguan`，因此即使后面另起别名输出 `zx.jingli as jingli_11`，看板仍会优先使用原 `jingli` 字段，导致展示事实宽表 `virtual_leader_email_name` 的旧架构。

**排查**：

1. 检查 raw SQL 最终层是否出现 `select zz.*`，且又额外输出 `zx.jingli as jingli_11`、`zx.xiaozu` 等字段。
2. 查询 `temp_table.dingxi01_jiagou_db` 的 `qici + employee_email_name`，确认期次架构。
3. 查询 `temp_table.dingxi01_jiagou_zx` 的 `employee_email_name`，确认当前在职架构。
4. 查询 `finance_dw.dim_finance_employee_df` 的 `leader_employee_email_name` 链路，确认 HR 直属上级链路。

**修复**：

最终输出层显式列出字段，不再直接输出 `zz.jingli` / `zz.zhuguan`：

```sql
coalesce(jg.jingli, zx.jingli, zz.jingli) as jingli,
coalesce(jg.xiaozu, zx.xiaozu, zz.zhuguan) as zhuguan,
coalesce(jg.xiaozu, zx.xiaozu, zz.zhuguan) as xiaozu,
coalesce(jg.jingli, zx.jingli, zz.jingli) as jingli_11
```

优先级固定为：期次架构表 `temp_table.dingxi01_jiagou_db` > 当前在职架构表 `temp_table.dingxi01_jiagou_zx` > 事实宽表 `virtual_*` 字段。

---

## 4.2 运营侧个人数据 2293 指标被 JOIN 放大

**症状**：运营侧数据看板 2293 中，同一期次/经理/主管/顾问的退前线索、退后线索、收款、退款、净收款同步偏高。例如 `20260703期` 下某顾问的运营侧个人退款金额约为转化数据 2253 的 2 倍，且线索数也偏高。

**根因**：

- `base` 层为了补外呼指标，`call_c` 按 `user_number + lead_id + section_assign_employee_email_prefix` 聚合；如果回连主数据只用 `user_id + employee_email_prefix`，同一用户多线索会重复匹配，放大 `data.*` 中已经携带的 `lead_count`、`valid_lead_count`、收款和退款。
- `f_call0` 如果按 `user_id + account_id + employee_email_name` 聚合，但回连只用 `user_id + employee_email_name`，也会产生重复。
- `zhuanhua` 已按展示粒度聚合后，最终层如果直接 join 原始 `temp_table.dingxi01_cost` 或 `temp_table.dingxi01_jiagou_db`，这些表 key 不唯一会再次放大所有 `sum` 指标。

**排查**：

1. 分别比较 `data`、`base`、`zhuanhua`、`final_result` 的 `count(*)`、`sum(lead_count)`、`sum(valid_lead_count)`、`sum(trade_refund)`。
2. 检查 `call_c` 回连是否带 `lead_id`。
3. 检查 `f_call0` 是否先聚合到 `user_id + employee_email_name`。
4. 检查 `dingxi01_cost` 是否按 `qici + channel + grade` 去重，并拆出 `grade = '0'` 通配行。
5. 检查 `dingxi01_jiagou_db` 是否先按 `qici + department + employee_email_name` 去重。

**修复**：参考 `resources/raw_sql/data_center_market_2293.sql`：

- `call_c` 回连主数据时补充 `and call_c.lead_id = data.lead_id`。
- `f_call0` 先按 `user_id, employee_email_name` 聚合，不把 `account_id` 留到回连层。
- `dingxi01_cost` 拆为 `cost_exact` 和 `cost_zero` 去重 CTE，最终用 `coalesce(ce.cost, cz.cost, 0)`。
- `dingxi01_jiagou_db` 先构造 `jiagou_period`，按 `qici + department + employee_email_name` 去重后再 join。

---

## 5. CRM 开课后转移/退费状态无法回写导致顾问仍有退前/退后线索

**症状**：CRM 前台显示某顾问当期线索已经全部转移、退费或转移给其他顾问，但运营侧看板、GMV communication 类数据集或全链路宽表仍能按该顾问拉出 `退前线索` / `退后线索` / 线索量。

**业务限制**：CRM 系统中，线索转移操作必须发生在当期开课前，数据库侧才能记录到该转移状态。若线索在当期开课后发生退费、转移顾问或其他状态变化，数据库可能无法记录该状态，因此看板/数据集中仍会保留原顾问、原期次、原架构或原归因口径下的数据。

**排查原则**：

1. 不要只用 CRM 当前前台状态否定数据库结果；先确认转移/退费发生时间是否晚于当期开课时间。
2. 不要把“当前 CRM 已转走但看板仍有数据”直接判定为 join 错误或主表脏数据；这可能是 CRM 状态记录边界造成的正常差异。
3. 排查运营侧个人数据、退前/退后线索、顾问线索归属时，应同时说明：数据库口径反映的是可记录的转移状态，不一定等于开课后 CRM 前台的最新状态。
4. 若业务需要按开课后实际转移状态重算，不能仅改 SQL join；需要确认是否存在可记录开课后转移/退费状态的独立明细表。当前知识库未确认该替代表，必须标记“待人工确认”。
