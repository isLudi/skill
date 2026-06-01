# 外呼过程数据看板 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- dashboard_id：`dashboard_3730722176629411841`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3730722176629411841&sourceType=1`
- profile 时间：2026-06-01 09:29:27
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\dashboard_profiles\market_consultant_20260601\外呼过程数据看板\profile.json`
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
| 期 | qici | 273592 | 20260605期 | 3 |
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
| 文本框 | unit_3798773484699615233 | u_text | 1 | page=5<br>download=0 | data_ready | rows=0 |
| 全局筛选器 | public_filter_relation_3798754154607599616 | public_filter_relation |  |  | filter_relation |  |
| 总体数据 | unit_3730781607175761920 | u_pivot | 2054 (内部渠道)外呼过程数据 | page=100<br>download=True | data_ready | task=1378410577,1378410578<br>rows=4<br>total=4 |
| 主管维度 | unit_3798743671868997638 | u_pivot | 2054 (内部渠道)外呼过程数据 | page=200<br>download=False | data_ready | task=1378410589,1378410588<br>rows=85<br>total=85 |
| 个人维度 | unit_3798745287165575173 | u_pivot | 2054 (内部渠道)外呼过程数据 | page=200<br>download=False | data_ready | task=1378410597,1378410595<br>rows=200<br>total=259 |

## 5. 分析单元字段结构

### 总体数据

- unit_id：`unit_3730781607175761920`；类型：`u_pivot`；模型：`2054` / (内部渠道)外呼过程数据
- 刷新：data_ready；task_ids：`1378410577,1378410578`；行数：4；序列：0 / 0 点
- 维度/表头字段：经理（id=322380）、线索渠道（id=273594）、年级（id=273595）、主管（id=273597）、顾问（id=273598）、人力（id=customized_977588664966885377）、退前线索（id=8465935477925888）、退后线索（id=8103974494234625）、总通时（id=8103974494234632）、通时(例均)（id=customized_977588665172406272）、通时(人均)（id=customized_977588665067548673）、首call（id=customized_977588665692499968）、5min外呼（id=customized_977588663733760001）、6h外呼（id=customized_977588663943475201）、12h外呼（id=customized_977588663209472000）、24h外呼（id=customized_977588663322718209）、48h外呼（id=customized_977588663528239104）、24h沟通（id=customized_977588663427575808）、48h沟通（id=customized_977588663628902400）、外呼频次（id=customized_977588664354516993）、平均接通时长(min)（id=customized_977588664765558785）、等待时长(h)（id=customized_977588665587642369）、外呼接通（id=customized_977588664253853697）、5min比例（id=customized_977588663838617600）、好友（id=customized_977588664459374592）、APP登陆（id=customized_977588664048332800）、异常（id=customized_977588665281458176）、深沟（id=customized_977588665386315777）、双沟（id=customized_977588664153190401）、已回收（id=customized_977588664664895489）、已双沟（id=customized_977588664560037888）、首节到课（id=customized_977588665797357569）、首节有效（id=customized_977588665902215168）
- 指标/序列字段：人力、退前线索、退后线索、总通时、通时(例均)、通时(人均)、首call、5min外呼、6h外呼、12h外呼、24h外呼、48h外呼、24h沟通、48h沟通、外呼频次、平均接通时长(min)、等待时长(h)、外呼接通、5min比例、好友、APP登陆、异常、深沟、双沟、已回收、已双沟、首节到课、首节有效

### 主管维度

- unit_id：`unit_3798743671868997638`；类型：`u_pivot`；模型：`2054` / (内部渠道)外呼过程数据
- 刷新：data_ready；task_ids：`1378410589,1378410588`；行数：85；序列：0 / 0 点
- 维度/表头字段：线索渠道（id=273594）、年级（id=273595）、经理（id=322380）、主管（id=273597）、接量人力（id=customized_977588664966885377）、有效例子（id=8103974494234625）、例子总通时（id=8103974494234632）、平均通时(例子)（id=customized_977588665172406272）、平均通时(人均)（id=customized_977588665067548673）、24h外呼率（id=customized_977588663322718209）、48h外呼率（id=customized_977588663528239104）、24h沟通率（id=customized_977588663427575808）、48h沟通率（id=customized_977588663628902400）、外呼频次（id=customized_977588664354516993）、平均接通时长(min)（id=customized_977588664765558785）、等待时长(h)（id=customized_977588665587642369）、外呼接通率（id=customized_977588664253853697）、5min比例（id=customized_977588663838617600）、好友率（id=customized_977588664459374592）、APP登陆率（id=customized_977588664048332800）、深沟率（id=customized_977588665386315777）、双沟率（id=customized_977588664153190401）、首节到课率（id=customized_977588665797357569）、首节有效率（id=customized_977588665902215168）
- 指标/序列字段：接量人力、有效例子、例子总通时、平均通时(例子)、平均通时(人均)、24h外呼率、48h外呼率、24h沟通率、48h沟通率、外呼频次、平均接通时长(min)、等待时长(h)、外呼接通率、5min比例、好友率、APP登陆率、深沟率、双沟率、首节到课率、首节有效率

### 个人维度

- unit_id：`unit_3798745287165575173`；类型：`u_pivot`；模型：`2054` / (内部渠道)外呼过程数据
- 刷新：data_ready；task_ids：`1378410597,1378410595`；行数：200；序列：0 / 0 点
- 维度/表头字段：线索渠道（id=273594）、年级（id=273595）、主管（id=273597）、顾问（id=273598）、有效例子（id=8103974494234625）、例子总通时（id=8103974494234632）、平均通时(例子)（id=customized_977588665172406272）、24h外呼率（id=customized_977588663322718209）、48h外呼率（id=customized_977588663528239104）、24h沟通率（id=customized_977588663427575808）、48h沟通率（id=customized_977588663628902400）、外呼频次（id=customized_977588664354516993）、平均接通时长(min)（id=customized_977588664765558785）、等待时长(h)（id=customized_977588665587642369）、外呼接通率（id=customized_977588664253853697）、5min比例（id=customized_977588663838617600）、好友率（id=customized_977588664459374592）、APP登陆率（id=customized_977588664048332800）、深沟率（id=customized_977588665386315777）、双沟率（id=customized_977588664153190401）、首节到课率（id=customized_977588665797357569）、首节有效率（id=customized_977588665902215168）
- 指标/序列字段：有效例子、例子总通时、平均通时(例子)、24h外呼率、48h外呼率、24h沟通率、48h沟通率、外呼频次、平均接通时长(min)、等待时长(h)、外呼接通率、5min比例、好友率、APP登陆率、深沟率、双沟率、首节到课率、首节有效率

## 6. 维护注意事项

- `u_text`、`u_material` 等非分析单元可能返回空数据，这是展示素材，不按刷新失败处理。
- 生成 SQL 或排查指标时，应回到对应 `knowledge/dashboards/*.md` 和 `knowledge/metrics/*.md` 确认业务口径；本文件只说明 Web BI 当前配置结构。
- 看板筛选器存在动态默认值时，应优先读取本文件中的字段 ID、默认值样例和作用单元，再按业务需求替换。
