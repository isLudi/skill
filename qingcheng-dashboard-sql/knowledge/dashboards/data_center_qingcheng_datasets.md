# 数据中心数据集源 SQL（青橙项目部）

## 1. 来源与范围

- 最近同步计划日期：2026-08-07
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：青橙项目部目录下的全部 SQL 数据集。
- canonical SQL 使用稳定文件名；更新时间与 SHA-256 由 `semantic/current_model_bindings.json` 记录。
- 更新必须执行 `dry-run -> expected plan hash -> atomic apply -> full validation`，旧日期文件不得进入活跃知识库。

## 2. 当前数据集清单

| 序号 | 数据集名称 | 数据集 ID | model_id | subjectId | 数据源 ID | 所属路径 | canonical SQL | SQL SHA-256 | 行数 |
|---:|---|---|---|---|---|---|---|---|---:|
| 1 | `青橙-过程数据` | `menu_set_3733940369833271296` | `2064` | `2054` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙-过程数据 | [data_center_qingcheng_2064.sql](../../resources/raw_sql/data_center_qingcheng_2064.sql) | `6c1cf44364b9d09b25c7363bf89857e5b599750e8126a1723f1077262d018b0e` | 947 |
| 2 | `转化数据` | `menu_set_3833505841890963456` | `2460` | `2450` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/转化数据 | [data_center_qingcheng_2460.sql](../../resources/raw_sql/data_center_qingcheng_2460.sql) | `3a451998811769b79dbc110482ab08afd03d01cd0dadcb86de414e5fd9647186` | 1016 |
| 3 | `青橙到课` | `menu_set_3765823085331369984` | `2244` | `2233` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙到课 | [data_center_qingcheng_2244.sql](../../resources/raw_sql/data_center_qingcheng_2244.sql) | `a921174d62701c9df0ff723eecdd8cf65e4fc3233d8029a0109d3b001cca5af2` | 150 |
| 4 | `团队完成度【月】` | `menu_set_3872620822275268609` | `2677` | `2667` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【月】 | [data_center_qingcheng_2677.sql](../../resources/raw_sql/data_center_qingcheng_2677.sql) | `f84f2244b9474679d1ee5e2701ae5a9968097b1c8a4088a6648754e5d25318fd` | 906 |
| 5 | `团队完成度【期】` | `menu_set_3873036408401260544` | `2680` | `2670` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【期】 | [data_center_qingcheng_2680.sql](../../resources/raw_sql/data_center_qingcheng_2680.sql) | `37e0294f01e7aa40a1c93a7f2efe7b82652a430cef866ae2aab2704bfa7e7109` | 906 |
| 6 | `青橙个人转化` | `menu_set_3893030630962376704` | `2769` | `2759` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙个人转化 | [data_center_qingcheng_2769.sql](../../resources/raw_sql/data_center_qingcheng_2769.sql) | `f4c545c9345efce20f4268b9f9b307be705e0716afbb5f07d0a243a2012c6630` | 946 |
| 7 | `TMK线索转移明细` | `menu_set_4006225706505322496` | `3180` | `3168` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/TMK线索转移明细 | [data_center_qingcheng_3180.sql](../../resources/raw_sql/data_center_qingcheng_3180.sql) | `ea422f78520ef3a6e661d43bd49db89aa637acfb144dc94dd38b7a76da4c1183` | 997 |
| 8 | `抖私-转化` | `menu_set_3884599059235647488` | `2740` | `2730` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/抖私-转化 | [data_center_qingcheng_2740.sql](../../resources/raw_sql/data_center_qingcheng_2740.sql) | `cdf02c3cef6af336b737b0e4e7f8289567abe37a6dcd49949a0f2f3fc0c9a277` | 832 |

## 3. 维护说明

- 默认命令只生成同步计划；Apply 必须携带完全匹配的 `--expected-plan-sha256`。
- 同一 model_id 只能覆盖稳定 canonical 文件，不能创建日期后缀副本。
- 模型替换涉及业务用途变化时，先更新 `semantic_slots` 的 current model 和看板证据，再 Apply。
- 青橙与市场顾问 current-model registry 相互隔离，不得跨域引用。
