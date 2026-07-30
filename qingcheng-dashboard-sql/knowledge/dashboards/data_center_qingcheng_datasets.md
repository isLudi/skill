# 数据中心数据集源 SQL（青橙项目部）

## 1. 来源与范围

- 最近同步计划日期：2026-07-29
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：青橙项目部目录下的全部 SQL 数据集。
- canonical SQL 使用稳定文件名；更新时间与 SHA-256 由 `semantic/current_model_bindings.json` 记录。
- 更新必须执行 `dry-run -> expected plan hash -> atomic apply -> full validation`，旧日期文件不得进入活跃知识库。

## 2. 当前数据集清单

| 序号 | 数据集名称 | 数据集 ID | model_id | subjectId | 数据源 ID | 所属路径 | canonical SQL | SQL SHA-256 | 行数 |
|---:|---|---|---|---|---|---|---|---|---:|
| 1 | `青橙-过程数据` | `menu_set_3733940369833271296` | `2064` | `2054` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙-过程数据 | [data_center_qingcheng_2064.sql](../../resources/raw_sql/data_center_qingcheng_2064.sql) | `a5e32e446328ca48201a314a28394dae2dbb5bf0f264071699795fe6072b500d` | 947 |
| 2 | `转化数据` | `menu_set_3833505841890963456` | `2460` | `2450` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/转化数据 | [data_center_qingcheng_2460.sql](../../resources/raw_sql/data_center_qingcheng_2460.sql) | `9cbdc5535317ec07473ef9469555dbd3ce9f1b6390ea8a3a181646e6ad4bdf5a` | 1016 |
| 3 | `青橙到课` | `menu_set_3765823085331369984` | `2244` | `2233` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙到课 | [data_center_qingcheng_2244.sql](../../resources/raw_sql/data_center_qingcheng_2244.sql) | `b2a242cc06dfb0f7962511044d59254ba005c698f7b0462ea122a3af2deb8837` | 150 |
| 4 | `团队完成度【月】` | `menu_set_3872620822275268609` | `2677` | `2667` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【月】 | [data_center_qingcheng_2677.sql](../../resources/raw_sql/data_center_qingcheng_2677.sql) | `63002dd4a1c13c23d2d0ba090f40301d29533ad09cb750bbd2d4655b01d1be08` | 459 |
| 5 | `团队完成度【期】` | `menu_set_3873036408401260544` | `2680` | `2670` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/团队完成度【期】 | [data_center_qingcheng_2680.sql](../../resources/raw_sql/data_center_qingcheng_2680.sql) | `567f2deba3e936fa2f5a79566c10ac9f0ed9b12406dffdb1f0f7dabd51e2ec08` | 458 |
| 6 | `青橙个人转化` | `menu_set_3893030630962376704` | `2769` | `2759` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/青橙个人转化 | [data_center_qingcheng_2769.sql](../../resources/raw_sql/data_center_qingcheng_2769.sql) | `26f8d27a156e92e03db5dc68036d1609b03db9ed490ed2e8988c3c3f1c774270` | 728 |
| 7 | `抖私-转化` | `menu_set_3884599059235647488` | `2740` | `2730` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部/抖私-转化 | [data_center_qingcheng_2740.sql](../../resources/raw_sql/data_center_qingcheng_2740.sql) | `d85b1f745c20935a9a29046655a05b48174b9a351bda93af4b0c5b3995f225c0` | 832 |

## 3. 维护说明

- 默认命令只生成同步计划；Apply 必须携带完全匹配的 `--expected-plan-sha256`。
- 同一 model_id 只能覆盖稳定 canonical 文件，不能创建日期后缀副本。
- 模型替换涉及业务用途变化时，先更新 `semantic_slots` 的 current model 和看板证据，再 Apply。
- 青橙与市场顾问 current-model registry 相互隔离，不得跨域引用。

## 4. 2026-07-29 转化数据与抖私转化口径对齐

### 4.1 `转化数据` / model `2460`

- `lead_map` 与 `normal_bb` 的一级、二级渠道 CASE 同步新增 `IP退费` 精确规则。规则名去除普通空格后匹配 `%青橙IP-招生退费-春春%`、`%青橙IP-招生退费-朱博士%`、`%青橙IP-招生退费-郭艺%`，二级分别输出 `春春`、`朱博士`、`郭艺`。
- 精确分支均位于宽泛 `%青橙IP%` 与 `%招生退费%` 之前；期次前缀不写死。
- 回归命中 785 条有效线索：`20260728期` 春春 182、朱博士 147；`20260803期` 春春 172、朱博士 259、郭艺 25。验证时目标规则没有标准订单金额，因此本次渠道改名未改变订单金额合计。

### 4.2 `抖私-转化` / model `2740`

- 复用 `2460` 的 `service_gmv + course_transfer_gmv` 标准订单集，不再维护独立的订单归因逻辑；仅在其上计算 `gmv_7`、`gmv_14`、`gmv_30`、`gmv_n30`、`gmv_7_h` 及对应退款分层。
- service 主表中 `transfer_in_amount` 或 `transfer_out_amount` 大于 0 的内部转移行，收入、退款、净营收和 `refund_4` 先归零；再从 2026-07-20 起补回交易时处于同一青橙顾问保护期的 B 用户课程转移正向支付。
- 团队架构由仅按员工 Join 改为 `employee_email_name + qici`，避免一名员工的多期架构行复制历史结果。
- `gmv_total = sum(promit_amount)`；退款字段保持负数展示，`refund_total = -sum(refund_amount)`。

### 4.3 数据验证与生产凭证

- 标准订单结果与 2740 均得到 46 个 `qici + channel_1 + channel_2` 组合；逐组合净营收最大差额 `0.00`，退款最大差额 `0.00`。
- 2740 每行的净营收桶与退款桶闭合差均为 `0.00`。
- 验证期次汇总：`20260710期` 净营收 3,704,157.93、退款 418,871.57；`20260716期` 净营收 2,362,957.14、退款 323,155.67；`20260722期` 净营收 2,316,801.90、退款 200,325.09；`20260728期` 净营收 938,218.35、退款 205,411.65。`20260803期`、`20260809期` 验证时尚无标准订单金额行。
- `2460` 保存后 SQL SHA-256 为 `9cbdc5535317ec07473ef9469555dbd3ce9f1b6390ea8a3a181646e6ad4bdf5a`，Preview task `1507317427`，新抽数记录 `161603508` 为 `SUCCESS`。
- `2740` 保存后 SQL SHA-256 为 `d85b1f745c20935a9a29046655a05b48174b9a351bda93af4b0c5b3995f225c0`，Preview task `1507319914`，新抽数记录 `161603511` 为 `SUCCESS`。
