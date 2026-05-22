# 看板型 SQL 模板

## 多 CTE 看板结构

```sql
with base_data as (
    select
        t.lead_id,
        t.user_number,
        t.employee_id,
        t.lead_period_name,
        t.channel_name_1,
        t.dt,
        t.hour
    from 完整库名.线索表 t
    where t.dt = 'YYYYMMDD'
      and t.hour = 'HH'
      and t.first_department_name = '<一级部门名称>'
),
call_data as (
    select
        c.lead_id,
        count(*) as call_cnt,
        sum(case when c.is_connected = 1 then 1 else 0 end) as connected_cnt
    from 完整库名.外呼表 c
    where c.dt = 'YYYYMMDD'
      and c.hour = 'HH'
    group by c.lead_id
),
stage_data as (
    select
        s.lead_id,
        max(s.sale_flow_stage_sequence) as sale_flow_stage_sequence
    from 完整库名.阶段表 s
    where s.dt = 'YYYYMMDD'
      and s.hour = 'HH'
      and s.assign_employee_first_level_department_name = '<一级部门名称>'
    group by s.lead_id
),
attendance_data as (
    select
        a.lead_id,
        count(*) as attendance_cnt
    from 完整库名.行课表 a
    where a.dt = 'YYYYMMDD'
      and a.hour = 'HH'
    group by a.lead_id
),
final_agg as (
    select
        b.lead_period_name,
        b.channel_name_1,
        b.employee_id,
        count(distinct b.lead_id) as lead_cnt,
        count(distinct case when 待确认有效线索条件 then b.lead_id end) as valid_lead_cnt,
        sum(coalesce(c.call_cnt, 0)) as call_cnt,
        sum(coalesce(c.connected_cnt, 0)) as connected_cnt
    from base_data b
    left join call_data c on b.lead_id = c.lead_id
    left join stage_data s on b.lead_id = s.lead_id
    left join attendance_data a on b.lead_id = a.lead_id
    group by
        b.lead_period_name,
        b.channel_name_1,
        b.employee_id
)
select *
from final_agg
limit 1000;
```

## 日期偏移兼容写法

公司查询平台会将 `date_add` 解析为 Hive 两参数函数。生成新 SQL 时不要使用 Presto 三参数写法：

```sql
-- 禁止：平台可能报 date_add() requires 2 argument, got 3
date_add('day', 4, date_trunc('week', cast(trade_time as timestamp)))
```

日期/时间偏移优先使用 `interval`：

```sql
date_trunc('week', cast(trade_time as timestamp) - interval '1' day) + interval '4' day
```

常用期次计算模板：

```sql
concat(
    date_format(
        date_trunc(
            'week',
            cast(trade_time as timestamp) - interval '1' day
        ) + interval '4' day,
        '%Y%m%d'
    ),
    '期'
) as qici
```

## 排名指标粒度与前端聚合

排名、比率、目标、差值等非明细粒度指标必须先确定计算粒度。若计算粒度与最终输出粒度不一致，前端聚合可能把指标重复累加。

典型风险：

- 排名按 `期次-部门-顾问` 计算，但最终输出为 `期次-日期-部门-顾问`。
- `target_completion_period_dept_rank_no`、`target_completion_rate`、`target_completion_gap_to_previous`、`receive_target`、`tuoke_rate` 等期次粒度字段在日维度结果中重复出现。
- 前端若对这些字段使用 `sum`，会导致排名跳号、目标或比率被放大。

优先方案：如果看板组件是 `期次-部门-顾问` 榜单，最终查询应以期次粒度 CTE 为主表。

```sql
select
    p.qici,
    p.dept,
    p.name,
    p.xiaozu,
    p.jingli,
    coalesce(tr.target_completion_rate, 0) as target_completion_rate,
    coalesce(tr.target_completion_period_dept_rank_no, 0) as target_completion_period_dept_rank_no,
    coalesce(tr.target_completion_gap_to_previous, 0) as target_completion_gap_to_previous
from period_ranked p
left join target_completion_ranked tr
  on p.qici = tr.qici
 and p.dept = tr.dept
 and p.name = tr.name
```

兼容方案：如果同一查询必须保留日维度指标，可以保留日维度输出，同时增加 `*_once` 字段，避免前端求和时重复放大。

