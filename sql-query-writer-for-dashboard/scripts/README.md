# scripts

## 物理表字段维护

本目录不再提供 PDF、图片或手工 JSON 字段解析脚本。物理表字段统一使用相邻 `usql-web-query-operator` Skill 的 `sync-datamap-fields` 命令，从天工数据地图探查并同步到 `knowledge/tables/`。

## ingest_dashboard_sql.py

从 `resources/raw_sql/` 读取历史看板 SQL，解析表、CTE、join、where、group by 和聚合指标，生成 `knowledge/dashboards/*.md` 和待确认指标文件。

```bash
python scripts/ingest_dashboard_sql.py
```

## validate_sql_rules.py

对生成 SQL 做规则校验。

```bash
python scripts/validate_sql_rules.py --sql-file examples/simple_table_exploration.sql --exploratory
```

校验内容包括完整库名、`dt`、`hour`、`limit`、`department_name` 范围限定、`group by`、字符串数字混用和知识库字段存在性。

## check_skill_integrity.py

检查 Skill 封装结构是否完整，包括入口文件、metadata、知识库目录、核心脚本、表文档结构、表索引覆盖及数据地图维护边界。

```bash
python scripts/check_skill_integrity.py
```
