# finance_dw.app_finance_performance_extend_details_hf

## 1. 中文名称

业绩归属信息扩展表

## 2. 表用途

该表用于记录财务口径的业绩归属、订单交易、前后置课程、员工与组织架构等信息。评优/顾问销售排名 SQL 使用该表计算顾问销售额、退款额、净收、ROI 等指标。

## 3. 数据粒度

- 订单/交易明细-小时快照粒度
- 同一订单可能因业绩归属、调课调班、退款等产生多条明细，查询时需结合 `id` 和订单号去重。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |
| hour | string | 小时分区 | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| employee_first_level_department_name | string | 'H业务线' | 是 | 业绩归属人一级部门，评优 SQL 常用范围 |
| employee_second_level_department_name | string | '市场部' | 是 | 业绩归属人二级部门，评优 SQL 常用范围 |
| employee_third_level_department_name | string | '市场顾问部' | 是 | 业绩归属人三级部门，评优 SQL 常用范围 |
| course_top_level_department_name | string | '<头部部门名称>' | 是 | 后置课程头部部门 |
| course_first_level_department_name | string | '<一级部门名称>' | 是 | 后置课程一级部门 |
| course_second_level_department_name | string | '<二级部门名称>' | 是 | 后置课程二级部门 |
| course_third_level_department_name | string | '<三级部门名称>' | 是 | 后置课程三级部门 |
| pre_course_top_level_department_name | string | '<头部部门名称>' | 是 | 前置课程头部部门 |
| pre_course_first_level_department_name | string | '<一级部门名称>' | 是 | 前置课程一级部门 |
| pre_course_second_level_department_name | string | '<二级部门名称>' | 是 | 前置课程二级部门 |
| pre_course_third_level_department_name | string | '<三级部门名称>' | 是 | 前置课程三级部门 |
| department | string | '<部门/架构名称>' | 是 | 业绩归属部门字段，虽非 department_name 也应按架构限定 |
| department_path | string | '<部门路径>' | 是 | 业绩归属人组织架构 |
| pre_assistant_department_path | string | '<部门路径>' | 是 | 前置辅导老师组织架构 |
| assistant_department_path | string | '<部门路径>' | 是 | 后置辅导老师组织架构 |

说明：凡查询中使用 `department_name` 相关字段或组织/架构字段，SQL 必须加范围限定。不确定取值时使用占位符并在说明中标注待替换。

## 7. 字段清单

