# temp_table.dingxi01_pingyou_jg

## 1. 中文名称

评优架构 / 新人承接期次维护临时表。

## 2. 表用途

- 平台标准表名：`temp_table.dingxi01_pingyou_jg`。
- 本地标准文件：`E:\1900_work\GAOTU\19002_市场顾问部看板维护表格\pingyou_jg.xlsx`。
- 平台登记 sheet：`Sheet4`，首行为表头。
- 数据中心模型 `2688`（`新人过程转化数据`）从本表取得顾问架构、渠道、人产和 `x_qi_count`。
- 2026-07-21 已验证版本：仅保留 `Sheet4`，数据行 5920 行、字段 14 个，文件 SHA-256 为 `885bedc830a5b3bc19c87fc34feee3c6d5262d90376e6937dd54ddee78c4e7ad`。

该表与 `temp_table.zhangjunyan01_pingyou_jg` 不是同一物理表。顾问销售评优脚本当前主要读取 `zhangjunyan01` 表；模型 `2688` 明确读取本表。不得只根据文件名 `pingyou_jg.xlsx` 猜测目标表，必须以当前 canonical SQL 和手工表 registry 为准。

## 3. 数据粒度

- 业务粒度：顾问 × 期次 × 评优/新人架构属性。
- 模型 `2688` 的实际关联键：`employee_email_name + qici`。
- 2026-07-21 本地终版与平台回读均确认：`employee_email_name + qici` 重复键为 0。
- `employee_email_name + x_qi_count` 在 `x_qi_count in (1,2,3,4)` 范围内必须唯一；值 `9` 允许跨多期重复。

## 4. 查询引擎

Presto。

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| 无 | 无 | 稳定临时表，无 `dt` / `hour` 分区 | 否 |

## 6. 强制范围限定字段

| 字段名 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|
| `qici` | `YYYYMMDD期` 或有界区间 | 是 | 排查、抽样和 join 必须限定期次 |
| `employee_email_name` | 指定顾问 | 条件必填 | 顾问问题优先限定姓名/编号 |
| `department` / `dept` | 指定部门 | 条件必填 | 部门问题限定原始或展示架构 |
| `channel` | 指定渠道 | 条件必填 | 渠道问题限定渠道 |

至少使用 `qici`，并根据问题增加顾问、部门或渠道条件；不要无条件把该表与大事实表全量关联。

## 7. 字段清单

| 字段名 | 维护含义 | 常见用途 | 约束 |
|---|---|---|---|
| `xiaozu_z` | 小组长邮箱前缀 | 架构标识 | 小写 ASCII 前缀 |
| `employee_email_prefix` | 顾问邮箱前缀 | 员工关联键 | 小写 ASCII 前缀 |
| `xiaozu` | 小组长姓名/编号 | 小组维度 | 不得因历史换组直接全表覆盖 |
| `employee_email_name` | 顾问姓名/编号 | 模型 `2688` 关联键 | 与 `qici` 组成唯一键 |
| `department` | 原始部门 | 部门范围 | 不得为空 |
| `zaizhi` | 在职状态 | 在职过滤 | 常见值 `1` / `2`，以业务维护为准 |
| `qici` | 业务期次 | 关联和筛选 | 固定格式 `YYYYMMDD期` |
| `dept` | 看板展示部门 | 展示维度 | 不得为空 |
| `jingli` | 经理 | 经理维度 | 历史期次可随组织变化 |
| `channel` | 渠道 | 渠道维度 | 不得为空 |
| `renchan` | 人产/目标 | 目标值 | 数值型维护 |
| `grade` | 年级 | 年级维度 | 上传前必须补全，不得留空 |
| `is_emp` | 是否参与评优 | 参评范围 | `是` / `否`；不同于 `zaizhi` |
| `x_qi_count` | 新人有效承接期次序号 | 模型 `2688` 的“承接期次”维度 | 仅允许 `1,2,3,4,9` |

平台上传会按内容推断字段类型；`x_qi_count` 在 Excel 中应维护为整数，但 SQL 中需以当前平台 DDL 为准。模型 `2688` 当前使用 `where ppg.x_qi_count not in ('9')` 排除值 `9`。

## 8. 常用过滤条件

- `t.qici = '20260716期'`
- `t.qici >= '20260101期' and t.qici <= '20260716期'`
- `t.employee_email_name = '<顾问>'`
- `t.department = '郑州市场顾问部'`
- `cast(t.x_qi_count as varchar) in ('1','2','3','4')`

## 9. 常用 join key

- 模型 `2688`：`ppg.employee_email_name = zz.employee_email_name and ppg.qici = zz.period_name`。
- 需要更细渠道/年级粒度时，可评估 `employee_email_name + qici + channel + grade`，但必须先做重复键 Probe；不要擅自把它替换为模型 `2688` 的已确认关联键。
- 同名顾问风险需结合 `employee_email_prefix` 排查；现有模型因事实聚合字段限制仍按 `employee_email_name + qici` 关联。

