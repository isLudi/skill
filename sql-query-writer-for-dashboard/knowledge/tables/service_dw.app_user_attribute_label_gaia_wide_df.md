# service_dw.app_user_attribute_label_gaia_wide_df

## 1. 中文名称

盖亚系统用户标签数据宽表

## 2. 表用途

用户标签宽表，用于查询用户标签、画像、学习意向等信息。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

## 3. 数据粒度

用户-标签粒度，待确认

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 | 来源 |
|---|---|---|---|---|---|
| 无 | - | - | 否 | 未识别 department_name 字段；若查询涉及业务范围仍需人工限定 | 字段目录 |

说明：
- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。
- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 分区过滤 | 是 |
| user_number | string | 用户ID | 主键/关联键 | 是 |
| type | string | 标签类型 key为枚举值类型 note为自定义值 value不限 | 待按需求确认 | 否 |
| resident | string | 走读/住校 | 待按需求确认 | 否 |
| tutoring | string | 补习情况 | 待按需求确认 | 否 |
| learning_attitude | string | 学习态度 | 待按需求确认 | 否 |
| holidays_situation | string | 放假情况 | 待按需求确认 | 否 |
| subject_selection | string | 学科选择 | 常用维度 | 是 |
| learn_principal | string | 学习负责人 | 待按需求确认 | 否 |
| learning_level | string | 学习水平 | 待按需求确认 | 否 |
| pass_cet_four | string | 通过四级 | 待按需求确认 | 否 |
| pass_cet_six | string | 通过六级 | 待按需求确认 | 否 |
| english_scores | string | 英语成绩 | 待按需求确认 | 否 |
| studying_abroad_major | string | 在读专业（留学） | 待按需求确认 | 否 |
| intention_major | string | 意向专业方向 | 待按需求确认 | 否 |
| learn_situation | string | 学情 | 待按需求确认 | 否 |
| notice_for_shiyedanwei | string | 公告情况 | 待按需求确认 | 否 |
| refund_warn | string | 高危退费 | 待按需求确认 | 否 |
| parent_attitude | string | 家长态度 | 待按需求确认 | 否 |
| adding_friends_purpose | string | 加好友初始目的 | 待按需求确认 | 否 |
| exam_reason | string | 参加考试原因 | 待按需求确认 | 否 |
| paid_attraction | string | 付费吸引点 | 待按需求确认 | 否 |
| conversion_difficulties | string | 转化难点 | 待按需求确认 | 否 |
| abnormal_traffic | string | 异常流量 | 待按需求确认 | 否 |
| renewal_intention | string | 续/扩/升/转意向 | 待按需求确认 | 否 |
| academic_record | string | 成绩 | 待按需求确认 | 否 |
| weak_subject | string | 薄弱学科 | 常用维度 | 是 |
| weak_point_comment | string | 薄弱点 | 待按需求确认 | 否 |
| learn_situation_all_comment | string | 学情/深沟 | 待按需求确认 | 否 |
| study_hours_per_day | string | 每天学习时长 | 待按需求确认 | 否 |
| gpa | string | 绩点情况 | 待按需求确认 | 否 |
| competition_experience | string | 大赛经验 | 待按需求确认 | 否 |
| english_proficiency | string | 英语水平 | 待按需求确认 | 否 |
| supervision_service | string | 督学服务 | 待按需求确认 | 否 |
| learning_plan | string | 学习计划 | 待按需求确认 | 否 |
| post_graduate_examination_reason | string | 考研原因 | 待按需求确认 | 否 |
| prepare_target | string | 备考目标 | 待按需求确认 | 否 |
| intention_study_abroad_stage | string | 留学意向阶段 | 待按需求确认 | 否 |
| intention_country_area | string | 意向国家地区 | 指标聚合 | 是 |
| go_abroad_time | string | 出国时间 | 时间分析 | 否 |
| customer_actual_needs | string | 客户实际需求 | 待按需求确认 | 否 |
| income_level | string | 月收入水平 | 待按需求确认 | 否 |
| occupation | string | 职业状态 | 待按需求确认 | 否 |
| work_year | string | 工作年限 | 待按需求确认 | 否 |
| education | string | 学历 | 待按需求确认 | 否 |
| post | string | 岗位 | 待按需求确认 | 否 |
| parents_background | string | 父母背景 | 待按需求确认 | 否 |
| graduate_level | string | 研究生圈层 | 待按需求确认 | 否 |
| language_portraits | string | 语言画像 | 待按需求确认 | 否 |
| intention_subjects | string | 意向科目 | 常用维度 | 是 |
| notes | string | 备注 | 待按需求确认 | 否 |
| parent_name | string | 家长姓名 | 待按需求确认 | 否 |
| school | string | 所在学校 | 待按需求确认 | 否 |
| class_frequency | string | 上课频次 | 待按需求确认 | 否 |
| schedule_time | string | 可排课时间 | 时间分析 | 否 |
| class_reporting_purpose_comment | string | 报班目的 | 待按需求确认 | 否 |
| speciality | string | 在读专业 | 待按需求确认 | 否 |
| post_graduate_examination_target_university | string | 考研目标学校 | 待按需求确认 | 否 |
| studying_university | string | 在读大学 | 待按需求确认 | 否 |
| intention_course | string | 意向课程 | 待按需求确认 | 否 |
| post_graduate_examination_prepare_year | string | 考研备考年份 | 待按需求确认 | 否 |
| civil_servant_prepare_year | string | 公职备考年份 | 待按需求确认 | 否 |
| entrance_area | string | 考试地区 | 待按需求确认 | 否 |
| age | string | 年龄 | 待按需求确认 | 否 |
| learning_person | string | 学习人 | 待按需求确认 | 否 |
| ca_user_portrait | string | 公职画像 | 待按需求确认 | 否 |
| can_sign_up | string | 可否报名 | 待按需求确认 | 否 |
| revising_exam_subject | string | 备考科目 | 常用维度 | 是 |
| revising_exam_period | string | 备考周期 | 常用维度 | 是 |
| number_of_free_lesson_hours | string | 赠课小时数 | 待按需求确认 | 否 |
| household_registration | string | 户籍 | 指标聚合 | 是 |
| educational_qualifications | string | 学籍学历 | 待按需求确认 | 否 |
| graduates | string | 应届生身份 | 待按需求确认 | 否 |
| cet | string | 四六级 | 待按需求确认 | 否 |
| political_status | string | 政治面貌 | 待按需求确认 | 否 |
| exam_preparation_status | string | 备考状态 | 指标聚合 | 是 |
| history_class_registration | string | 公考类历史报班 | 指标聚合 | 是 |
| student_age_range | string | 学员年龄区间 | 待按需求确认 | 否 |
| only_child | string | 独生子 | 待按需求确认 | 否 |
| living_standard | string | 生活水平 | 待按需求确认 | 否 |
| guardian | string | 监护人 | 待按需求确认 | 否 |
| parents_age_range | string | 家长年龄区间 | 待按需求确认 | 否 |
| parents_marital_status | string | 家长婚姻状态 | 待按需求确认 | 否 |
| teacher_age_range | string | 教师年龄区间 | 待按需求确认 | 否 |
| teaching_subject | string | 教授学科 | 常用维度 | 是 |
| postgraduate_entrance_examination_school | string | 目标院校 | 待按需求确认 | 否 |
| postgraduate_entrance_examination_majors | string | 目标专业 | 待按需求确认 | 否 |
| not_pay_reasons | string | 不购买原因 | 待按需求确认 | 否 |
| start_year | string | 入学年份 | 待按需求确认 | 否 |
| undergraduate_school_level | string | 本科院校层级 | 待按需求确认 | 否 |
| user_demand_points | string | 用户需求点 | 待按需求确认 | 否 |
| annual_income_level | string | 年收入水平 | 待按需求确认 | 否 |
| professional_course_rankings | string | 专业课排名 | 待按需求确认 | 否 |
| total_score | string | 目前总分 | 待按需求确认 | 否 |
| achievement_level | string | 成绩水平 | 待按需求确认 | 否 |
| student_information | string | 学情交接 | 待按需求确认 | 否 |
| exam_preparation_goals | string | 备考目标 | 指标聚合 | 是 |
| over_exam_times | string | 历史考试次数 | 时间分析 | 否 |
| exam_preparation_plan | string | 备考计划 | 指标聚合 | 是 |
| application_experience | string | 报考经历 | 待按需求确认 | 否 |
| training_experience | string | 参培经历 | 待按需求确认 | 否 |
| special_service_period | string | 专项服务期 | 常用维度 | 是 |
| supervision_service_period | string | 督学服务期 | 常用维度 | 是 |
| learning_status | string | 学习状态 | 待按需求确认 | 否 |
| preparation_status | string | 准备情况 | 指标聚合 | 是 |
| preferential_learning_methods | string | 偏好学习方式 | 待按需求确认 | 否 |
| expected_investment_funds | string | 预计投入资金 | 待按需求确认 | 否 |
| exam_preparation_obstacles | string | 备考障碍 | 指标聚合 | 是 |
| learning_demands | string | 学习诉求 | 待按需求确认 | 否 |
| learning_direction | string | 学习方向 | 待按需求确认 | 否 |
| age_range | string | 年龄区间 | 待按需求确认 | 否 |
| admission | string | 录取情况 | 待按需求确认 | 否 |

## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`

## 9. 常用 join key

- `user_number`：用户关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.user_number,
    t.type,
    t.resident,
    t.tutoring,
    t.learning_attitude,
    t.holidays_situation,
    t.subject_selection,
    t.learn_principal,
    t.learning_level,
    t.pass_cet_four,
    t.pass_cet_six,
    t.english_scores,
    t.studying_abroad_major,
    t.intention_major,
    t.learn_situation
from service_dw.app_user_attribute_label_gaia_wide_df t
where t.dt = 'YYYYMMDD'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 112。
- 所属项目：服务域；owner：梁壮。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 112。
- 所属项目：服务域；owner：梁壮。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 112。
- 所属项目：服务域；owner：梁壮。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 分区限制：查询分区表必须带分区条件。
- department_name 范围限定：涉及部门字段必须过滤；未给取值时使用占位符。
- 字段类型注意事项：PDF 图片 OCR 低置信度字段必须先人工确认。
- 常见报错：字段不存在、库名前缀不正确、小时表遗漏 hour、group by 不完整。
- 待人工确认问题：
- PDF 第 1-4 页为图片型字段表，已人工录入部分清晰字段；完整字段需复核。
