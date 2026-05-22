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

来源：`resources/raw_sql/qingcheng_conversion_raw_20260522.sql`。

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
- 如果只分析青橙线索量，应优先使用线索表的 `section_assign_employee_*` 和 `period_mapping_*` 范围；如果分析订单业绩，应同时确认业绩归属和课程范围。