字段来源：`E:\2000_work\GAOTU\新建 Microsoft Word 文档.docx`，共 145 个非分区字段。

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| id | bigint | 业绩归属Id | 标识/关联键 | 是 |
| order_number | bigint | 后置订单号 | 标识/关联键 | 是 |
| pre_order_number | bigint | 前置订单号 | 标识/关联键 | 否 |
| user_id | bigint | 用户id | 标识/关联键 | 是 |
| pre_subclazz_number | bigint | 前置辅导班 | 课程/班级维度 | 否 |
| pre_employee_id | int | 业绩归属人ID | 员工/顾问维度 | 是 |
| type | string | "业绩归属类型：0, 无归属。1, 长期班保护期续班。2, 长期班扩科。3, 长期班召回。4, 长期班窗口期扩科。5, 长期班保护期外出单。6, 短期班保护期续班。7, 短期班扩科。8, 短期班召回。9, 短期班保护期外出单。10, 其他扩科。11,12, 好课扩科。13，入口班保护期续班，14，入口班保护期扩科，15，入口班召回。16，转介绍。21，续班。22，扩科。23，召回。24，拉新。" | 状态/类型过滤 | 否 |
| judge_type | string | "判断类型：1，独立。2，继承。3，重判。" | 状态/类型过滤 | 否 |
| real_price | double | "实付金额" | 金额/占比指标 | 是 |
| transfer_price | double | 调课金额（调入调出） | 金额/占比指标 | 是 |
| user_ratio | double | 人数占比 | 金额/占比指标 | 否 |
| price_ratio | double | 金额占比 | 金额/占比指标 | 否 |
| order_ratio | double | 订单占比 | 金额/占比指标 | 否 |
| trade_status | string | 交易状态 | 状态/类型过滤 | 是 |
| trade_type | string | 交易类型 | 状态/类型过滤 | 是 |
| trade_time | string | 交易时间 | 时间过滤/期次归属 | 是 |
| pre_paid_time | string | 前置订单的支付时间 | 时间过滤/期次归属 | 否 |
| renewal_type | string | 续班类型：前置学季 - 后置学季 | 状态/类型过滤 | 否 |
| price | double | （支付金额 + 调课金额） * 金额占比 | 金额/占比指标 | 是 |
| top_order_number | bigint | 后置订单的原始父订单 | 标识/关联键 | 否 |
| pre_top_order_number | bigint | 前置订单的原始父订单 | 标识/关联键 | 否 |
| display_number | bigint | 员工工号 | 员工/顾问维度 | 否 |
| employee_name | string | 员工姓名 | 员工/顾问维度 | 否 |
| employee_email_name | string | 员工姓名（带编号） | 员工/顾问维度 | 是 |
| email_prefix | string | 邮箱前缀 | 员工/顾问维度 | 是 |
| is_on_job | bigint | 是否在职 | 状态/类型过滤 | 否 |
| city_code | bigint | 城市编码 | 状态/类型过滤 | 否 |
| city_name | string | 城市名称 | 明细属性 | 否 |
| talent_type_code | bigint | 人才类型编码 | 状态/类型过滤 | 否 |
| talent_type_name | string | 人才类型名称 | 状态/类型过滤 | 否 |
| first_enroll_date | string | 首次入职时间 | 时间过滤/期次归属 | 否 |
| last_enroll_date | string | 最后一次入职时间 | 时间过滤/期次归属 | 否 |
| last_resign_date | string | 最后一次离职时间 | 时间过滤/期次归属 | 否 |
| department_path | string | 组织架构 | 组织架构范围限定 | 是 |
| department_code_path | string | 组织架构编码 | 组织架构范围限定 | 否 |
| position_number | bigint | 职位编码 | 标识/关联键 | 否 |
| position_name | string | 职位名称 | 明细属性 | 否 |
| leader_display_number | bigint | 上级员工工号 | 员工/顾问维度 | 否 |
| leader_employee_email_name | string | 上级员工姓名 | 员工/顾问维度 | 是 |
| pre_biz_number | string | 前置辅导班业务id | 标识/关联键 | 否 |
| pre_subclazz_name | string | 前置辅导班名称 | 课程/班级维度 | 否 |
| pre_subclazz_status | int | 前置辅导班状态 | 课程/班级维度 | 否 |
| pre_clazz_number | bigint | 前置班级number | 课程/班级维度 | 否 |
| pre_clazz_biz_number | string | 前置班级业务id | 课程/班级维度 | 否 |
| pre_clazz_name | string | 前置班级名称 | 课程/班级维度 | 否 |
| pre_clazz_type_name | string | 前置班级标签 | 课程/班级维度 | 否 |
| pre_clazz_classify_type | int | 前置班级类型 | 课程/班级维度 | 否 |
| pre_course_number | bigint | 前置课程编号 | 课程/班级维度 | 否 |
| pre_course_biz_number | string | 前置课程业务编号 | 课程/班级维度 | 否 |
| pre_course_name | string | 前置课程名称 | 课程/班级维度 | 否 |
| pre_course_subject | string | 前置科目 | 课程/班级维度 | 否 |
| pre_course_term_id | string | 前置学季 | 课程/班级维度 | 否 |
| pre_course_year | string | 前置学年 | 课程/班级维度 | 否 |
| pre_course_type | int | 前置课程类型 | 课程/班级维度 | 否 |
| pre_course_grade | string | 前置年级 | 课程/班级维度 | 否 |
| pre_assistant_number | bigint | 前置辅导老师number | 课程/班级维度 | 否 |
| pre_assistant_email_prefix | string | 前置辅导老师邮箱前缀 | 员工/顾问维度 | 否 |
| pre_assistant_name | string | 前置辅导老师姓名 | 课程/班级维度 | 否 |
| pre_assistant_talent_type | int | 前置辅导老师人才类型编号 | 课程/班级维度 | 否 |
| pre_assistant_talent_type_name | string | 前置辅导老师人才类型名称 | 课程/班级维度 | 否 |
| pre_assistant_city_code | int | 前置辅导老师城市code | 课程/班级维度 | 否 |
| pre_assistant_city | string | 前置辅导老师城市名称 | 课程/班级维度 | 否 |
| pre_teacher_email_prefix | string | 前置主讲老师邮箱前缀 | 员工/顾问维度 | 否 |
| pre_teacher_name | string | 前置主讲老师名称 | 课程/班级维度 | 否 |
| pre_teacher_number | bigint | 前置主讲老师number | 课程/班级维度 | 否 |
| pre_teacher_talent_type | int | 前置主讲老师人才类型 | 课程/班级维度 | 否 |
| pre_teacher_talent_type_name | string | 前置主讲老师人才类型名称 | 课程/班级维度 | 否 |
| pre_course_department | string | 前置课程学部 | 组织架构范围限定 | 否 |
| pre_teacher_nickname | string | 前置主讲老师昵称 | 课程/班级维度 | 否 |
| subclazz_number | bigint | 后置辅导班number | 课程/班级维度 | 否 |
| biz_number | string | 后置辅导班业务id | 标识/关联键 | 是 |
| subclazz_name | string | 后置辅导班名称 | 课程/班级维度 | 否 |
| subclazz_status | int | 后置辅导班状态 | 课程/班级维度 | 否 |
| clazz_number | bigint | 后置班级number | 课程/班级维度 | 否 |
| clazz_biz_number | string | 后置班级业务id | 课程/班级维度 | 否 |
| clazz_name | string | 后置班级名称 | 课程/班级维度 | 是 |
| clazz_type_name | string | 后置班级标签 | 课程/班级维度 | 否 |
| clazz_classify_type | int | 后置班级类型 | 课程/班级维度 | 否 |
| course_number | bigint | 后置课程number | 课程/班级维度 | 否 |
| course_biz_number | string | 后置课程业务id | 课程/班级维度 | 否 |
| course_name | string | 后置课程名称 | 课程/班级维度 | 否 |
| course_subject | string | 后置科目 | 课程/班级维度 | 是 |
| course_term_id | string | 后置学季 | 课程/班级维度 | 是 |
| course_year | string | 后置学年 | 课程/班级维度 | 否 |
| course_type | int | 后置课程类型 | 课程/班级维度 | 否 |
| course_grade | string | 后置年级 | 课程/班级维度 | 是 |
| assistant_number | bigint | 后置辅导老师number | 课程/班级维度 | 否 |
| assistant_email_prefix | string | 后置辅导老师邮箱前缀 | 员工/顾问维度 | 否 |
| assistant_name | string | 后置辅导老师姓名 | 课程/班级维度 | 否 |
| assistant_talent_type | int | 后置辅导老师人才类型 | 课程/班级维度 | 否 |
| assistant_talent_type_name | string | 后置辅导老师人才类型名称 | 课程/班级维度 | 否 |
| assistant_city_code | int | 后置辅导老师城市 | 课程/班级维度 | 否 |
| assistant_city | string | 后置辅导老师城市名称 | 课程/班级维度 | 否 |
| teacher_email_prefix | string | 后置主讲老师邮箱前缀 | 员工/顾问维度 | 否 |
| teacher_name | string | 后置主讲老师姓名 | 课程/班级维度 | 是 |
| teacher_number | bigint | 后置主讲老师number | 课程/班级维度 | 否 |
| teacher_talent_type | int | 后置主讲老师人才类型 | 课程/班级维度 | 否 |
| teacher_talent_type_name | string | 主讲老师人才类型名称 | 课程/班级维度 | 否 |
| course_department | string | 后置课程学部 | 组织架构范围限定 | 否 |
| teacher_nickname | string | 后置主讲老师昵称 | 课程/班级维度 | 否 |
| order_price | double | 订单金额 | 金额/占比指标 | 否 |
| order_refund_price | double | 退款金额 | 金额/占比指标 | 否 |
| order_paid_time | string | 支付时间 | 时间过滤/期次归属 | 是 |
| order_status | string | 订单状态 | 状态/类型过滤 | 否 |
| department | string | 学部 | 组织架构范围限定 | 是 |
| note | string | 全部退款不扣绩效备注 | 状态/类型过滤 | 否 |
| pre_clazz_begin_time | string | 前置班级开课时间 | 时间过滤/期次归属 | 否 |
| clazz_begin_time | string | 后置班级开课时间 | 时间过滤/期次归属 | 否 |
| type_code | int | 业绩归属类型编码 | 状态/类型过滤 | 否 |
| judge_type_code | int | 判单类型编码 | 状态/类型过滤 | 否 |
| trade_status_code | int | 交易状态编码 | 状态/类型过滤 | 否 |
| trade_type_code | int | 交易类型编码 | 状态/类型过滤 | 否 |
| order_status_code | int | 订单状态编码 | 状态/类型过滤 | 否 |
| department_code | int | 学部编码 | 组织架构范围限定 | 否 |
| note_code | int | 全部退款不扣绩效备注 | 状态/类型过滤 | 否 |
| gray_type | int | 灰名单类型 | 状态/类型过滤 | 否 |
| is_black | int | 黑名单标识，1:是，0：否 | 状态/类型过滤 | 否 |
| top_paid_time | string | 原始父订单支付时间 | 时间过滤/期次归属 | 否 |
| pre_assistant_department_path | string | 前置辅导老师组织架构 | 组织架构范围限定 | 否 |
| assistant_department_path | string | 后置辅导老师组织架构 | 组织架构范围限定 | 否 |
| refund_order_number | string | 退款记录编号 | 金额/占比指标 | 否 |
| pre_clazz_end_time | string | 前置开课时间 | 时间过滤/期次归属 | 否 |
| clazz_end_time | string | 后置开课时间 | 时间过滤/期次归属 | 否 |
| employee_first_level_department_name | string | 业绩归属人一级部门名称 | 组织架构范围限定 | 是 |
| employee_first_level_department_code | bigint | 业绩归属人一级部门编码 | 组织架构范围限定 | 否 |
| employee_second_level_department_name | string | 业绩归属人二级部门名称 | 组织架构范围限定 | 是 |
| employee_second_level_department_code | bigint | 业绩归属人二级部门编码 | 组织架构范围限定 | 否 |
| employee_third_level_department_name | string | 业绩归属人三级部门名称 | 组织架构范围限定 | 是 |
| employee_third_level_department_code | bigint | 业绩归属人三级部门编码 | 组织架构范围限定 | 否 |
| course_top_level_department_code | bigint | 后置课程头部部门代码 | 组织架构范围限定 | 否 |
| course_top_level_department_name | string | 后置课程头部部门名称 | 组织架构范围限定 | 是 |
| course_first_level_department_code | bigint | 后置课程一级部门代码 | 组织架构范围限定 | 否 |
| course_first_level_department_name | string | 后置课程一级部门名称 | 组织架构范围限定 | 是 |
| course_second_level_department_code | bigint | 后置课程二级部门代码 | 组织架构范围限定 | 否 |
| course_second_level_department_name | string | 后置课程二级部门名称 | 组织架构范围限定 | 是 |
| course_third_level_department_code | bigint | 后置课程三级部门代码 | 组织架构范围限定 | 否 |
| course_third_level_department_name | string | 后置课程三级部门名称 | 组织架构范围限定 | 是 |
| pre_course_top_level_department_code | bigint | 前置课程头部部门代码 | 组织架构范围限定 | 否 |
| pre_course_top_level_department_name | string | 前置课程头部部门名称 | 组织架构范围限定 | 是 |
| pre_course_first_level_department_code | bigint | 前置课程一级部门代码 | 组织架构范围限定 | 否 |
| pre_course_first_level_department_name | string | 前置课程一级部门名称 | 组织架构范围限定 | 是 |
| pre_course_second_level_department_code | bigint | 前置课程二级部门代码 | 组织架构范围限定 | 否 |
| pre_course_second_level_department_name | string | 前置课程二级部门名称 | 组织架构范围限定 | 是 |
| pre_course_third_level_department_code | bigint | 前置课程三级部门代码 | 组织架构范围限定 | 否 |
| pre_course_third_level_department_name | string | 前置课程三级部门名称 | 组织架构范围限定 | 是 |

