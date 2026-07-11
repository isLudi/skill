# 青-抖私-转化 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3884629814875697153`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3884629814875697153&sourceType=1`
- profile 时间：2026-07-11 10:00:26
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\青橙项目部\青-抖私-转化\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 4 |
| `value_unit_count` | 4 |
| `data_ready_unit_count` | 3 |
| `analytic_unit_count` | 2 |
| `analytic_data_ready_unit_count` | 2 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
|  |  |  |  |  |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3885623155693903872 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 文本框 | unit_3886043646744297473 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 透视表 | unit_3885634016216997889 | u_pivot | 2740 抖私-转化 | page=500<br>download=1 | data_ready | task=1459213048,1459213047<br>rows=16<br>total=16 |
| 透视表_副本 | unit_3893209576598749188 | u_pivot | 2740 抖私-转化 | page=500<br>download=1 | data_ready | task=1459213094,1459213091<br>rows=1232<br>total=154 |

## 5. 分析单元字段结构

### 透视表

- unit_id：`unit_3885634016216997889`；类型：`u_pivot`；模型：`2740` / 抖私-转化
- 刷新：data_ready；task_ids：`1459213048,1459213047`；行数：16；序列：0 / 0 点
- 单元筛选字段：qici（id=431248）、grade_list（id=431251）、channel_1（id=431249）、channel_2（id=441233）

### 透视表_副本

- unit_id：`unit_3893209576598749188`；类型：`u_pivot`；模型：`2740` / 抖私-转化
- 刷新：data_ready；task_ids：`1459213094,1459213091`；行数：1232；序列：0 / 0 点
- 维度/表头字段：渠道（id=431249）
- 单元筛选字段：qici（id=431248）、grade_list（id=431251）、channel_1（id=431249）
