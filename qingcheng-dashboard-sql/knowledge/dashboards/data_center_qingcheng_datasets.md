# 数据中心数据集源 SQL（青橙项目部）

## 1. 来源与范围

- 最近同步计划日期：2026-09-17
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：青橙项目部目录下的全部 SQL 数据集。
- canonical SQL 使用稳定文件名；更新时间与 SHA-256 由 `semantic/current_model_bindings.json` 记录。
- 更新必须执行 `dry-run -> expected plan hash -> atomic apply -> full validation`，旧日期文件不得进入活跃知识库。

## 2. 当前数据集清单

| 序号 | 数据集名称 | 数据集 ID | model_id | subjectId | 数据源 ID | 所属路径 | canonical SQL | SQL SHA-256 | 行数 |
|---:|---|---|---|---|---|---|---|---|---:|
| 1 | `青橙-过程数据` | `menu_set_3733940369833271296` | `2064` | `2054` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙-过程数据 | [data_center_qingcheng_2064.sql](../../resources/raw_sql/data_center_qingcheng_2064.sql) | `24dcdafbe46d2e0c51c0024c9d83e533cbdb79eadadc256aa86d912c20aa882c` | 928 |
| 2 | `转化数据` | `menu_set_3833505841890963456` | `2460` | `2450` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/转化数据 | [data_center_qingcheng_2460.sql](../../resources/raw_sql/data_center_qingcheng_2460.sql) | `2a562ce7af7e54a1035d0a7de5f3af1a1008cd10cf6ad72fa13279a75bcdc54b` | 1025 |
| 3 | `青橙到课` | `menu_set_3765823085331369984` | `2244` | `2233` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙到课 | [data_center_qingcheng_2244.sql](../../resources/raw_sql/data_center_qingcheng_2244.sql) | `729c84138e8628367251dbb5d7ae26025d263f9151f1024bf7eefd9724dbbcad` | 152 |
| 4 | `团队完成度【月】` | `menu_set_3872620822275268609` | `2677` | `2667` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【月】 | [data_center_qingcheng_2677.sql](../../resources/raw_sql/data_center_qingcheng_2677.sql) | `e686520210c9b6eb7f1db5aed080a24b38fc27208252b78d9e73bb948944568c` | 932 |
| 5 | `团队完成度【期】` | `menu_set_3873036408401260544` | `2680` | `2670` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【期】 | [data_center_qingcheng_2680.sql](../../resources/raw_sql/data_center_qingcheng_2680.sql) | `a86e6542f8257ac765ac3946e187ba90800a2922a4fcc0c5e3da86e483473427` | 932 |
| 6 | `青橙个人转化` | `menu_set_3893030630962376704` | `2769` | `2759` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙个人转化 | [data_center_qingcheng_2769.sql](../../resources/raw_sql/data_center_qingcheng_2769.sql) | `ff1188881e26f2d35c2abc58d92fd81c3dcaefb2009fbf42588d29944d4c43e7` | 967 |
| 7 | `TMK线索转移明细` | `menu_set_4006225706505322496` | `3180` | `3168` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/TMK线索转移明细 | [data_center_qingcheng_3180.sql](../../resources/raw_sql/data_center_qingcheng_3180.sql) | `6f280155d5029885cf920921af408f8b393aae0ca649278cd7cf3eb1500aec4d` | 1215 |
| 8 | `抖私-转化` | `menu_set_3884599059235647488` | `2740` | `2730` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/抖私-转化 | [data_center_qingcheng_2740.sql](../../resources/raw_sql/data_center_qingcheng_2740.sql) | `53ebef574254de54e45225531c8544391259b0d47428ef6b2e7ca390932f0bb5` | 834 |

## 3. 维护说明

- 默认命令只生成同步计划；Apply 必须携带完全匹配的 `--expected-plan-sha256`。
- 同一 model_id 只能覆盖稳定 canonical 文件，不能创建日期后缀副本。
- 模型替换涉及业务用途变化时，先更新 `semantic_slots` 的 current model 和看板证据，再 Apply。
- 青橙与市场顾问 current-model registry 相互隔离，不得跨域引用。
