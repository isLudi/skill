with org_t as (
    select
        dep_path,
        email_prefix,
        name,
        min(begin_time) as begin_time,
        max(end_time) as end_time
    from (
        select distinct
            email_prefix,
            path_name,
            array_join(slice(split(path_name, '-'), 1, 3), '-') as dep_path,
            name,
            talent_type_name,
            position_name,
            source_hr_status,
            leave_time,
            execute_time,
            begin_time,
            end_time
        from dw.dim_employee_chain
        where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
          and array_join(slice(split(path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'
    ) t
    group by
        dep_path,
        email_prefix,
        name
),
finance_base as (
    select
        x.*,
        concat(
            date_format(
                cast(
                    case day_of_week(x.trade_dt - interval '1' day)
                        when 1 then x.trade_dt + interval '3' day
                        when 2 then x.trade_dt + interval '2' day
                        when 3 then x.trade_dt + interval '1' day
                        when 4 then x.trade_dt
                        when 5 then x.trade_dt - interval '1' day
                        when 6 then x.trade_dt - interval '2' day
                        when 7 then x.trade_dt - interval '3' day
                    end as timestamp
                ),
                '%Y%m%d'
            ),
            '期'
        ) as trade_qici
    from (
        select
            fe.*,
            cast(cast(fe.trade_time as timestamp) as date) as trade_dt
        from finance_dw.app_finance_performance_extend_details_hf fe
        where fe.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
          and fe.hour = format_datetime(now() - interval '2' hour, 'HH')
          and fe.employee_first_level_department_name = 'H业务线'
          and fe.employee_second_level_department_name = '市场部'
          and fe.employee_third_level_department_name = '市场顾问部'
    ) x
),
dd_0 as (
    select
        id,
        order_number,
        substring(biz_number, 1, 10) as sub_biz_number,
        pre_biz_number,
        clazz_name,
        user_id as user_id1,
        pre_employee_id,
        type,
        trade_status,
        trade_type,
        order_paid_time as paid_time,
        trade_time,
        case
            when trade_status in ('全部退款', '部分退款') then -real_price
            else real_price
        end as real_price_0,
        transfer_price,
        price,
        email_prefix,
        employee_email_name as name,
        talent_type_name,
        city_name as city,
        department,
        biz_number,
        course_grade as grade_list,
        course_subject as subject,
        trade_qici as qici,
        case
            when trade_qici = '20260731期' then concat(substr(trade_qici, 1, 4), '08')
            else substr(trade_qici, 1, 6)
        end as natural_month,
        leader_employee_email_name,
        teacher_name,
        case course_term_id
            when 'C' then '春季'
            when 'X' then '夏季'
            when 'Q' then '秋季'
            when 'D' then '冬季'
            else '其他'
        end as school_term_id,
        note
    from finance_base
    where trade_qici >= '20260403期'
),
dd as (
    select dd_0.*
    from dd_0
    inner join org_t ot
      on ot.email_prefix = dd_0.email_prefix
    where dd_0.trade_time >= ot.begin_time
      and dd_0.trade_time <= ot.end_time
),
gmv_t as (
    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        natural_month,
        school_term_id,
        teacher_name,
        name_total_price
    from (
        select
            *,
            row_number() over (
                partition by name, user_id1
                order by id
            ) as dup_rn
        from (
            select
                *,
                round(sum(price) over (partition by name, user_id1), 3) as name_total_price
            from dd
            where trade_type = '调课调班'
        ) t1
        where name_total_price != 0
    ) t2
    where dup_rn = 1
),
gmv_z as (
    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        natural_month,
        school_term_id,
        teacher_name,
        sum(price) as name_total_price
    from dd
    where trade_type = '正常订单'
    group by
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        natural_month,
        school_term_id,
        teacher_name
),
rd as (
    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        natural_month,
        school_term_id,
        teacher_name,
        name_total_price
    from gmv_z

    union all

    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        natural_month,
        school_term_id,
        teacher_name,
        name_total_price
    from gmv_t
),
jiagou_zx_active as (
    select
        employee_email_name,
        employee_email_prefix,
        xiaozu,
        jingli,
        department
    from (
        select
            zx.*,
            row_number() over (
                partition by zx.employee_email_name
                order by
                    case
                        when zx.department = '郑州顾问部' then 1
                        when zx.department = '西安一部' then 2
                        when zx.department = '西安二部' then 3
                        else 9
                    end,
                    zx.employee_email_prefix,
                    zx.xiaozu,
                    zx.jingli
            ) as rn
        from temp_table.dingxi01_jiagou_zx zx
        where cast(zx.zaizhi as varchar) = '1'
          and zx.department in ('郑州顾问部', '西安一部', '西安二部')
    ) x
    where rn = 1
),
rd_0 as (
    select
        rd.qici,
        rd.natural_month,
        rd.name,
        rd.user_id1,
        case
            when rd.trade_status like '%退款%' then '退款'
            when rd.trade_status like '%支付%' then '支付'
            else '未知'
        end as trade_status,
        zz.xiaozu,
        zz.jingli,
        case
            when zz.department like '%西安%' then '西安'
            when zz.department like '%郑州%' then '郑州'
            else '未知'
        end as dept,
        rd.grade_list,
        sum(case when rd.name_total_price >= 0 then rd.name_total_price else 0 end) as income,
        sum(case when rd.name_total_price < 0 then abs(rd.name_total_price) else 0 end) as refund,
        sum(rd.name_total_price) as promit
    from rd
    left join jiagou_zx_active zz
      on zz.employee_email_name = rd.name
    group by
        rd.qici,
        rd.natural_month,
        rd.name,
        rd.user_id1,
        case
            when rd.trade_status like '%退款%' then '退款'
            when rd.trade_status like '%支付%' then '支付'
            else '未知'
        end,
        zz.xiaozu,
        zz.jingli,
        case
            when zz.department like '%西安%' then '西安'
            when zz.department like '%郑州%' then '郑州'
            else '未知'
        end,
        rd.grade_list
),
base_result as (
    select
        qici,
        natural_month,
        name,
        xiaozu,
        jingli,
        dept,
        sum(income) as income,
        sum(refund) as refund,
        sum(promit) as pmit
    from rd_0
    group by
        qici,
        natural_month,
        name,
        xiaozu,
        jingli,
        dept
),
month_agg as (
    select
        natural_month,
        array_join(array_sort(array_agg(distinct qici)), ',') as qici_list,
        dept,
        name,
        xiaozu,
        jingli,
        sum(income) as period_income,
        sum(refund) as period_refund,
        sum(pmit) as period_pmit
    from base_result
    group by
        natural_month,
        dept,
        name,
        xiaozu,
        jingli
),
month_rank_raw as (
    select
        natural_month,
        qici_list,
        dept,
        name,
        xiaozu,
        jingli,
        period_income,
        period_refund,
        period_pmit,
        '自然月-部门' as period_dept_rank_scope,
        row_number() over (
            partition by natural_month, dept
            order by period_pmit desc, name
        ) as period_dept_rank_no,
        lag(period_pmit) over (
            partition by natural_month, dept
            order by period_pmit desc, name
        ) as period_previous_pmit
    from month_agg
),
month_ranked as (
    select
        natural_month,
        qici_list,
        dept,
        name,
        xiaozu,
        jingli,
        period_income as income,
        period_refund as refund,
        period_pmit as pmit,
        period_income,
        period_refund,
        period_pmit,
        period_dept_rank_scope,
        period_dept_rank_no,
        case
            when period_previous_pmit is null then cast(0 as double)
            else period_previous_pmit - period_pmit
        end as period_dept_need_pmit_to_previous
    from month_rank_raw
),
eligible_consultant_name as (
    select distinct
        employee_email_name as name
    from jiagou_zx_active
),
cost_dim as (
    select
        trim(channel) as channel,
        max(try_cast(cost as double)) as cost
    from temp_table.dingxi01_cost
    where try_cast(cost as double) > 0
    group by
        trim(channel)
),
conversion_base as (
    select
        x.*,
        concat(
            date_format(
                cast(
                    case day_of_week(x.group_period_date - interval '1' day)
                        when 1 then x.group_period_date + interval '3' day
                        when 2 then x.group_period_date + interval '2' day
                        when 3 then x.group_period_date + interval '1' day
                        when 4 then x.group_period_date
                        when 5 then x.group_period_date - interval '1' day
                        when 6 then x.group_period_date - interval '2' day
                        when 7 then x.group_period_date - interval '3' day
                    end as timestamp
                ),
                '%Y%m%d'
            ),
            '期'
        ) as period_name_calc
    from (
        select
            fl.*,
            case
                when regexp_like(
                    replace(concat(coalesce(fl.group_period_year, ''), coalesce(fl.group_period_term, '')), '期', ''),
                    '^[0-9]{8}$'
                )
                then cast(
                    date_parse(
                        replace(concat(coalesce(fl.group_period_year, ''), coalesce(fl.group_period_term, '')), '期', ''),
                        '%Y%m%d'
                    ) as date
                )
            end as group_period_date
        from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df fl
        where fl.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
          and fl.hour = format_datetime(now() - interval '3' hour, 'HH')
          and fl.section_assign_employee_first_level_department_name = 'H业务线'
          and fl.section_assign_employee_second_level_department_name = '市场部'
          and fl.section_assign_employee_third_level_department_name = '市场顾问部'
          and (
                fl.period_mapping_first_level_department_name = 'H业务线'
                or fl.period_mapping_first_level_department_name is null
              )
          and (
                fl.period_mapping_second_level_department_name in ('精品班学部', '市场部')
                or fl.period_mapping_second_level_department_name is null
              )
    ) x
    where x.group_period_date is not null
),
conversion_data as (
    select distinct
        period_name_calc as period_name,
        case
            when period_name_calc = '20260731期' then concat(substr(period_name_calc, 1, 4), '08')
            else substr(period_name_calc, 1, 6)
        end as natural_month,
        virtual_third_department_name as depart_1,
        virtual_fourth_department_name as depart,
        virtual_leader_email_name as jingli,
        virtual_direct_leader_email_name as zhuguan,
        employee_email_name,
        rule_name,
        t1.lead_id,
        user_id,
        case when flow_pool_name in ('高途学习规划','智辉老师讲规划') then '市场私域视频号'
when rule_name like '%语数英%' and third_department_name = '新媒体内容运营部' then '语数英'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') then '孟亚飞99-2组'
when third_department_name = '投放部' and ad_account_name like '%周帅%' then '信息流-周帅'
when source_manager_name in ('韩正卿') then '抖音私信'
when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆') then '进校私域合作'
when channel_name_1='市场私域' and (virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'
when put_plan_name like '%周司鹏%' then '品宣组KOC'
when put_plan_name like '%公导私%' and put_plan_name like '%未购课%' then '公导私报名失败'
when third_department_name = '图书营销部' and rule_name like '%点睛卷%' then '押题卷'
when put_plan_name like '%迪九学%' then '市场私域代运营'
when third_department_name = '投放部' and channel_name_2 = '小红书' and channel_name_1 <> '搜索营销' then '信息流-小红书'
when third_department_name = '线上商务部' and channel_name_2 = '小红书' then '小红书'
when (flow_pool_name like '%肖晗%' or sku_id_name like '%肖晗%' or put_plan_name like '%肖晗9元%') and third_department_name='直播部'  then '肖晗'
when (flow_pool_name like '%北大汤哥%' or flow_pool_name like '%海淀名师高阶%') and sku_id_name like '%小艺%'  then '郭艺'
when  third_department_name like '%私域%' and rule_name like '%私域%' and rule_name like '%图书%' then '市场私域图书'
when  third_department_name like '%私域%' and rule_name like '%品效%'  then '市场私域品效'
when  third_department_name like '%私域%' and rule_name like '%公域学霸%'  then '市场私域公域组'
when  third_department_name like '%私域%' and rule_name like '%IE%'  then '市场私域IE'
when  third_department_name like '%私域%' and rule_name like '%裂变%'  then '市场私域裂变'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%退%' and flow_pool_name ='电商退款用户池'  then '退款订单复用'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%失败%' and flow_pool_name ='电商退款用户池'  then '赠课失败'
when third_department_name in ('直播部','新媒体内容运营部','市场一组')  and (flow_pool_name ='初阶化学规划' or flow_pool_name like '%启迪-初阶老师%')  then '曹忆'
when (third_department_name = '图书营销部' and sku_id_name like '%真题%') or (third_department_name='直播部' and sku_id_name like '%真题%') then '西安图书直播间-直播'
when (third_department_name = '图书营销部' and sku_id_name not like '%真题%') or (third_department_name='直播部' and sku_id_name  like '%秒懂%') or (third_department_name='直播部' and sku_id_name  like '%图书赠送%') then '西安图书直播间-挂链'
when rule_name like '%99元智学%' then 'AI直播'
when channel_provider_name = '宿迁伯岳' then '小程序'
when third_department_name in ('直播部','新媒体内容运营部','市场一组') and (flow_pool_name like '%海淀高阶名师%' or flow_pool_name like '%海淀老师高阶%' or flow_pool_name like '%小艺%') then '郭艺'
when put_plan_name like '%国培教育-0元%' or put_plan_name like '%易喆教育-0元%' or put_plan_name like '%钟情-0元%' or put_plan_name like '%中望达-0元%' or put_plan_name like '%晨硕-0元%' or put_plan_name like '%彩石-0元入群%'  then '创新商务入群'
when put_plan_name like '%0元入群-进校%' and third_department_name = '线上商务部' then '创新商务入群'
when put_plan_name like '%qq0元%' and third_department_name = '线上商务部' then '创新QQ'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%失败%' then '自孵化KOC-赠课失败'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%退%' then '自孵化KOC-退款订单复用'
when source_manager_name = '方俊结01' and put_plan_name like '%赠课后退款%' then 'KOC-赠课后退款' 
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') then '陈瑞春'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%') then '朱博士99'
when (third_department_name = '直播部' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and sku_id_name not like '%急%' and sku_id_name not like '%礼盒29%') or (third_department_name = '直播部' and sku_id_name like '%朱博士9%') then '朱博士9元'
when channel_name_1 = '商务' and channel_name_2 = '短信' then '短信'
when ad_account_name like '%肖晗%' and channel_name_1 = '信息流' then '信息流-肖晗'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%亚飞%' or source_put_plan_name like '%亚飞%'  or rule_name like '%亚飞%' or page_id_name like '%初中-0元%') then 'B站信息流-亚飞'
when channel_name_1 = '信息流' and (page_id_name like '%亚飞%' or ad_account_name like '%亚飞%') then '信息流-亚飞'
when (flow_pool_name like '%朱博士%' or flow_pool_name like '%双博士%' or flow_pool_name like '%教育规划%') and third_department_name <> '线上商务部' and period_name not like '%多学科拓展%' and rule_name not like '%张杰%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when put_plan_name like '%朱博士说教育%' and period_name not like '%多学科拓展%' and flow_pool_name not like '%高分讲堂%' and  flow_pool_name not like '%总裁%' and third_department_name='直播部' then '朱博士29'
when flow_pool_name like '%朱博士讲英语%' and sku_id_name like '%马凯鹏IP%' and third_department_name='直播部' then '马凯鹏29'
when (flow_pool_name like '%朱博士讲英语%' or flow_pool_name like '%朱博士英语%' or flow_pool_name like '%朱汉祺说英语%' or flow_pool_name like '%朱博士说英语%' or flow_pool_name like '%教育规划%' or flow_pool_name like '%双博士英语规划%' or flow_pool_name like '%朱博士满分英语%' or flow_pool_name like '%英语教父朱博士%' or (flow_pool_name like '%中考决胜天团%' and lead_purchase_intention_level1_category_name = '规划系统')) and third_department_name = '直播部' and period_name not like '%多学科拓展%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when (flow_pool_name like '%汤哥%' or flow_pool_name like '%汤老师%') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部')  then '汤老师'
when (flow_pool_name like '%中考百日冲刺%') and period_name not like '%多学科拓展%' and third_department_name='直播部'  then '曹忆9.9纯课'	
when (flow_pool_name like '%马总%' or  flow_pool_name = '减法化学马老师' or flow_pool_name like '%总裁讲化学%' or flow_pool_name like '%高分讲堂%') and period_name not like '%多学科拓展%' and sku_id_name  like '%99%' and third_department_name='直播部'  then '马凯鹏99'
when (flow_pool_name like '%马总%' or  flow_pool_name = '减法化学马老师' or flow_pool_name like '%总裁讲化学%' or flow_pool_name like '%高分讲堂%') and period_name not like '%多学科拓展%' and sku_id_name not like '%99%' and third_department_name='直播部'  then '马凯鹏29'
when (flow_pool_name like '%北大杰哥%' or flow_pool_name like '%张小杰%') and period_name not like '%多学科拓展%' and third_department_name='直播部' then '张杰'
when flow_pool_name like '%教育规划%' and rule_name like '%张杰%' and third_department_name='直播部' then '张杰'
when source_manager_name = '陈晓菁04' and channel_provider_name not like '%开拓%' and put_plan_name not like '%九学%' then '商务低价'	
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '百度'  then '孟亚飞百度数字人'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部'  then '孟亚飞9元'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'	
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' then '孟亚飞9元'	
when (flow_pool_name like '%肖晗%' or sku_id_name like '%肖晗%') and third_department_name='直播部'  then '肖晗'
when flow_pool_name like '%峥峥%' and period_name not like '%多学科拓展%' and third_department_name='直播部'  then '何峥峥'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name not like '%亚飞%' and third_department_name='直播部'  then '王汐子'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' then '孟亚飞9元'
when (flow_pool_name like '%曹忆%' or flow_pool_name like '%dudu%' or flow_pool_name like '%中考决胜天团%' or flow_pool_name like '%具象思维%' or flow_pool_name like '%在逃发面馒头%' or flow_pool_name like '%库洛米%' and lead_purchase_intention_level1_category_name <> '规划系统') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when flow_pool_name = '正价课判单补录' then '正价课判单补录'
when channel_name_1 = '转介绍' then '转介绍'
when first_department_name ='市场部' and channel_name_1 <> '站内获客' and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name like '%未加好友%' then '市场私域未加好友'
when put_plan_name like '%私域-信息流%' then '市场私域待支付'
when third_department_name = '私域运营部' and rule_name not like '%训练营%' and virtual_fifth_department_name not in ('罗江博团队') and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' then '市场私域低价单'
when third_department_name = '私域运营部' and rule_name not like '%训练营%'  and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' and flow_original_order_activity_price = '0.0' then '市场私域低价单'
when third_department_name = '私域运营部' and channel_name_1 = '信息流获客' then '市场私域小红书'
when channel_name_1= '信息流' and (put_plan_name like '%抖音私信%' or put_plan_name like '%初三0元%' or put_plan_name like '%高中0元%') then '信息流-抖音私信'
when channel_name_2 in ('APP','M站','PC') and flow_pool_name not like '%途途%' then 'APP'
when source_manager_name in ('高文羽') and lead_purchase_intention_name = 'AI定制' then '人工外呼-AI'
when channel_provider_name like '%唐山TMK%' then '唐山TMK' 
when source_manager_name in ('高文羽') and channel_provider_name not like '%唐山TMK%' and channel_provider_name not like '%郑州%' then '人工外呼' 
when source_manager_name in ('高文羽') and channel_provider_name not like '%唐山TMK%' and channel_provider_name  like '%郑州%' then '郑州TMK-2组' 
when source_manager_name = '冯银晨' and channel_name_2 = '小红书' then '信息流-小红书'	
when channel_name_1 = '信息流获客' and flow_original_order_activity_price like '%1990%' then '信息流19'
when (channel_name_1 = '信息流' and channel_name_2 <> 'B站' and third_department_name NOT LIKE '%商务%' and put_plan_name not like '%初三0元%' and put_plan_name not like '%抖音私信%' and put_plan_name not like '%高中0元%' and flow_original_order_activity_price not like '%1990%') or (channel_name_2 = 'B站' and third_department_name like '%投放%') then '信息流'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%郭艺%') then 'B站信息流-郭艺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%肖晗%' then 'B站信息流-肖晗'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%马凯鹏%' or ad_account_name like '%化学%') then 'B站信息流-马凯鹏'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and  (sku_id_name like '%陈瑞春%' or rule_name like '%陈瑞春%') and (ad_account_name  like '%语文%' or source_put_plan_name like '%自然流%' or page_id_name like '%春春%') then 'B站信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name like '%语文%' and  (flow_original_order_activity_price like '%1980%' or flow_original_order_activity_price like '%2980%' or flow_original_order_activity_price like '%2990%') then 'B站信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name not like '%语文%' then 'B站信息流-周帅'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_order_price like '%1980%' and ad_account_name like '%数学%' then 'B站信息流-周帅'
when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and  sku_id_name like '%陈瑞春%' and flow_pool_name like '%自然流%'  then 'B站信息流-陈瑞春'
when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and  sku_id_name like '%朱博士%' and flow_pool_name like '%自然流%'  then 'B站信息流-朱汉祺'
when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%春春%' then 'B站信息流-陈瑞春'
when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%朱博士%' then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_original_order_activity_price not like '%2980%' and flow_original_order_activity_price not like '%2990%' and flow_original_order_activity_price not like '%1980%' then 'B站信息流'
when flow_pool_name = '百度搜索引擎' or channel_name_1='搜索营销' then '信息流搜索'
when channel_name_1 = '信息流获客' and channel_name_2 = '小红书' and source_manager_name in ('王慧敏13','张琳02','王樱琦01') then '小红书投放'
when  flow_pool_name like '%小红书班课%' then '小红书投放'
when third_department_name = '投放部' and get_customer_way_name = '短视频信息流' and flow_original_order_activity_price like '%100%' then '信息流'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%原型题%') then 'KOC-书课包'
when flow_pool_name = '中考加油' and sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%帅师%' then 'KOC-周帅数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%肖晗%' then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%孟帝%' or sku_id_name like '%dudu%' or sku_id_name like '%市场初二%' or rule_name like '%亚飞%' or sku_id_name like '%初二高阳%' or sku_id_name like '%高阳初二%' or sku_id_name like '%精品初二%' or sku_id_name like '%菁英初三%' or (virtual_second_department_name = '菁英班学部' and lead_purchase_intention_level2_category_name='初级' and lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%帅师%' or rule_name like '%周帅%') then 'KOC-周帅数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%肖晗%' or rule_name like '%肖晗%') then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and period_name not like '%多学科拓展%' and (flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount like '%500%') and (sku_id_name like '%朱汉祺%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺5元%' or sku_id_name like '%koc5元-朱博士%' or rule_name like '%朱汉祺%') then 'KOC-5元朱汉祺'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%朱汉祺%' or sku_id_name like '%29元%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺%' or rule_name like '%朱博士%' ) and (flow_original_order_activity_price not like '%1100%' or rule_name like '%29%') and sku_id_name not like '%周帅%' then 'KOC-5元朱汉祺'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and period_name not like '%多学科拓展%' and sku_id_name not like '%朱汉祺%' and sku_id_name not like '%朱博士%' and sku_id_name not like '%周帅%' and sku_id_name not like '%29元%' then 'KOC-5元纯课'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%周帅%' then 'KOC-周帅'
--when (channel_name_2 like '%KOL%' and source_manager_name in ('崔文轩','孙培尧')) or (channel_name_2 like '%抖音%' and source_manager_name in ('徐绮鹤')) and period_name not like '%多学科拓展%' then '自孵化KOC'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL')  then '自孵化KOC-5元纯课'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL') and (sku_id_name like '%5元%'or sku_id_name like '%11元%' or flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount  like '%1100%' or flow_orders_income_amount  like '%500%' ) then '自孵化KOC-5元纯课'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%社群%' then '进校社群'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%TMK%' and page_id_name like '%1元%' then '进校TMK1元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '进校TMK9元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%书商%' then '进校书商'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%综合%' and put_plan_name like '%18%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%直播%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04') and put_plan_name not like '%0元%' and flow_pool_name not like '%家校共育%' and flow_pool_name not like '%保持热爱%' and flow_pool_name not like '%青松%' and flow_pool_name not like '%原子初三%' and flow_pool_name not like '%南通欣创%' and flow_pool_name not like '%悟之道%' and flow_pool_name not like '%济南梦航%' and channel_name_3 <> '社群' and put_plan_name not like '%善悟%' and put_plan_name not like '%人人通%'  and put_plan_name not like '%%济南格乐' and flow_pool_name not like '%晨硕智学%' and flow_pool_name not like '%兴尧文化%'  and flow_pool_name not like '%济南映像%' and flow_pool_name not like '%山东简单%' and flow_pool_name not like '%争鸣科技%'  then '商务低价'
when flow_pool_name like '%原子初三%' or flow_pool_name like '%原子系统%'  then '原子'
when flow_pool_name like '%市场部-公转私%' then '市场私域公导私'
when flow_pool_name like '%南通欣创%' or  flow_pool_name like '%人人通科技%' or flow_pool_name like '%易而购%' or flow_pool_name like '%济南梦航%' or flow_pool_name like '%晨硕智学%' or flow_pool_name like '%兴尧文化%' or flow_pool_name like '%济南映像%' or flow_pool_name like '%山东简单%' or flow_pool_name like '%争鸣科技%'  then '进校私域合作'
when (flow_pool_name like '%家校共育%' or flow_pool_name like '%保持热爱%' or flow_pool_name like '%青松%' or flow_pool_name like '%悟之道%') and put_plan_name not like '%0元%'  then '进校私域合作'
when source_manager_name = '李宁24' and put_plan_name like '%0转低%' then '进校私域合作'
when third_department_name = '私域运营部' and  flow_original_order_activity_price in ('100.0','900.0','300.0')  then '进校私域合作'
when third_department_name = '私域运营部' and  flow_original_order_activity_price in ('0.0') and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '进校私域合作'
when third_department_name = '私域运营部' and channel_name_1='市场私域' and put_plan_name not like '%公导私%' and put_plan_name not like '%公转私%' and flow_original_order_activity_price = '0.0' and rule_name not like '%激活%' and rule_name not like '%咨询%' and rule_name not like '%训练营%'  and virtual_fifth_department_name not like '%罗江博%' and virtual_fifth_department_name not like '%郑州学习顾问二部%' and source_manager_name not in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '市场私域低价单'
when flow_pool_name like '%青岛寻知%' or flow_pool_name like '%禾兴信息%' then '商务0元'
when put_plan_name like '%益企发1元%' or put_plan_name like '%腾瑞教育1元%' then '进校APP合作'
when put_plan_name like '%外部图书供量%' or  flow_pool_name='高途旗舰店—线索—yuxinru' then  '外部图书慧敏'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%社群%' then '创新社群'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%直推%' or put_plan_name like '%直推%') then '创新直推'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%书商%' or put_plan_name like '%书商%' or page_id_name like '%书商%') then '创新书商'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%TMK%' and page_id_name like '%1元%' then '创新TMK1元'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '创新TMK9元'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%直播%' or page_id_name like '%进校%') then '创新直播'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2<>'公众号' and channel_name_1 = '商务' and flow_pool_name <> '高途云集图书专营店-自然流' and flow_pool_name <> '高途旗舰店—线索—yuxinru' and put_plan_name not like '%社群%' and put_plan_name not like '%小红书班课%' and put_plan_name not like '%外部图书供量%' and channel_second_provider_name not like '%沃德丰店铺线索赠课%' and channel_second_provider_name not like '%智慧城-图书%' and put_plan_name not like '%育甲%' and flow_pool_name not like '%周长磊%'  then '创新商务'
when flow_pool_name like '%周长磊%' then '创新APP'
when channel_provider_name like '%唐成刚%' or flow_pool_name = '高途云集图书专营店-自然流' then '图书唐成刚'
when channel_second_provider_name like '%沃德丰店铺线索赠课%' or channel_second_provider_name like '%智慧城-图书%' or put_plan_name like '%育甲%' then '外部图书慧敏'
when flow_pool_name like '%高途图书产品学部%' then '图书任炯旭'
when source_manager_name in ('王春宵') then '武汉图书直播间'
when source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
when flow_pool_name like '%高中视频书%' or flow_pool_name like '%高中教辅书%' or flow_pool_name like '%朵拉老师%' then '北京图书直播间'
when flow_pool_name like '%市场部-原子合作%' then '原子'
when flow_pool_name like '%市场部-微信私域%' or flow_pool_name like '%市场部-规划报告%' or flow_pool_name like '%规划报告%' or flow_pool_name like '%市场部-小红书%' or flow_pool_name like '%孟浩宇%' then '市场私域低价单'
when flow_pool_name like '%待支付%' then '市场私域待支付'
when flow_pool_name like '%未加好友%' then '市场私域未加好友'
when flow_pool_name like '%内部换量%' then '市场私域首期掉海'
when flow_pool_name like '公导私' then '进校私域合作'
when source_manager_name in ('方宇02','李月林') then '菁英市场流量'
when channel_name_2 = '公众号' then '公众号'
when (flow_pool_name like '%增长组%' or channel_name_3 = '公众号' or second_department_name = '微信生态部') and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name  like '%济南格乐%' and put_plan_name  like '%表单%'  then '商务0元'
when put_plan_name like '%B类%' or put_plan_name like '%b类%' or channel_second_provider_name like '%KOC当期%' then 'KOC分层测试'
when put_plan_name like '%星耀%' or put_plan_name like '%物理展博%' or  put_plan_name like '%物理谢丽荣%' or put_plan_name like '%牟恩伯%' or  put_plan_name like '%王赞%' or put_plan_name like '%张磊老师高中数学%' or put_plan_name like '%雯姐高中物理大讲堂%' then '百度星耀'
when source_manager_name = '刘福云' and (sku_id_name like '%瑞春%' or sku_id_name like '%春春%') then '陈瑞春'
when source_manager_name = '刘福云' and sku_id_name like '%周帅%' then '周帅'
when third_department_name = '直播部' and sku_id_name like '%周帅%' and channel_name_2 in ('百度','B站')  then '周帅-百度数字人'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' and sku_id_name like '%199%' then '孟亚飞199'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' then '孟亚飞9元'
when third_department_name = '直播部' and sku_id_name like '%朱汉祺%' then '朱博士29'
when third_department_name = '直播部' and sku_id_name like '%肖晗%' then '肖晗'
when flow_pool_name like '%0转低转正%' or channel_name_2='产研测试' then '进校私域合作'
when  source_manager_name in ('陈甜06','梁晓敏') then '图书挂车'
when flow_pool_name like '%天津智慧双子%'	then '创新社群'
when third_department_name like '%城市定制%' then '点睛卷'	
when first_department_name like '%KM%' and flow_pool_name not like '%天津智慧双子%' then '途途商务'
when period_name like '%多学科拓展%' and third_department_name like '%私域运营%' then '市场私域入群'
when put_plan_name like '%赠课失败%' and third_department_name = '线上商务部' then 'KOC赠课失败'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%周帅%' then 'KOC-周帅'	
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%肖晗%' then 'KOC-肖晗'	
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%朱汉祺%'  and flow_original_order_activity_price like '%1100%' then 'KOC-5元朱汉祺'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%朱汉祺%'  and flow_original_order_activity_price not like '%1100%' then 'KOC-朱汉祺29'
when flow_pool_name like '%自然流%' and source_manager_name in ('赵语诗','崔文轩','孙培尧')	then '自孵化KOC-5元纯课'
when flow_pool_name like '%自然流%' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士9元'
when flow_pool_name like '%自然流%' and sku_id_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and rule_name like '%99%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99-1组'	
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组')  then '孟亚飞9元'	
when flow_pool_name like '%自然流%' and sku_id_name like '%曹忆%' then '曹忆'	
when flow_pool_name like '%自然流%' and rule_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and source_manager_name like '%邵万昕%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'	
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%'  then '孟亚飞9元'	
when flow_pool_name like '%自然流%' and rule_name like '%曹忆%' then '曹忆'		
when flow_pool_name like '%途途教室%' or first_department_name like 'TUTU' then '途途APP'
when second_department_name = '市场二部' and get_customer_way_name = 'KOL直播' then '市场二部KOC'
when second_department_name = '市场四部' then '市场四部'
when source_manager_name in ('宋莹莹','辛世如') and channel_name_2 in ('视频号') then '信息流-虚拟号挂车'
when put_plan_name like '%高三复读%' then '市场私域高三复读'
when put_plan_name ='美玲测试' then '途途信息流私信'
when rule_name like '%训练营%' and rule_name like '%市场私域%' then '市场私域入群'
when flow_pool_name like '%青少-私域%' then '青少私域'
when first_department_name = 'TT业务线' and third_department_name like '%商务招生%' then '途途商务'
when second_department_name = '战略客户部' then '文旅进校'
when put_plan_name like '%AI名师%' then 'AI直播'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') then '途途私域'
else '其他未知流量' end as channel_map,
        case
            when rule_name like '%高一%' then '高一'
            when rule_name like '%高二%' then '高二'
            when rule_name like '%高三%' then '高三'
            when rule_name like '%初二%' then '初二'
            when rule_name like '%初三%' then '初三'
            else '未知'
        end as grade_1,
        coalesce(lead_count, 0) as lead_count,
        coalesce(valid_lead_count, 0) as valid_lead_count,
        coalesce(merge_assign_lead_count, 0) as merge_assign_lead_count,
        coalesce(merge_valid_lead_count, 0) as merge_valid_lead_count,
        coalesce(conversion_lead_count, 0) as conversion_lead_count,
        coalesce(subject_count, 0) as subject_count,
        coalesce(same_lead_period_subject_count, 0) as same_lead_period_subject_count,
        coalesce(lb_subject_count, 0) as lb_subject_count,
        coalesce(same_lead_period_lb_subject_count, 0) as same_lead_period_lb_subject_count,
        coalesce(order_count, 0) as order_count,
        coalesce(income_amount, 0) as income_amount,
        coalesce(in_pay_period_refund_amount, 0) as in_pay_period_refund_amount,
        coalesce(non_pay_period_refund_amount, 0) as non_pay_period_refund_amount,
        coalesce(jp_cross_department_refund_amount, 0) as jp_cross_department_refund_amount,
        coalesce(same_lead_period_order_count, 0) as same_lead_period_order_count,
        coalesce(same_lead_period_conversion_lead_count, 0) as same_lead_period_conversion_lead_count,
        coalesce(same_lead_period_income_amount, 0) as same_lead_period_income_amount,
        coalesce(same_lead_period_refund_amount, 0) as same_lead_period_refund_amount
    from conversion_base t1
    where period_name_calc >= '20260403期'
),
conversion_by_channel as (
    select
        cd.period_name as qici,
        cd.natural_month,
        cd.employee_email_name as name,
        max(cd.jingli) as jingli,
        max(cd.zhuguan) as zhuguan,
        cd.channel_map,
        cd.grade_1,
        sum(
            case
                when cd.channel_map = '抖音私域' then cd.merge_assign_lead_count
                else cd.lead_count
            end
        ) as leads_count,
        sum(
            case
                when cd.channel_map = '抖音私域' then cd.merge_valid_lead_count
                else cd.valid_lead_count
            end
        ) as can_renew_ds_count_a,
        sum(cd.conversion_lead_count) as pay_users,
        sum(cd.same_lead_period_conversion_lead_count) as pay_users_on_period,
        sum(cd.conversion_lead_count - cd.same_lead_period_conversion_lead_count) as pay_users_not_on_period,
        sum(cd.subject_count) as pay_user_subs,
        sum(cd.same_lead_period_subject_count) as pay_user_subs_on_period,
        sum(cd.subject_count - cd.same_lead_period_subject_count) as pay_user_subs_not_on_period,
        sum(cd.lb_subject_count) as pay_user_subs_joint,
        sum(cd.same_lead_period_lb_subject_count) as pay_user_subs_joint_onp,
        sum(cd.lb_subject_count - cd.same_lead_period_lb_subject_count) as pay_user_subs_joint_nonp,
        sum(cd.income_amount / 100) as trade_income,
        sum(cd.in_pay_period_refund_amount / 100 + cd.non_pay_period_refund_amount / 100) as trade_refund,
        sum(cd.income_amount / 100 - cd.in_pay_period_refund_amount / 100 - cd.non_pay_period_refund_amount / 100) as trade_profit,
        sum(cd.same_lead_period_income_amount / 100) as xb_trade_income,
        sum(cd.same_lead_period_income_amount / 100 - cd.same_lead_period_refund_amount / 100) as xb_trade_profit,
        sum(cd.income_amount / 100 - cd.same_lead_period_income_amount / 100) as kk_trade_income,
        sum(cd.non_pay_period_refund_amount / 100) as pre_refund
    from conversion_data cd
    inner join eligible_consultant_name ec
      on ec.name = cd.employee_email_name
    group by
        cd.period_name,
        cd.natural_month,
        cd.employee_email_name,
        cd.channel_map,
        cd.grade_1
),
conversion_with_target as (
    select
        cc.qici,
        cc.natural_month,
        cc.name,
        cc.jingli,
        cc.zhuguan,
        cc.channel_map,
        cc.grade_1,
        cc.leads_count,
        cc.can_renew_ds_count_a,
        cc.pay_users,
        cc.pay_users_on_period,
        cc.pay_users_not_on_period,
        cc.pay_user_subs,
        cc.pay_user_subs_on_period,
        cc.pay_user_subs_not_on_period,
        cc.pay_user_subs_joint,
        cc.pay_user_subs_joint_onp,
        cc.pay_user_subs_joint_nonp,
        cc.trade_income,
        cc.trade_refund,
        cc.trade_profit,
        cc.xb_trade_income,
        cc.xb_trade_profit,
        cc.kk_trade_income,
        cc.pre_refund,
        cc.leads_count * coalesce(cd.cost, 0) as receive_target
    from conversion_by_channel cc
    left join cost_dim cd
      on cd.channel = cc.channel_map
),
conversion_agg as (
    select
        natural_month,
        name,
        max(jingli) as jingli,
        max(zhuguan) as zhuguan,
        sum(leads_count) as leads_count,
        sum(can_renew_ds_count_a) as can_renew_ds_count_a,
        case
            when sum(can_renew_ds_count_a) >= 5 then sum(can_renew_ds_count_a)
            else 0
        end as s_lead,
        case
            when sum(can_renew_ds_count_a) >= 5
             and sum(trade_profit) > 0 then 1
            else 0
        end as podan,
        sum(receive_target) as receive_target,
        sum(pay_users) as pay_users,
        sum(pay_users_on_period) as pay_users_on_period,
        sum(pay_users_not_on_period) as pay_users_not_on_period,
        sum(pay_user_subs) as pay_user_subs,
        sum(pay_user_subs_on_period) as pay_user_subs_on_period,
        sum(pay_user_subs_not_on_period) as pay_user_subs_not_on_period,
        sum(pay_user_subs_joint) as pay_user_subs_joint,
        sum(pay_user_subs_joint_onp) as pay_user_subs_joint_onp,
        sum(pay_user_subs_joint_nonp) as pay_user_subs_joint_nonp,
        sum(trade_income) as trade_income,
        sum(trade_refund) as trade_refund,
        sum(trade_profit) as trade_profit,
        sum(xb_trade_income) as xb_trade_income,
        sum(xb_trade_profit) as xb_trade_profit,
        sum(kk_trade_income) as kk_trade_income,
        sum(pre_refund) as pre_refund
    from conversion_with_target
    group by
        natural_month,
        name
),
conversion_metric_base as (
    select
        natural_month,
        name,
        jingli,
        zhuguan,
        leads_count,
        can_renew_ds_count_a,
        s_lead,
        podan,
        receive_target,
        pay_users,
        pay_users_on_period,
        pay_users_not_on_period,
        pay_user_subs,
        pay_user_subs_on_period,
        pay_user_subs_not_on_period,
        pay_user_subs_joint,
        pay_user_subs_joint_onp,
        pay_user_subs_joint_nonp,
        trade_income,
        trade_refund,
        trade_profit,
        xb_trade_income,
        xb_trade_profit,
        kk_trade_income,
        pre_refund,
        case
            when receive_target is null or receive_target = 0 then cast(0 as double)
            else trade_profit / receive_target
        end as target_completion_rate,
        case
            when pay_users is null or pay_users = 0 then cast(0 as double)
            else cast(pay_user_subs as double) / pay_users
        end as tuoke_rate
    from conversion_agg
),
target_completion_rank_raw as (
    select
        p.natural_month,
        p.dept,
        p.name,
        coalesce(cm.target_completion_rate, 0) as target_completion_rate,
        row_number() over (
            partition by p.natural_month, p.dept
            order by coalesce(cm.target_completion_rate, 0) desc, p.name
        ) as target_completion_period_dept_rank_no,
        lag(coalesce(cm.target_completion_rate, 0)) over (
            partition by p.natural_month, p.dept
            order by coalesce(cm.target_completion_rate, 0) desc, p.name
        ) as previous_target_completion_rate
    from month_ranked p
    inner join eligible_consultant_name ec
      on p.name = ec.name
    left join conversion_metric_base cm
      on p.natural_month = cm.natural_month
     and p.name = cm.name
),
target_completion_ranked as (
    select
        natural_month,
        dept,
        name,
        target_completion_rate,
        target_completion_period_dept_rank_no,
        case
            when previous_target_completion_rate is null then cast(0 as double)
            else previous_target_completion_rate - target_completion_rate
        end as target_completion_gap_to_previous
    from target_completion_rank_raw
)
select
    p.natural_month,
    concat(substr(p.natural_month, 1, 4), '年', substr(p.natural_month, 5, 2), '月') as natural_month_name,
    p.qici_list,
    p.dept,
    p.name,
    p.xiaozu,
    coalesce(p.jingli, cm.jingli) as jingli,
    coalesce(cm.zhuguan, '未知') as zhuguan,
    p.income,
    p.refund,
    p.pmit,

    p.period_dept_rank_scope,
    p.period_dept_rank_no,
    p.period_dept_need_pmit_to_previous,

    p.period_income,
    p.period_refund,
    p.period_pmit,

    coalesce(cm.leads_count, 0) as leads_count,
    coalesce(cm.can_renew_ds_count_a, 0) as can_renew_ds_count_a,
    coalesce(cm.s_lead, 0) as s_lead,
    coalesce(cm.podan, 0) as podan,
    coalesce(cm.receive_target, 0) as receive_target,
    coalesce(cm.pay_users, 0) as pay_users,
    coalesce(cm.pay_users_on_period, 0) as pay_users_on_period,
    coalesce(cm.pay_users_not_on_period, 0) as pay_users_not_on_period,
    coalesce(cm.pay_user_subs, 0) as pay_user_subs,
    coalesce(cm.pay_user_subs_on_period, 0) as pay_user_subs_on_period,
    coalesce(cm.pay_user_subs_not_on_period, 0) as pay_user_subs_not_on_period,
    coalesce(cm.pay_user_subs_joint, 0) as pay_user_subs_joint,
    coalesce(cm.pay_user_subs_joint_onp, 0) as pay_user_subs_joint_onp,
    coalesce(cm.pay_user_subs_joint_nonp, 0) as pay_user_subs_joint_nonp,
    coalesce(cm.trade_income, 0) as trade_income,
    coalesce(cm.trade_refund, 0) as trade_refund,
    coalesce(cm.trade_profit, 0) as trade_profit,
    coalesce(cm.xb_trade_income, 0) as xb_trade_income,
    coalesce(cm.xb_trade_profit, 0) as xb_trade_profit,
    coalesce(cm.kk_trade_income, 0) as kk_trade_income,
    coalesce(cm.pre_refund, 0) as pre_refund,

    coalesce(cm.target_completion_rate, 0) as target_completion_rate,
    '自然月-部门' as target_completion_month_rank_scope,
    coalesce(tr.target_completion_period_dept_rank_no, 0) as target_completion_period_dept_rank_no,
    coalesce(tr.target_completion_gap_to_previous, 0) as target_completion_gap_to_previous,
    coalesce(cm.tuoke_rate, 0) as tuoke_rate
from month_ranked p
inner join eligible_consultant_name ec
  on p.name = ec.name
left join conversion_metric_base cm
  on p.natural_month = cm.natural_month
 and p.name = cm.name
left join target_completion_ranked tr
  on p.natural_month = tr.natural_month
 and p.dept = tr.dept
 and p.name = tr.name
order by
    p.natural_month,
    p.dept,
    p.period_dept_rank_no,
    p.name
