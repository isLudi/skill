# 数据中心数据集源 SQL（青橙项目部）

## 1. 来源与范围

- current-model registry 基线日期：2026-07-11；最近业务 SQL 修正：2026-07-09
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：青橙项目部目录下的全部 SQL 数据集。
- 维护方式：`sync-data-center-sql` 先生成同步计划，Apply 必须绑定精确计划哈希；每个 model_id 原子替换稳定 canonical 文件。
- SQL 存放：完整源 SQL 存放在 `resources/raw_sql/data_center_qingcheng_<model_id>.sql`；SHA-256 与 current model/语义槽位登记在 `semantic/current_model_bindings.json`。

## 2. 数据集清单

| 序号 | 数据集名称 | 数据集 ID | fileValue | subjectId | 数据源 ID | 所属路径 | 源 SQL 文件 | 行数 |
|---:|---|---|---|---|---|---|---|---:|
| 1 | `青橙-过程数据` | `menu_set_3733940369833271296` | `2064` | `2054` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙-过程数据 | [data_center_qingcheng_2064.sql](../../resources/raw_sql/data_center_qingcheng_2064.sql) | 345 |
| 2 | `转化数据` | `待补充` | `2460` | `待补充` | `待补充` | 青橙项目部 / 转化数据看板使用的 2460 数据集；本次回写未重新抓取数据中心详情元数据 | [data_center_qingcheng_2460.sql](../../resources/raw_sql/data_center_qingcheng_2460.sql) | 473 |
| 3 | `抖私-转化` | `待补充` | `2740` | `待补充` | `待补充` | 青橙项目部 / 青-抖私-转化看板当前绑定模型 | [data_center_qingcheng_2740.sql](../../resources/raw_sql/data_center_qingcheng_2740.sql) | 158 |

## 3. 维护说明

- 2026-07-09：2460 current model 已包含 `20260716期` 暑期业务日历修正，并同步修正订单侧、线索侧和当期判断短期次。
- 更新时先运行 `sync-data-center-sql --target-skill qingcheng`，审阅 `plan_sha256` 后再运行 `--write --expected-plan-sha256 <hash>`；禁止直接复制日期文件。
- 同一 model_id 只允许一个稳定 canonical 文件；跨 model_id 替代必须同时更新语义槽位并显式退役旧模型。
- 若需要解释字段、指标或看板口径，应在读取源 SQL 后再维护 `knowledge/tables`、`knowledge/metrics` 或专题文档；不要只凭数据集名称补口径。
- 青橙与市场顾问业务知识库相互隔离：青橙数据集只写入 `qingcheng-dashboard-sql`，市场顾问数据集只写入 `sql-query-writer-for-dashboard`。