## 8. 常用过滤条件

- 分区：`t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')`，`t.hour = format_datetime(now() - interval '2' hour, 'HH')`
- 业绩归属部门：`t.employee_first_level_department_name = 'H业务线'`，`t.employee_second_level_department_name = '市场部'`，`t.employee_third_level_department_name = '市场顾问部'`
- 交易类型：`t.trade_type in ('正常订单', '调课调班')`
- 期次口径：通常使用 `trade_time` 按周五生成 `qici`，遇到春季特殊周需按原看板 SQL 的 case when 口径处理。
- 学期口径：`course_term_id` 常见映射：C=春季，X=夏季，Q=秋季，D=冬季。

## 9. 常用 join key

- `employee_email_name`：可与评优架构表 `temp_table.dingxi01_pingyou_jg.employee_email_name` 关联。
- `email_prefix`：员工邮箱前缀，可用于员工维表/架构表关联，关联前需确认对方字段口径。
- `user_id`：用户维度关联键。
- `order_number`、`top_order_number`、`refund_order_number`：订单/退款明细关联键。
- `biz_number`、`pre_biz_number`：前后置班课/期次业务编号，不等同于顾问评优看板的 `qici`，需注意转换口径。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from finance_dw.app_finance_performance_extend_details_hf t
where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and t.hour = format_datetime(now() - interval '2' hour, 'HH')
  and t.employee_first_level_department_name = 'H业务线'
  and t.employee_second_level_department_name = '市场部'
  and t.employee_third_level_department_name = '市场顾问部'
