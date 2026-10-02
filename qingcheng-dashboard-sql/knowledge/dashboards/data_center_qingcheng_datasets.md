# 数据中心数据集源 SQL（青橙项目部）

## 1. 来源与范围

- 最近同步计划日期：2026-09-29
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：青橙项目部目录下的全部 SQL 数据集。
- canonical SQL 使用稳定文件名；更新时间与 SHA-256 由 `semantic/current_model_bindings.json` 记录。
- 更新必须执行 `dry-run -> expected plan hash -> atomic apply -> full validation`，旧日期文件不得进入活跃知识库。

## 2. 当前数据集清单

| 序号 | 数据集名称 | 数据集 ID | model_id | subjectId | 数据源 ID | 所属路径 | canonical SQL | SQL SHA-256 | 行数 |
|---:|---|---|---|---|---|---|---|---|---:|
| 1 | `青橙-过程数据` | `menu_set_3733940369833271296` | `2064` | `2054` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙-过程数据 | [data_center_qingcheng_2064.sql](../../resources/raw_sql/data_center_qingcheng_2064.sql) | `f65fbd786a480d8d774ddd2c1f7fecdc1daaf3acfef1d2703ff3e77a6be60051` | 1029 |
| 2 | `转化数据` | `menu_set_3833505841890963456` | `2460` | `2450` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/转化数据 | [data_center_qingcheng_2460.sql](../../resources/raw_sql/data_center_qingcheng_2460.sql) | `b5a77e0dbc931e4257ae53c6e77c97e91fdd4d5e71feacc13d24c530b4f04005` | 1148 |
| 3 | `青橙到课` | `menu_set_3765823085331369984` | `2244` | `2233` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙到课 | [data_center_qingcheng_2244.sql](../../resources/raw_sql/data_center_qingcheng_2244.sql) | `e42bcc4a985e94dcb302ad5e3dc6c9fc23d92e5e3e8b6db5ce7d5b494f117d9c` | 149 |
| 4 | `团队完成度【月】` | `menu_set_3872620822275268609` | `2677` | `2667` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【月】 | [data_center_qingcheng_2677.sql](../../resources/raw_sql/data_center_qingcheng_2677.sql) | `d6dacf6d56615761cd572dee851709c27c5b96e6cb7bf4a7636d5395c68ef62b` | 932 |
| 5 | `团队完成度【期】` | `menu_set_3873036408401260544` | `2680` | `2670` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【期】 | [data_center_qingcheng_2680.sql](../../resources/raw_sql/data_center_qingcheng_2680.sql) | `072df742a3174378216d281746452e437b058e96c2363d1c16e1423aaa81ec7b` | 932 |
| 6 | `青橙个人转化` | `menu_set_3893030630962376704` | `2769` | `2759` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙个人转化 | [data_center_qingcheng_2769.sql](../../resources/raw_sql/data_center_qingcheng_2769.sql) | `9c8a37ca69a52ef857db95fa80cb8b31b3978eb835ecb183cdf39997dcff43aa` | 967 |
| 7 | `年季月营收情况` | `menu_set_3852443821873790977` | `2576` | `2566` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/年季月营收情况 | [data_center_qingcheng_2576.sql](../../resources/raw_sql/data_center_qingcheng_2576.sql) | `cf74bd8cb3dd0e9a17f98cc88f54e5c6990cd0fae2653dba7ff4145915423391` | 182 |
| 8 | `TMK线索转移明细` | `menu_set_4006225706505322496` | `3180` | `3168` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/TMK线索转移明细 | [data_center_qingcheng_3180.sql](../../resources/raw_sql/data_center_qingcheng_3180.sql) | `d891bd304a2ca44e896a9a7d103b149eac3d67e9837c2ec3bdbc3a721085f4f0` | 1215 |
| 9 | `青橙退费率` | `menu_set_4020793803259944960` | `3226` | `3214` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙退费率 | [data_center_qingcheng_3226.sql](../../resources/raw_sql/data_center_qingcheng_3226.sql) | `afcdd2114026f3237fafbbdc0b222731d3db338def83d56c6bb5ebc96991e2aa` | 1138 |
| 10 | `青橙分年级科目产品` | `menu_set_4020830593003642880` | `3227` | `3215` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙分年级科目产品 | [data_center_qingcheng_3227.sql](../../resources/raw_sql/data_center_qingcheng_3227.sql) | `989e46584efd1b2241ee068338acdaf323abd927aa4494459caa1da45b5b795d` | 851 |
| 11 | `青橙退费原因` | `menu_set_4023513186437709824` | `3240` | `3228` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙退费原因 | [data_center_qingcheng_3240.sql](../../resources/raw_sql/data_center_qingcheng_3240.sql) | `7a9761df07a92c6382dc00c036fdf4a9c03dcc1fc94a49396ce1356dcb1a80ca` | 826 |
| 12 | `青橙退费整体数据` | `menu_set_4023645146585849856` | `3264` | `3252` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙退费整体数据 | [data_center_qingcheng_3264.sql](../../resources/raw_sql/data_center_qingcheng_3264.sql) | `abd63e65dc7c4eeecbe5676638043a3f3f42d9a9fc32e74ec7310746ffc84c96` | 1127 |
| 13 | `抖私-转化` | `menu_set_3884599059235647488` | `2740` | `2730` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/抖私-转化 | [data_center_qingcheng_2740.sql](../../resources/raw_sql/data_center_qingcheng_2740.sql) | `bdd36eff174e7b318c4726f29c1f8d31b58b73d8d5fb48d4fb1bb81c5ff4993b` | 803 |

## 3. 维护说明

- 默认命令只生成同步计划；Apply 必须携带完全匹配的 `--expected-plan-sha256`。
- 同一 model_id 只能覆盖稳定 canonical 文件，不能创建日期后缀副本。
- 模型替换涉及业务用途变化时，先更新 `semantic_slots` 的 current model 和看板证据，再 Apply。
- 青橙与市场顾问 current-model registry 相互隔离，不得跨域引用。
