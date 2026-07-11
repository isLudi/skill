# 团队转化完成度-青橙 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3872626876332130305`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3872626876332130305&sourceType=1`
- profile 时间：2026-07-11 09:59:58
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\青橙项目部\团队转化完成度-青橙\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 10 |
| `value_unit_count` | 8 |
| `data_ready_unit_count` | 7 |
| `analytic_unit_count` | 6 |
| `analytic_data_ready_unit_count` | 6 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | qici | 430609 | 1 | 3 |
| 月 | month | 414311 | 1 | 3 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3872636709627731969 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 文本框 | unit_3884690273524596737 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 全局筛选器 | public_filter_relation_3884310637094973441 | public_filter_relation |  |  | filter_relation |  |
| 小组-期_退4 | unit_3884268636652077057 | u_pivot | 2680 团队完成度【期】 | page=50<br>download=1 | data_ready | task=1459212402,1459212401<br>rows=22<br>total=22 |
| 大组-期_退4 | unit_3884652049659666436 | u_pivot | 2680 团队完成度【期】 | page=50<br>download=1 | data_ready | task=1459212412,1459212411<br>rows=7<br>total=7 |
| 学部-期_退4 | unit_3884652097619013635 | u_pivot | 2680 团队完成度【期】 | page=50<br>download=1 | data_ready | task=1459212417,1459212416<br>rows=2<br>total=2 |
| 全局筛选器 | public_filter_relation_3884310962329395200 | public_filter_relation |  |  | filter_relation |  |
| 小组-月 | unit_3872631539138375680 | u_pivot | 2677 团队完成度【月】 | page=50<br>download=1 | data_ready | task=1459212445,1459212444<br>rows=22<br>total=22 |
| 大组-月 | unit_3884667936917241860 | u_pivot | 2677 团队完成度【月】 | page=50<br>download=1 | data_ready | task=1459212456,1459212455<br>rows=8<br>total=8 |
| 学部-月 | unit_3884668794603847684 | u_pivot | 2677 团队完成度【月】 | page=50<br>download=1 | data_ready | task=1459212507,1459212505<br>rows=2<br>total=2 |

## 5. 分析单元字段结构

### 小组-期_退4

- unit_id：`unit_3884268636652077057`；类型：`u_pivot`；模型：`2680` / 团队完成度【期】
- 刷新：data_ready；task_ids：`1459212402,1459212401`；行数：22；序列：0 / 0 点
- 单元筛选字段：xiaozu（id=414770）

### 大组-期_退4

- unit_id：`unit_3884652049659666436`；类型：`u_pivot`；模型：`2680` / 团队完成度【期】
- 刷新：data_ready；task_ids：`1459212412,1459212411`；行数：7；序列：0 / 0 点

### 学部-期_退4

- unit_id：`unit_3884652097619013635`；类型：`u_pivot`；模型：`2680` / 团队完成度【期】
- 刷新：data_ready；task_ids：`1459212417,1459212416`；行数：2；序列：0 / 0 点

### 小组-月

- unit_id：`unit_3872631539138375680`；类型：`u_pivot`；模型：`2677` / 团队完成度【月】
- 刷新：data_ready；task_ids：`1459212445,1459212444`；行数：22；序列：0 / 0 点
- 单元筛选字段：xiaozu（id=414316）

### 大组-月

- unit_id：`unit_3884667936917241860`；类型：`u_pivot`；模型：`2677` / 团队完成度【月】
- 刷新：data_ready；task_ids：`1459212456,1459212455`；行数：8；序列：0 / 0 点

### 学部-月

- unit_id：`unit_3884668794603847684`；类型：`u_pivot`；模型：`2677` / 团队完成度【月】
- 刷新：data_ready；task_ids：`1459212507,1459212505`；行数：2；序列：0 / 0 点
