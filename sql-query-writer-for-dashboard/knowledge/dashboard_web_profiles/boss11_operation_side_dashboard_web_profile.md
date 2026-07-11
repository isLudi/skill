# 11老板_运营侧数据看板 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3833805337379700736`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3833805337379700736&sourceType=1`
- profile 时间：2026-07-11 09:48:47
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\市场顾问数据\11老板_运营侧数据看板\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 22 |
| `value_unit_count` | 18 |
| `data_ready_unit_count` | 17 |
| `analytic_unit_count` | 17 |
| `analytic_data_ready_unit_count` | 17 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | period_name | 311320 | 2 | 4 |
| 年级 | lead_purchase_intention_level2_category_name | 311322 |  | 4 |
| 渠道 | channel_map | 311321 |  | 4 |
| 规则 | rule_name | 374091 |  | 4 |
| 期次 | period_name | 335728 | 1 | 2 |
| 渠道 | channel_map | 335729 |  | 2 |
| 年级 | grade_1 | 335730 |  | 2 |
| 经理 | jingli | 335733 |  | 2 |
| 期次 | period_name | 319190 |  | 6 |
| 部门 | depart | 319194 |  | 6 |
| 经理 | jingli | 319195 |  | 6 |
| 年级 | grade_1 | 319192 |  | 6 |
| 期次 | qici | 365654 |  | 2 |
| 渠道 | channel_1 | 365769 |  | 2 |
| 年级 | grade_list | 365657 |  | 2 |
| 经理 | jingli | 365656 |  | 2 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3833805476815142913 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3833805476815142919 | public_filter_relation |  |  | filter_relation |  |
| 进量_转化分析 | unit_3833805476815142964 | u_pivot | 2345 进量测试(市场渠道) | page=100<br>download=0 | data_ready | task=1459208475,1459208474<br>rows=5<br>total=5 |
| 全局筛选器 | public_filter_relation_3833805476815142970 | public_filter_relation |  |  | filter_relation |  |
| 进量节奏分析 | unit_3833805476815142965 | u_line | 2345 进量测试(市场渠道) | download=0 | data_ready | task=1459208479<br>rows=0 |
| 整体数据 | unit_3833805476815142914 | card | 2253 转化数据_市场顾问 | download=0 | data_ready | task=1459208480<br>rows=9 |
| 经理 | unit_3833805476815142920 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459208483,1459208482<br>rows=54<br>total=54 |
| 主管 | unit_3833805476815142958 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459208491,1459208489<br>rows=54<br>total=54 |
| 个人 | unit_3833805476815142959 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459208494,1459208493<br>rows=54<br>total=54 |
| 全局筛选器 | public_filter_relation_3833805476815142929 | public_filter_relation |  |  | filter_relation |  |
| KOC自孵化 | unit_3833805476815142941 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459208497,1459208495<br>rows=54<br>total=54 |
| 春春 | unit_3833805476815142926 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459208511,1459208510<br>rows=54<br>total=54 |
| 亚飞 | unit_3833805476815142925 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459208514,1459208512<br>rows=54<br>total=54 |
| 曹忆 | unit_3833805476815142939 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459208521,1459208520<br>rows=54<br>total=54 |
| 肖晗IP | unit_3833805476815142953 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459208526,1459208525<br>rows=54<br>total=54 |
| 周帅IP | unit_3833805476815142976 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459208529,1459208528<br>rows=54<br>total=54 |
| 收款分时间占比 | unit_3833805476815142977 | u_pivot | 2424 每日转化数据表 | page=500<br>download=0 | data_ready | task=1459208532,1459208531<br>rows=12<br>total=12 |
| 全局筛选器 | public_filter_relation_3833805476815142987 | public_filter_relation |  |  | filter_relation |  |
| 日度净收走势 | unit_3833805476815142978 | u_line | 2423 每日转化情况 | download=0 | data_ready | task=1459208546<br>rows=0 |
| 线索分时间转化数据 | unit_3833805476815142960 | u_pivot | 2344 分析--分周期转化 | page=200<br>download=1 | data_ready | task=1459208547,1459208549<br>rows=12<br>total=12 |
| 行课数据 | unit_3833805476815142946 | u_pivot | 2132 (内部)到课衰减情况 | page=100<br>download=1 | data_ready | task=1459208552,1459208551<br>rows=14<br>total=14 |
| 外呼数据 | unit_3833805476815142947 | u_pivot | 2054 (内部渠道)外呼过程数据 | page=200<br>download=1 | data_ready | task=1459208555,1459208554<br>rows=11<br>total=11 |

