# 个人转化数据-青橙 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`青橙项目部`
- dashboard_id：`dashboard_3873038327756636161`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3873038327756636161&sourceType=1`
- profile 时间：2026-06-24 18:45:34
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260624-184137\青橙项目部\个人转化数据-青橙\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 4 |
| `value_unit_count` | 4 |
| `data_ready_unit_count` | 3 |
| `analytic_unit_count` | 2 |
| `analytic_data_ready_unit_count` | 2 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
|  |  |  |  |  |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3873038340305993730 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 文本框 | unit_3893236780015427585 | u_text | 1 None | download=0 | data_ready | rows=0 |
| 期产出 | unit_3873038340305993729 | u_pivot | 2769 青橙个人转化 | page=500<br>download=1 | data_ready | task=1424548625,1424548624<br>rows=187<br>total=187 |
| 月度产出 | unit_3893056410852823041 | u_pivot | 2769 青橙个人转化 | page=500<br>download=1 | data_ready | task=1424548667,1424548666<br>rows=158<br>total=158 |

## 5. 分析单元字段结构

### 期产出

- unit_id：`unit_3873038340305993729`；类型：`u_pivot`；模型：`2769` / 青橙个人转化
- 刷新：data_ready；task_ids：`1424548625,1424548624`；行数：187；序列：0 / 0 点
- 单元筛选字段：qici（id=437989）、xuebu（id=437995）、dazu（id=437993）、leader_employee_email_name（id=437992）、data_level（id=496578）

### 月度产出

- unit_id：`unit_3893056410852823041`；类型：`u_pivot`；模型：`2769` / 青橙个人转化
- 刷新：data_ready；task_ids：`1424548667,1424548666`；行数：158；序列：0 / 0 点
- 单元筛选字段：moth（id=437990）、xuebu（id=437995）、dazu（id=437993）、leader_employee_email_name（id=437992）、qici（id=437989）、data_level（id=496578）
