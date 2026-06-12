# 市场顾问-用户画像分析 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`市场顾问数据`
- dashboard_id：`dashboard_3804681042591760385`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3804681042591760385&sourceType=1`
- profile 时间：2026-06-12 16:53:55
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\artifacts\20260612-164827\市场顾问数据\市场顾问-用户画像分析\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 25 |
| `value_unit_count` | 21 |
| `data_ready_unit_count` | 13 |
| `analytic_unit_count` | 16 |
| `analytic_data_ready_unit_count` | 13 |
| `error_count` | 0 |
| `all_analytic_units_ready` | False |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | period_name | 449728 | 2 | 4 |
| 渠道 | channel_map | 449729 |  | 2 |
| 年级 | grade_name | 449730 |  | 2 |
| 经理 | manager_name | 449731 |  | 2 |
| 期次 | qici | 337135 | 20260605期 | 5 |
| 渠道 | channel_1 | 337136 |  | 5 |
| 年级 | grade_list | 337139 |  | 5 |
| 经理 | jingli | 337137 |  | 5 |
| 期次 | period_name | 415757 | 2 | 1 |
| 渠道 | channel_map | 415758 |  | 1 |
| 年级 | grade_1 | 415759 |  | 1 |
| 期次 | period_name | 461589 | 20260605期 | 6 |
| 渠道 | channel_map | 461590 |  | 6 |
| 年级 | grade_name | 461592 |  | 6 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3804755797370580993 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 标题图 | unit_3833864070902894593 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 流量用户画像 | unit_3874154854137556993 | u_pivot | 2683 前期流量画像-城市 | page=100<br>download=1 | data_ready | task=1396381994,1396381989<br>rows=28<br>total=28 |
| 标题图_副本 | unit_3874151640555405313 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3901640697883406336 | public_filter_relation |  |  | filter_relation |  |
| 指标卡组 | unit_3901639638629822464 | card | 2809 成单用户画像整体数据 | download=0 | data_ready | task=1396382071<br>rows=6 |
| 多科用户成单表 | unit_3901691404520521729 | u_pivot | 2809 成单用户画像整体数据 | page=200<br>download=1 | data_ready | task=1396382112,1396382113<br>rows=32<br>total=32 |
| 透视表_副本 | unit_3901885938907897856 | u_pivot | 2812 用户画像成单用户城市标签 | page=100<br>download=0 | data_ready | task=1396382145,1396382144<br>rows=7<br>total=7 |
| 成单用户城市占比 | unit_3901733362643238912 | u_pie | 2812 用户画像成单用户城市标签 | download=0 | data_ready | task=1396382167<br>rows=0 |
| 成单用户首call通时占比 | unit_3911763282149220353 | u_pie | 2836 市场渠道用户成单分析 | download=0 | data_ready | task=1396382183<br>rows=0 |
| 成单用户上课时长占比 | unit_3913644842373492738 | u_pie | 2885 市场渠道用户成单分析3 | download=0 | data_ready | task=1396382208<br>rows=0 |
| 深沟成单用户占比 | unit_3913651535506427905 | u_pie | 2883 市场渠道用户成单分析2 | download=0 | data_ready | task=1396382229<br>rows=0 |
| 标题图 | unit_3833856102394322945 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 标题图_副本 | unit_3911760818112954369 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 1 | unit_3913632965000523776 | u_pivot | 2836 市场渠道用户成单分析 | page=100<br>download=0 | data_ready | task=1396382277,1396382275<br>rows=5<br>total=5 |
| 1_副本 | unit_3913648004741677057 | u_pivot | 2885 市场渠道用户成单分析3 | page=100<br>download=0 | data_ready | task=1396382318,1396382317<br>rows=6<br>total=6 |
| 1_副本_副本 | unit_3913653568806137857 | u_pivot | 2883 市场渠道用户成单分析2 | page=100<br>download=0 | data_ready | task=1396382330,1396382329<br>rows=4<br>total=4 |
| 全局筛选器 | public_filter_relation_3804782665266020352 | public_filter_relation |  |  | filter_relation |  |
| 全局筛选器_副本 | public_filter_relation_3874159861500256261 | public_filter_relation |  |  | filter_relation |  |
| 全局筛选器_副本_副本 | public_filter_relation_3922299105533534211 | public_filter_relation |  |  | filter_relation |  |
| 不同科目退费占比 | unit_3804745414220034049 | u_bar | 2349 退费_科目_产品 | download=0 | loaded_empty | rows=0 |
| 指标卡组 | unit_3933611388482850816 | card | 2886 退费整体数据 | download=0 | data_ready | task=1396383316<br>rows=6 |
| 多科用户退费占比 | unit_3935197018570850305 | u_pivot | 2890 多科用户退费 | page=100<br>download=1 | data_ready | task=1396383335,1396383334<br>rows=27<br>total=27 |
| 退费原因占比 | unit_3804774188543500288 | u_pie | 2353 退费原因分析 | download=0 | loaded_empty | rows=0 |
| 不同产品退费占比 | unit_3804761632267427840 | u_bar | 2349 退费_科目_产品 | download=0 | loaded_empty | rows=0 |

## 5. 分析单元字段结构

### 流量用户画像

- unit_id：`unit_3874154854137556993`；类型：`u_pivot`；模型：`2683` / 前期流量画像-城市
- 刷新：data_ready；task_ids：`1396381994,1396381989`；行数：28；序列：0 / 0 点

### 指标卡组

- unit_id：`unit_3901639638629822464`；类型：`card`；模型：`2809` / 成单用户画像整体数据
- 刷新：data_ready；task_ids：`1396382071`；行数：6；序列：0 / 0 点

### 多科用户成单表

- unit_id：`unit_3901691404520521729`；类型：`u_pivot`；模型：`2809` / 成单用户画像整体数据
- 刷新：data_ready；task_ids：`1396382112,1396382113`；行数：32；序列：0 / 0 点

### 透视表_副本

- unit_id：`unit_3901885938907897856`；类型：`u_pivot`；模型：`2812` / 用户画像成单用户城市标签
- 刷新：data_ready；task_ids：`1396382145,1396382144`；行数：7；序列：0 / 0 点

### 成单用户城市占比

- unit_id：`unit_3901733362643238912`；类型：`u_pie`；模型：`2812` / 用户画像成单用户城市标签
- 刷新：data_ready；task_ids：`1396382167`；行数：0；序列：1 / 5 点

### 成单用户首call通时占比

- unit_id：`unit_3911763282149220353`；类型：`u_pie`；模型：`2836` / 市场渠道用户成单分析
- 刷新：data_ready；task_ids：`1396382183`；行数：0；序列：1 / 5 点
- 单元筛选字段：analysis_type（id=461593）

### 成单用户上课时长占比

- unit_id：`unit_3913644842373492738`；类型：`u_pie`；模型：`2885` / 市场渠道用户成单分析3
- 刷新：data_ready；task_ids：`1396382208`；行数：0；序列：1 / 5 点

### 深沟成单用户占比

- unit_id：`unit_3913651535506427905`；类型：`u_pie`；模型：`2883` / 市场渠道用户成单分析2
- 刷新：data_ready；task_ids：`1396382229`；行数：0；序列：1 / 4 点

### 1

- unit_id：`unit_3913632965000523776`；类型：`u_pivot`；模型：`2836` / 市场渠道用户成单分析
- 刷新：data_ready；task_ids：`1396382277,1396382275`；行数：5；序列：0 / 0 点

### 1_副本

- unit_id：`unit_3913648004741677057`；类型：`u_pivot`；模型：`2885` / 市场渠道用户成单分析3
- 刷新：data_ready；task_ids：`1396382318,1396382317`；行数：6；序列：0 / 0 点

### 1_副本_副本

- unit_id：`unit_3913653568806137857`；类型：`u_pivot`；模型：`2883` / 市场渠道用户成单分析2
- 刷新：data_ready；task_ids：`1396382330,1396382329`；行数：4；序列：0 / 0 点

### 不同科目退费占比

- unit_id：`unit_3804745414220034049`；类型：`u_bar`；模型：`2349` / 退费_科目_产品
- 刷新：loaded_empty；task_ids：``；行数：0；序列：0 / 0 点

### 指标卡组

- unit_id：`unit_3933611388482850816`；类型：`card`；模型：`2886` / 退费整体数据
- 刷新：data_ready；task_ids：`1396383316`；行数：6；序列：0 / 0 点

### 多科用户退费占比

- unit_id：`unit_3935197018570850305`；类型：`u_pivot`；模型：`2890` / 多科用户退费
- 刷新：data_ready；task_ids：`1396383335,1396383334`；行数：27；序列：0 / 0 点

### 退费原因占比

- unit_id：`unit_3804774188543500288`；类型：`u_pie`；模型：`2353` / 退费原因分析
- 刷新：loaded_empty；task_ids：``；行数：0；序列：0 / 0 点

### 不同产品退费占比

- unit_id：`unit_3804761632267427840`；类型：`u_bar`；模型：`2349` / 退费_科目_产品
- 刷新：loaded_empty；task_ids：``；行数：0；序列：0 / 0 点
