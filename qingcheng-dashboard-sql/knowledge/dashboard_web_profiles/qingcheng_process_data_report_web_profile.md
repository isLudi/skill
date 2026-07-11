# 过程数据报表-青橙 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3733927793301065728`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3733927793301065728&sourceType=1`
- profile 时间：2026-07-11 09:57:30
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\青橙项目部\过程数据报表-青橙\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 10 |
| `value_unit_count` | 9 |
| `data_ready_unit_count` | 8 |
| `analytic_unit_count` | 7 |
| `analytic_data_ready_unit_count` | 7 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | qici | 275415 | 1 | 7 |
| 渠道 | channel_map_1 | 275417 |  | 7 |
| 年级 | grade_1 | 275418 |  | 7 |
| 学部 | department | 275419 |  | 7 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 文本框 | unit_3758225654486126593 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 标题图 | unit_3751144765087657984 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3751145027574013953 | public_filter_relation |  |  | filter_relation |  |
| 渠道-整体 | unit_3751299765728346112 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | data_ready | task=1459211268,1459211266<br>rows=7<br>total=7 |
| 渠道-年级 | unit_3751309023765233664 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | data_ready | task=1459211288,1459211286<br>rows=13<br>total=13 |
| 渠道-主管 | unit_3751316651509710849 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | data_ready | task=1459211333,1459211331<br>rows=55<br>total=55 |
| 二级-整体 | unit_3751349188973985793 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | data_ready | task=1459211342,1459211343<br>rows=9<br>total=9 |
| 二级-年级 | unit_3751356204584960000 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | data_ready | task=1459211356,1459211354<br>rows=16<br>total=16 |
| 二级-主管 | unit_3751364262109941760 | u_pivot | 2064 青橙-过程数据 | page=200<br>download=1 | data_ready | task=1459211364,1459211362<br>rows=59<br>total=59 |
| 伙伴数据 | unit_3751156666810601472 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | data_ready | task=1459211370,1459211369<br>rows=100<br>total=103 |

## 5. 分析单元字段结构

### 渠道-整体

- unit_id：`unit_3751299765728346112`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1459211268,1459211266`；行数：7；序列：0 / 0 点

### 渠道-年级

- unit_id：`unit_3751309023765233664`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1459211288,1459211286`；行数：13；序列：0 / 0 点

### 渠道-主管

- unit_id：`unit_3751316651509710849`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1459211333,1459211331`；行数：55；序列：0 / 0 点
- 单元筛选字段：department（id=275419）

### 二级-整体

- unit_id：`unit_3751349188973985793`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1459211342,1459211343`；行数：9；序列：0 / 0 点

### 二级-年级

- unit_id：`unit_3751356204584960000`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1459211356,1459211354`；行数：16；序列：0 / 0 点

### 二级-主管

- unit_id：`unit_3751364262109941760`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1459211364,1459211362`；行数：59；序列：0 / 0 点

### 伙伴数据

- unit_id：`unit_3751156666810601472`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1459211370,1459211369`；行数：100；序列：0 / 0 点
- 单元筛选字段：grade_1（id=275418）、channel_map_2（id=281834）
