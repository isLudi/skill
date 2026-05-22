# temp_table.dingxi01_daoke_1_6_t

## 1. 中文名称

到课课次映射表

## 2. 表用途

稳定临时表，按渠道、期次、年级、开课时间映射第 1-6 课课次，支持首节到课、有效到课和课次到课口径。

数据来源：`E:\2000_work\GAOTU\看板维护表格\daoke_t_one_six.xlsx`，sheet `Sheet1`。

本次扫描：Excel 数据行 2862 行，字段 7 个。检测到空行 1 行。

## 3. 数据粒度

- 渠道-期次-年级-开课时间-课次粒度；Excel 中存在重复 key，join 前建议先 distinct。
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
| qici | string | <YYYYMMDD期> | 是 | 必须限定期次防止扫全表 |
| qudao | string | <渠道> | 是 | 与看板 channel_map_1 关联 |
| grade | string | <年级> | 是 | 与线索年级关联 |
| ke_1 | bigint（Excel 推断） | 1/3 | 是 | 首节到课通常取 1；曹忆IP99元取 3 |

说明：临时表虽然规模不大，但生成看板 SQL 时仍应避免无条件扫全表或无约束 join。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 样例值 | 是否常用 |
|---|---|---|---|---|---|
| qudao | string | 原始渠道/看板渠道匹配字段 | 到课渠道匹配 | 春春ip99元；koc5元；图书KOC | 是 |
| begin_time | string | 开课时间，用于与行课明细的 begin_time 匹配 | 开课时间 join | 2026-01-16 18:20:00；2026-01-16 19:40:00；2026-01-17 18:20:00 | 是 |
| qici | string | 期次，格式通常为 yyyyMMdd期 | 期次过滤/join | 20260116期；20260109期；20260123期 | 是 |
| dow | bigint（Excel 推断） | 周几/星期标签，Excel 中为数字 | 课程时间标签 | 4；5；6 | 否 |
| grade | string | 年级 | 年级维度/join | 高一；高二；高三 | 是 |
| ke_1 | bigint（Excel 推断） | 第 1-6 课课次标签 | 首节/课次到课口径 | 1；2；3 | 是 |
| channel | string | 展示/归因渠道名称 | 渠道展示/聚合 | 陈瑞春；自孵化KOC-5元纯课；图书KOC达人 | 是 |

## 8. 常用过滤条件

- `t.qici = '20260403期'`
- `t.ke_1 in (1, 3)`
- `t.qudao = '<渠道>'`
- `t.grade = '<年级>'`

## 9. 常用 join key

- `qici + qudao + grade + begin_time` 关联 `service_dw.dws_service_user_learn_detail_hf` 的 `qici/channel_map_1/grade_1/begin_time`。
- `ke_1` 只用于课次筛选，不建议单独作为 join key。

本次 Excel key 重复检查：

| join key | 唯一组合数 | 重复组合数 | 涉及重复行数 | 最大重复次数 |
|---|---:|---:|---:|---:|
| qici + qudao + grade + begin_time | 2556 | 306 | 612 | 2 |
| qici + qudao + grade + begin_time + ke_1 | 2556 | 306 | 612 | 2 |

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from temp_table.dingxi01_daoke_1_6_t t
where t.qici = '20260403期'
limit 20;
```

### 字段分布探索

```sql
select
    t.qici,
    count(*) as cnt
from temp_table.dingxi01_daoke_1_6_t t
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
                partition by t.qici, t.qudao, t.grade, t.begin_time
                order by t.qici desc
            ) as rn
        from temp_table.dingxi01_daoke_1_6_t t
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
- 到课看板中：一般渠道首节到课取 `ke_1 = 1`，`曹忆IP99元` 取 `ke_1 = 3`；需与行课表 `begin_time` 严格匹配。

### 流量画像 SQL 使用备注

- `traffic_profile.sql` 使用 `qici + channel + grade + begin_time` 关联，而不是 `qudao` 字段。
- `曹忆` 渠道使用 `ke_1 = '3'` 判断到课/有效到课，其他渠道使用 `ke_1 = '1'`。
- 普通到课判断来自行课表 `live_learn_duration > 0`，有效到课判断来自行课表 `is_valid_live_learn = '1'`；该临时表只提供课次映射。
