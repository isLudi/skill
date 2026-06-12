# 转化数据看板 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3885764906392891392`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3885764906392891392&sourceType=1`
- profile 时间：2026-06-12 16:59:23
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260612-164827\青橙项目部\转化数据看板\profile.json`
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
| 指标卡组 | unit_3885824427184324609 | card | 2460 转化数据 | download=0 | data_ready | task=1396396336<br>rows=5 |
| 渠道-总 | unit_3885802565373767680 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1396396358,1396396357<br>rows=3<br>total=3 |
| 部门-总 | unit_3885799917415424001 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1396396382,1396396381<br>rows=4<br>total=4 |
| 渠道-大组 | unit_3916477914471084040 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1396396407,1396396408<br>rows=10<br>total=10 |
| 一级渠道-年级 | unit_3885804389298036736 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1396396426,1396396425<br>rows=5<br>total=5 |
| 一级渠道-主管 | unit_3885807778524864512 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1396396458,1396396457<br>rows=16<br>total=16 |
| 一级渠道-年级_副本_副本 | unit_3885809281027678208 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1396396500,1396396497<br>rows=9<br>total=9 |
| 二级渠道-年级 | unit_3885812440113995776 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1396396567,1396396566<br>rows=11<br>total=11 |
| 二级渠道-主管 | unit_3885812858531909632 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1396396589,1396396586<br>rows=27<br>total=27 |
| 伙伴数据 | unit_3885813531449008129 | u_pivot | 2460 转化数据 | page=500<br>download=1 | data_ready | task=1396396621,1396396617<br>rows=51<br>total=51 |

## 5. 分析单元字段结构

### 指标卡组

- unit_id：`unit_3885824427184324609`；类型：`card`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1396396336`；行数：5；序列：0 / 0 点

### 渠道-总

- unit_id：`unit_3885802565373767680`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1396396358,1396396357`；行数：3；序列：0 / 0 点

### 部门-总

- unit_id：`unit_3885799917415424001`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1396396382,1396396381`；行数：4；序列：0 / 0 点

### 渠道-大组

- unit_id：`unit_3916477914471084040`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1396396407,1396396408`；行数：10；序列：0 / 0 点

### 一级渠道-年级

- unit_id：`unit_3885804389298036736`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1396396426,1396396425`；行数：5；序列：0 / 0 点

### 一级渠道-主管

- unit_id：`unit_3885807778524864512`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1396396458,1396396457`；行数：16；序列：0 / 0 点

### 一级渠道-年级_副本_副本

- unit_id：`unit_3885809281027678208`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1396396500,1396396497`；行数：9；序列：0 / 0 点
- 单元筛选字段：channel_map_2（id=374753）

### 二级渠道-年级

- unit_id：`unit_3885812440113995776`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1396396567,1396396566`；行数：11；序列：0 / 0 点
- 单元筛选字段：channel_map_2（id=374753）

### 二级渠道-主管

- unit_id：`unit_3885812858531909632`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1396396589,1396396586`；行数：27；序列：0 / 0 点
- 单元筛选字段：channel_map_2（id=374753）

### 伙伴数据

- unit_id：`unit_3885813531449008129`；类型：`u_pivot`；模型：`2460` / 转化数据
- 刷新：data_ready；task_ids：`1396396621,1396396617`；行数：51；序列：0 / 0 点
- 单元筛选字段：grade_1（id=408277）、channel_map_2（id=374753）
