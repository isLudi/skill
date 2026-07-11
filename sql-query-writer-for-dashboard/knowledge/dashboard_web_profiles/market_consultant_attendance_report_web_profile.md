# 市场顾问部_行课报表 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3748410696516800512`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3748410696516800512&sourceType=1`
- profile 时间：2026-07-11 09:46:30
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\市场顾问数据\市场顾问部_行课报表\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 5 |
| `value_unit_count` | 4 |
| `data_ready_unit_count` | 3 |
| `analytic_unit_count` | 3 |
| `analytic_data_ready_unit_count` | 3 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | qici | 289670 | 2 | 3 |
| 线索渠道 | channel_map_1 | 289671 | 进校0元,训练营,未知,线索复用 | 3 |
| 年级 | grade_1 | 289672 |  | 3 |
| 规则 | rule_name | 374265 |  | 3 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3748416372584517632 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3748432894568730625 | public_filter_relation |  |  | filter_relation |  |
| 渠道年级行课 | unit_3748421949431779328 | u_pivot | 2132 (内部)到课衰减情况 | page=100<br>download=1 | data_ready | task=1459207447,1459207446<br>rows=11<br>total=11 |
| 主管行课 | unit_3748425123565043713 | u_pivot | 2132 (内部)到课衰减情况 | page=100<br>download=1 | data_ready | task=1459207453,1459207452<br>rows=23<br>total=23 |
| 伙伴行课 | unit_3748430264775114753 | u_pivot | 2132 (内部)到课衰减情况 | page=100<br>download=1 | data_ready | task=1459207459,1459207458<br>rows=100<br>total=555 |

## 5. 分析单元字段结构

### 渠道年级行课

- unit_id：`unit_3748421949431779328`；类型：`u_pivot`；模型：`2132` / (内部)到课衰减情况
- 刷新：data_ready；task_ids：`1459207447,1459207446`；行数：11；序列：0 / 0 点

### 主管行课

- unit_id：`unit_3748425123565043713`；类型：`u_pivot`；模型：`2132` / (内部)到课衰减情况
- 刷新：data_ready；task_ids：`1459207453,1459207452`；行数：23；序列：0 / 0 点
- 单元筛选字段：department（id=289674）

### 伙伴行课

- unit_id：`unit_3748430264775114753`；类型：`u_pivot`；模型：`2132` / (内部)到课衰减情况
- 刷新：data_ready；task_ids：`1459207459,1459207458`；行数：100；序列：0 / 0 点
- 单元筛选字段：xiaozu（id=289673）、channel_map_1（id=289671）