```sql
final_day_base as (
    select
        d.*,
        row_number() over (
            partition by d.qici, d.dept, d.name
            order by d.trade_date
        ) as period_consultant_day_rn
    from day_ranked d
)
select
    d.qici,
    d.trade_date,
    d.dept,
    d.name,
    d.income,
    d.refund,
    d.pmit,
    coalesce(tr.target_completion_period_dept_rank_no, 0) as target_completion_period_dept_rank_no,
    case
        when d.period_consultant_day_rn = 1
        then coalesce(tr.target_completion_period_dept_rank_no, 0)
    end as target_completion_period_dept_rank_no_once
from final_day_base d
left join target_completion_ranked tr
  on d.qici = tr.qici
 and d.dept = tr.dept
 and d.name = tr.name
```

输出说明中必须提示：日维度结果中的期次排名、目标、比率、差值类字段前端应使用 `max`、`min` 或“不聚合”，不要使用 `sum`；若前端无法控制聚合，使用 `*_once` 字段。

## 评优名单与在职架构名单

`temp_table.dingxi01_pingyou_jg` 只用于用户明确要求“评优/参评名单/评优架构/人产”时。该表含 `qici`，按 `qici + employee_email_name` 关联会限制结果只能落在该临时表已维护期次内。

当用户不要求严格评优参评名单，只需要市场顾问在职架构范围时，可使用 `temp_table.dingxi01_jiagou_zx` 替代，典型模板如下：

```sql
jiagou_zx_active as (
    select
        employee_email_name,
        employee_email_prefix,
        xiaozu,
        jingli,
        department
    from (
        select
            t.*,
            row_number() over (
                partition by t.employee_email_name
                order by
                    case
                        when t.department = '郑州顾问部' then 1
                        when t.department = '西安一部' then 2
                        when t.department = '西安二部' then 3
                        else 9
                    end,
                    t.employee_email_prefix,
                    t.xiaozu,
                    t.jingli
            ) as rn
        from temp_table.dingxi01_jiagou_zx t
        where cast(t.zaizhi as varchar) = '1'
          and t.department in ('郑州顾问部', '西安一部', '西安二部')
    ) x
    where rn = 1
),
eligible_consultant_name as (
    select distinct
        employee_email_name as name
    from jiagou_zx_active
)
```

使用该替代方案时，必须在 SQL 解释中说明口径从“参评顾问”变为“在职架构顾问”，且 `temp_table.dingxi01_jiagou_zx` 无 `qici`，不能按期次限定名单。

## 结果缺失与未来期次排查

当用户反馈“某期次/经理/顾问查不到”时，先判断查询驱动表：

- 事实主表驱动：从 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 等事实表出发，再 join 架构表。含义是只展示已有事实数据的人或期次。
- 名单/架构表驱动：从 `temp_table.dingxi01_jiagou_db`、参评名单或在职名单出发 left join 指标。含义是展示名单，即使指标为 0。

不要把“临时架构表已维护目标期次”直接判断为“事实主表应有目标期次”。`temp_table.dingxi01_jiagou_db` 可能提前维护未来期次，事实主表通常只产出当前已发生或已入库期次。若目标期次晚于当前日期或晚于事实主表最大派生期次，应优先归类为数据时效/未来期次未产出。

排查顺序：

1. 查名单/架构表目标期次和目标经理是否存在。
2. 查事实主表当前分区的最大派生期次。
3. 查事实主表在目标期次是否有数据。
4. 查事实主表目标期次 + 目标顾问名单是否有数据。
5. 逐步叠加部门范围、虚拟部门、期归属部门过滤。
6. 最后检查结果层过滤，例如 `valid_lead_count > 0`、`jg.department is not null`、渠道黑名单等。

查最新期次时不要使用 `order by qici asc limit N`，这会返回最早的 N 个期次并截断最新期次。应使用 `order by qici desc limit N`，或直接显式过滤目标期次。

错误模式：

```sql
and f.employee_email_prefix in (
    select jg.employee_email_prefix
    from temp_table.dingxi01_jiagou_db jg
    where jg.qici = '20260522期'
)
group by 派生qici
order by 1
limit 50
```

该写法只限定了“0522 期架构名单中的顾问”，没有限定事实主表的派生期次；结果会返回这些顾问的历史所有期次。`order by 1 limit 50` 还可能截断最新期次。

指定期次事实存在性验证模板：

