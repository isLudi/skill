# 运营侧数据看板 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3759973841100165121`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3759973841100165121&sourceType=1`
- profile 时间：2026-06-12 16:51:12
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260612-164827\市场顾问数据\运营侧数据看板\profile.json`
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
| 期次 | period_name | 311320 | 1 | 5 |
| 年级 | lead_purchase_intention_level2_category_name | 311322 |  | 5 |
| 渠道 | channel_map | 311321 |  | 5 |
| 规则 | rule_name | 374091 |  | 5 |
| 期次 | period_name | 335728 | 1 | 2 |
| 渠道 | channel_map | 335729 |  | 2 |
| 年级 | grade_1 | 335730 |  | 2 |
| 经理 | jingli | 335733 |  | 2 |
| 规则 | rule_name | 386424 |  | 2 |
| 期次 | period_name | 319190 |  | 6 |
| 部门 | depart | 319194 |  | 6 |
| 经理 | jingli | 319195 |  | 6 |
| 年级 | grade_1 | 319192 |  | 6 |
| 期次 | qici | 365768 |  | 2 |
| 渠道 | channel_1 | 365769 |  | 2 |
| 经理 | jingli | 365770 |  | 2 |
| 年级 | grade | 459235 |  | 1 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3788658743304962049 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3788927744572502016 | public_filter_relation |  |  | filter_relation |  |
| 进量_转化分析 | unit_3803445342673076224 | u_pivot | 2345 进量测试(市场渠道) | page=100<br>download=1 | data_ready | task=1396379081,1396379079<br>rows=4<br>total=4 |
| 全局筛选器 | public_filter_relation_3803541065796739073 | public_filter_relation |  |  | filter_relation |  |
| 进量节奏分析 | unit_3803529738811367424 | u_line | 2345 进量测试(市场渠道) | download=0 | data_ready | task=1396379120<br>rows=0 |
| 整体数据 | unit_3788678212592971777 | card | 2253 转化数据_市场顾问 | download=0 | data_ready | task=1396379144<br>rows=11 |
| 经理 | unit_3788931121683902464 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1396379178,1396379177<br>rows=8<br>total=8 |
| 主管 | unit_3800256717559488520 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1396379206,1396379202<br>rows=8<br>total=8 |
| 个人 | unit_3800257159308951556 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1396379243,1396379242<br>rows=8<br>total=8 |
| 收款分时间占比_副本 | unit_3910424477630115844 | u_pivot | 2293 运营侧个人数据 | page=500<br>download=1 | data_ready | task=1396379284,1396379282<br>rows=8<br>total=8 |
| 全局筛选器 | public_filter_relation_3791452476511903745 | public_filter_relation |  |  | filter_relation |  |
| B站亚飞 | unit_3864395442075807750 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1396379327,1396379324<br>rows=8<br>total=8 |
| 抖私1 | unit_3889082426239688709 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1396379346,1396379344<br>rows=8<br>total=8 |
| koc整体 | unit_3889083573032431621 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1396379387,1396379385<br>rows=8<br>total=8 |
| 自孵化koc | unit_3889084874430734339 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1396379404,1396379403<br>rows=8<br>total=8 |
| koc常规 | unit_3889085855924989958 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1396379440,1396379441<br>rows=8<br>total=8 |
| 亚飞 | unit_3791433812547198984 | u_pivot | 2293 运营侧个人数据 | page=100<br>download=1 | data_ready | task=1396379455,1396379453<br>rows=8<br>total=8 |
| 同渠道分部门(不可外传) | unit_3793248921101189120 | u_pivot | 2310 分二级部门转化 | page=100<br>download=1 | data_ready | task=1396379468,1396379467<br>rows=9<br>total=9 |
| 收款分时间占比 | unit_3823452752095543296 | u_pivot | 2424 每日转化数据表 | page=500<br>download=0 | data_ready | task=1396379498,1396379497<br>rows=8<br>total=8 |
| 全局筛选器 | public_filter_relation_3823479160974778368 | public_filter_relation |  |  | filter_relation |  |
| 日度净收走势 | unit_3823468976835567616 | u_line | 2423 每日转化情况 | download=0 | data_ready | task=1396379522<br>rows=0 |
| 线索分时间转化数据 | unit_3803175274388676608 | u_pivot | 2344 分析--分周期转化 | page=200<br>download=1 | data_ready | task=1396379549,1396379547<br>rows=7<br>total=7 |
| 行课数据 | unit_3791886183119278081 | u_pivot | 2132 (内部)到课衰减情况 | page=100<br>download=1 | data_ready | task=1396379598,1396379597<br>rows=10<br>total=10 |
| 外呼数据 | unit_3791903466230407169 | u_pivot | 2054 (内部渠道)外呼过程数据 | page=200<br>download=1 | data_ready | task=1396379621,1396379620<br>rows=7<br>total=7 |

## 5. 分析单元字段结构

### 进量_转化分析

- unit_id：`unit_3803445342673076224`；类型：`u_pivot`；模型：`2345` / 进量测试(市场渠道)
- 刷新：data_ready；task_ids：`1396379081,1396379079`；行数：4；序列：0 / 0 点

### 进量节奏分析

- unit_id：`unit_3803529738811367424`；类型：`u_line`；模型：`2345` / 进量测试(市场渠道)
- 刷新：data_ready；task_ids：`1396379120`；行数：0；序列：2 / 8 点

### 整体数据

- unit_id：`unit_3788678212592971777`；类型：`card`；模型：`2253` / 转化数据_市场顾问
- 刷新：data_ready；task_ids：`1396379144`；行数：11；序列：0 / 0 点
- 单元筛选字段：depart（id=311388）、depart_1（id=316910）

### 经理

- unit_id：`unit_3788931121683902464`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1396379178,1396379177`；行数：8；序列：0 / 0 点

