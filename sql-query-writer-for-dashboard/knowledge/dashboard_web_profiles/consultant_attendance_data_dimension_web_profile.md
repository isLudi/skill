# 到课数据-顾问维度 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3706108893345009664`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3706108893345009664&sourceType=1`
- profile 时间：2026-06-24 19:20:19
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-191824\市场顾问数据\到课数据-顾问维度\profile.json`
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
| 分渠道到课数据 | unit_3706154500070973441 | u_pivot | 1938 到课数据散装 | page=100<br>download=1 | data_ready | task=1424631449,1424631451<br>rows=3<br>total=3 |

## 5. 分析单元字段结构

### 分渠道到课数据

- unit_id：`unit_3706154500070973441`；类型：`u_pivot`；模型：`1938` / 到课数据散装
- 刷新：data_ready；task_ids：`1424631449,1424631451`；行数：3；序列：0 / 0 点
- 单元筛选字段：qici（id=298395）、department（id=257774）、channel_map_1（id=257738）、xiaozu（id=257740）、employee_email_name（id=257741）
