# 过程数据--顾问维度 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3699054046816116737`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3699054046816116737&sourceType=1`
- profile 时间：2026-06-24 19:19:15
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-191824\市场顾问数据\过程数据--顾问维度\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 2 |
| `value_unit_count` | 2 |
| `data_ready_unit_count` | 2 |
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
| 文本框 | unit_3710382499028934657 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 分渠道过程数据看板 | unit_3704899273732792321 | u_pivot | 1933 散装过程数据 | page=100<br>download=1 | data_ready | task=1424629029,1424629027<br>rows=100<br>total=1226 |

## 5. 分析单元字段结构

### 分渠道过程数据看板

- unit_id：`unit_3704899273732792321`；类型：`u_pivot`；模型：`1933` / 散装过程数据
- 刷新：data_ready；task_ids：`1424629029,1424629027`；行数：100；序列：0 / 0 点
- 单元筛选字段：qici（id=256752）、department（id=277211）、channel_map_1（id=256754）、grade_1（id=256756）、xiaozu（id=256758）、employee_email_name（id=256759）
