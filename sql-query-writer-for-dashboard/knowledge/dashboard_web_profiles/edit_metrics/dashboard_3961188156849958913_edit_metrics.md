# KOC播报文字 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3961188156849958913`
- dashboard_name: `KOC播报文字`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:13:34`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `25b4d699c613b797aa712befe35a5824b58b7007095c8994cae63c0d1db3c412`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3961188156849958913&htmlId=html_3983985054447169536`
- loaded_html_id: `html_3983985054447169536`
- config_html_id: `html_3983985089018605569`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3961188156849958913_edit_profile.json`
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
| 过程表头1 | `node_ocmnmz5r5a1` | `unit_3961188213791830017` | u_text | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=5 | False / False |
| 过程文字1 | `node_ocmnnaad0t1` | `unit_3961188213791830020` | u_text | node_ocllzw8twf1 /  | x=0, y=5, w=20, h=7 | False / False |
| 过程表头2 | `node_ocmnnaadyx1` | `unit_3961188213791830025` | u_text | node_ocllzw8twf1 /  | x=0, y=12, w=20, h=5 | False / False |
| 过程文字2 | `node_ocmnr8r1sm1` | `unit_3961188213791830028` | u_text | node_ocllzw8twf1 /  | x=0, y=17, w=20, h=7 | False / False |

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

- `unit_3961188213791830017`: 💎 期次：${504041}<br>💎 部门：${504105}
- `unit_3961188213791830020`: 🚨<br>${504119}
- `unit_3961188213791830028`: 🚨${504119}

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
