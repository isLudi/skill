# 青橙期次×渠道过程数据导出模板

## 1. 定位

- 业务域：`qingcheng`
- 模板编号：Q3
- 用途：从青橙 canonical 过程数据中筛选目标期次和渠道/规则，输出可在 Excel 或 BI 按部门、年级、主管重算的过程指标。
- 权威 SQL：`resources/raw_sql/data_center_qingcheng_2064.sql`
- 过程指标：`knowledge/metrics/qingcheng_process_data_metrics.md`
- 历史验证工作簿：`runtime/qingcheng-reports/20260710_sec_refund/青橙_20260710期_SEC招生退费_过程数据及透视表_20260716.xlsx`

Q3 不重复归档 runtime 中 921 行的全量查询。数据中心 2064 已包含 SEC 招生退费、首呼/沟通、APP、首节到课和 14 天过程字段，复用时应从当前 canonical SQL 构建过滤与展示层。

## 2. QuerySpec 骨架

| 槽位 | 取值/要求 |
|---|---|
| `domain` | `qingcheng` |
| `intent` | 青橙指定期次/渠道过程数据导出 |
| `metrics` | 有效线索、好友、首呼/沟通、8min、外呼时长/频次、APP、首节到课、14 天过程分子分母 |
| `dimensions` | 期次、规则、分配日、渠道一/二级、年级、部门/组、顾问 |
| `filters` | `qici` + `channel_map_1/channel_map_2` 或受控 `rule_name` 列表 |
| `calculation_grain` | canonical 数据集现有输出粒度 |
| `output_grain` | 明细导出保持 canonical 粒度；透视层可聚合到部门、年级、主管 |
| `candidate_tables` | 以 current model `2064` 的 source-backed SQL 为准 |
| `join_path` | 不在导出层新增 Join；需要变更底层 Join 时回到 canonical SQL 审阅 |

## 3. 过滤参数

- `qici_list`：目标业务期次，不能默认按周五推导暑期期次。
- `channel_level_1_list` / `channel_level_2_list`：优先使用已登记的青橙渠道映射。
- `rule_name_list`：仅在业务明确给出规则时使用；更换渠道不能只改规则字面量而忽略渠道映射。
- `assign_day_range`：需要按分配日限制时左闭右开。
- `organization_scope`：青橙部门、组和顾问范围。

历史 SEC 招生退费只是一组调用示例，不把 `20260710期` 或两个规则名固化为模板默认值。

## 4. 可加总字段与比率

导出层保留原始分子、分母和累计值；展示层再计算：

```text
好友率 = sum(is_friend_lead) / sum(v_lead)
APP率 = sum(is_app_denglu) / sum(v_lead)
24h首call率 = sum(first_call_in_24h) / sum(v_lead)
48h首call率 = sum(first_call_in_48h) / sum(v_lead)
首call率 = sum(first_call_cnt) / sum(v_lead)
24h沟通率 = sum(first_call_connected_in_24h) / sum(v_lead)
48h沟通率 = sum(first_call_connected_in_48h) / sum(v_lead)
沟通率 = sum(first_call_connected_cnt) / sum(v_lead)
14天首call率 = sum(first_call_cnt_14d) / sum(v_lead_14d_denominator)
14天沟通率 = sum(first_call_connected_cnt_14d) / sum(v_lead_14d_denominator)
14天8min = sum(is_long_call_14d) / sum(v_lead_14d_denominator)
14天外呼时长 = sum(call_duration_14d) / sum(v_lead_14d_denominator)
14天外呼频次 = sum(zong_call_ci_14d) / sum(v_lead_14d_denominator)
```

禁止对行级百分比求和或平均。

## 5. 历史验证与门禁

- 历史成品簿有 29 个业务结果行、221 条有效线索，并按部门、年级、主管提供聚合公式。
- 当前 canonical SQL 的 14 天字段已有线上成功抽数证据；Q3 只是调用示例，不改变 contract 状态。
- `temp_table.dingxi01_qing_daoke` 与 `temp_table.dingxi01_jiagou_db` 的来源/刷新仍有待确认边界；若更换底层课次或架构表，必须回到青橙 Join/临时表文档审阅。
- 本模板不授权修改数据中心或看板。