### 主管

- unit_id：`unit_3800256717559488520`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1396379206,1396379202`；行数：8；序列：0 / 0 点

### 个人

- unit_id：`unit_3800257159308951556`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1396379243,1396379242`；行数：8；序列：0 / 0 点

### 收款分时间占比_副本

- unit_id：`unit_3910424477630115844`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1396379284,1396379282`；行数：8；序列：0 / 0 点

### B站亚飞

- unit_id：`unit_3864395442075807750`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1396379327,1396379324`；行数：8；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 抖私1

- unit_id：`unit_3889082426239688709`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1396379346,1396379344`；行数：8；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### koc整体

- unit_id：`unit_3889083573032431621`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1396379387,1396379385`；行数：8；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 自孵化koc

- unit_id：`unit_3889084874430734339`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1396379404,1396379403`；行数：8；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### koc常规

- unit_id：`unit_3889085855924989958`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1396379440,1396379441`；行数：8；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 亚飞

- unit_id：`unit_3791433812547198984`；类型：`u_pivot`；模型：`2293` / 运营侧个人数据
- 刷新：data_ready；task_ids：`1396379455,1396379453`；行数：8；序列：0 / 0 点
- 单元筛选字段：channel_map（id=319191）

### 同渠道分部门(不可外传)

- unit_id：`unit_3793248921101189120`；类型：`u_pivot`；模型：`2310` / 分二级部门转化
- 刷新：data_ready；task_ids：`1396379468,1396379467`；行数：9；序列：0 / 0 点
- 单元筛选字段：period_name（id=322466）、lead_purchase_intention_level2_category_name（id=322468）、channel_map（id=322467）

### 收款分时间占比

- unit_id：`unit_3823452752095543296`；类型：`u_pivot`；模型：`2424` / 每日转化数据表
- 刷新：data_ready；task_ids：`1396379498,1396379497`；行数：8；序列：0 / 0 点

### 日度净收走势

- unit_id：`unit_3823468976835567616`；类型：`u_line`；模型：`2423` / 每日转化情况
- 刷新：data_ready；task_ids：`1396379522`；行数：0；序列：5 / 5 点

### 线索分时间转化数据

- unit_id：`unit_3803175274388676608`；类型：`u_pivot`；模型：`2344` / 分析--分周期转化
- 刷新：data_ready；task_ids：`1396379549,1396379547`；行数：7；序列：0 / 0 点
- 单元筛选字段：qici（id=335527）、grade_list（id=335531）、channel_1（id=335528）

### 行课数据

- unit_id：`unit_3791886183119278081`；类型：`u_pivot`；模型：`2132` / (内部)到课衰减情况
- 刷新：data_ready；task_ids：`1396379598,1396379597`；行数：10；序列：0 / 0 点
- 单元筛选字段：qici（id=289670）、department（id=289674）、grade_1（id=289672）、channel_map_1（id=289671）、rule_name（id=374265）

### 外呼数据

- unit_id：`unit_3791903466230407169`；类型：`u_pivot`；模型：`2054` / (内部渠道)外呼过程数据
- 刷新：data_ready；task_ids：`1396379621,1396379620`；行数：7；序列：0 / 0 点
- 单元筛选字段：qici（id=273592）、grade_1（id=273595）、channel_map_1（id=273594）、jingli（id=322380）
