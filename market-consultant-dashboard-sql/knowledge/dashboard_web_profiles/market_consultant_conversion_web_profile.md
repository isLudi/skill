# 转化数据 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3767151344579387392`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3767151344579387392&sourceType=1`
- profile 时间：2026-07-11 09:47:19
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\市场顾问数据\转化数据\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 13 |
| `value_unit_count` | 12 |
| `data_ready_unit_count` | 11 |
| `analytic_unit_count` | 11 |
| `analytic_data_ready_unit_count` | 11 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期 | period_name | 311320 | 2 | 10 |
| 渠道 | channel_map | 311321 |  | 9 |
| 经理 | jingli | 311389 |  | 9 |
| 年级 | grade_1 | 349838 |  | 9 |
| 规则 | rule_name | 374091 |  | 9 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3768302365927813121 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3767176899681124353 | public_filter_relation |  |  | filter_relation |  |
| 指标卡组 | unit_3767152837735378945 | card | 2253 转化数据_市场顾问 | download=0 | data_ready | task=1459207747<br>rows=5 |
| 分学部-日度同环比 | unit_3890255989767979009 | u_table | 2742 转化各学部同比 | page=500<br>download=0 | data_ready | task=1459207749,1459207748<br>rows=19<br>total=19 |
| 渠道-部门-转化 | unit_3769948772219289601 | u_pivot | 2253 转化数据_市场顾问 | page=100<br>download=1 | data_ready | task=1459207775,1459207773<br>rows=100<br>total=113 |
| 渠道-主管-转化_副本 | unit_3923523375308914691 | u_pivot | 2253 转化数据_市场顾问 | page=100<br>download=1 | data_ready | task=1459207793,1459207792<br>rows=100<br>total=140 |
| 渠道-主管-转化 | unit_3770180547675414537 | u_pivot | 2253 转化数据_市场顾问 | page=100<br>download=1 | data_ready | task=1459207822,1459207818<br>rows=100<br>total=374 |
| 渠道-顾问-转化 | unit_3770181969476136976 | u_pivot | 2253 转化数据_市场顾问 | page=300<br>download=1 | data_ready | task=1459207841,1459207840<br>rows=300<br>total=896 |
| 渠道-部门 | unit_3770178971070095368 | u_pivot | 2253 转化数据_市场顾问 | page=100<br>download=1 | data_ready | task=1459207851,1459207850<br>rows=30<br>total=30 |
| 部门--转化 | unit_3769950646823006217 | u_pivot | 2253 转化数据_市场顾问 | page=100<br>download=1 | data_ready | task=1459207868,1459207866<br>rows=4<br>total=4 |
| 经理--转化 | unit_3770133595114242055 | u_pivot | 2253 转化数据_市场顾问 | page=100<br>download=1 | data_ready | task=1459207875,1459207874<br>rows=5<br>total=5 |
| 主管--转化 | unit_3768315793457872897 | u_pivot | 2253 转化数据_市场顾问 | page=100<br>download=1 | data_ready | task=1459207880,1459207879<br>rows=30<br>total=30 |
| 部门-个人 | unit_3912232685751894018 | u_pivot | 2253 转化数据_市场顾问 | page=500<br>download=1 | data_ready | task=1459207889,1459207887<br>rows=265<br>total=265 |

## 5. 分析单元字段结构

### 指标卡组

- unit_id：`unit_3767152837735378945`；类型：`card`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459207747`；行数：5；序列：0 / 0 点

### 分学部-日度同环比

- unit_id：`unit_3890255989767979009`；类型：`u_table`；模型：`2742` / 转化各学部同比
- 刷新：data_ready；task_ids：`1459207749,1459207748`；行数：19；序列：0 / 0 点
- 单元筛选字段：max_trade_date（id=432093）、jingli（id=432089）、xiaozu（id=432088）

### 渠道-部门-转化

- unit_id：`unit_3769948772219289601`；类型：`u_pivot`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459207775,1459207773`；行数：100；序列：0 / 0 点

### 渠道-主管-转化_副本

- unit_id：`unit_3923523375308914691`；类型：`u_pivot`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459207793,1459207792`；行数：100；序列：0 / 0 点

### 渠道-主管-转化

- unit_id：`unit_3770180547675414537`；类型：`u_pivot`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459207822,1459207818`；行数：100；序列：0 / 0 点

### 渠道-顾问-转化

- unit_id：`unit_3770181969476136976`；类型：`u_pivot`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459207841,1459207840`；行数：300；序列：0 / 0 点

### 渠道-部门

- unit_id：`unit_3770178971070095368`；类型：`u_pivot`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459207851,1459207850`；行数：30；序列：0 / 0 点

### 部门--转化

- unit_id：`unit_3769950646823006217`；类型：`u_pivot`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459207868,1459207866`；行数：4；序列：0 / 0 点

### 经理--转化

- unit_id：`unit_3770133595114242055`；类型：`u_pivot`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459207875,1459207874`；行数：5；序列：0 / 0 点

### 主管--转化

- unit_id：`unit_3768315793457872897`；类型：`u_pivot`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459207880,1459207879`；行数：30；序列：0 / 0 点
- 单元筛选字段：channel_map（id=311321）

### 部门-个人

- unit_id：`unit_3912232685751894018`；类型：`u_pivot`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459207889,1459207887`；行数：265；序列：0 / 0 点