## 10. 常用 SQL 片段

### 期次范围与行数

```sql
select
    min(qici) as min_qici,
    max(qici) as max_qici,
    count(distinct qici) as qici_count,
    count(*) as row_count
from temp_table.dingxi01_pingyou_jg
where qici >= '20260101期';
```

### 顾问期次重复键

```sql
select employee_email_name, qici, count(*) as cnt
from temp_table.dingxi01_pingyou_jg
where qici >= '20260101期'
group by employee_email_name, qici
having count(*) > 1
limit 100;
```

### 顾问有效序号重复

```sql
select
    employee_email_name,
    cast(x_qi_count as varchar) as x_qi_count,
    count(distinct qici) as repeated_qici_count
from temp_table.dingxi01_pingyou_jg
where qici >= '20260101期'
  and cast(x_qi_count as varchar) in ('1','2','3','4')
group by employee_email_name, cast(x_qi_count as varchar)
having count(distinct qici) > 1
limit 100;
```

## 11. 注意事项

- `x_qi_count` 由 Excel 原样传入，模型不会替业务重新计算或自动去重。出现跨期重复时先修源表，不要先在最终 SQL 外层加 `distinct`。
- 终版只能保留 `Sheet4` 和上述 14 列；不得残留公式、辅助列或其他 sheet。
- 14 列所有数据行必须非空。本次 6 个空 `grade` 行在上传后发生字段错位并形成 `qici='1'`。
- 上传必须使用登记表 `dingxi01_pingyou_jg` 和 `overwrite` 全量覆盖，禁止 append；回执数据量必须等于本地数据行数。
- `xiaozu_z`、`employee_email_prefix` 使用小写 ASCII。
- `曹可悦` 跨期对应不同经理/小组属于已核验的历史组织变化，不能只因一人多主管就删除历史行。
- 若临时表已有最新期次而模型仍缺失，继续检查 `data_center_market_2688.sql` 的线索、开课和员工入部门日期角色是否都映射同一暑期业务日历。

## 12. `x_qi_count` 业务含义

`x_qi_count` 不是可求和指标，而是“该顾问进入新人观察口径后的第几个有效承接期次”维度：

- `1`：第 1 个有效新人承接期次。
- `2`：第 2 个有效新人承接期次。
- `3`：第 3 个有效新人承接期次。
- `4`：第 4 个有效新人承接期次。
- `9`：不进入新人前四期展示；包括原本已标记为 `9` 的排除行，以及第 5 个及以后有效期次。

维护原则：先保留原表中已经为 `9` 的行；只对原来非 `9` 的行按同一顾问的 `qici` 升序重新编号为 `1,2,3,4`，第 5 个及以后改为 `9`。不能把历史 `9` 自动重新激活为 `1`—`4`。

示例：蔡铁骑应为 `20260619期=1 → 20260626期=2 → 20260703期=3 → 20260710期=4 → 20260716期=9`。耿玉琳原值 `1,2,"3,2",4,9` 中，`"3,2"` 是非法文本，修正后为 `1,2,3,4,9`。

## 13. Excel 维护公式

终版不得新增字段。计算时可以临时使用 O 列，完成后粘贴为值并删除 O 列：

1. 将原 N 列 `x_qi_count` 复制为值到临时 O 列，作为“原始是否为 9”的判断依据。
2. 先删除完全重复行，并确认 `D 列 employee_email_name + G 列 qici` 唯一。
3. 在 N2 输入下式并向下填充。当前 5920 行数据的末行是 5921；行数变化时同步替换公式中的末行。

```excel
=IF(OR($O2="",$O2=9),9,LET(k,COUNTIFS($D$2:$D$5921,$D2,$G$2:$G$5921,"<="&$G2,$O$2:$O$5921,"<>9",$O$2:$O$5921,"<>"),IF(k<=4,k,9)))
```

4. 完整重算后，将 N 列公式粘贴为值，删除临时 O 列。
5. 终版必须仍为 14 个字段，且不得残留公式。

固定宽度 `YYYYMMDD期` 可以按文本升序比较；若 `qici` 出现 `1`、空值或其他非标准格式，必须先修复，不能直接套公式。

## 14. 2026-07-21 已验证状态

- 平台行数：5920。
- 期次范围：`20260101期` 至 `20260716期`，共 28 个期次。
- 非法 `x_qi_count`：0。
- `employee_email_name + qici` 重复键：0。
- 顾问有效 `x_qi_count` 重复键：0。
- 最新期次 `20260716期` 分布：`1=5`、`2=2`、`3=6`、`4=1`、`9=205`。

专项故障复盘见 `../pitfalls/newcomer_x_qi_count_and_pingyou_upload.md`；暑期期次边界见 `../sql_patterns/market_summer_qici_corrections.md`；当前模型 SQL 见 `../../resources/raw_sql/data_center_market_2688.sql`。
