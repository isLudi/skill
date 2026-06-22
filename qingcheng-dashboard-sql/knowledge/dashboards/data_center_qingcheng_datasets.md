# 数据中心数据集源 SQL（青橙项目部）

## 1. 来源与范围

- 同步日期：2026-06-22
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：青橙项目部目录下的全部 SQL 数据集。
- 维护方式：脚本仅保存数据中心“数据集详情”接口返回的 `executeSql` 源 SQL，不改写业务逻辑。
- SQL 存放：完整源 SQL 存放在 `resources/raw_sql`；本文件只维护数据集到 raw SQL 文件的映射。

## 2. 数据集清单

| 序号 | 数据集名称 | 数据集 ID | fileValue | subjectId | 数据源 ID | 所属路径 | 源 SQL 文件 | 行数 |
|---:|---|---|---|---|---|---|---|---:|
| 1 | `青橙个人转化` | `menu_set_3893030630962376704` | `2769` | `2759` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙个人转化 | [data_center_qingcheng_2769_20260622.sql](../../resources/raw_sql/data_center_qingcheng_2769_20260622.sql) | 573 |

## 3. 维护说明

- 若数据中心数据集顺序、名称或 SQL 发生变化，重新运行 `sync-data-center-sql --write` 刷新本文件和对应 raw SQL。
- 若需要解释字段、指标或看板口径，应在读取源 SQL 后再维护 `knowledge/tables`、`knowledge/metrics` 或专题文档；不要只凭数据集名称补口径。
- 青橙与市场顾问业务知识库相互隔离：青橙数据集只写入 `qingcheng-dashboard-sql`，市场顾问数据集只写入 `sql-query-writer-for-dashboard`。
