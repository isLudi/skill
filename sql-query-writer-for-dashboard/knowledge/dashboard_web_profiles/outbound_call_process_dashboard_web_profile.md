# 外呼过程数据看板 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3730722176629411841`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3730722176629411841&sourceType=1`
- profile 时间：2026-06-24 19:20:38
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-191824\市场顾问数据\外呼过程数据看板\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 6 |
| `value_unit_count` | 5 |
| `data_ready_unit_count` | 4 |
| `analytic_unit_count` | 3 |
| `analytic_data_ready_unit_count` | 3 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期 | qici | 273592 | 1 | 3 |
| 部门 | department | 273596 |  | 3 |
| 线索渠道 | channel_map_1 | 273594 |  | 3 |
| 年级 | grade_1 | 273595 |  | 3 |
| 经理 | jingli | 322380 |  | 3 |
| 主管 | xiaozu | 273597 |  | 3 |
| 顾问 | employee_email_name | 273598 |  | 3 |
| 规则 | rule_name | 273593 |  | 3 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3798750134270525441 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 文本框 | unit_3798773484699615233 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 全局筛选器 | public_filter_relation_3798754154607599616 | public_filter_relation |  |  | filter_relation |  |
| 总体数据 | unit_3730781607175761920 | u_pivot | 2054 (内部渠道)外呼过程数据 | page=100<br>download=1 | data_ready | task=1424632149,1424632146<br>rows=4<br>total=4 |
| 主管维度 | unit_3798743671868997638 | u_pivot | 2054 (内部渠道)外呼过程数据 | page=200<br>download=0 | data_ready | task=1424632202,1424632199<br>rows=148<br>total=148 |
| 个人维度 | unit_3798745287165575173 | u_pivot | 2054 (内部渠道)外呼过程数据 | page=200<br>download=0 | data_ready | task=1424632260,1424632258<br>rows=200<br>total=531 |

## 5. 分析单元字段结构

### 总体数据

- unit_id：`unit_3730781607175761920`；类型：`u_pivot`；模型：`2054` / (内部渠道)外呼过程数据
- 刷新：data_ready；task_ids：`1424632149,1424632146`；行数：4；序列：0 / 0 点

### 主管维度

- unit_id：`unit_3798743671868997638`；类型：`u_pivot`；模型：`2054` / (内部渠道)外呼过程数据
- 刷新：data_ready；task_ids：`1424632202,1424632199`；行数：148；序列：0 / 0 点

### 个人维度

- unit_id：`unit_3798745287165575173`；类型：`u_pivot`；模型：`2054` / (内部渠道)外呼过程数据
- 刷新：data_ready；task_ids：`1424632260,1424632258`；行数：200；序列：0 / 0 点
