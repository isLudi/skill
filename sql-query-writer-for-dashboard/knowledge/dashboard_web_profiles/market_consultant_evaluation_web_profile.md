# 市场顾问--评优看板 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3822396843512627200`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3822396843512627200&sourceType=1`
- profile 时间：2026-06-12 16:54:20
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260612-164827\市场顾问数据\市场顾问--评优看板\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 7 |
| `value_unit_count` | 7 |
| `data_ready_unit_count` | 6 |
| `analytic_unit_count` | 5 |
| `analytic_data_ready_unit_count` | 5 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
|  |  |  |  |  |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3822397039671836672 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 文本框 | unit_3839289622860058624 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 测试渠道 | unit_3921968339834413056 | u_table | 2856 评优看板测试渠道 | page=100<br>download=0 | data_ready | task=1396385758,1396385756<br>rows=100<br>total=202 |
| 期次看板 | unit_3822404499349848065 | u_pivot | 2421 评优看板 | page=10<br>download=1 | data_ready | task=1396385865,1396385795<br>rows=10<br>total=2352 |
| 月度看板 | unit_3862869318688346115 | u_pivot | 2632 月度评优 | page=10<br>download=1 | data_ready | task=1396385940,1396385936<br>rows=10<br>total=869 |
| 季度看板 | unit_3865819236965679107 | u_pivot | 2643 季度评优 | page=10<br>download=1 | data_ready | task=1396386004,1396385999<br>rows=10<br>total=385 |
| 年度看板 | unit_3865826671804780546 | u_pivot | 2644 半年度评优 | page=50<br>download=1 | data_ready | task=1396386037,1396386034<br>rows=50<br>total=385 |

## 5. 分析单元字段结构

### 测试渠道

- unit_id：`unit_3921968339834413056`；类型：`u_table`；模型：`2856` / 评优看板测试渠道
- 刷新：data_ready；task_ids：`1396385758,1396385756`；行数：100；序列：0 / 0 点
- 单元筛选字段：qici（id=475707）

### 期次看板

- unit_id：`unit_3822404499349848065`；类型：`u_pivot`；模型：`2421` / 评优看板
- 刷新：data_ready；task_ids：`1396385865,1396385795`；行数：10；序列：0 / 0 点
- 单元筛选字段：qici（id=364758）、employee_email_name（id=380315）

### 月度看板

- unit_id：`unit_3862869318688346115`；类型：`u_pivot`；模型：`2632` / 月度评优
- 刷新：data_ready；task_ids：`1396385940,1396385936`；行数：10；序列：0 / 0 点
- 单元筛选字段：moth（id=407355）、employee_email_name（id=407356）

### 季度看板

- unit_id：`unit_3865819236965679107`；类型：`u_pivot`；模型：`2643` / 季度评优
- 刷新：data_ready；task_ids：`1396386004,1396385999`；行数：10；序列：0 / 0 点
- 单元筛选字段：quarter（id=409848）、employee_email_name（id=409849）

### 年度看板

- unit_id：`unit_3865826671804780546`；类型：`u_pivot`；模型：`2644` / 半年度评优
- 刷新：data_ready；task_ids：`1396386037,1396386034`；行数：50；序列：0 / 0 点
- 单元筛选字段：half_year（id=409860）、employee_email_name（id=409861）
