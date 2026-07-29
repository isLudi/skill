# 市场渠道财务正价课科目结构指标

## 1. 适用模板

- M6：`knowledge/dashboards/market_finance_positive_subject_structure_template.md`
- M8：`knowledge/sql_patterns/market_channel_positive_subject_course_worked_example.md`

## 2. 正价课识别

财务侧候选订单：

```text
real_price <> 0
and trade_type in ('正常订单', '调课调班')
```

再按目标 `qici + user_id` 与线索用户集合关联。该识别在历史结果中可用，但与 2809 运营转化口径不一致，因此整体 contract 保持 `pending_confirmation`。

## 3. 可加总字段

| 字段 | 计算粒度 | 含义 |
|---|---|---|
| `subject_user_count_num` | 组 + 科目 | 购买该科目的去重正价课用户数 |
| `total_positive_user_den` | 组 | 同组去重正价课用户数；在科目行重复展示 |
| `subject_person_count_num` | 组 + 科目 | 科目人次 |
| `total_subject_person_den` | 组 | 同组总科目人次；在科目行重复展示 |
| `subject_amount_num` | 组 + 科目 | 科目净额，元 |
| `total_subject_amount_den` | 组 | 同组全部科目净额，元；在科目行重复展示 |
| `subject_order_count` | 组 + 科目 | 科目订单数 |

“组”在 M6 为 `period + channel + grade + manager`；M8 可继续增加订单类型、课程部门、版本标记、课程、班级和子班维度。

## 4. 聚合规则

- 比率一律在目标展示粒度用分子总和除以唯一分母重算。
- 同一分母随科目重复时，不能跨科目直接求和。
- 用户覆盖占比可因一人多科而跨科目合计超过 100%；这是多科覆盖，不是互斥构成。
- 金额使用财务明细净额；负净额和调课调班链的解释需要与订单口径一起复核。

## 5. 待确认项

- 财务正价课识别能否作为所有渠道的正式口径。
- `trade_type='调课调班'` 是否应计入，以及内部调课如何守恒。
- 财务期次与线索期次的匹配策略是否对所有产品一致。
- M8 的课程部门和版本关键词属于可替换产品分类，不是固定渠道指标。
