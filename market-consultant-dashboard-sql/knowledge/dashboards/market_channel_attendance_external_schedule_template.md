# 市场顾问指定渠道外部课表到课模板

## 1. 定位

- 业务域：`market_consultant`
- 模板编号：M4
- 用途：已知某个渠道、期次、年级的真实开课时刻时，查询第 1—6 讲普通到课和有效到课。
- 历史 SQL：`resources/raw_sql/market_channel_attendance_external_schedule_example_20260718.sql`
- 历史结果：`runtime/chenruichun_attendance_20260619_20260710/attendance_workbook.xlsx`
- 复用指标：`knowledge/metrics/market_consultant_lead_conversion_attendance_metrics.md`

本模板不新建另一套到课指标。它只提供一种“外部课表驱动”的取数方式；普通到课仍为 `live_learn_duration > 0`，有效到课仍为 `is_valid_live_learn = 1`。

## 2. 不变量与可替换参数

### 2.1 不变量

1. 先在有效线索主表得到一行一个 `期次 + 渠道 + 年级 + 线索 + 用户 + 顾问` 的基础集合。
2. 外部课表必须整理成 `channel_label + qici + grade + lesson_no + begin_time_slot`。
3. 行课表先按 `user_number + minute(begin_time)` 聚合，再与线索用户和课表时刻关联。
4. 每一讲在用户—线索粒度取 `max(flag)`，下游按人数求和；禁止直接统计行课明细行数。
5. 到课率在最终展示粒度使用 `sum(lesson_n_attended) / sum(valid_lead)` 重算。

### 2.2 每次必须替换

| 参数 | 要求 |
|---|---|
| `channel_label` | 展示名称，可为任意本域渠道；不能沿用历史样例名称 |
| `channel_scope_predicate` | 使用当前线索字段或当前 canonical 渠道映射定义渠道范围；必须先做有界命中探查 |
| `period_list` | 目标期次列表 |
| `grade_list` | 目标年级列表 |
| `schedule_rows` | 每个渠道、期次、年级的第 1—6 讲真实开课时刻 |
| `lead_department_scope` | 线索承接组织范围 |
| `course_department_scope` | 行课课程组织范围 |
| `learn_time_window` | 覆盖全部课表时刻的左闭右开窗口 |

历史样例中的“陈瑞春”只是一次验证值，不是模板身份，也不是固定渠道契约。更换渠道时，指标、用户级压缩和分子分母逻辑保持不变，只替换以上范围参数。

## 3. QuerySpec 骨架

| 槽位 | 取值/要求 |
|---|---|
| `domain` | `market_consultant` |
| `intent` | 指定渠道按外部课表查询第 1—6 讲到课 |
| `metrics` | 有效线索、课 1—6 普通到课人数、课 1—6 有效到课人数 |
| `dimensions` | 期次、渠道、规则、年级、顾问；可选部门 |
| `time_range` | 期次列表 + 行课时间窗口 |
| `calculation_grain` | `qici + channel + grade + lead_id + user_id + employee + lesson_no` |
| `output_grain` | 一行一个 `qici + channel + grade + lead_id + user_id + employee` |
| `candidate_tables` | 市场全链路宽表、用户行课明细 |
| `join_path` | 线索用户 × 外部课表；再按 `user_id + begin_time_slot` 关联行课 |

## 4. 与 canonical 自动课次模板的选择

- 有可信的业务课表、需要严格按指定开课时刻计算：使用 M4。
- 没有外部课表、希望从真实行课槽位自动排序课 1—6：使用 `market_consultant_lead_conversion_attendance.sql`。
- 两种方法并行核对时，先在 `qici + channel + grade` 粒度比较课次槽位，再比较到课人数；不要只看最终比率。

## 5. Join 与校验门禁

- `market_consultant:join:lead_to_learning_detail` 当前仍为 `pending_confirmation`，因此 M4 是人工 SQL 模板，不允许自动编译。
- 外部课表键 `channel_label + qici + grade + lesson_no` 必须唯一；同一键有多个开课时刻时先确认补课/重播规则。
- 行课 `begin_time` 统一截到分钟；若业务课表存在秒级差异，先做分钟槽位分布探查。
- 历史样例工作簿包含 19,336 条有效线索明细，4 个期次、2 个年级和课 1—6；该规模只作验证证据，不是未来结果预期。

## 6. 不可直接复用边界

- 不能只替换 SQL 中的渠道字符串；必须同时替换渠道识别谓词、课表、组织范围和时间窗口。
- 若新渠道通过完整 `channel_map` CASE 识别，引用 `knowledge/sql_patterns/channel_mapping_case_when.md` 的当前入口，不复制旧长 CASE。
- 本模板不定义渠道归因本身；渠道范围变更后需重新检查规则命中数、用户去重数、课表覆盖率和每讲分子不超过有效线索分母。
