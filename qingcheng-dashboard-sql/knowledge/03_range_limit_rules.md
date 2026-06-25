# 青橙范围限定规则

## 1. 总原则

字段名包含 `department_name`，或业务语义为部门、业务线、学部、项目、小组、团队、员工架构、虚拟架构时，必须加过滤条件。

如果用户没有明确青橙范围字段取值，SQL 中使用占位符，并在解释里明确“需要替换后执行”。

## 2. 常见范围字段

| 字段名 | 默认占位符 | 说明 |
|---|---|---|
| assign_employee_first_level_department_name | `'<青橙一级部门名称>'` | 分配员工一级部门 |
| assign_employee_second_level_department_name | `'<青橙二级部门名称>'` | 分配员工二级部门 |
| assign_employee_third_level_department_name | `'<青橙三级部门/项目名称>'` | 分配员工三级部门或项目 |
| section_assign_employee_first_level_department_name | `'<青橙一级部门名称>'` | 截面分配员工一级部门 |
| section_assign_employee_second_level_department_name | `'<青橙二级部门名称>'` | 截面分配员工二级部门 |
| section_assign_employee_third_level_department_name | `'<青橙三级部门/项目名称>'` | 截面分配员工三级部门或项目 |
| performance_first_level_department_name | `'<青橙一级部门名称>'` | 业绩一级部门 |
| performance_second_level_department_name | `'<青橙二级部门名称>'` | 业绩二级部门 |
| performance_third_level_department_name | `'<青橙三级部门/项目名称>'` | 业绩三级部门或项目 |
| employee_first_level_department_name | `'<青橙一级部门名称>'` | 员工一级部门 |
| employee_second_level_department_name | `'<青橙二级部门名称>'` | 员工二级部门 |
| employee_third_level_department_name | `'<青橙三级部门/项目名称>'` | 员工三级部门或项目 |
| course_first_level_department_name | `'<课程一级部门名称>'` | 课程一级部门 |
| course_second_level_department_name | `'<课程二级部门名称>'` | 课程二级部门 |
| mapping_first_level_department_name | `'<青橙一级部门名称>'` | 映射一级部门 |
| mapping_second_level_department_name | `'<青橙二级部门名称>'` | 映射二级部门 |
| period_mapping_first_level_department_name | `'<青橙一级部门名称>'` | 期次映射一级部门 |
| period_mapping_second_level_department_name | `'<青橙二级部门名称>'` | 期次映射二级部门 |
| virtual_first_department_name | `'<青橙一级部门名称>'` | 虚拟一级部门 |
| virtual_second_department_name | `'<青橙二级部门名称>'` | 虚拟二级部门 |
| virtual_third_department_name | `'<青橙三级部门/项目名称>'` | 虚拟三级部门或项目 |
| virtual_fourth_department_name | `'<青橙小组/团队名称>'` | 虚拟四级部门或团队 |
| first_level_department_name | `'<青橙一级部门名称>'` | 一级部门 |
| second_level_department_name | `'<青橙二级部门名称>'` | 二级部门 |
| third_level_department_name | `'<青橙三级部门/项目名称>'` | 三级部门或项目 |

## 3. 已知青橙关键词

| 关键词 | 用途 | 使用建议 |
|---|---|---|
| `青橙项目部` | 青橙项目部识别关键词 | 可用于探索验证；生产 SQL 仍需结合具体字段确认 |

## 4. 不得默认复用的其他部门范围

以下范围值或语义如果出现在青橙 SQL 入库材料中，必须标注“待人工确认”：

- `市场顾问部`
- `评优`
- `参评名单`
- `人产`
- 市场顾问专属渠道 CASE
- 市场顾问专属临时表

## 5. 转化 SQL 范围口径

来源：`resources/raw_sql/qingcheng_conversion_raw_20260615.sql`。

青橙转化 SQL 使用两类范围：

