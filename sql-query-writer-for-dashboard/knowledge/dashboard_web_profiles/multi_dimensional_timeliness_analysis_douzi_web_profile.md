# 多维度时效分析-抖咨 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- 文件夹：`??????`
- dashboard_id：`dashboard_3861041931986931712`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3861041931986931712&sourceType=1`
- profile 时间：2026-07-11 10:54:32
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\p3-validation-20260711\retry-market-timeliness\多维度时效分析-抖咨\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 10 |
| `value_unit_count` | 2 |
| `data_ready_unit_count` | 1 |
| `analytic_unit_count` | 8 |
| `analytic_data_ready_unit_count` | 1 |
| `error_count` | 7 |
| `all_analytic_units_ready` | False |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | period_name | 405153 | 1 | 8 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3861068961718165504 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3861067180758081537 | public_filter_relation |  |  | filter_relation |  |
| 部门 | unit_3861063716424466433 | u_pivot | 2623 抖音私信- 分时间段 | page=300<br>download=0 | unprofiled |  |
| 经理 | unit_3861063388582449154 | u_pivot | 2623 抖音私信- 分时间段 | page=300<br>download=0 | unprofiled |  |
| 顾问_副本 | unit_3861061473331204097 | u_pivot | 2623 抖音私信- 分时间段 | page=300<br>download=0 | unprofiled |  |
| 顾问 | unit_3861044167111950336 | u_pivot | 2623 抖音私信- 分时间段 | page=300<br>download=0 | unprofiled |  |
| 部门 | unit_3861107228588707841 | u_pivot | 2625 分触达时间段--抖音咨询 | page=300<br>download=0 | unprofiled |  |
| 经理 | unit_3861108524580036608 | u_pivot | 2625 分触达时间段--抖音咨询 | page=300<br>download=0 | data_ready | task=1459238160,1459238161<br>rows=1<br>total=1 |
| 主管 | unit_3861106694555324416 | u_pivot | 2625 分触达时间段--抖音咨询 | page=300<br>download=0 | unprofiled |  |
| 顾问 | unit_3861088496817307649 | u_pivot | 2625 分触达时间段--抖音咨询 | page=300<br>download=0 | unprofiled |  |

## 5. 分析单元字段结构

### 部门

- unit_id：`unit_3861063716424466433`；类型：`u_pivot`；模型：`2623` / 抖音私信- 分时间段
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点
- 维度/表头字段：时间段（id=405161）

### 经理

- unit_id：`unit_3861063388582449154`；类型：`u_pivot`；模型：`2623` / 抖音私信- 分时间段
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点
- 维度/表头字段：时间段（id=405161）

### 顾问_副本

- unit_id：`unit_3861061473331204097`；类型：`u_pivot`；模型：`2623` / 抖音私信- 分时间段
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点
- 维度/表头字段：时间段（id=405161）

### 顾问

- unit_id：`unit_3861044167111950336`；类型：`u_pivot`；模型：`2623` / 抖音私信- 分时间段
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点
- 维度/表头字段：时间段（id=405161）

### 部门

- unit_id：`unit_3861107228588707841`；类型：`u_pivot`；模型：`2625` / 分触达时间段--抖音咨询
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点
- 维度/表头字段：触达时间（id=405279）

### 经理

- unit_id：`unit_3861108524580036608`；类型：`u_pivot`；模型：`2625` / 分触达时间段--抖音咨询
- 刷新：data_ready；task_ids：`1459238160,1459238161`；行数：1；序列：0 / 0 点
- 维度/表头字段：触达时间（id=405279）

### 主管

- unit_id：`unit_3861106694555324416`；类型：`u_pivot`；模型：`2625` / 分触达时间段--抖音咨询
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点
- 维度/表头字段：触达时间（id=405279）

### 顾问

- unit_id：`unit_3861088496817307649`；类型：`u_pivot`；模型：`2625` / 分触达时间段--抖音咨询
- 刷新：unknown；task_ids：``；行数：0；序列：0 / 0 点
- 维度/表头字段：触达时间（id=405279）

## 6. 采集异常

- `unit_3861063716424466433`：APIRequestContext.post: Timeout 45000ms exceeded.
Call log:
  - → POST https://uanalysis.baijia.com/uanalysis-intelligence/value/unit
    - user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0
    - accept: */*
    - accept-encoding: gzip,deflate,br
    - content-type: application/json
    - content-length: 308
    - cookie: JSESSIONID=9EC9AFACE5BE421A609392FD30EDD05D; _const_d_jsession_id_=b5155d95c2b44b11b1879ad3744b8b65.uanalysis.baijia.com; CAS_AC_CURRENT_ROLE=umetric_common_user

- `unit_3861063388582449154`：APIRequestContext.post: Timeout 45000ms exceeded.
Call log:
  - → POST https://uanalysis.baijia.com/uanalysis-intelligence/value/unit
    - user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0
    - accept: */*
    - accept-encoding: gzip,deflate,br
    - content-type: application/json
    - content-length: 308
    - cookie: JSESSIONID=8BD9D8D5490024A9125557D0B2D96FAC; _const_d_jsession_id_=b5155d95c2b44b11b1879ad3744b8b65.uanalysis.baijia.com; CAS_AC_CURRENT_ROLE=umetric_common_user

- `unit_3861061473331204097`：APIRequestContext.post: Timeout 45000ms exceeded.
Call log:
  - → POST https://uanalysis.baijia.com/uanalysis-intelligence/value/unit
    - user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0
    - accept: */*
    - accept-encoding: gzip,deflate,br
    - content-type: application/json
    - content-length: 308
    - cookie: JSESSIONID=8177000272E00381B34B674802694705; _const_d_jsession_id_=b5155d95c2b44b11b1879ad3744b8b65.uanalysis.baijia.com; CAS_AC_CURRENT_ROLE=umetric_common_user

- `unit_3861044167111950336`：APIRequestContext.post: Timeout 45000ms exceeded.
Call log:
  - → POST https://uanalysis.baijia.com/uanalysis-intelligence/value/unit
    - user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0
    - accept: */*
    - accept-encoding: gzip,deflate,br
    - content-type: application/json
    - content-length: 308
    - cookie: JSESSIONID=CE2A224FD62DD007B91AE60084CD23A7; _const_d_jsession_id_=b5155d95c2b44b11b1879ad3744b8b65.uanalysis.baijia.com; CAS_AC_CURRENT_ROLE=umetric_common_user

- `unit_3861107228588707841`：APIRequestContext.post: Timeout 45000ms exceeded.
Call log:
  - → POST https://uanalysis.baijia.com/uanalysis-intelligence/value/unit
    - user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0
    - accept: */*
    - accept-encoding: gzip,deflate,br
    - content-type: application/json
    - content-length: 308
    - cookie: JSESSIONID=FEB5B0C23547DB5DDA4B9E32EE17F689; _const_d_jsession_id_=b5155d95c2b44b11b1879ad3744b8b65.uanalysis.baijia.com; CAS_AC_CURRENT_ROLE=umetric_common_user

- `unit_3861106694555324416`：APIRequestContext.post: Timeout 45000ms exceeded.
Call log:
  - → POST https://uanalysis.baijia.com/uanalysis-intelligence/value/unit
    - user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0
    - accept: */*
    - accept-encoding: gzip,deflate,br
    - content-type: application/json
    - content-length: 308
    - cookie: JSESSIONID=B6ED89E01634B522B894E2AE075D1621; _const_d_jsession_id_=b5155d95c2b44b11b1879ad3744b8b65.uanalysis.baijia.com; CAS_AC_CURRENT_ROLE=umetric_common_user

- `unit_3861088496817307649`：APIRequestContext.post: Timeout 45000ms exceeded.
Call log:
  - → POST https://uanalysis.baijia.com/uanalysis-intelligence/value/unit
    - user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0
    - accept: */*
    - accept-encoding: gzip,deflate,br
    - content-type: application/json
    - content-length: 308
    - cookie: JSESSIONID=9751E82C79E96F11479CBC77B72BCBD9; _const_d_jsession_id_=b5155d95c2b44b11b1879ad3744b8b65.uanalysis.baijia.com; CAS_AC_CURRENT_ROLE=umetric_common_user
