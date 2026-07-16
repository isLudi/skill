# 数据中心数据集源 SQL（青橙项目部）

## 1. 来源与范围

- 最近同步计划日期：2026-07-16
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：青橙项目部目录下的全部 SQL 数据集。
- canonical SQL 使用稳定文件名；更新时间与 SHA-256 由 `semantic/current_model_bindings.json` 记录。
- 更新必须执行 `dry-run -> expected plan hash -> atomic apply -> full validation`，旧日期文件不得进入活跃知识库。

## 2. 当前数据集清单

| 序号 | 数据集名称 | 数据集 ID | model_id | subjectId | 数据源 ID | 所属路径 | canonical SQL | SQL SHA-256 | 行数 |
|---:|---|---|---|---|---|---|---|---|---:|
| 1 | `青橙-过程数据` | `menu_set_3733940369833271296` | `2064` | `2054` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙-过程数据 | [data_center_qingcheng_2064.sql](../../resources/raw_sql/data_center_qingcheng_2064.sql) | `4d75c1219cdc550485203a854328f3687e5cac43ce1ba3845cf7c4640eb38f8d` | 905 |
| 2 | `转化数据` | `menu_set_3833505841890963456` | `2460` | `2450` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/转化数据 | [data_center_qingcheng_2460.sql](../../resources/raw_sql/data_center_qingcheng_2460.sql) | `5d6286bf8cda1384467a5b2d99071ba20f4a46417967d1869c3cff8f21106e70` | 499 |
| 3 | `抖私-转化` |  | `2740` |  |  | 青橙项目部/抖私-转化 | [data_center_qingcheng_2740.sql](../../resources/raw_sql/data_center_qingcheng_2740.sql) | `ba008980d05b30c1702a88cd933e8a7533144b1bd1872ee736af7d73a3f9c704` | 235 |

## 3. 维护说明

- 默认命令只生成同步计划；Apply 必须携带完全匹配的 `--expected-plan-sha256`。
- 同一 model_id 只能覆盖稳定 canonical 文件，不能创建日期后缀副本。
- 模型替换涉及业务用途变化时，先更新 `semantic_slots` 的 current model 和看板证据，再 Apply。
- 青橙与市场顾问 current-model registry 相互隔离，不得跨域引用。
