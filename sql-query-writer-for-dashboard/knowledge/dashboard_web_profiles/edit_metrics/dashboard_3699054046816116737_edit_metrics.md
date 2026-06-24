# 过程数据--顾问维度 edit metrics

> Source: Taitan dashboard edit-page read-only API. Use together with the web profile and the Data Center SQL file for the same model_id.

## Snapshot

- dashboard_id: `dashboard_3699054046816116737`
- dashboard_name: `过程数据--顾问维度`
- captured_at: `2026-06-24 19:27:38`
- loaded_url: `https://udata.baijia.com/taitan/?dashboardId=dashboard_3699054046816116737&htmlId=html_3959900399253454849`
- loaded_html_id: `html_3959900399253454849`
- runtime_json: `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\edit-metrics-market-20260624\dashboard_3699054046816116737_edit_metrics_profile.json`
- pivot_units: `1`
- configured_fields: `20`
- measures: `9`
- custom_formulas: `5`
- text_notes: `2`

## Dataset SQL mapping

| model_id | model_name | one SQL file | pivot unit count |
|---|---|---|---:|
| `1933` | 散装过程数据 | - | 1 |

## Text units

- `unit_3710382499028934657`: 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问  ----2.指标计算：深沟=深沟+已双沟；双沟=已双沟
- `unit_3710382499028934657`: 1.最新数据来自两小时前；点击表头指标单元格可进行升降序选择；点击表头维度单元格可进行展开收起选择；最细筛选节点为顾问<br>2.指标计算：深沟=深沟+已双沟；双沟=已双沟

## Pivot units

### 分渠道过程数据看板

- unit_id: `unit_3704899273732792321`
- unit_type: `u_pivot`
- model: `1933` / 散装过程数据
- dimensions: 部门 / `department`; 线索渠道 / `channel_map_1`; 年级 / `grade_1`; 主管 / `xiaozu`; 顾问 / `employee_email_name`; qici; department; channel_map_1; grade_1; xiaozu; employee_email_name
- measures: 带班; 好友数 / `friend_lead`; 好友率; 深沟 / `shengou`; 深沟率; 双沟 / `shuanggou`; 双沟率; AB意向 / `AB_intention_level`; AB意向占比 / `ab意向占比`

## Metric fields

| show_name | business_name / metric id | role | formula | description | dependencies | pivot_units |
|---|---|---|---|---|---|---|
| 带班 | 带班<br>`customized_953328667400339456` | custom_measure | sum(${lead}) |  | {'paramId': '8003058177107968', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道过程数据看板 |
| 好友数 | friend_lead<br>`8003058177107969` | measure | sum(8003058177107969) |  |  | 分渠道过程数据看板 |
| 好友率 | 好友率<br>`customized_953328667270316033` | custom_measure | sum(${friend_lead})/sum(${lead}) |  | {'paramId': '8003058177107969', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8003058177107968', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道过程数据看板 |
| 深沟 | shengou<br>`8003058177107971` | measure | sum(8003058177107971) |  |  | 分渠道过程数据看板 |
| 深沟率 | 深沟率<br>`customized_953328667526168576` | custom_measure | sum(${shengou})/sum(${lead}) |  | {'paramId': '8003058177107971', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8003058177107968', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道过程数据看板 |
| 双沟 | shuanggou<br>`8003058177107972` | measure | sum(8003058177107972) |  |  | 分渠道过程数据看板 |
| 双沟率 | 双沟率<br>`customized_953328667127709697` | custom_measure | sum(${shuanggou})/sum(${lead}) |  | {'paramId': '8003058177107972', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8003058177107968', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道过程数据看板 |
| AB意向 | AB_intention_level<br>`8426545881245696` | measure | sum(8426545881245696) |  |  | 分渠道过程数据看板 |
| AB意向占比 | ab意向占比<br>`customized_953328667001880577` | custom_measure | sum(${AB_intention_level})/sum(${lead}) |  | {'paramId': '8426545881245696', 'orgParamType': 1, 'needBoundaryValue': False}<br>{'paramId': '8003058177107968', 'orgParamType': 1, 'needBoundaryValue': False} | 分渠道过程数据看板 |
