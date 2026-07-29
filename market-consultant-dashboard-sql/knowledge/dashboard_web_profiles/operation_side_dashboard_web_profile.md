# 运营侧数据看板 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3759973841100165121`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3759973841100165121&sourceType=1`
- profile 时间：2026-07-11 09:46:54
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\profile-all\市场顾问数据\运营侧数据看板\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 24 |
| `value_unit_count` | 20 |
| `data_ready_unit_count` | 19 |
| `analytic_unit_count` | 19 |
| `analytic_data_ready_unit_count` | 19 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | period_name | 319190 |  | 5 |
| 年级 | grade_1 | 319192 |  | 5 |
| 渠道 | channel_map | 319191 |  | 5 |
| 规则 | rule_name | 374215 |  | 5 |
| 经理 | jingli | 319195 |  | 5 |
| 期次 | period_name | 335728 | 1 | 2 |
| 渠道 | channel_map | 335729 |  | 2 |
| 年级 | grade_1 | 335730 |  | 2 |
| 经理 | jingli | 335733 |  | 2 |
| 规则 | rule_name | 386424 |  | 2 |
| 期次 | period_name | 319190 |  | 6 |
| 部门 | depart | 319194 |  | 6 |
| 经理 | jingli | 319195 |  | 6 |
| 年级 | grade_1 | 319192 |  | 6 |
| 期次 | qici | 365768 |  | 1 |
| 渠道 | channel_1 | 365769 |  | 1 |
| 经理 | jingli | 365770 |  | 1 |
| 年级 | grade | 459235 |  | 1 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3788658743304962049 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3788927744572502016 | public_filter_relation |  |  | filter_relation |  |
| 进量_转化分析 | unit_3803445342673076224 | u_pivot | 2345 进量测试(市场渠道) | page=100<br>download=1 | data_ready | task=1459207556,1459207554<br>rows=5<br>total=5 |
| 全局筛选器 | public_filter_relation_3803541065796739073 | public_filter_relation |  |  | filter_relation |  |
| 进量节奏分析 | unit_3803529738811367424 | u_line | 2345 进量测试(市场渠道) | download=0 | data_ready | task=1459207564<br>rows=0 |
| 整体数据 | unit_3953902454021992459 | card | 2293 运营侧个人数据 | download=0 | data_ready | task=1459207565<br>rows=11 |
| 经理 | unit_3788931121683902464 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459207568,1459207566<br>rows=54<br>total=54 |
| 主管 | unit_3800256717559488520 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459207574,1459207572<br>rows=54<br>total=54 |
| 个人 | unit_3800257159308951556 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459207581,1459207579<br>rows=54<br>total=54 |
| 收款分时间占比_副本 | unit_3910424477630115844 | u_pivot | 2293 运营侧个人数据 | page=500<br>download=1 | data_ready | task=1459207583,1459207582<br>rows=54<br>total=54 |
| 全局筛选器 | public_filter_relation_3791452476511903745 | public_filter_relation |  |  | filter_relation |  |
| B站亚飞 | unit_3864395442075807750 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459207588,1459207587<br>rows=54<br>total=54 |
| 抖私1 | unit_3889082426239688709 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459207591,1459207589<br>rows=54<br>total=54 |
| koc整体 | unit_3889083573032431621 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459207594,1459207592<br>rows=54<br>total=54 |
| 自孵化koc | unit_3889084874430734339 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459207599,1459207597<br>rows=54<br>total=54 |
| koc常规 | unit_3889085855924989958 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459207602,1459207601<br>rows=54<br>total=54 |
| 亚飞 | unit_3791433812547198984 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1459207609,1459207608<br>rows=54<br>total=54 |
| 同渠道转化数据对比 | unit_3793248921101189120 | u_pivot | 2310 分二级部门转化 | page=100<br>download=1 | data_ready | task=1459207617,1459207615<br>rows=13<br>total=13 |
| 收款分时间占比 | unit_3823452752095543296 | u_pivot | 2424 每日转化数据表 | page=500<br>download=0 | data_ready | task=1459207621,1459207620<br>rows=12<br>total=12 |
| 全局筛选器 | public_filter_relation_3823479160974778368 | public_filter_relation |  |  | filter_relation |  |
| 线索分时间转化数据 | unit_3803175274388676608 | u_pivot | 2344 分析--分周期转化 | page=200<br>download=1 | data_ready | task=1459207631,1459207630<br>rows=12<br>total=12 |
| 新老人转化对比 | unit_3975643530358935552 | u_pivot | 3039 新老人转化对比 | page=20<br>download=0 | data_ready | task=1459207633,1459207632<br>rows=20<br>total=54 |
| 行课数据 | unit_3791886183119278081 | u_pivot | 2132 (内部)到课衰减情况 | page=100<br>download=1 | data_ready | task=1459207636,1459207635<br>rows=14<br>total=14 |
| 外呼数据 | unit_3791903466230407169 | u_pivot | 2054 (内部渠道)外呼过程数据 | page=200<br>download=1 | data_ready | task=1459207647,1459207645<br>rows=11<br>total=11 |