limit 20;
```

### 按 dt/hour 统计分区数据量

```sql
select
    t.dt,
    t.hour,
    count(*) as cnt
from finance_dw.app_finance_performance_extend_details_hf t
where t.dt in ('YYYYMMDD')
group by t.dt, t.hour
order by t.dt desc, t.hour desc
limit 50;
```

### 字段分布探索

```sql
select
    t.trade_type,
    t.trade_status,
    count(*) as cnt,
    sum(t.price) as price_sum
from finance_dw.app_finance_performance_extend_details_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.employee_first_level_department_name = '<一级部门名称>'
group by t.trade_type, t.trade_status
order by cnt desc
limit 50;
```

### 顾问-期次销售额口径示例

```sql
with base as (
    select
        t.id,
        t.order_number,
        t.user_id,
        t.employee_email_name,
        t.trade_type,
        t.trade_status,
        t.trade_time,
        t.price,
        case
            when substr(t.trade_time, 1, 10) >= '2026-02-25' and substr(t.trade_time, 1, 10) <= '2026-03-02' then '20260227期'
            when substr(t.trade_time, 1, 10) >= '2026-02-17' and substr(t.trade_time, 1, 10) <= '2026-02-24' then '20260220期'
            when substr(t.trade_time, 1, 10) >= '2026-02-09' and substr(t.trade_time, 1, 10) <= '2026-02-16' then '20260213期'
            when substr(t.trade_time, 1, 10) >= '2026-02-03' and substr(t.trade_time, 1, 10) <= '2026-02-08' then '20260206期'
            when substr(t.trade_time, 1, 10) >= '2026-01-27' and substr(t.trade_time, 1, 10) <= '2026-02-02' then '20260130期'
            when substr(t.trade_time, 1, 10) >= '2026-01-20' and substr(t.trade_time, 1, 10) <= '2026-01-26' then '20260123期'
            else concat(date_format(date_add('day', 4, date_trunc('week', date_add('day', -1, cast(t.trade_time as timestamp)))), '%Y%m%d'), '期')
        end as qici
    from finance_dw.app_finance_performance_extend_details_hf t
    where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t.hour = format_datetime(now() - interval '2' hour, 'HH')
      and t.employee_first_level_department_name = 'H业务线'
      and t.employee_second_level_department_name = '市场部'
      and t.employee_third_level_department_name = '市场顾问部'
)
select
    b.qici,
    b.employee_email_name,
    sum(b.price) as sales_amount
