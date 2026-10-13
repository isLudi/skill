# temp_table.dingxi01_ceshiqudao_pingyou

## 1. 中文名称

评优测试渠道指标临时表。

## 2. 表用途

市场顾问部半年度评优数据集 2644 已使用的手工临时表。`usql-web-query-operator/references/manual_temp_table_registry.json` 登记来源为市场顾问部的 `ceshiqudao_pingyou.xlsx`，表头为 `qici, qudao, name, gmv, gmv_goal, gmv_rate`。

2026-10-09 在线只读 Query ID `1622218726` 使用 `typeof(max(字段))` 验证上述六个字段均为 `string`。Query ID `1622218740` 经精确历史回读确认 `Success`，结果 API 返回的全列元数据恰为上述六个字段；没有重新提交该查询。查询用恒假条件排除所有数据行，返回的 `scanned_rows=0` 是验证设计，不代表表为空、顾问无业绩或期次未维护。本记录不宣称取得了完整 DDL。

## 3. 数据粒度

Registry 表头含期次、渠道和姓名；`qici + qudao + name` 是否唯一尚未验证，不登记为已确认主键。2644 的 `ceshi_metric` CTE 按 `name` 聚合，最终按员工姓名关联；这是现有 SQL 的使用事实，不是新的 Join 或指标契约。

## 4. 查询引擎

在线 `Presto_lakehouse` 查询环境。不要根据引擎名称将平台返回的 `string` 类型改记为数值类型。

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| 无已登记 dt/hour | 无 | Registry 按稳定手工临时表维护；未取得分区 DDL | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| qici | string | 按请求明确期次 | 探索时收窄 | 不为已有半年度聚合新增期次过滤 |
| name | string | 按请求明确员工 | 探索时收窄 | 不将姓名列自动视为邮箱前缀或唯一键 |

未观察到组织部门列。本次登记不授权改变任何生产 SQL 的部门、期次或参评范围。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 样例值 | 是否常用 |
|---|---|---|---|---|---|
| qici | string | Registry 中的期次列 | 期次筛选 | 未读取数据值 | 是 |
| qudao | string | Registry 中的渠道列 | 渠道维度 | 未读取数据值 | 是 |
| name | string | 姓名列；2644 聚合后的员工姓名关联字段 | 员工聚合/关联 | 未读取数据值 | 是 |
| gmv | string | 现有 SQL 显式 cast 为 double 后用于比值分子 | 测试渠道指标 | 未读取数据值 | 是 |
| gmv_goal | string | 现有 SQL 显式 cast 为 double 后用于比值分母 | 测试渠道指标 | 未读取数据值 | 是 |
| gmv_rate | string | Registry 中的比率列；2644 当前 CTE 不直接使用 | 原始维护字段 | 未读取数据值 | 否 |

## 8. 常用过滤条件

探索时使用具体员工及期次，并保留 `limit`。2644 现有 CTE 使用 `name is not null`；本次未改动此条件，也未把它提升为其他需求的默认范围。

## 9. 常用 join key

2644 先按 `name` 聚合为每个姓名一行，再按 `employee_email_name` 关联。原表姓名和复合键唯一性均未验证，不能直接将原表明细 Join 到金额流水。

## 10. 常用 SQL 片段

仅核对字段类型、不读取数据行：

```sql
select typeof(max(t.gmv)) as gmv_type
from temp_table.dingxi01_ceshiqudao_pingyou t
where t.name = '<具体员工姓名>' and t.qici = '<具体期次>' and 1 = 0
limit 1
```

## 11. 注意事项

- 六个已核验字段都是 `string`；不要仅按列名推断为数值。转换异常、单位、NULL 和非法字符串处理均需另行取证，不能通过目录登记重新定义。
- 2644 当前按 `cast(gmv as double) / nullif(cast(gmv_goal as double), 0) > 0.8` 生成标志，并按姓名取 `max`。本次不修改这一业务口径。
- 不属于青橙项目部，不改动另一部门的目录或业务契约。DataMap 字段同步适配器跳过 `temp_table.*`，本表依据现有临时表 Registry 和在线只读类型验证登记。
- 临时表数据、上传配置、参评名单及生产 SQL 均未变更。
