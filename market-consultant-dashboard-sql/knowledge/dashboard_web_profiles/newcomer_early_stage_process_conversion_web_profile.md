# 【新人】前期过程转化数据 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3874439982521286657`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3874439982521286657&sourceType=1`
- profile 时间：2026-08-08 18:46:03
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\dashboard-profiles\knowledge-market-20260808\市场顾问数据\【新人】前期过程转化数据\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 3 |
| `value_unit_count` | 0 |
| `data_ready_unit_count` | 0 |
| `analytic_unit_count` | 1 |
| `analytic_data_ready_unit_count` | 0 |
| `error_count` | 0 |
| `all_analytic_units_ready` | None |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 部门 | depart | 418288 | 郑州市场顾问部,五组 | 1 |
| 第几期 | x_qi_count | 419801 |  | 1 |
| 顾问 | employee_email_name | 418291 |  | 1 |
| 负责人 | jingli_1 | 418295 |  | 1 |
| 主管 | xiaozu | 418294 |  | 1 |
| 带班期次 | period_name | 418286 |  | 1 |
| 新人入营期次 | new_qici | 529602 |  | 1 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3874440144128913408 | u_material | 1 主题分析 |  | unprofiled |  |
| 全局筛选器 | public_filter_relation_3874444624579076097 | public_filter_relation |  |  | filter_relation |  |
| 新人过程-转化 | unit_3874462234150735872 | u_pivot | 2688 新人过程转化数据 | page=50<br>download=1 | unprofiled |  |

## 5. 分析单元字段结构

### 新人过程-转化

- unit_id：`unit_3874462234150735872`；类型：`u_pivot`；模型：`2688` / 新人过程转化数据
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点
