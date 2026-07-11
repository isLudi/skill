# 过程播报文字 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3845252580183867393`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3845252580183867393&sourceType=1`
- profile 时间：2026-07-11 09:49:13
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\市场顾问数据\过程播报文字\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 4 |
| `value_unit_count` | 4 |
| `data_ready_unit_count` | 4 |
| `analytic_unit_count` | 0 |
| `analytic_data_ready_unit_count` | 0 |
| `error_count` | 0 |
| `all_analytic_units_ready` | False |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
|  |  |  |  |  |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 过程表头1 | unit_3845252836647428097 | u_text | 2054 (内部渠道)外呼过程数据 | download=0 | data_ready | task=1459208682,1459208681<br>rows=0 |
| 过程表头2 | unit_3965411005219385346 | u_text | 2054 (内部渠道)外呼过程数据 | download=0 | data_ready | task=1459208687,1459208688<br>rows=0 |
| 分析1 | unit_3845581912081747968 | u_text | 2533 过程文本数据 | download=0 | data_ready | task=1459208696,1459208695<br>rows=0 |
| 分析2 | unit_3965411778827202563 | u_text | 2533 过程文本数据 | download=0 | data_ready | task=1459208705,1459208704<br>rows=0 |

## 5. 分析单元字段结构

- 未返回可分析单元字段结构。
