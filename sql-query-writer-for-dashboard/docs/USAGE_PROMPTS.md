# 新对话调用模板

这些模板用于在 Codex 的其他对话框中明确加载本 Skill。推荐直接复制“标准加载模板”，再追加你的具体需求。

## 1. 标准加载模板

```text
#加载并使用 Codex Skill：sql-query-writer-for-dashboard。

#Skill 路径优先使用：
C:\Users\Ludim\.codex\skills\sql-query-writer-for-dashboard

#先读取该 Skill 的 SKILL.md、metadata.json 和 knowledge/01_table_index.md，再按我的需求检索相关的 knowledge/tables、knowledge/metrics、knowledge/dashboards、knowledge/joins 和 knowledge/sql_patterns。

#后续所有 SQL 都必须按公司看板取数规则生成：
- 只生成 Presto SQL；
- 所有物理表必须带完整库名前缀；
- 分区表必须加 dt；
- 小时表建议加 dt 和 hour；
- 探索/抽样查询必须加 limit；
- 涉及 department_name、部门、架构、业务线字段时必须加范围限定；
- 不得使用知识库不存在的字段；
- 排名、比率、目标、差值等非明细粒度指标必须说明计算粒度和最终输出粒度；若输出到日维度结果中，需提示前端聚合方式，避免排名或比率被 sum 放大；
- 只有明确要求评优/参评名单/评优架构/人产口径时才使用 temp_table.dingxi01_pingyou_jg；若只需在职架构顾问，可考虑 temp_table.dingxi01_jiagou_zx，并说明口径变化；
- 公司查询平台会将 date_add 解析为 Hive 两参数函数，禁止生成 date_add('day', n, expr) 三参数写法；日期偏移优先使用 interval；
- SQL 后必须解释使用表、字段、join key、分区条件、范围限定、指标口径、是否加 limit、待确认事项。
- 除非我特别明确要求“更新/入库/维护 Skill 知识库”，否则不得修改现有 Skill 文件、knowledge 文档或 resources/raw_sql，只在对话中给出 SQL 查询语句参考。
- 撰写SQL查询语句必须给出完整代码，不能有任何遗漏，即使出现data CTE 的完整 channel_map CASE非常多的情况，也要调取历史SQL，给出全部内容。禁止使用注释让用户手动替换。

#我的需求是：
{撰写SQL查询语句，}
```

## 2. 简短加载模板

```text
请使用 sql-query-writer-for-dashboard skill 处理下面的公司内部看板取数 SQL 需求。先检索 skill 的 knowledge，再生成或修复 Presto SQL，并按 skill 规则输出解释。

除非我特别明确要求更新 Skill 知识库，否则不要修改现有 Skill 文件，只在对话中给出 SQL 参考。

需求：
【在这里写需求】
```

## 3. SQL 报错修复模板

```text
请加载 sql-query-writer-for-dashboard skill，按 Presto 和公司查询平台规则帮我修复 SQL 报错。

要求：
1. 先判断报错属于语法、字段、表权限、分区、范围限定、group by、类型混用还是平台解析问题；
2. 只基于 skill 知识库中存在的表和字段给出修改；
3. 输出修复后的 SQL；
4. 解释修改点和仍需人工确认的口径。

错误信息：
【粘贴错误信息】

SQL：
【粘贴 SQL】
```

## 4. 看板 SQL 改写模板

```text
#请加载 sql-query-writer-for-dashboard skill，并基于已有看板知识库改写 SQL。
#请优先检索：
- knowledge/dashboards/
- knowledge/metrics/
- knowledge/joins/
- resources/raw_sql/
- 相关 knowledge/tables/
#改写要求：
【写清楚要新增/删除/替换的逻辑】

#保持不变的业务逻辑：
【写清楚不能改的逻辑】

#默认只输出改写后的 SQL 参考，不更新 resources/raw_sql 或 knowledge；只有我明确说“入库/更新知识库/维护 Skill”时才可以修改 Skill 文件。
```

## 5. 知识库维护模板

```text
请加载 sql-query-writer-for-dashboard skill，更新 skill 知识库。

资料来源：
【写文件路径，例如 E:\2000_work\GAOTU\xxx.docx 或 resources/raw_sql/xxx.sql】

请更新：
- knowledge/tables/ 或 knowledge/dashboards/ 或 knowledge/metrics/
- knowledge/joins/common_join_keys.md
- knowledge/joins/table_relationships.md
- knowledge/01_table_index.md
- knowledge/update_log/changelog.md

要求：
不确定的字段、库名、指标口径必须标记“待人工确认”，不得编造。
更新 `knowledge/update_log/changelog.md` 时必须按时间正序追加到文件末尾；不要把新记录插入文件顶部。
```
