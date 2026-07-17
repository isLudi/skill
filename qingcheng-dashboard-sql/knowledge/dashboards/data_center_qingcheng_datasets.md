# 数据中心数据集源 SQL（青橙项目部）

## 1. 来源与范围

- 最近同步计划日期：2026-07-17
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：青橙项目部目录下的全部 SQL 数据集。
- canonical SQL 使用稳定文件名；更新时间与 SHA-256 由 `semantic/current_model_bindings.json` 记录。
- 更新必须执行 `dry-run -> expected plan hash -> atomic apply -> full validation`，旧日期文件不得进入活跃知识库。

## 2. 当前数据集清单

| 序号 | 数据集名称 | 数据集 ID | model_id | subjectId | 数据源 ID | 所属路径 | canonical SQL | SQL SHA-256 | 行数 |
|---:|---|---|---|---|---|---|---|---|---:|
| 1 | `青橙到课` | `menu_set_3765823085331369984` | `2244` | `2233` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙到课 | [data_center_qingcheng_2244.sql](../../resources/raw_sql/data_center_qingcheng_2244.sql) | `dcbd66c000d3c6f0f1ccecd81c9c6271a3a5912d1434fa1d828904f5b7538561` |  |
| 2 | `青橙-过程数据` | `menu_set_3733940369833271296` | `2064` | `2054` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙-过程数据 | [data_center_qingcheng_2064.sql](../../resources/raw_sql/data_center_qingcheng_2064.sql) | `a89b41f0f9b2ba8336226d5a6c5d5b2b5bfb8388faca1f500bbaacb12ce2bfce` | 934 |
| 3 | `转化数据` | `menu_set_3833505841890963456` | `2460` | `2450` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/转化数据 | [data_center_qingcheng_2460.sql](../../resources/raw_sql/data_center_qingcheng_2460.sql) | `e137d83e0e68c5116b60e8ffaf45a58ea19229f3506f6a2c75bba46f96eb39dc` | 577 |
| 4 | `团队完成度【月】` | `menu_set_3872620822275268609` | `2677` | `2667` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【月】 | [data_center_qingcheng_2677.sql](../../resources/raw_sql/data_center_qingcheng_2677.sql) | `2c865d42bd935ccba9b1e6274369e7a978b19f04bc14d69a460920292b6aba2f` | 457 |
| 5 | `团队完成度【期】` | `menu_set_3873036408401260544` | `2680` | `2670` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【期】 | [data_center_qingcheng_2680.sql](../../resources/raw_sql/data_center_qingcheng_2680.sql) | `e9096fa3c4ae29b0159e0ee340dd3c0e4d09c6184dd1f7c42d8a5bd8da1b0317` | 456 |
| 6 | `青橙个人转化` | `menu_set_3893030630962376704` | `2769` | `2759` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙个人转化 | [data_center_qingcheng_2769.sql](../../resources/raw_sql/data_center_qingcheng_2769.sql) | `8e613de45f493058878a961d9f73f7ae4cd5185f4a331f68753dc48079704c90` | 724 |
| 7 | `抖私-转化` |  | `2740` |  |  | 青橙项目部/抖私-转化 | [data_center_qingcheng_2740.sql](../../resources/raw_sql/data_center_qingcheng_2740.sql) | `ba008980d05b30c1702a88cd933e8a7533144b1bd1872ee736af7d73a3f9c704` | 235 |

## 3. 维护说明

- 默认命令只生成同步计划；Apply 必须携带完全匹配的 `--expected-plan-sha256`。
- 同一 model_id 只能覆盖稳定 canonical 文件，不能创建日期后缀副本。
- 模型替换涉及业务用途变化时，先更新 `semantic_slots` 的 current model 和看板证据，再 Apply。
- 青橙与市场顾问 current-model registry 相互隔离，不得跨域引用。
