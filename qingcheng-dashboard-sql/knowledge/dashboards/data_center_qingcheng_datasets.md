# 数据中心数据集源 SQL（青橙项目部）

## 1. 来源与范围

- 同步日期：2026-06-24
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：青橙项目部目录下的全部 SQL 数据集。
- 维护方式：脚本仅保存数据中心“数据集详情”接口返回的 `executeSql` 源 SQL，不改写业务逻辑。
- SQL 存放：完整源 SQL 存放在 `resources/raw_sql`；本文件只维护数据集到 raw SQL 文件的映射。

## 2. 数据集清单

| 序号 | 数据集名称 | 数据集 ID | fileValue | subjectId | 数据源 ID | 所属路径 | 源 SQL 文件 | 行数 |
|---:|---|---|---|---|---|---|---|---:|
| 1 | `青橙-过程数据` | `menu_set_3733940369833271296` | `2064` | `2054` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙-过程数据 | [data_center_qingcheng_2064_20260624.sql](../../resources/raw_sql/data_center_qingcheng_2064_20260624.sql) | 340 |
| 2 | `青橙到课` | `menu_set_3765823085331369984` | `2244` | `2233` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙到课 | [qingcheng_daoke_raw_20260522.sql](../../resources/raw_sql/qingcheng_daoke_raw_20260522.sql) | 124 |
| 3 | `转化数据` | `menu_set_3833505841890963456` | `2460` | `2450` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/转化数据 | [data_center_qingcheng_2460_20260624.sql](../../resources/raw_sql/data_center_qingcheng_2460_20260624.sql) | 256 |
| 4 | `年季月营收情况` | `menu_set_3852443821873790977` | `2576` | `2566` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/年季月营收情况 | [qingcheng_revenue_year_quarter_month_raw_20260522.sql](../../resources/raw_sql/qingcheng_revenue_year_quarter_month_raw_20260522.sql) | 182 |
| 5 | `团队完成度【月】` | `menu_set_3872620822275268609` | `2677` | `2667` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【月】 | [qingcheng_team_completion_month_raw_20260522.sql](../../resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql) | 380 |
| 6 | `团队完成度【期】` | `menu_set_3873036408401260544` | `2680` | `2670` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【期】 | [qingcheng_team_completion_period_raw_20260522.sql](../../resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql) | 379 |
| 7 | `抖私-转化` | `menu_set_3884599059235647488` | `2740` | `2730` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/抖私-转化 | [data_center_qingcheng_2740_20260624.sql](../../resources/raw_sql/data_center_qingcheng_2740_20260624.sql) | 235 |
| 8 | `青橙个人转化` | `menu_set_3893030630962376704` | `2769` | `2759` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙个人转化 | [qingcheng_personal_conversion_raw_20260522.sql](../../resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql) | 644 |
| 9 | `转化-宽表-市场渠道` | `menu_set_3910768114507018240` | `2834` | `2822` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/转化-宽表-市场渠道 | [qingcheng_conversion_wide_table_market_channel_20260611.sql](../../resources/raw_sql/qingcheng_conversion_wide_table_market_channel_20260611.sql) | 347 |

## 3. 维护说明

- 若数据中心数据集顺序、名称或 SQL 发生变化，重新运行 `sync-data-center-sql --write` 刷新本文件和对应 raw SQL。
- 若需要解释字段、指标或看板口径，应在读取源 SQL 后再维护 `knowledge/tables`、`knowledge/metrics` 或专题文档；不要只凭数据集名称补口径。
- 青橙与市场顾问业务知识库相互隔离：青橙数据集只写入 `qingcheng-dashboard-sql`，市场顾问数据集只写入 `sql-query-writer-for-dashboard`。