from base b
group by b.qici, b.employee_email_name
limit 100;
```

## 11. 注意事项

- 该表为小时表，查询必须加 `dt` 和 `hour`，禁止无分区扫描。
- 使用 `employee_*_department_name`、`course_*_department_name`、`pre_course_*_department_name` 时必须加范围限定。
- 评优 SQL 中对 `trade_type = '调课调班'` 有单独去重/汇总逻辑，生成新 SQL 时需优先复用历史看板口径。
- `price` 是按支付金额和调课金额计算后的金额口径，`real_price`、`transfer_price` 也可用于明细校验。
- 若用于顾问评优，需同时关联 `temp_table.dingxi01_pingyou_jg` 获取顾问期次、架构、人产、渠道等维度。
- 字段描述已按 Word 文档补充，指标口径仍需结合历史 SQL 和业务确认。

### 流量画像 SQL 使用备注

- `traffic_profile.sql` 的 `dd` CTE 使用该表按 `trade_time` 派生 `qici`，再按 `qici + user_id + employee_email_name` 统计 `count(distinct subject)`，用于输出成交科目档位 `sub`。
- 科目归一化规则覆盖英语/英文、语文、数学、物理、化学、历史、政治、生物、地理、日语，其他保留原 `course_subject`。
- 范围限定为 `employee_first_level_department_name = 'H业务线'`、`employee_second_level_department_name = '市场部'`、`employee_third_level_department_name = '市场顾问部'`，并过滤 `real_price <> 0`。
- 2026-05-15 `city_channel.txt` 版本最终在 `base` CTE 使用 `${period_name1}`、`${period_name2}` 控制主线索期次范围；`dd` CTE 自身没有单独期次过滤，依赖后续 join 和最终范围过滤。
- `dd` 最终 join 到主线索只使用 `qici + user_id`，未带 `employee_email_name`，用户跨顾问成交时可能放大或错配。

### 退费分析 SQL 使用备注

- `refund_multi_subject_user_ratio.sql`、`refund_subject_product.sql`、`refund_reason_analysis.sql` 均以该表为财务业绩主表，按 `trade_time` 推导 `qici`。
- 常用范围限定为 `employee_first_level_department_name = 'H业务线'`、`employee_second_level_department_name = '市场部'`、`employee_third_level_department_name = '市场顾问部'`。
- 多科用户退费占比和退费原因分析使用 `price <> 0`，并按 `zong_price < 0` 判断退款、`zong_price > 0` 判断收款。
- 退费科目产品 SQL 使用 `case when trade_status in ('全部退款','部分退款') then -real_price else real_price end as real_price_0`，同时保留 `price`；金额正负口径与其他两份 SQL 不完全一致。
- 三份 SQL 均选出 `course_first_level_department_name`、`course_second_level_department_name`、`course_top_level_department_name`，但未在财务主表层单独过滤课程部门，复用时需确认是否补充。

## 12. 反向联动速查

被以下看板高频使用：

- `../dashboards/consultant_sales_ranking_evaluation.md`：顾问销售评优和人产排名。
- `../dashboards/traffic_profile.md`：成交科目档位 `sub`。
- `../dashboards/refund_multi_subject_user_ratio.md`、`../dashboards/refund_subject_product.md`、`../dashboards/refund_reason_analysis.md`：退费分析财务主表。

已知风险：

- Web 查询环境正常可用。
- 原表文档中的历史 SQL 片段含三参数 `date_add` 示例；生成新 SQL 时按 `../sql_patterns/dashboard_query_patterns.md` 改成 interval 写法。
- 顾问评优只在明确要求评优/参评名单/人产时使用 `temp_table.dingxi01_pingyou_jg`。
