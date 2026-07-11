# 青橙项目部_行课报表 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3765824192103694336`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3765824192103694336&sourceType=1`
- profile 时间：2026-07-11 09:57:44
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\青橙项目部\青橙项目部_行课报表\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 6 |
| `value_unit_count` | 5 |
| `data_ready_unit_count` | 4 |
| `analytic_unit_count` | 4 |
| `analytic_data_ready_unit_count` | 4 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | qici | 310146 | 2 | 4 |
| 线索渠道 | channel_map_2 | 310148 | 顾问未加好友,SEC首期掉海,SEC未加好友, | 4 |
| 年级 | grade_1 | 310149 |  | 4 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3765824210457968640 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3765824210457968649 | public_filter_relation |  |  | filter_relation |  |
| 主管行课 | unit_3765824210457968642 | u_pivot | 2244 青橙到课 | page=100<br>download=1 | data_ready | task=1459211452,1459211451<br>rows=17<br>total=17 |
| 伙伴行课 | unit_3765824210457968645 | u_pivot | 2244 青橙到课 | page=100<br>download=1 | data_ready | task=1459211458,1459211456<br>rows=93<br>total=93 |
| 渠道部门行课 | unit_3765824210457968641 | u_pivot | 2244 青橙到课 | page=100<br>download=1 | data_ready | task=1459211462,1459211461<br>rows=8<br>total=8 |
| 渠道年级行课 | unit_3766965643325820932 | u_pivot | 2244 青橙到课 | page=100<br>download=1 | data_ready | task=1459211474,1459211473<br>rows=13<br>total=13 |

## 5. 分析单元字段结构

### 主管行课

- unit_id：`unit_3765824210457968642`；类型：`u_pivot`；模型：`2244` / 青橙到课
- 刷新：data_ready；task_ids：`1459211452,1459211451`；行数：17；序列：0 / 0 点
- 单元筛选字段：dept_2（id=311120）

### 伙伴行课

- unit_id：`unit_3765824210457968645`；类型：`u_pivot`；模型：`2244` / 青橙到课
- 刷新：data_ready；task_ids：`1459211458,1459211456`；行数：93；序列：0 / 0 点
- 单元筛选字段：dept_2（id=311120）

### 渠道部门行课

- unit_id：`unit_3765824210457968641`；类型：`u_pivot`；模型：`2244` / 青橙到课
- 刷新：data_ready；task_ids：`1459211462,1459211461`；行数：8；序列：0 / 0 点

### 渠道年级行课

- unit_id：`unit_3766965643325820932`；类型：`u_pivot`；模型：`2244` / 青橙到课
- 刷新：data_ready；task_ids：`1459211474,1459211473`；行数：13；序列：0 / 0 点
