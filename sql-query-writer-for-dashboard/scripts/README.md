# scripts

## extract_pdf_to_md.py

从 `resources/raw_pdfs/` 读取 PDF，抽取文本，渲染图片型页面，生成表结构 Markdown 和 `resources/pdf_extract_report.md`。

```bash
python scripts/extract_pdf_to_md.py
python scripts/extract_pdf_to_md.py --overwrite
```

## normalize_schema_md.py

统一 `knowledge/tables/*.md` 格式，自动补充 `department_name` 强制范围限定字段，并更新 `knowledge/01_table_index.md`。

```bash
python scripts/normalize_schema_md.py
```

## import_baijia_external_knowledge.py

从百家字段目录 JSON 和 row permissions JSON 批量补全表知识库，修正已确认库名前缀，新增高频表，并更新表索引与范围限定规则。

```bash
python scripts/import_baijia_external_knowledge.py
python scripts/import_baijia_external_knowledge.py --catalog path/to/table_fields.json --permissions path/to/row_permissions.json
```

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

检查 Skill 封装结构是否完整，包括入口文件、metadata、知识库目录、核心脚本、表文档结构和表索引覆盖。

```bash
python scripts/check_skill_integrity.py
```