## 5. 分析单元字段结构

### 进量_转化分析

- unit_id：`unit_3833805476815142964`；类型：`u_pivot`；模型：`2345` / 进量测试(市场渠道)
- 刷新：data_ready；task_ids：`1459208475,1459208474`；行数：5；序列：0 / 0 点

### 进量节奏分析

- unit_id：`unit_3833805476815142965`；类型：`u_line`；模型：`2345` / 进量测试(市场渠道)
- 刷新：data_ready；task_ids：`1459208479`；行数：0；序列：2 / 10 点

### 整体数据

- unit_id：`unit_3833805476815142914`；类型：`card`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1459208480`；行数：9；序列：0 / 0 点
- 单元筛选字段：depart（id=311388）、depart_1（id=316910）

### 经理

- unit_id：`unit_3833805476815142920`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459208483,1459208482`；行数：54；序列：0 / 0 点

### 主管

- unit_id：`unit_3833805476815142958`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459208491,1459208489`；行数：54；序列：0 / 0 点

### 个人

- unit_id：`unit_3833805476815142959`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459208494,1459208493`；行数：54；序列：0 / 0 点

### KOC自孵化

- unit_id：`unit_3833805476815142941`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459208497,1459208495`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 春春

- unit_id：`unit_3833805476815142926`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459208511,1459208510`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 亚飞

- unit_id：`unit_3833805476815142925`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459208514,1459208512`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 曹忆

- unit_id：`unit_3833805476815142939`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459208521,1459208520`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 肖晗IP

- unit_id：`unit_3833805476815142953`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459208526,1459208525`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 周帅IP

- unit_id：`unit_3833805476815142976`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459208529,1459208528`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 收款分时间占比

- unit_id：`unit_3833805476815142977`；类型：`u_pivot`；模型：`2424` / 每日转化数据表
- 刷新：data_ready；task_ids：`1459208532,1459208531`；行数：12；序列：0 / 0 点

### 日度净收走势

- unit_id：`unit_3833805476815142978`；类型：`u_line`；模型：`2423` / 每日转化情况
- 刷新：data_ready；task_ids：`1459208546`；行数：0；序列：5 / 5 点

### 线索分时间转化数据

- unit_id：`unit_3833805476815142960`；类型：`u_pivot`；模型：`2344` / 分析--分周期转化
- 刷新：data_ready；task_ids：`1459208547,1459208549`；行数：12；序列：0 / 0 点
- 单元筛选字段：qici（id=335527）、grade_list（id=335531）、channel_1（id=335528）

### 行课数据

- unit_id：`unit_3833805476815142946`；类型：`u_pivot`；模型：`2132` / (内部)到课衰减情况
- 刷新：data_ready；task_ids：`1459208552,1459208551`；行数：14；序列：0 / 0 点
- 单元筛选字段：qici（id=289670）、department（id=289674）、grade_1（id=289672）、channel_map_1（id=289671）、rule_name（id=374265）

### 外呼数据

- unit_id：`unit_3833805476815142947`；类型：`u_pivot`；模型：`2054` / (内部渠道)外呼过程数据
- 刷新：data_ready；task_ids：`1459208555,1459208554`；行数：11；序列：0 / 0 点
- 单元筛选字段：qici（id=273592）、department（id=273596）、grade_1（id=273595）、channel_map_1（id=273594）
