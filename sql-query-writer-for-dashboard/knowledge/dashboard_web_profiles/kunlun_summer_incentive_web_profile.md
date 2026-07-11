# 昆仑山战役-暑期激励数据看板 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3881610656431284224`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3881610656431284224&sourceType=1`
- profile 时间：2026-07-11 09:56:17
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\市场顾问数据\昆仑山战役-暑期激励数据看板\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 9 |
| `value_unit_count` | 9 |
| `data_ready_unit_count` | 8 |
| `analytic_unit_count` | 6 |
| `analytic_data_ready_unit_count` | 6 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
|  |  |  |  |  |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3881611004233035777 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 文本框 | unit_3881612212014751744 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 文本框_副本 | unit_3890428705223966720 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 天级数据-西安 | unit_3890409769709219842 | u_pivot | 2727 暑期激励看板 | page=500<br>download=0 | data_ready | task=1459210978,1459210977<br>rows=374<br>total=374 |
| 天级数据-郑州 | unit_3890469963619188736 | u_pivot | 2727 暑期激励看板 | page=500<br>download=0 | data_ready | task=1459210980,1459210979<br>rows=374<br>total=374 |
| 期次数据-西安 | unit_3913361199684935681 | u_pivot | 2751 暑期激励v2 | page=100<br>download=0 | data_ready | task=1459210994,1459210993<br>rows=100<br>total=298 |
| 月度数据-西安 | unit_3913379858514313219 | u_pivot | 2842 暑期激励v3-月份 | page=100<br>download=0 | data_ready | task=1459211000,1459210999<br>rows=100<br>total=271 |
| 月度数据-郑州 | unit_3913387360440238081 | u_pivot | 2842 暑期激励v3-月份 | page=100<br>download=0 | data_ready | task=1459211002,1459211001<br>rows=100<br>total=271 |
| 期次数据-郑州 | unit_3913378722861166595 | u_pivot | 2751 暑期激励v2 | page=100<br>download=0 | data_ready | task=1459211014,1459211013<br>rows=100<br>total=298 |

## 5. 分析单元字段结构

### 天级数据-西安

- unit_id：`unit_3890409769709219842`；类型：`u_pivot`；模型：`2727` / 暑期激励看板
- 刷新：data_ready；task_ids：`1459210978,1459210977`；行数：374；序列：0 / 0 点
- 单元筛选字段：trade_date（id=427435）、dept（id=427433）、jingli（id=427432）

### 天级数据-郑州

- unit_id：`unit_3890469963619188736`；类型：`u_pivot`；模型：`2727` / 暑期激励看板
- 刷新：data_ready；task_ids：`1459210980,1459210979`；行数：374；序列：0 / 0 点
- 单元筛选字段：trade_date（id=427435）、dept（id=427433）、jingli（id=427432）

### 期次数据-西安

- unit_id：`unit_3913361199684935681`；类型：`u_pivot`；模型：`2751` / 暑期激励v2
- 刷新：data_ready；task_ids：`1459210994,1459210993`；行数：100；序列：0 / 0 点
- 单元筛选字段：dept（id=435530）、jingli（id=435533）、qici（id=463215）

### 月度数据-西安

- unit_id：`unit_3913379858514313219`；类型：`u_pivot`；模型：`2842` / 暑期激励v3-月份
- 刷新：data_ready；task_ids：`1459211000,1459210999`；行数：100；序列：0 / 0 点
- 单元筛选字段：dept（id=462993）、natural_month（id=462990）、jingli（id=462996）

### 月度数据-郑州

- unit_id：`unit_3913387360440238081`；类型：`u_pivot`；模型：`2842` / 暑期激励v3-月份
- 刷新：data_ready；task_ids：`1459211002,1459211001`；行数：100；序列：0 / 0 点
- 单元筛选字段：dept（id=462993）、natural_month（id=462990）、jingli（id=462996）

### 期次数据-郑州

- unit_id：`unit_3913378722861166595`；类型：`u_pivot`；模型：`2751` / 暑期激励v2
- 刷新：data_ready；task_ids：`1459211014,1459211013`；行数：100；序列：0 / 0 点
- 单元筛选字段：dept（id=435530）、jingli（id=435533）、qici（id=463215）