```sql
select
    count(distinct f.employee_email_prefix) as employee_cnt,
    count(f.lead_id) as matched_rows,
    sum(coalesce(f.lead_count, 0)) as lead_count,
    sum(coalesce(f.valid_lead_count, 0)) as valid_lead_count
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and f.hour = format_datetime(now() - interval '3' hour, 'HH')
  and f.section_assign_employee_first_level_department_name = 'H业务线'
  and f.section_assign_employee_second_level_department_name = '市场部'
  and f.section_assign_employee_third_level_department_name = '市场顾问部'
  and (f.period_mapping_first_level_department_name = 'H业务线' or f.period_mapping_first_level_department_name is null)
  and (f.period_mapping_second_level_department_name in ('精品班学部', '市场部') or f.period_mapping_second_level_department_name is null)
  and f.virtual_third_department_name = '市场顾问部'
  and concat(
      date_format(
          date_trunc(
              'week',
              date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') - interval '1' day
          ) + interval '4' day,
          '%Y%m%d'
      ),
      '期'
  ) = '<目标期次>'
  and f.employee_email_prefix in (
      select jg.employee_email_prefix
      from temp_table.dingxi01_jiagou_db jg
      where jg.qici = '<目标期次>'
        and jg.jingli = '<经理>'
        and cast(jg.zaizhi as varchar) = '1'
      group by jg.employee_email_prefix
  )
limit 20
```

如果目标期次事实数据为 0，而架构表有名单，结论应写为“名单已维护，事实主表当前分区尚未产出该期数据”。若业务要求提前展示未来期次名单且指标为 0，需要改为名单/架构表驱动 left join 指标，并调整最终层 `valid_lead_count > 0` 等过滤；这是展示口径变更，必须人工确认。

## 渠道 CASE 映射

市场顾问渠道映射长 CASE 已独立维护在：

- `knowledge/sql_patterns/channel_mapping_case_when.md`
- `resources/raw_sql/market_channel_case_when_0515.sql`

生成或改写市场顾问相关看板 SQL 时，如果需要最新渠道归因口径，优先使用该 CASE 片段。不要直接复用旧看板中的历史 `channel_map` 长 CASE，除非用户明确要求沿用旧口径。

该 CASE 输出别名为 `qudao`。如果目标看板使用 `channel_map` 或 `channel_map_1`，只改最终别名，不要调整分支顺序。

## 首 call 任务指标

首 call 任务指标已独立维护在：

- `knowledge/sql_patterns/first_call_task_metric_pattern.md`

生成 `is_f_call`、首 call 任务数、首 call 任务率时，必须使用 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`，通过 `account_id` 关联 `finance_dw.dim_finance_employee_df` 转出顾问姓名，再用 `employee_email_name + user_id` 关联主线索数据。

不要使用 `service_dw.app_h_crm_lead_task_process_info_detail_hf.call_answer_lead_count` 作为首 call 任务来源。该旧过程表只保留双表发送/回收、任务过程、电话接通等非首 call 任务用途。

## 流量画像增强模式

流量画像类 SQL 可参考 `resources/raw_sql/traffic_profile.sql` 和 `knowledge/dashboards/traffic_profile.md`，在市场顾问主全链路表基础上增加画像/过程维度：

- APP 登录：`dw.dim_cstm_active_user_c_appliction_mb_df` 按 `user_number` 取最新 `last_event_time`，派生近 7 日 `is_app_denglu` 和最新 `last_app_channel`。
- 首呼时效：主表 `section_assign_time` 与 `first_call_time` 计算小时差，再按 24/48 小时窗口标记。
- 外呼长通话：`service_dw.app_h_crm_lead_employee_workload_detail_hf` 聚合 `call_duration > 300`，join 时优先确认是否需要带 `lead_id`。
- 深沟阶段：`service_dw.dwd_crm_assign_private_detail_hf` 按 `private_sea_update_time desc` 取最新阶段，`450/470` 映射深沟/已双沟。
- 到课：行课表派生 `qici` 后关联 `temp_table.dingxi01_daoke_1_6_t`，`曹忆` 使用第 3 节，其他渠道使用第 1 节。
- 成交科目档位：财务业绩明细按 `qici + user_id + employee_email_name` 统计去重科目数；如最终只按 `qici + user_id` join，必须说明顾问粒度重复风险。
- 城市渠道维度：2026-05-15 `city_channel.txt` 版本从主全链路表直接输出 `province_name`、`city_name`、`city_level_name`；省市归属和城市等级口径待人工确认。
- 期次过滤：当前版本使用 `period_name >= ${period_name1}` 且 `period_name < ${period_name2}`，生成可执行 SQL 前必须替换参数；若用户没有给期次范围，使用占位符并在说明中标明待替换。

生成新 SQL 时不要照抄历史三参数 `date_add`；应替换为本文件“日期偏移兼容写法”中的 `interval` 模板。

## 必须解释

- 每个 CTE 的用途。
- 每个 join key 的来源和风险。
- 每个指标口径是否来自知识库。
- 待确认字段或条件。
