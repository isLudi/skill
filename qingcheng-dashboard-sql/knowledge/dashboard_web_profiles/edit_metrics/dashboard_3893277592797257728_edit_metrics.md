# 完成度文字播报_青 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3893277592797257728`
- dashboard_name: `完成度文字播报_青`
- domain: `qingcheng`
- captured_at: `2026-07-11 10:17:32`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `e26b9b306260fd78d1e6dfa2d9ffff41f4e6a820138a0491022338e604e8bece`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3893277592797257728&htmlId=html_3983989064151408641`
- loaded_html_id: `html_3983989064151408641`
- config_html_id: `html_3983989099400392704`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-qing-project\dashboard_3893277592797257728_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `0` / `0` / `0` / `0`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
|  |  |  | 0 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 青橙完成度文字 | `node_ocmnhazfa31` | `unit_3893277603098468352` | u_text | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=11 | False / False |

## Pivot units

- 无透视表组件；如存在文字组件，其内容见下方 Text units。
## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Filters

### Public filters

- 无公共筛选器快照。

### Component filters

- 无组件级筛选器快照。

## Text units

- `unit_3893277603098468352`: 🔈团队完成度看板已更新~<br>当前推送期次👉${430609}<br>每一次的进步都是大家跑出来战绩，祝本期爆单💰！！！
- `unit_3893277603098468352`: 🔈评优看板已更新~<br>当前推送期次👉${364758}<br>评优排名方式👉市场顾问部所有带班伙伴通排(排除主管)<br>优秀值得掌声，成长更需关注💕伙伴们上期辛苦啦~<br>昨天的最好表现是今天的最低要求，祝本期爆单💰！！！

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
