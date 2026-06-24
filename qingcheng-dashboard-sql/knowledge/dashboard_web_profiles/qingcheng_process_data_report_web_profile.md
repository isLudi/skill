# 过程数据报表-青橙 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3733927793301065728`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3733927793301065728&sourceType=1`
- profile 时间：2026-06-24 18:42:34
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-184137\青橙项目部\过程数据报表-青橙\profile.json`
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
| 渠道-整体 | unit_3751299765728346112 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | data_ready | task=1424540671,1424540668<br>rows=10<br>total=10 |
| 渠道-年级 | unit_3751309023765233664 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | data_ready | task=1424540714,1424540713<br>rows=15<br>total=15 |
| 渠道-主管 | unit_3751316651509710849 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | data_ready | task=1424540726,1424540725<br>rows=61<br>total=61 |
| 二级-整体 | unit_3751349188973985793 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | data_ready | task=1424540770,1424540768<br>rows=12<br>total=12 |
| 二级-年级 | unit_3751356204584960000 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | data_ready | task=1424540787,1424540788<br>rows=18<br>total=18 |
| 二级-主管 | unit_3751364262109941760 | u_pivot | 2064 青橙-过程数据 | page=200<br>download=1 | data_ready | task=1424540807,1424540803<br>rows=64<br>total=64 |
| 伙伴数据 | unit_3751156666810601472 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | data_ready | task=1424540838,1424540833<br>rows=100<br>total=126 |

## 5. 分析单元字段结构

### 渠道-整体

- unit_id：`unit_3751299765728346112`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1424540671,1424540668`；行数：10；序列：0 / 0 点

### 渠道-年级

- unit_id：`unit_3751309023765233664`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1424540714,1424540713`；行数：15；序列：0 / 0 点

### 渠道-主管

- unit_id：`unit_3751316651509710849`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1424540726,1424540725`；行数：61；序列：0 / 0 点
- 单元筛选字段：department（id=275419）

### 二级-整体

- unit_id：`unit_3751349188973985793`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1424540770,1424540768`；行数：12；序列：0 / 0 点

### 二级-年级

- unit_id：`unit_3751356204584960000`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1424540787,1424540788`；行数：18；序列：0 / 0 点

### 二级-主管

- unit_id：`unit_3751364262109941760`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1424540807,1424540803`；行数：64；序列：0 / 0 点

### 伙伴数据

- unit_id：`unit_3751156666810601472`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1424540838,1424540833`；行数：100；序列：0 / 0 点
- 单元筛选字段：grade_1（id=275418）、channel_map_2（id=281834）
