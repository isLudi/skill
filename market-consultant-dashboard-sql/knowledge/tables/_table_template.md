# 完整库名.表名

## 1. 中文名称

待填写

## 2. 表用途

待填写

## 3. 数据粒度

待确认

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级分区 yyyyMMdd | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|

说明：
- 对所有 department_name 相关字段，标记为需要范围限定；
- 不知道默认值时，推荐取值写 `'<待填写>'`。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|

## 8. 常用过滤条件

## 9. 常用 join key

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from 完整库名.表名 t
where t.dt = 'YYYYMMDD'
limit 20;
```

### 最近小时分区抽样

```sql
select *
from 完整库名.表名 t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
limit 20;
```

### 按 dt/hour 统计分区数据量

```sql
select t.dt, t.hour, count(*) as cnt
from 完整库名.表名 t
where t.dt in ('YYYYMMDD')
group by t.dt, t.hour
order by t.dt desc, t.hour desc
limit 50;
```

### 字段分布探索

```sql
select t.字段名, count(*) as cnt
from 完整库名.表名 t
where t.dt = 'YYYYMMDD'
group by t.字段名
order by cnt desc
limit 50;
```

### 每用户或每线索取最新记录

```sql
select *
from (
    select
        t.*,
        row_number() over (
            partition by t.user_number
            order by t.update_time desc
        ) as rn
    from 完整库名.表名 t
    where t.dt = 'YYYYMMDD'
) x
where x.rn = 1
limit 100;
```

## 11. 注意事项

- 分区限制：待确认。
- department_name 范围限定：待确认。
- 字段类型注意事项：待确认。
- 常见报错：待确认。
- 待人工确认问题：待确认。
