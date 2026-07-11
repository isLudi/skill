# 过程数据--顾问维度 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3699054046816116737`
- dashboard_name: `过程数据--顾问维度`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:07:35`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `5619996e4411c23385ba7feb4a32e3cc3f9f547c7a120645a663464c13a3b952`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3699054046816116737&htmlId=html_3983978930195058688`
- loaded_html_id: `html_3983978930195058688`
- config_html_id: `html_3983978962785497089`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3699054046816116737_edit_profile.json`
- pivot_units / configured_fields / measures / custom_formulas: `1` / `20` / `9` / `5`

## P3 binding gate

| expected pivots | validated pivots | dataset refs | selected field refs | formula refs | component filter refs | errors |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 29 | 9 | 6 | 0 |

## Datasets

| model_id | model_name | subject_ids | pivot unit count |
|---|---|---|---:|
| `1933` | 散装过程数据 | 135210 | 1 |

## Components and layout

| title | component_id | unit_id | type | container / tab | layout | hidden / locked |
|---|---|---|---|---|---|---|
| 容器组件 | `node_dockcviv8fo1` | `` | Page |  /  |  | False / False |
|  | `node_ocllzw8twf1` | `` | RootContentNew | node_dockcviv8fo1 /  |  | False / False |
| 分渠道过程数据看板 | `node_ocmjsikfzy3` | `unit_3704899273732792321` | u_pivot | node_ocllzw8twf1 /  | x=0, y=6, w=20, h=71 | False / False |
| 文本框 | `node_ocmjy0m51d1` | `unit_3710382499028934657` | u_text | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=6 | False / False |

## Pivot units

### 分渠道过程数据看板

- unit_id: `unit_3704899273732792321`
- model: `1933` / 散装过程数据
- dimensions: 部门 / `department`; 线索渠道 / `channel_map_1`; 年级 / `grade_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; qici; department; channel_map_1; grade_1; xiaozu; employee_email_name
- measures: 带班; 好友数 / `friend_lead`; 好友率; 深沟 / `shengou`; 深沟率; 双沟 / `shuanggou`; 双沟率; AB意向 / `AB_intention_level`; AB意向占比 / `ab意向占比`
- component: `node_ocmjsikfzy3` / `PivotTable`

## Configured field meanings

| show_name | business_name / field_id | role / group | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| AB意向占比 | ab意向占比<br>`customized_953328667001880577` | custom_measure / measure | sum(${AB_intention_level})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8426545881245696"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8003058177107968"}] | 分渠道过程数据看板 |
| 双沟率 | 双沟率<br>`customized_953328667127709697` | custom_measure / measure | sum(${shuanggou})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8003058177107972"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8003058177107968"}] | 分渠道过程数据看板 |
| 好友率 | 好友率<br>`customized_953328667270316033` | custom_measure / measure | sum(${friend_lead})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8003058177107969"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8003058177107968"}] | 分渠道过程数据看板 |
| 带班 | 带班<br>`customized_953328667400339456` | custom_measure / measure | sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8003058177107968"}] | 分渠道过程数据看板 |
| 深沟率 | 深沟率<br>`customized_953328667526168576` | custom_measure / measure | sum(${shengou})/sum(${lead}) |  | [{"needBoundaryValue": false, "orgParamType": 1, "paramId": "8003058177107971"}, {"needBoundaryValue": false, "orgParamType": 1, "paramId": "8003058177107968"}] | 分渠道过程数据看板 |
| channel_map_1 | channel_map_1<br>`256754` | dimension / filter |  |  | [] | 分渠道过程数据看板 |
| department | department<br>`277211` | dimension / filter |  |  | [] | 分渠道过程数据看板 |
| employee_email_name | employee_email_name<br>`256759` | dimension / filter |  |  | [] | 分渠道过程数据看板 |
| grade_1 | grade_1<br>`256756` | dimension / filter |  |  | [] | 分渠道过程数据看板 |
| qici | qici<br>`256752` | dimension / filter |  |  | [] | 分渠道过程数据看板 |
| xiaozu | xiaozu<br>`256758` | dimension / filter |  |  | [] | 分渠道过程数据看板 |
| 主管 | xiaozu<br>`256758` | dimension / row_dimension |  |  | [] | 分渠道过程数据看板 |
| 年级 | grade_1<br>`256756` | dimension / row_dimension |  |  | [] | 分渠道过程数据看板 |
| 线索渠道 | channel_map_1<br>`256754` | dimension / row_dimension |  |  | [] | 分渠道过程数据看板 |
| 部门 | department<br>`277211` | dimension / row_dimension |  |  | [] | 分渠道过程数据看板 |
| 顾问 | employee_email_name<br>`256759` | dimension / row_dimension |  |  | [] | 分渠道过程数据看板 |
| AB意向 | AB_intention_level<br>`8426545881245696` | measure / measure | sum(8426545881245696) |  | [] | 分渠道过程数据看板 |
| 双沟 | shuanggou<br>`8003058177107972` | measure / measure | sum(8003058177107972) |  | [] | 分渠道过程数据看板 |
| 好友数 | friend_lead<br>`8003058177107969` | measure / measure | sum(8003058177107969) |  | [] | 分渠道过程数据看板 |
| 深沟 | shengou<br>`8003058177107971` | measure / measure | sum(8003058177107971) |  | [] | 分渠道过程数据看板 |

## Filters

### Public filters

- 无公共筛选器快照。

### Component filters

| unit_id | field_id | business_name | condition | filter_type |
|---|---|---|---|---|
| `unit_3704899273732792321` | `256752` | qici | in | ["detailFilter"] |
| `unit_3704899273732792321` | `256754` | channel_map_1 | in | ["detailFilter"] |
| `unit_3704899273732792321` | `256756` | grade_1 | in | ["detailFilter"] |
| `unit_3704899273732792321` | `256758` | xiaozu | in | ["detailFilter"] |
| `unit_3704899273732792321` | `256759` | employee_email_name | in | ["detailFilter"] |
| `unit_3704899273732792321` | `277211` | department | in | ["detailFilter"] |

## Text units

- `unit_3710382499028934657`: 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问  ----2.指标计算：深沟=深沟+已双沟；双沟=已双沟
- `unit_3710382499028934657`: 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问<br>2.指标计算：深沟=深沟+已双沟；双沟=已双沟

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
