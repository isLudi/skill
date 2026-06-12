# 青橙-渠道过程数据-天 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3910621974690701312`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3910621974690701312&sourceType=1`
- profile 时间：2026-06-12 16:59:59
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260612-164827\青橙项目部\青橙-渠道过程数据-天\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 7 |
| `value_unit_count` | 6 |
| `data_ready_unit_count` | 5 |
| `analytic_unit_count` | 4 |
| `analytic_data_ready_unit_count` | 4 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | qici | 275415 | 1 | 4 |
| 一级渠道 | channel_map_1 | 275417 |  | 4 |
| 二级渠道 | channel_map_2 | 281834 |  | 4 |
| 年级 | grade_1 | 275418 |  | 4 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 文本框 | unit_3910621992189337617 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 标题图 | unit_3910621992189337601 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3910621992189337604 | public_filter_relation |  |  | filter_relation |  |
| 渠道-整体 | unit_3910621992189337610 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | data_ready | task=1396397746,1396397743<br>rows=28<br>total=28 |
| 渠道-年级 | unit_3910621992189337611 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | data_ready | task=1396397760,1396397757<br>rows=26<br>total=26 |
| 渠道-主管 | unit_3910621992189337612 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | data_ready | task=1396397776,1396397775<br>rows=100<br>total=244 |
| 伙伴数据 | unit_3910621992189337609 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | data_ready | task=1396397807,1396397804<br>rows=100<br>total=470 |

## 5. 分析单元字段结构

### 渠道-整体

- unit_id：`unit_3910621992189337610`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1396397746,1396397743`；行数：28；序列：0 / 0 点

### 渠道-年级

- unit_id：`unit_3910621992189337611`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1396397760,1396397757`；行数：26；序列：0 / 0 点

### 渠道-主管

- unit_id：`unit_3910621992189337612`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1396397776,1396397775`；行数：100；序列：0 / 0 点
- 单元筛选字段：department（id=275419）

### 伙伴数据

- unit_id：`unit_3910621992189337609`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：data_ready；task_ids：`1396397807,1396397804`；行数：100；序列：0 / 0 点
- 单元筛选字段：grade_1（id=275418）、assign_day（id=460871）