| 场景 | 字段 | 取值 |
|---|---|---|
| 业绩归属 | `performance_second_level_department_name` | `'青橙项目部'` |
| 青橙线索 | `section_assign_employee_first_level_department_name` | `'H业务线'` |
| 青橙线索 | `section_assign_employee_second_level_department_name` | `'青橙项目部'` |
| 青橙线索 | `period_mapping_first_level_department_name` | `'H业务线'` |
| 课程范围 | `course_first_level_department_name` | 长白名单，包含 `H业务线` 等 |
| 课程范围 | `course_second_level_department_name` | 长白名单，包含 `青橙项目部` |

注意：

- 转化 SQL 的青橙业绩归属核心过滤是 `performance_second_level_department_name = '青橙项目部'`。
- 课程部门白名单非常长，复用时优先从 raw SQL 拷贝，不要手工删减。
- 2026-06-25 已补充课程部门白名单：一级部门新增 `CA业务线`、`创新中心`；二级部门新增 `创新学部`、`升学规划中心`、`线上考研学部`。
- 如果只分析青橙线索量，应优先使用线索表的 `section_assign_employee_*` 和 `period_mapping_*` 范围；如果分析订单业绩，应同时确认业绩归属和课程范围。

## 6. 年季月营收 SQL 范围口径

来源：`resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql`。

该 SQL 使用“员工当前/历史组织链 + 财务员工部门”双重限制：

| 场景 | 字段/表达式 | 取值 |
|---|---|---|
| 员工组织链 | `array_join(slice(split(path_name, '-'), 1, 3), '-')` | `'高途-H业务线-青橙项目部'` |
| 财务业绩表 | `employee_first_level_department_name` | `'H业务线'` |
| 财务业绩表 | `employee_second_level_department_name` | `'青橙项目部'` |
| 任职期间 | `trade_time >= begin_time and trade_time <= end_time` | 交易发生在员工属于青橙期间 |

注意：

- 该口径不同于转化 SQL 的 `performance_second_level_department_name = '青橙项目部'`。
- 该口径不同于只按最新架构表回填的看板；它会剔除交易时间不在青橙任职窗口内的记录。
- 如果 `dw.dim_employee_chain` 里 `end_time` 为空或未来时间处理不一致，可能影响在职员工记录，需确认。

## 7. 团队完成度【月/期】和个人转化 SQL 范围口径

来源：`resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql`。
期次版来源：`resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql`。
个人转化来源：`resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql`。

这些 SQL 与年季月营收类似，也使用“员工组织链 + 财务员工部门”双重限制，但组织路径更宽：

| 场景 | 字段/表达式 | 取值 |
|---|---|---|
| 员工组织链 | `path_name` | `like '高途-H业务线-青橙项目部%'` |
| 财务业绩表 | `employee_first_level_department_name` | `'H业务线'` |
| 财务业绩表 | `employee_second_level_department_name` | `'青橙项目部'` |
| 任职期间 | `trade_time >= begin_time and (end_time is null or trade_time <= end_time)` | 交易发生在员工属于青橙期间 |
| 退款课节表 | `course_first_level_department_name` | `'H业务线'` |
| 退款课节表 | `course_second_level_department_name` | `('精品班学部','菁英班学部','一对一学部')` |

注意：

- `path_name like '高途-H业务线-青橙项目部%'` 会包含青橙项目部下更多层级。
- 月度团队目标来自 `temp_table.dingxi01_qing_team_goal`，按 `month = moth` 对齐。
- 期次团队目标来自 `temp_table.dingxi01_qing_team_g_qi`，按 `qici = qici` 对齐。
- 月份来自 `temp_table.dingxi01_qing_qi_moth.moth`，不是直接从 `trade_time` 自然月截取；期次版保留该字段但最终目标 join 不依赖月份。
- 个人转化不 join 目标表，而是以 `temp_table.dingxi01_qing_team_jg` 为主表，按 `employee_email_name + qici` 合并个人业绩。
