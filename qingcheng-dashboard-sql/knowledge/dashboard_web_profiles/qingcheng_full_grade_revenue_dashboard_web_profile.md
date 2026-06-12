# 青橙-全年级营收看板 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3865509979877412864`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3865509979877412864&sourceType=1`
- profile 时间：2026-06-12 16:57:59
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260612-164827\青橙项目部\青橙-全年级营收看板\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 9 |
| `value_unit_count` | 9 |
| `data_ready_unit_count` | 8 |
| `analytic_unit_count` | 7 |
| `analytic_data_ready_unit_count` | 7 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
|  |  |  |  |  |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3865509994020605953 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 文本框 | unit_3865509994020605956 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 月度同环比 | unit_3865509994020605966 | card | 2576 年季月营收情况 | download=0 | data_ready | task=1396393004<br>rows=5 |
| 分学部-日度同环比 | unit_3865509994020605969 | u_table | 2576 年季月营收情况 | page=500<br>download=1 | data_ready | task=1396393054,1396393052<br>rows=13<br>total=13 |
| 期次同环比 | unit_3865509994020605968 | card | 2576 年季月营收情况 | download=0 | data_ready | task=1396393081<br>rows=5 |
| 期次数据 | unit_3865509994020605954 | u_pivot | 2576 年季月营收情况 | page=100<br>download=1 | data_ready | task=1396393126,1396393125<br>rows=100<br>total=462 |
| 月度数据 | unit_3865509994020605957 | u_pivot | 2576 年季月营收情况 | page=100<br>download=1 | data_ready | task=1396393182,1396393181<br>rows=100<br>total=104 |
| 季度数据 | unit_3865509994020605961 | u_pivot | 2576 年季月营收情况 | page=100<br>download=1 | data_ready | task=1396393236,1396393235<br>rows=44<br>total=44 |
| 年度数据 | unit_3865509994020605964 | u_pivot | 2576 年季月营收情况 | page=100<br>download=1 | data_ready | task=1396393300,1396393298<br>rows=28<br>total=28 |

## 5. 分析单元字段结构

### 月度同环比

- unit_id：`unit_3865509994020605966`；类型：`card`；模型：`2576` / 年季月营收情况
- 刷新：data_ready；task_ids：`1396393004`；行数：5；序列：0 / 0 点
- 单元筛选字段：max_trade_date（id=395131）、grade_list（id=409310）

### 分学部-日度同环比

- unit_id：`unit_3865509994020605969`；类型：`u_table`；模型：`2576` / 年季月营收情况
- 刷新：data_ready；task_ids：`1396393054,1396393052`；行数：13；序列：0 / 0 点
- 单元筛选字段：max_trade_date（id=395131）、xuebu（id=396625）、dazhuguan（id=396624）

### 期次同环比

- unit_id：`unit_3865509994020605968`；类型：`card`；模型：`2576` / 年季月营收情况
- 刷新：data_ready；task_ids：`1396393081`；行数：5；序列：0 / 0 点
- 单元筛选字段：max_trade_date（id=395131）、grade_list（id=409310）

### 期次数据

- unit_id：`unit_3865509994020605954`；类型：`u_pivot`；模型：`2576` / 年季月营收情况
- 刷新：data_ready；task_ids：`1396393126,1396393125`；行数：100；序列：0 / 0 点
- 单元筛选字段：qici（id=395130）、xuebu（id=396625）、dazhuguan（id=396624）

### 月度数据

- unit_id：`unit_3865509994020605957`；类型：`u_pivot`；模型：`2576` / 年季月营收情况
- 刷新：data_ready；task_ids：`1396393182,1396393181`；行数：100；序列：0 / 0 点
- 单元筛选字段：max_year（id=395242）、max_month（id=395244）、xuebu（id=396625）、dazhuguan（id=396624）

### 季度数据

- unit_id：`unit_3865509994020605961`；类型：`u_pivot`；模型：`2576` / 年季月营收情况
- 刷新：data_ready；task_ids：`1396393236,1396393235`；行数：44；序列：0 / 0 点
- 单元筛选字段：max_year（id=395242）、max_quarter（id=395243）、xuebu（id=396625）、dazhuguan（id=396624）

### 年度数据

- unit_id：`unit_3865509994020605964`；类型：`u_pivot`；模型：`2576` / 年季月营收情况
- 刷新：data_ready；task_ids：`1396393300,1396393298`；行数：28；序列：0 / 0 点
- 单元筛选字段：max_year（id=395242）、xuebu（id=396625）、dazhuguan（id=396624）
