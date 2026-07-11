# 评优文字播报 编辑器组件与字段快照

> 来源：Taitan 看板编辑页只读 API。该快照用于组件、数据集、字段、公式和筛选器反查；未经业务契约确认，不把同名字段自动视为可编译指标。

## Snapshot

- dashboard_id: `dashboard_3839499028752805888`
- dashboard_name: `评优文字播报`
- domain: `market_consultant`
- captured_at: `2026-07-11 10:11:29`
- menu_status: `active`
- completeness: `complete`
- binding_validation: `complete`
- profile_sha256: `2129ef38073c35e154dc0b11dcb67bf77d72ea24a486cb4c5489237d061726d3`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3839499028752805888&htmlId=html_3983982973496422400`
- loaded_html_id: `html_3983982973496422400`
- config_html_id: `html_3983983007861821440`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\edit-market\dashboard_3839499028752805888_edit_profile.json`
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
| 文本框 | `node_ocmnhazfa31` | `unit_3839505972048355328` | u_text | node_ocllzw8twf1 /  | x=0, y=0, w=20, h=24 | False / False |

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

- `unit_3839505972048355328`: 🔈评优看板已更新~<br>当前推送期次👉${364758}<br>评优排名方式👉市场顾问部所有带班伙伴通排(排除主管)<br>优秀值得掌声，成长更需关注💕伙伴们上期辛苦啦~<br>昨天的最好表现是今天的最低要求，祝本期爆单💰！！！
- `unit_3839505972048355328`: 🔈评优看板已更新~<br>当前推送期次👉${364758}<br>评优排名方式👉市场顾问部所有带班伙伴通排(排除主管)<br>【一、指标说明】<br>1.完成度 (预算完成度=ROI完成度) <br>人产目标完成度=周期内净营收/周期内人产目标<br>2.退费率<br>金额退费率=周期内退费金额/周期内总营收<br>3.渠道测试<br>参与渠道测试可得分，不累计(测试1期是10分，测试10期也是10分)；<br>参与渠道测试并达成单期完成度80%以上得分，不累计(没有获得过80%以上完成度不加分，达成过1次80%以上是2分，达成10次也还是2分)<br>【二、其他说明】<br>业绩考核项👉 计算部门常规大班课营收及退费；跨部门、跨产品等不计入。<br>渠道测试👉整个市场顾问部没有打通过的新渠道定义为测试渠道，渠道历史以业务负责人及运营伙伴确认为准。<br>排名周期👉当前推送期次数据，伙伴可进行核对，如有异常，可于周六前由主管统一收集、反馈至HRBP处。月度及以上更长周期数据由各期次数据汇总得来，不再另行核对。长周期评优以集团公布评优考核周期为准，如月度TOP顾问、半年度/年度绩效考核、晋升周期等。

## Boundary

- 本文件是前端配置证据，不单独授权 SQL 编译、看板 Apply 或 Publish。
- 同名字段必须回到本业务域的 confirmed contract、权威 SQL 和 grain/range/join 证据后才能进入确定性编译。
- `incomplete` 快照不得进入 P3 design/apply 链路；`paused` 看板可用于历史反查，但默认不作为新设计目标。
