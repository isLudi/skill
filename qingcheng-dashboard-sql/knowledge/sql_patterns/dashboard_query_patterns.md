# 看板 SQL 模式

## 1. 推荐结构

复杂看板 SQL 优先使用以下结构：

```sql
with base as (
    select
        ...
    from <库名.事实表> t
    where t.dt = '<yyyy-mm-dd>'
      and <青橙范围字段> = '<青橙范围取值>'
),
metric as (
    select
        ...
    from base
    group by ...
)
select *
from metric
```

## 2. 青橙范围先行

事实主表层优先加青橙范围限定，再做指标计算。不得先计算全量再在外层按青橙过滤，除非历史 SQL 已明确如此设计且不会改变口径。

## 3. 临时表 join

join 青橙临时表前必须确认：

- 临时表是否已入库到 `knowledge/temp_tables/`；
- 临时表数据粒度；
- 临时表有效期；
- 是否会把事实数据限制到临时表名单内；
- join key 是否会产生一对多放大。

## 4. 指标粒度

排名、比率、目标、差值等非明细粒度指标必须说明：

- 指标计算粒度；
- 最终输出粒度；
- 如果两者不一致，前端如何聚合，是否需要 `*_once` 防重复字段。

