---
name: jingpin-dashboard-sql
description: Resolve 精品班学部 business semantics and build governed QuerySpec or bounded read-only probes for its refund, channel, learning, contact, ASR, and advisor-tenure analysis. Use when the requested course scope is 精品班学部. Do not route 市场顾问部 or 青橙项目部 semantics here.
---

# 精品班学部 SQL

## 领域边界

本 Skill 只负责 `domain_id=jingpin_department`。课程范围至少包含 `course_first_level_department_name='H业务线'` 和 `course_second_level_department_name='精品班学部'`。精品班课程覆盖多个业绩部门，不得追加市场顾问部、青橙项目部或单一业绩二级部门过滤，除非用户明确要求该子群。不得从其他领域补齐精品班的期次、产品、渠道、组织或 Join 定义。

## 工作方式

1. 将需求整理为 QuerySpec，显式记录指标、维度、过滤、业务范围、时间、计算粒度、输出粒度、候选表、Join、证据和未决项。
2. 读取 [统计范围与指标](knowledge/metrics/scope_metrics.md)。涉及渠道、触达、学习、退款原因、ASR或司龄时，再读取 [渠道、触达与原因](knowledge/channel_touch_reason.md)。
3. 只有来源 Hash 绑定的 `confirmed` 合同可进入可执行计划。精品班暑秋产品分类、跨业绩部门二讲身份或员工组织范围未确认时，只生成受限物理探查。
4. `usql-web-query-operator` 必须识别 `jingpin_department`，不得借用其他域绕过 allowlist。
5. 本 Skill 不授权执行、下载、飞书写入、发布或 Git 操作。

## 验收不变量

- 退款先按学员和统计窗口累计，再应用500元门槛，不按单笔流水先过滤。
- 保留购买人数、实收GMV、退费人数和退款金额，四项率由同一切面的分子分母计算。
- 人数在输出分组内去重，不能相加分组人数充当总体人数。
- 历史渠道CASE保持版本和分支先匹配语义，未知不得为满足排名目标强制归类。
- 节点分析排除节点前已退款学员，有效接通为 `call_status=1 AND call_duration>0`。
- ASR原文、手机号、学员标识和个人证据不进入飞书交付。
- 只描述观察性差异，不把渠道、触达或司龄直接解释为退费因果。

## 当前能力状态

精品班日期到标准期的映射已确认，且不存在名为“20260501期”的配置；专题起点按不早于2026-05-01处理并单列审计5月1至2日。暑秋正价产品范围和标准/D30学员累计500元门槛已确认。历史二讲身份来源、员工组织完整范围仍为 `pending_confirmation`，只阻断依赖这些字段的对应专题，不阻断已确认范围内的财务与渠道汇总。
