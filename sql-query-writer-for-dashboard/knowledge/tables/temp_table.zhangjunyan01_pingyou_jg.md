# temp_table.zhangjunyan01_pingyou_jg

## 1. 中文名称

评优架构人产临时表

## 2. 表用途

稳定临时表，用于顾问销售评优看板的期次、架构、渠道、年级、人产和是否参评维度。

数据来源：`E:\2000_work\GAOTU\看板维护表格\pingyou_jg.xlsx`，sheet `Sheet4`。

本次扫描：Excel 数据行 1220 行，字段 14 个。

## 3. 数据粒度

- 顾问-期次-渠道-年级-架构粒度；存在 1 个空表头列，知识库已忽略。
- 稳定临时表，无 `dt`/`hour` 分区，生成 SQL 时必须用期次、架构、渠道或员工条件收窄范围。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| 无 | 无 | 稳定临时表无 dt/hour 分区 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| qici | string | <YYYYMMDD期> | 是 | 无分区表，必须限定期次 |
| department | string | <部门> | 是 | 原始部门范围限定 |
| dept | string | <展示架构> | 是 | 看板架构范围限定 |
| channel | string | <渠道> | 是 | 评优渠道维度 |
| grade | string | <年级> | 是 | 评优年级维度 |
| zaizhi | bigint（Excel 推断） | 1 | 是 | 通常只取在职顾问 |
| is_emp | string | 是 | 是 | 是否参与评优，`是` 表示参与，`否` 表示不参与 |

说明：临时表虽然规模不大，但生成看板 SQL 时仍应避免无条件扫全表或无约束 join。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 样例值 | 是否常用 |
|---|---|---|---|---|---|
| xiaozu_z | string | 小组长邮箱前缀/拼音标识 | 小组长标识 | xueyuan02；guojiyuan；lixiya02 | 否 |
| employee_email_prefix | string | 顾问/员工邮箱前缀 | 顾问 join key | qiujunwu；mahuilong；liangzhihua | 是 |
| xiaozu | string | 小组长姓名或带编号姓名 | 小组维度 | 薛源02；郭纪园；李西亚02 | 是 |
| employee_email_name | string | 顾问/员工姓名，部分值带数字编号 | 顾问 join key | 邱君武；马会龙；梁志华 | 是 |
| department | string | 架构/部门名称 | 架构范围限定 | 郑州市场顾问部；西安市场顾问部 | 是 |
| zaizhi | bigint（Excel 推断） | 在职状态标记，常用 1 表示在职 | 在职过滤 | 1；2 | 是 |
| qici | string | 期次，格式通常为 yyyyMMdd期 | 期次过滤/join | 20260101期；20260327期；20260403期 | 是 |
| dept | string | 看板展示架构/部门 | 评优架构维度 | 郑州顾问部；西安一部；西安二部 | 是 |
| jingli | string | 经理/主管姓名 | 经理维度 | 薛源02；吴志强03；靳煜08 | 是 |
| channel | string | 展示/归因渠道名称 | 渠道展示/聚合 | 主动咨询,抖音私域；抖音私域,主动咨询；主动咨询 | 是 |
| renchan | bigint（Excel 推断） | 人产/目标或基准金额 | 人产/ROI 分母 | 22500；9750；26000 | 是 |
| grade | string | 年级 | 年级维度/join | 高中；高一；高三 | 是 |
| is_emp | string | 是否参与评优，`是` 表示参与，`否` 表示不参与 | 参评人员过滤 | 是；否 | 是 |
| x_qi_count | bigint（Excel 推断） | 连续/统计期数，用于评优维度 | 评优期数维度 | 9；1；2 | 否 |

## 8. 常用过滤条件

- `t.qici >= '20260101期'`
- `t.zaizhi = '1'`
- `t.is_emp = '是'`
- `t.dept = '<架构>'`

其中 `t.is_emp = '是'` 表示仅保留参与评优的人员；如果需求是展示 `pingyou_jg` 已维护的所有在职顾问，不应使用该条件过滤。

## 9. 常用 join key

- `qici + employee_email_name` 关联顾问销售明细的 `qici + name/employee_email_name`。
- `qici + employee_email_name + channel + grade` 用于评优维度更细的匹配，建议 join 前检查唯一性。

本次 Excel key 重复检查：

| join key | 唯一组合数 | 重复组合数 | 涉及重复行数 | 最大重复次数 |
|---|---:|---:|---:|---:|
| qici + employee_email_name | 1219 | 1 | 2 | 2 |
| qici + employee_email_name + channel + grade | 1219 | 1 | 2 | 2 |

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from temp_table.zhangjunyan01_pingyou_jg t
where t.qici >= '20260101期'
limit 20;
```

### 字段分布探索

```sql
select
    t.qici,
    count(*) as cnt
from temp_table.zhangjunyan01_pingyou_jg t
group by t.qici
order by cnt desc
limit 50;
```

### 去重 join 前处理模板

```sql
with mapped as (
    select *
    from (
        select
            t.*,
            row_number() over (
                partition by t.qici, t.employee_email_name
                order by t.qici desc
            ) as rn
        from temp_table.zhangjunyan01_pingyou_jg t
    ) x
    where x.rn = 1
)
select *
from mapped
limit 20;
```

## 11. 注意事项

- 字段类型来自 Excel 内容推断，若查询平台中实际 DDL 不同，以平台为准。
- 所有探索查询必须加 `limit`；涉及架构或部门字段时必须加范围限定。
- 如果 join key 存在重复，生成 SQL 时需使用 `row_number`、`distinct` 或先聚合，避免主表行数被放大。
- Excel 最后一列表头为空且未发现有效值，本文档未将其纳入字段清单。
- 仅在用户明确要求“评优/参评名单/评优架构/人产”口径时使用该表过滤顾问名单。该表含 `qici`，按 `qici + employee_email_name` 关联会把结果限制在本表已维护期次内；如果最新期次未维护，会导致最新期次数据被过滤掉。
- `is_emp` 是“是否参与评优”业务字段：`是` 表示参与评优，`否` 表示不参与评优。不要将其理解为是否在职；在职状态由 `zaizhi` 表示。
- 如果用户不要求严格评优参评名单，只需要市场顾问在职架构范围，应考虑改用 `temp_table.dingxi01_jiagou_zx` 并说明口径变化。
- 不要与 `temp_table.dingxi01_pingyou_jg` 混用：模型 `2688`（新人过程转化数据）当前读取 `dingxi01` 表；本表主要服务当前顾问销售评优 SQL。两个表即使都来自同名 Excel，也必须按 canonical SQL 的物理表名分别维护和校验。

## 12. 反向联动速查

被以下看板使用：

- `../dashboards/consultant_sales_ranking_evaluation.md`：评优架构、人产、参评顾问范围。

已知风险：

- Web 查询环境正常可用。只在用户明确要求评优/参评名单/评优架构/人产时使用。
- 该表会把结果限制到已维护期次；如果用户问最新期次且查不到，先确认本表是否维护，再判断事实主表是否产出。
