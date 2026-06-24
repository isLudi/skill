# 转化数据看板 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3885764906392891392`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3885764906392891392&sourceType=1`
- profile 时间：2026-06-24 18:46:47
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-184137\青橙项目部\转化数据看板\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 12 |
| `value_unit_count` | 11 |
| `data_ready_unit_count` | 10 |
| `analytic_unit_count` | 10 |
| `analytic_data_ready_unit_count` | 10 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | qici | 408276 | 1 | 9 |
| 渠道 | channel_1 | 408280 |  | 9 |
| 年级 | grade_1 | 408277 |  | 9 |
| 学部 | dept_2 | 408282 |  | 9 |
| 大组 | dazu | 439812 |  | 9 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3885765321595432960 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3885825940437295104 | public_filter_relation |  |  | filter_relation |  |
| 指标卡组 | unit_3885824427184324609 | card | 2460 转化数据 | download=0 | data_ready | task=1424551293<br>rows=5 |
| 渠道-总 | unit_3885802565373767680 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1424551341,1424551340<br>rows=6<br>total=6 |
| 部门-总 | unit_3885799917415424001 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1424551365,1424551364<br>rows=1<br>total=1 |
| 渠道-大组 | unit_3916477914471084040 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1424551398,1424551394<br>rows=10<br>total=10 |
| 一级渠道-年级 | unit_3885804389298036736 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1424551444,1424551443<br>rows=20<br>total=20 |
| 一级渠道-主管 | unit_3885807778524864512 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1424551478,1424551474<br>rows=6<br>total=6 |
| 一级渠道-年级_副本_副本 | unit_3885809281027678208 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1424551509,1424551504<br>rows=8<br>total=8 |
| 二级渠道-年级 | unit_3885812440113995776 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1424551553,1424551550<br>rows=26<br>total=26 |
| 二级渠道-主管 | unit_3885812858531909632 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1424551602,1424551600<br>rows=8<br>total=8 |
| 伙伴数据 | unit_3885813531449008129 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1424551629,1424551626<br>rows=188<br>total=188 |

## 5. 分析单元字段结构

### 指标卡组

- unit_id：`unit_3885824427184324609`；类型：`card`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1424551293`；行数：5；序列：0 / 0 点

### 渠道-总

- unit_id：`unit_3885802565373767680`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1424551341,1424551340`；行数：6；序列：0 / 0 点

### 部门-总

- unit_id：`unit_3885799917415424001`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1424551365,1424551364`；行数：1；序列：0 / 0 点

### 渠道-大组

- unit_id：`unit_3916477914471084040`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1424551398,1424551394`；行数：10；序列：0 / 0 点

### 一级渠道-年级

- unit_id：`unit_3885804389298036736`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1424551444,1424551443`；行数：20；序列：0 / 0 点

### 一级渠道-主管

- unit_id：`unit_3885807778524864512`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1424551478,1424551474`；行数：6；序列：0 / 0 点

### 一级渠道-年级_副本_副本

- unit_id：`unit_3885809281027678208`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1424551509,1424551504`；行数：8；序列：0 / 0 点
- 单元筛选字段：channel_map_2（id=374753）

### 二级渠道-年级

- unit_id：`unit_3885812440113995776`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1424551553,1424551550`；行数：26；序列：0 / 0 点
- 单元筛选字段：channel_map_2（id=374753）

### 二级渠道-主管

- unit_id：`unit_3885812858531909632`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1424551602,1424551600`；行数：8；序列：0 / 0 点
- 单元筛选字段：channel_map_2（id=374753）

### 伙伴数据

- unit_id：`unit_3885813531449008129`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1424551629,1424551626`；行数：188；序列：0 / 0 点
- 单元筛选字段：grade_1（id=408277）、channel_map_2（id=374753）
