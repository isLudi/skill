# 过程数据报表-青橙 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3733927793301065728`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3733927793301065728&sourceType=1`
- profile 时间：2026-08-05 20:53:54
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\analysis\profile_all_qingcheng_20260805\20260805-205327-48464-2e1469f8\青橙项目部\过程数据报表-青橙\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 10 |
| `value_unit_count` | 0 |
| `data_ready_unit_count` | 0 |
| `analytic_unit_count` | 7 |
| `analytic_data_ready_unit_count` | 0 |
| `error_count` | 0 |
| `all_analytic_units_ready` | None |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | qici | 275415 | 1 | 7 |
| 渠道 | channel_map_1 | 275417 |  | 7 |
| 年级 | grade_1 | 275418 |  | 7 |
| 学部 | department | 275419 |  | 7 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 文本框 | unit_3758225654486126593 | u_text | 1 None | download=0 | unprofiled |  |
| 标题图 | unit_3751144765087657984 | u_material | 1 主题分析 |  | unprofiled |  |
| 全局筛选器 | public_filter_relation_3751145027574013953 | public_filter_relation |  |  | filter_relation |  |
| 渠道-整体 | unit_3993036395152396288 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | unprofiled |  |
| 渠道-年级 | unit_3993036430906298369 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | unprofiled |  |
| 渠道-主管 | unit_3993036466760892416 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | unprofiled |  |
| 二级渠道-整体 | unit_3991587710573936641 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | unprofiled |  |
| 二级渠道-年级 | unit_3991592130078507015 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | unprofiled |  |
| 二级渠道-主管 | unit_3991592160799137795 | u_pivot | 2064 青橙-过程数据 | page=50<br>download=1 | unprofiled |  |
| 伙伴数据 | unit_3751156666810601472 | u_pivot | 2064 青橙-过程数据 | page=100<br>download=1 | unprofiled |  |

## 5. 分析单元字段结构

### 渠道-整体

- unit_id：`unit_3993036395152396288`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点

### 渠道-年级

- unit_id：`unit_3993036430906298369`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点

### 渠道-主管

- unit_id：`unit_3993036466760892416`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点

### 二级渠道-整体

- unit_id：`unit_3991587710573936641`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点

### 二级渠道-年级

- unit_id：`unit_3991592130078507015`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点

### 二级渠道-主管

- unit_id：`unit_3991592160799137795`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点

### 伙伴数据

- unit_id：`unit_3751156666810601472`；类型：`u_pivot`；模型：`2064` / 青橙-过程数据
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点
- 单元筛选字段：grade_1（id=275418）、channel_map_2（id=281834）
