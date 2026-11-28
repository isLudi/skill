WITH base_rows AS (
    SELECT b.lead_id, b.user_id,
        concat(date_format(date_trunc('week',
            try(date_parse(replace(concat(b.group_period_year, b.group_period_term), '期', ''), '%Y%m%d')))
            + interval '4' day, '%Y%m%d'), '期') AS period_name,
        coalesce(nullif(trim(b.virtual_leader_email_name), ''), '未知') AS manager,
        coalesce(nullif(trim(b.virtual_direct_leader_email_name), ''), '未知') AS supervisor,
        coalesce(nullif(trim(b.employee_email_name), ''), '未知') AS advisor,
        coalesce(b.lead_count, 0) AS lead_count,
        try_cast(b.lead_create_time AS timestamp) AS created_at
    FROM bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df b
    WHERE b.dt = date_format(cast(cast(current_timestamp AS date) - interval '1' day AS timestamp), '%Y%m%d') AND b.hour = '23'
      AND b.section_assign_employee_first_level_department_name = 'H业务线'
      AND b.section_assign_employee_second_level_department_name = '市场部'
      AND b.section_assign_employee_third_level_department_name = '市场顾问部'
      AND b.period_mapping_first_level_department_name = 'H业务线'
      AND b.period_mapping_second_level_department_name IN ('精品班学部', '市场部', '菁英班学部', '本地化大班学部', '一对一学部')
), period_base AS (
    SELECT period_name, lead_id, manager, supervisor, advisor, sum(lead_count) AS lead_count
    FROM base_rows
    WHERE period_name > '20261106期'
    GROUP BY period_name, lead_id, manager, supervisor, advisor
), channel_dimension AS (
    SELECT d.lead_id,
        CASE WHEN count(DISTINCT nullif(trim(d.channel_map), '')) = 1
            THEN min(nullif(trim(d.channel_map), '')) END AS channel
    FROM gaotu_hl.dim_mkt_h_lead_channel_df d
    WHERE d.dt = date_format(cast(cast(current_timestamp AS date) - interval '1' day AS timestamp), '%Y%m%d') AND d.lead_id IS NOT NULL
    GROUP BY d.lead_id
), period_users AS (
    SELECT DISTINCT user_id
    FROM base_rows
    WHERE period_name > '20261106期' AND user_id > 0
), touches AS (
    SELECT try_cast(outer_channel_task_id AS bigint) AS task_key,
        try_cast(receiver_id AS bigint) AS user_key,
        count(DISTINCT plan_id) AS plan_count,
        min(try_cast(actual_send_time AS timestamp)) AS first_sent_at,
        max(try_cast(actual_send_time AS timestamp)) AS last_sent_at,
        count_if(try_cast(actual_send_time AS timestamp) IS NULL) AS missing_send_rows
    FROM fairy_data_center.dwd_service_reach_wide_channel_subtask_prod_v2_di
    WHERE dt BETWEEN '20260401' AND date_format(cast(cast(current_timestamp AS date) - interval '1' day AS timestamp), '%Y%m%d')
      AND scene_code = 'ai_call_auto_add_friend' AND reach_type = 25
      AND plan_id IN (4214, 4235, 4255, 4288) AND channel_subtask_status IN ('3', '4')
      AND try_cast(outer_channel_task_id AS bigint) > 0
      AND try_cast(receiver_id AS bigint) IN (SELECT user_id FROM period_users)
      AND coalesce(try_cast(actual_send_time AS timestamp), try_cast(create_time AS timestamp)) < cast(cast(current_timestamp AS date) AS timestamp)
    GROUP BY try_cast(outer_channel_task_id AS bigint), try_cast(receiver_id AS bigint)
), lead_candidates AS (
    SELECT l.user_id, l.period_name, l.lead_id, min(l.created_at) AS created_at
    FROM base_rows l
    WHERE l.user_id IN (SELECT user_key FROM touches)
      AND l.period_name IS NOT NULL AND l.lead_id IS NOT NULL
    GROUP BY l.user_id, l.period_name, l.lead_id
), private_sea AS (
    SELECT DISTINCT p.user_number, p.lead_id, try_cast(p.assign_time AS timestamp) AS assigned_at,
        nullif(try_cast(p.close_time AS timestamp), TIMESTAMP '1970-01-01 08:00:00') AS closed_at,
        nullif(try_cast(p.fall_sea_time AS timestamp), TIMESTAMP '1970-01-01 08:00:00') AS fell_at
    FROM service_dw.dwd_crm_assign_private_detail_hf p
    WHERE p.dt = date_format(cast(cast(current_timestamp AS date) - interval '1' day AS timestamp), '%Y%m%d') AND p.hour = '23'
      AND p.assign_employee_first_level_department_name = 'H业务线'
      AND p.assign_employee_second_level_department_name = '市场部'
      AND p.assign_employee_third_level_department_name = '市场顾问部'
      AND p.is_del = 0 AND p.lead_id IS NOT NULL
      AND p.user_number IN (SELECT user_key FROM touches)
), task_candidates AS (
    SELECT t.task_key, t.user_key, t.plan_count, t.missing_send_rows,
        count(DISTINCT CASE WHEN l.lead_id IS NOT NULL
            THEN concat(l.period_name, ':', cast(l.lead_id AS varchar)) END) AS candidate_count,
        count(DISTINCT CASE WHEN l.created_at <= t.first_sent_at
            THEN concat(l.period_name, ':', cast(l.lead_id AS varchar)) END) AS pre_send_count,
        min(l.period_name) AS unique_period, min(l.lead_id) AS unique_lead,
        count(DISTINCT CASE WHEN assignment.lead_id IS NOT NULL AND l.created_at <= t.first_sent_at
            THEN concat(l.period_name, ':', cast(l.lead_id AS varchar)) END) AS private_count,
        min(CASE WHEN assignment.lead_id IS NOT NULL AND l.created_at <= t.first_sent_at THEN l.period_name END) AS private_period,
        min(CASE WHEN assignment.lead_id IS NOT NULL AND l.created_at <= t.first_sent_at THEN l.lead_id END) AS private_lead
    FROM touches t
    LEFT JOIN lead_candidates l ON t.user_key = l.user_id AND l.created_at <= t.last_sent_at
    LEFT JOIN private_sea assignment ON l.user_id = assignment.user_number AND l.lead_id = assignment.lead_id
        AND assignment.assigned_at <= t.first_sent_at
        AND (assignment.closed_at IS NULL OR assignment.closed_at > t.last_sent_at)
        AND (assignment.fell_at IS NULL OR assignment.fell_at > t.last_sent_at)
    GROUP BY t.task_key, t.user_key, t.plan_count, t.missing_send_rows
), candidate_owner AS (
    SELECT task_key, user_key,
        CASE
            WHEN plan_count = 1 AND missing_send_rows = 0 AND candidate_count = 1 AND pre_send_count = 1 THEN unique_period
            WHEN plan_count = 1 AND missing_send_rows = 0 AND private_count = 1 THEN private_period
        END AS period_name,
        CASE
            WHEN plan_count = 1 AND missing_send_rows = 0 AND candidate_count = 1 AND pre_send_count = 1 THEN unique_lead
            WHEN plan_count = 1 AND missing_send_rows = 0 AND private_count = 1 THEN private_lead
        END AS lead_id,
        CASE
            WHEN plan_count <> 1 THEN 'multiple_plans'
            WHEN missing_send_rows > 0 THEN 'missing_send_time'
            WHEN candidate_count = 0 OR pre_send_count = 0 THEN 'missing_pre_send_lead'
            WHEN candidate_count = 1 OR private_count = 1 THEN 'resolved'
            ELSE 'ambiguous_lead'
        END AS attribution
    FROM task_candidates
), owner_dimensions AS (
    SELECT period_name, lead_id
    FROM period_base
    WHERE lead_id IS NOT NULL
    GROUP BY period_name, lead_id
    HAVING count(*) = 1
), task_owners AS (
    SELECT a.task_key, a.user_key, a.period_name, a.lead_id,
        CASE
            WHEN a.attribution <> 'resolved' THEN a.attribution
            WHEN a.period_name <= '20261106期' THEN 'before_first_period'
            WHEN organization.lead_id IS NULL THEN 'ambiguous_organization'
            ELSE 'in_scope'
        END AS attribution
    FROM candidate_owner a
    LEFT JOIN owner_dimensions organization ON a.period_name = organization.period_name AND a.lead_id = organization.lead_id
), call_events AS (
    SELECT nullif(trim(c.call_id), '') AS call_id,
        min(c.predict_task_id) AS task_key, min(c.user_number) AS user_key,
        max(CASE WHEN c.call_status = 1 THEN 1 ELSE 0 END) AS connected
    FROM one_dw.dwd_mkt_tmk_call_record_hf c
    INNER JOIN touches t ON c.predict_task_id = t.task_key AND c.user_number = t.user_key
    WHERE c.dt = date_format(cast(cast(current_timestamp AS date) - interval '1' day AS timestamp), '%Y%m%d') AND c.hour = '23' AND c.call_type = 2
      AND c.call_time >= '2026-04-01 00:00:00' AND c.call_time < concat(date_format(cast(cast(current_timestamp AS date) AS timestamp), '%Y-%m-%d'), ' 00:00:00')
      AND nullif(trim(c.call_id), '') IS NOT NULL
    GROUP BY nullif(trim(c.call_id), '')
    HAVING count(DISTINCT concat(cast(c.predict_task_id AS varchar), ':', cast(c.user_number AS varchar))) = 1
), calls_by_task AS (
    SELECT task_key, user_key, count(*) AS dials, sum(connected) AS connected
    FROM call_events
    GROUP BY task_key, user_key
), friends_by_task AS (
    SELECT f.task_id AS task_key, f.user_id AS user_key,
        count(DISTINCT CASE WHEN f.status IN (1, 2) THEN f.id END) AS sent,
        max(CASE WHEN f.status = 2 THEN 1 ELSE 0 END) AS added
    FROM data_lake_ods.ods_ones_business_agent_ai_add_friend_record_rt f
    INNER JOIN touches t ON f.task_id = t.task_key AND f.user_id = t.user_key
    WHERE f.create_time >= TIMESTAMP '2026-04-01 00:00:00' AND f.create_time < cast(cast(current_timestamp AS date) AS timestamp)
      AND coalesce(f.update_time, f.create_time) < cast(cast(current_timestamp AS date) AS timestamp)
      AND f.source_type IN (2, 3) AND f.is_del = 0
    GROUP BY f.task_id, f.user_id
), task_facts AS (
    SELECT o.task_key, o.user_key, o.period_name, o.lead_id, o.attribution,
        coalesce(dial_fact.dials, 0) AS dials, coalesce(dial_fact.connected, 0) AS connected,
        coalesce(friend_fact.sent, 0) AS sent, coalesce(friend_fact.added, 0) AS added
    FROM task_owners o
    LEFT JOIN calls_by_task dial_fact ON o.task_key = dial_fact.task_key AND o.user_key = dial_fact.user_key
    LEFT JOIN friends_by_task friend_fact ON o.task_key = friend_fact.task_key AND o.user_key = friend_fact.user_key
), by_lead AS (
    SELECT period_name, lead_id,
        sum(dials) AS dials, sum(connected) AS connected, sum(sent) AS sent, max(added) AS added
    FROM task_facts
    WHERE attribution = 'in_scope'
    GROUP BY period_name, lead_id
), advisor_metrics AS (
    SELECT lead_base.period_name, coalesce(mapping.channel, '未知') AS channel,
        lead_base.manager, lead_base.supervisor, lead_base.advisor, sum(lead_base.lead_count) AS all_leads,
        count(ai_facts.lead_id) AS ai_leads, sum(coalesce(ai_facts.dials, 0)) AS dials,
        sum(coalesce(ai_facts.connected, 0)) AS connected, sum(coalesce(ai_facts.sent, 0)) AS sent,
        sum(coalesce(ai_facts.added, 0)) AS added
    FROM period_base lead_base
    LEFT JOIN channel_dimension mapping ON cast(lead_base.lead_id AS varchar) = mapping.lead_id
    LEFT JOIN by_lead ai_facts ON lead_base.period_name = ai_facts.period_name AND lead_base.lead_id = ai_facts.lead_id
    GROUP BY lead_base.period_name, coalesce(mapping.channel, '未知'), lead_base.manager, lead_base.supervisor, lead_base.advisor
)
SELECT period_name AS "期次", channel AS "渠道", manager AS "经理",
    supervisor AS "主管", advisor AS "顾问",
    all_leads AS "总线索数", ai_leads AS "AI外呼线索数", dials AS "AI拨打频次",
    cast(dials AS double) / nullif(all_leads, 0) AS "AI例均频次",
    dials AS "AI例均频次_分子", all_leads AS "AI例均频次_分母",
    cast(connected AS double) / nullif(dials, 0) AS "AI接通率",
    connected AS "AI接通率_分子", dials AS "AI接通率_分母",
    cast(sent AS double) / nullif(connected, 0) AS "AI-发起加微率",
    sent AS "AI-发起加微率_分子", connected AS "AI-发起加微率_分母",
    cast(added AS double) / nullif(all_leads, 0) AS "AI-好友率",
    added AS "AI-好友率_分子", all_leads AS "AI-好友率_分母",
    concat(
        replace(replace(period_name, '%', '%25'), '|', '%7C'), '|',
        replace(replace(channel, '%', '%25'), '|', '%7C'), '|',
        replace(replace(manager, '%', '%25'), '|', '%7C'), '|',
        replace(replace(supervisor, '%', '%25'), '|', '%7C'), '|',
        replace(replace(advisor, '%', '%25'), '|', '%7C')
    ) AS "主键",
    cast(current_timestamp AS timestamp) AS "更新时间"
FROM advisor_metrics
WHERE ai_leads > 0
