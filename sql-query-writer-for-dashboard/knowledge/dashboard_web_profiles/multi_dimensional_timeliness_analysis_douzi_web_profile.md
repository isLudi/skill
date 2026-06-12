# 多维度时效分析-抖咨 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3861041931986931712`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3861041931986931712&sourceType=1`
- profile 时间：2026-06-12 16:55:50
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260612-164827\市场顾问数据\多维度时效分析-抖咨\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 10 |
| `value_unit_count` | 9 |
| `data_ready_unit_count` | 8 |
| `analytic_unit_count` | 8 |
| `analytic_data_ready_unit_count` | 8 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | period_name | 405153 | 1 | 8 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3861068961718165504 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3861067180758081537 | public_filter_relation |  |  | filter_relation |  |
| 部门 | unit_3861063716424466433 | u_pivot | 2623 抖音私信- 分时间段 | page=300<br>download=0 | data_ready | task=1396388717,1396388718<br>rows=12<br>total=2 |
| 经理 | unit_3861063388582449154 | u_pivot | 2623 抖音私信- 分时间段 | page=300<br>download=0 | data_ready | task=1396388792,1396388791<br>rows=18<br>total=3 |
| 顾问_副本 | unit_3861061473331204097 | u_pivot | 2623 抖音私信- 分时间段 | page=300<br>download=0 | data_ready | task=1396388849,1396388851<br>rows=54<br>total=9 |
| 顾问 | unit_3861044167111950336 | u_pivot | 2623 抖音私信- 分时间段 | page=300<br>download=0 | data_ready | task=1396388928,1396388926<br>rows=198<br>total=33 |
| 部门 | unit_3861107228588707841 | u_pivot | 2625 分触达时间段--抖音咨询 | page=300<br>download=0 | data_ready | task=1396388963,1396388962<br>rows=16<br>total=2 |
| 经理 | unit_3861108524580036608 | u_pivot | 2625 分触达时间段--抖音咨询 | page=300<br>download=0 | data_ready | task=1396389006,1396389007<br>rows=24<br>total=3 |
| 主管 | unit_3861106694555324416 | u_pivot | 2625 分触达时间段--抖音咨询 | page=300<br>download=0 | data_ready | task=1396389052,1396389050<br>rows=72<br>total=9 |
| 顾问 | unit_3861088496817307649 | u_pivot | 2625 分触达时间段--抖音咨询 | page=300<br>download=0 | data_ready | task=1396389114,1396389113<br>rows=264<br>total=33 |

## 5. 分析单元字段结构

### 部门

- unit_id：`unit_3861063716424466433`；类型：`u_pivot`；模型：`2623` / 抖音私信- 分时间段
- 刷新：data_ready；task_ids：`1396388717,1396388718`；行数：12；序列：0 / 0 点
- 维度/表头字段：时间段（id=405161）

### 经理

- unit_id：`unit_3861063388582449154`；类型：`u_pivot`；模型：`2623` / 抖音私信- 分时间段
- 刷新：data_ready；task_ids：`1396388792,1396388791`；行数：18；序列：0 / 0 点
- 维度/表头字段：时间段（id=405161）

### 顾问_副本

- unit_id：`unit_3861061473331204097`；类型：`u_pivot`；模型：`2623` / 抖音私信- 分时间段
- 刷新：data_ready；task_ids：`1396388849,1396388851`；行数：54；序列：0 / 0 点
- 维度/表头字段：时间段（id=405161）

### 顾问

- unit_id：`unit_3861044167111950336`；类型：`u_pivot`；模型：`2623` / 抖音私信- 分时间段
- 刷新：data_ready；task_ids：`1396388928,1396388926`；行数：198；序列：0 / 0 点
- 维度/表头字段：时间段（id=405161）

### 部门

- unit_id：`unit_3861107228588707841`；类型：`u_pivot`；模型：`2625` / 分触达时间段--抖音咨询
- 刷新：data_ready；task_ids：`1396388963,1396388962`；行数：16；序列：0 / 0 点
- 维度/表头字段：触达时间（id=405279）

### 经理

- unit_id：`unit_3861108524580036608`；类型：`u_pivot`；模型：`2625` / 分触达时间段--抖音咨询
- 刷新：data_ready；task_ids：`1396389006,1396389007`；行数：24；序列：0 / 0 点
- 维度/表头字段：触达时间（id=405279）

### 主管

- unit_id：`unit_3861106694555324416`；类型：`u_pivot`；模型：`2625` / 分触达时间段--抖音咨询
- 刷新：data_ready；task_ids：`1396389052,1396389050`；行数：72；序列：0 / 0 点
- 维度/表头字段：触达时间（id=405279）

### 顾问

- unit_id：`unit_3861088496817307649`；类型：`u_pivot`；模型：`2625` / 分触达时间段--抖音咨询
- 刷新：data_ready；task_ids：`1396389114,1396389113`；行数：264；序列：0 / 0 点
- 维度/表头字段：触达时间（id=405279）
