# temp_table.zhangjunyan01_pingyou_jg

## 1. 中文名称

评优架构人产临时表

## 2. 表用途

稳定临时表，用于顾问销售评优看板的期次、架构、渠道、年级、人产和是否参评维度。

数据来源：`E:\2000_work\GAOTU\看板维护表格\pingyou_jg.xlsx`，sheet `Sheet4`。

历史 Excel 样本为 1220 行、14 个字段；不能作为当前平台行数。

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
| zaizhi | string（平台 SQL 解析） | 1 | 是 | 通常只取在职顾问 |
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
| zaizhi | string（平台 SQL 解析） | 在职状态标记，常用 1 表示在职 | 在职过滤 | 1；2 | 是 |
| qici | string | 期次，格式通常为 yyyyMMdd期 | 期次过滤/join | 20260101期；20260327期；20260403期 | 是 |
| dept | string | 看板展示架构/部门 | 评优架构维度 | 郑州顾问部；西安一部；西安二部 | 是 |
| jingli | string | 经理/主管姓名 | 经理维度 | 薛源02；吴志强03；靳煜08 | 是 |
| channel | string | 展示/归因渠道名称 | 渠道展示/聚合 | 主动咨询,抖音私域；抖音私域,主动咨询；主动咨询 | 是 |
| renchan | string（平台 SQL 解析） | 人产/目标或基准金额 | 人产/ROI 分母 | 22500；9750；26000 | 是 |
| grade | string | 年级 | 年级维度/join | 高中；高一；高三 | 是 |
| is_emp | string | 是否参与评优，`是` 表示参与，`否` 表示不参与 | 参评人员过滤 | 是；否 | 是 |
| x_qi_count | string（平台 SQL 解析） | 新人有效承接期次序号，用于新人过程展示 | 评优期数维度 | 9；1；2 | 否 |

## 8. 常用过滤条件

- `t.qici >= '20260101期'`
- `t.zaizhi = '1'`
- `t.is_emp = '是'`
- `t.dept = '<架构>'`

其中 `t.is_emp = '是'` 表示仅保留参与评优的人员；如果需求是展示 `pingyou_jg` 已维护的所有在职顾问，不应使用该条件过滤。

## 9. 常用 join key

- `qici + employee_email_name` 关联顾问销售明细的 `qici + name/employee_email_name`。
- `qici + employee_email_name + channel + grade` 用于评优维度更细的匹配，建议 join 前检查唯一性。

历史 Excel 样本的 key 重复检查（当前数据需重新核验）：

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

### 重复键处理

关联前先核验同一顾问期次是否多行。若存在差异行，须依据经业务确认的规则处理；仅按同一个期次排序的 `row_number` 无法确定应保留哪一行。

## 11. 注意事项

- 平台 SQL 解析返回所有 14 列均为 string；完整 DDL 和当前数据质量须另行核验。
- 所有探索查询必须加 `limit`；涉及架构或部门字段时必须加范围限定。
- 如果 join key 存在重复，应先确认差异及业务去重规则，再决定如何处理，避免主表行数被放大。
- Excel 最后一列表头为空且未发现有效值，本文档未将其纳入字段清单。
- 仅在用户明确要求“评优/参评名单/评优架构/人产”口径时使用该表过滤顾问名单。该表含 `qici`，按 `qici + employee_email_name` 关联会把结果限制在本表已维护期次内；如果最新期次未维护，会导致最新期次数据被过滤掉。
- `is_emp` 是“是否参与评优”业务字段：`是` 表示参与评优，`否` 表示不参与评优。不要将其理解为是否在职；在职状态由 `zaizhi` 表示。
- 如果用户不要求严格评优参评名单，只需要市场顾问在职架构范围，应考虑改用 `temp_table.lvshuai01_jiagou_zx` 并说明口径变化。
- 2026-11-28 回读的模型 2688 SQL 已读取本表。此前用户确认接受旧表与本表的数据差异并切换；结构一致不代表历史数据、期次覆盖或唯一性一致。

## 12. 反向联动速查

被以下看板使用：

- `../dashboards/consultant_sales_ranking_evaluation.md`：评优架构、人产、参评顾问范围。

已知风险：

- Web 查询环境正常可用。只在用户明确要求评优/参评名单/评优架构/人产时使用。
- 该表会把结果限制到已维护期次；如果用户问最新期次且查不到，先确认本表是否维护，再判断事实主表是否产出。

## 新人承接期次与结构核验

`x_qi_count` 是维度而不是可求和指标：`1`—`4` 表示前四个有效新人承接期，`9` 表示不进入前四期展示。历史旧表的公式、唯一性和上传规则不能直接作为本表当前数据质量结论；按目标模型核验期次、顾问键和异常值。

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`xiaozu_z`、`employee_email_prefix`、`xiaozu`、`employee_email_name`、`department`、`zaizhi`、`qici`、`dept`、`jingli`、`channel`、`renchan`、`grade`、`is_emp`、`x_qi_count`。
