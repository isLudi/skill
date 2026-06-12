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

## 2. daoke 表 → 到课率全为 0

**症状**：应出勤人数 > 0（`lead > 0`），但 `ke_1`~`ke_6`、`v_ke_1`~`v_ke_6` 全为 0。

**根因**：`temp_table.dingxi01_daoke_1_6_t` 未覆盖特定的 `(qudao, grade)` 组合，或 `begin_time` 不匹配。

**排查**：
1. 按 `(channel_map_1, grade_1)` LEFT JOIN daoke 表，查 `ke_qici_cnt = 0` 的组合
2. 对比看板 `begin_time` 与 daoke 表 `begin_time` 格式

**修复**：在 daoke Excel 中补充缺失的 `(qudao, grade, begin_time)` 映射记录，重新导入 temp table。

---

## 2.1 daoke 表有渠道，但看板渠道消失

**症状**：`temp_table.dingxi01_daoke_1_6_t` 中目标期次已经维护了某个渠道，例如 `孟亚飞IP99元`，但到课看板从某期开始不再出现该渠道，或该渠道到课指标全为 0。

**优先根因**：超长渠道 CASE 顺序问题。目标 `rule_name` 仍存在，但先被前面的宽泛分支命中，导致 `channel_map_1` 输出成别的渠道，后续 `dk.channel_map_1 = ke.qudao` 断裂。

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

## 5. CRM 开课后转移/退费状态无法回写导致顾问仍有退前/退后线索

**症状**：CRM 前台显示某顾问当期线索已经全部转移、退费或转移给其他顾问，但运营侧看板、GMV communication 类数据集或全链路宽表仍能按该顾问拉出 `退前线索` / `退后线索` / 线索量。

**业务限制**：CRM 系统中，线索转移操作必须发生在当期开课前，数据库侧才能记录到该转移状态。若线索在当期开课后发生退费、转移顾问或其他状态变化，数据库可能无法记录该状态，因此看板/数据集中仍会保留原顾问、原期次、原架构或原归因口径下的数据。

**排查原则**：

1. 不要只用 CRM 当前前台状态否定数据库结果；先确认转移/退费发生时间是否晚于当期开课时间。
2. 不要把“当前 CRM 已转走但看板仍有数据”直接判定为 join 错误或主表脏数据；这可能是 CRM 状态记录边界造成的正常差异。
3. 排查运营侧个人数据、退前/退后线索、顾问线索归属时，应同时说明：数据库口径反映的是可记录的转移状态，不一定等于开课后 CRM 前台的最新状态。
4. 若业务需要按开课后实际转移状态重算，不能仅改 SQL join；需要确认是否存在可记录开课后转移/退费状态的独立明细表。当前知识库未确认该替代表，必须标记“待人工确认”。
