# 市场顾问-进量节奏 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3791961955008733184`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3791961955008733184&sourceType=1`
- profile 时间：2026-07-11 09:47:30
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\市场顾问数据\市场顾问-进量节奏\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 1 |
| `value_unit_count` | 1 |
| `data_ready_unit_count` | 1 |
| `analytic_unit_count` | 1 |
| `analytic_data_ready_unit_count` | 1 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
|  |  |  |  |  |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 分渠道进量节奏 | unit_3903063829110960129 | u_pivot | 2307 进量节奏 | page=200<br>download=0 | data_ready | task=1459207959,1459207958<br>rows=157<br>total=157 |

## 5. 分析单元字段结构

### 分渠道进量节奏

- unit_id：`unit_3903063829110960129`；类型：`u_pivot`；模型：`2307` / 进量节奏
- 刷新：data_ready；task_ids：`1459207959,1459207958`；行数：157；序列：0 / 0 点
- 单元筛选字段：group_period_name（id=321701）、qudao（id=361904）、jingli（id=361906）
