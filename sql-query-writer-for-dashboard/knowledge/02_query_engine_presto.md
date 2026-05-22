# Presto 查询引擎规则

## 基本约束

- 只生成 Presto SQL。
- 字符串使用单引号。
- 日期分区 `dt` 通常为 `YYYYMMDD` 字符串。
- 小时分区 `hour` 通常为 `HH` 字符串。
- 时间函数使用 Presto 写法，例如 `format_datetime(now() - interval '1' hour, 'YYYYMMdd')`。

## 常见注意事项

- `group by` 必须包含所有非聚合 select 字段。
- 避免数字字段和字符串字面量混比，例如 `lead_count >= '2'`。
- `row_number()` 取最新记录时，必须明确 `partition by` 主键和 `order by` 时间字段。
- 大表必须加分区条件；小时表建议加 `dt` 和 `hour`。
