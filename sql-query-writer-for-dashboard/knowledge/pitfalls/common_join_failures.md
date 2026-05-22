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