## 5. 分析单元字段结构

### 进量_转化分析

- unit_id：`unit_3803445342673076224`；类型：`u_pivot`；模型：`2345` / 进量测试(市场渠道)
- 刷新：data_ready；task_ids：`1459207556,1459207554`；行数：5；序列：0 / 0 点

### 进量节奏分析

- unit_id：`unit_3803529738811367424`；类型：`u_line`；模型：`2345` / 进量测试(市场渠道)
- 刷新：data_ready；task_ids：`1459207564`；行数：0；序列：2 / 10 点

### 整体数据

- unit_id：`unit_3953902454021992459`；类型：`card`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207565`；行数：11；序列：0 / 0 点

### 经理

- unit_id：`unit_3788931121683902464`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207568,1459207566`；行数：54；序列：0 / 0 点

### 主管

- unit_id：`unit_3800256717559488520`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207574,1459207572`；行数：54；序列：0 / 0 点

### 个人

- unit_id：`unit_3800257159308951556`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207581,1459207579`；行数：54；序列：0 / 0 点

### 收款分时间占比_副本

- unit_id：`unit_3910424477630115844`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207583,1459207582`；行数：54；序列：0 / 0 点

### B站亚飞

- unit_id：`unit_3864395442075807750`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207588,1459207587`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 抖私1

- unit_id：`unit_3889082426239688709`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207591,1459207589`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### koc整体

- unit_id：`unit_3889083573032431621`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207594,1459207592`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 自孵化koc

- unit_id：`unit_3889084874430734339`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207599,1459207597`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### koc常规

- unit_id：`unit_3889085855924989958`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207602,1459207601`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 亚飞

- unit_id：`unit_3791433812547198984`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1459207609,1459207608`；行数：54；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 同渠道转化数据对比

- unit_id：`unit_3793248921101189120`；类型：`u_pivot`；模型：`2310` / 分二级部门转化
- 刷新：data_ready；task_ids：`1459207617,1459207615`；行数：13；序列：0 / 0 点
- 单元筛选字段：period_name（id=322466）、lead_purchase_intention_level2_category_name（id=322468）、channel_map（id=322467）

### 收款分时间占比

- unit_id：`unit_3823452752095543296`；类型：`u_pivot`；模型：`2424` / 每日转化数据表
- 刷新：data_ready；task_ids：`1459207621,1459207620`；行数：12；序列：0 / 0 点

### 线索分时间转化数据

- unit_id：`unit_3803175274388676608`；类型：`u_pivot`；模型：`2344` / 分析--分周期转化
- 刷新：data_ready；task_ids：`1459207631,1459207630`；行数：12；序列：0 / 0 点
- 单元筛选字段：qici（id=335527）、grade_list（id=335531）、channel_1（id=335528）

### 新老人转化对比

- unit_id：`unit_3975643530358935552`；类型：`u_pivot`；模型：`3039` / 新老人转化对比
- 刷新：data_ready；task_ids：`1459207633,1459207632`；行数：20；序列：0 / 0 点
- 单元筛选字段：period_name（id=519162）、channel_map（id=519163）、manager_name（id=519165）、grade_1（id=519164）

### 行课数据

- unit_id：`unit_3791886183119278081`；类型：`u_pivot`；模型：`2132` / (内部)到课衰减情况
- 刷新：data_ready；task_ids：`1459207636,1459207635`；行数：14；序列：0 / 0 点
- 单元筛选字段：qici（id=289670）、department（id=289674）、grade_1（id=289672）、channel_map_1（id=289671）、rule_name（id=374265）

### 外呼数据

- unit_id：`unit_3791903466230407169`；类型：`u_pivot`；模型：`2054` / (内部渠道)外呼过程数据
- 刷新：data_ready；task_ids：`1459207647,1459207645`；行数：11；序列：0 / 0 点
- 单元筛选字段：qici（id=273592）、grade_1（id=273595）、channel_map_1（id=273594）、jingli（id=322380）
