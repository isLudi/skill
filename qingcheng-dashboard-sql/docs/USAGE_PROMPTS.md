# 新对话调用模板

这些模板用于在 Codex 的其他对话中明确加载青橙项目部专用 Skill。推荐直接复制“标准加载模板”，再追加具体需求。

## 1. 标准加载模板

```text
# 加载并使用 Codex Skill：qingcheng-dashboard-sql。

# Skill 路径优先使用：
C:\Users\Ludim\.codex\skills\qingcheng-dashboard-sql

# 先读取该 Skill 的 SKILL.md、metadata.json、knowledge/04_qingcheng_project_profile.md 和 knowledge/01_table_index.md，再按我的需求检索相关 knowledge/tables、knowledge/temp_tables、knowledge/metrics、knowledge/dashboards、knowledge/joins 和 knowledge/sql_patterns。

# 后续所有 SQL 都必须按青橙项目部独立口径生成：
- 只生成 Presto SQL；
- 所有物理表必须带完整库名前缀；
- 分区表必须加 dt；
- 小时表建议加 dt 和 hour；
- 探索/抽样查询必须加 limit；
- 涉及 department_name、部门、架构、项目、业务线字段时必须加青橙范围限定；
- 不得使用知识库不存在的字段；
- 不得套用市场顾问部/市场顾问部评优/市场顾问临时表/市场渠道 CASE 口径；
- 青橙临时表必须先查 knowledge/temp_tables/，没有入库时标注“临时表口径待确认”；
- 公司查询平台会将 date_add 解析为 Hive 两参数函数，禁止生成 date_add('day', n, expr) 三参数写法；日期偏移优先使用 interval；
- SQL 后必须解释使用表、临时表、字段、join key、分区条件、青橙范围限定、指标口径、是否加 limit、待确认事项。
- 除非我特别明确要求“更新/入库/维护 Skill 知识库”，否则不得修改现有 Skill 文件、knowledge 文档或 resources/raw_sql，只在对话中给出 SQL 查询语句参考。

# 我的需求是：
【在这里写青橙项目部 SQL 需求】
```

## 2. 简短加载模板

```text
请使用 qingcheng-dashboard-sql skill 处理下面的青橙项目部看板取数 SQL 需求。先检索 skill 的 knowledge，再生成或修复 Presto SQL，并按 skill 规则输出解释。

除非我特别明确要求更新 Skill 知识库，否则不要修改现有 Skill 文件，只在对话中给出 SQL 参考。

需求：
【在这里写需求】
```

## 3. 青橙看板 SQL 入库模板

```text
请加载 qingcheng-dashboard-sql skill，维护青橙项目部知识库。

资料来源：
【粘贴 SQL 或写文件路径】

请更新：
- resources/raw_sql/
- knowledge/dashboards/
- knowledge/metrics/
- knowledge/temp_tables/
- knowledge/joins/common_join_keys.md
- knowledge/joins/table_relationships.md
- knowledge/01_table_index.md
- knowledge/update_log/changelog.md

要求：
不确定的字段、库名、临时表语义、指标口径必须标记“待人工确认”，不得编造。
不得套用市场顾问部口径。
更新 changelog 时按时间正序追加到文件末尾。
```

## 4. SQL 报错修复模板

```text
请加载 qingcheng-dashboard-sql skill，按青橙项目部口径、Presto 和公司查询平台规则帮我修复 SQL 报错。

要求：
1. 先判断报错属于语法、字段、表权限、分区、范围限定、group by、类型混用还是平台解析问题；
2. 只基于青橙 skill 知识库中存在的表、临时表和字段给出修改；
3. 输出修复后的 SQL；
4. 解释修改点和仍需人工确认的青橙口径；
5. 不得引入市场顾问部专属逻辑。

错误信息：
【粘贴错误信息】

SQL：
【粘贴 SQL】
```

