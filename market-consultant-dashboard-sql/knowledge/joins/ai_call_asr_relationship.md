# AI 通话记录、分析结果与 ASR 的候选关联

记录日期：2026-09-17。用户提供的预期查询源文本 SHA-256：`060ea7bbd775b2078ec3ae5d1deecc74d4b9d3d1d8db202fc724d907e4aa9194`。

## 关联路径

- 主表：`service_dw.ods_service_ai_ones_business_copilot__call_record_df`。
- 候选 AI 结果：同分区 `call_id` 接 `service_dw.ods_service_ai_ones_business_copilot__ai_call_analysis_result_df`，分析结果取 `is_del=0`。
- 候选 ASR：`call_url = origin_file_url` 接 `one_dw.dwd_mkt_ai_assistant_asr_record_df`，ASR 取 `state=2 AND parsed_content IS NOT NULL`。
- 三表本身均无市场顾问部门字段；业务范围必须由已限定的线索人群经通话表 `user_number` 传递。这里的物理探查不等于市场顾问口径确认。

## 已验证的分区物理事实

- `dt='20260915'`：ASR 159,507,223 行，通话 81,108,669 行，AI 结果 69,375,212 行。数据地图把 ASR 标为增量表，把后两表标为全量表。同分区不自动保证跨表录音覆盖。计数 Query：`1591080868`、`1591083960`。
- ASR `state=2` 有 157,748,922 行，其中 `parsed_content` 非空且非空串 157,174,987 行、`origin_file_url` 空值或空串 8,507 行。附件条件只排除原文 NULL，没有排除空串或空 URL。状态 Query：`1591084542`。
- 定向基数探针（Query `1591086950`）只取 `dt='20260915'`、`call_time` 日期 `2026-09-15`、`user_number IS NOT NULL` 且 `mod(user_number,1000)=0` 的 88 条通话；这是非市场专属的诊断子集。样本有 88 个不同 `call_id`，没有空 `call_id` 或空 `call_url`。
- 在该样本上，按 `a.dt=r.dt AND a.call_id=r.call_id AND a.is_del=0`，88 条均匹配且没有多匹配；按 ASR URL 关联，88 条均匹配，但 3 条通话多匹配，最多 3 条 ASR/通话。样本命中率和 AI 唯一性不能外推至全分区。
- 对此样本，直接双 `LEFT JOIN` 后的通话时长相当于 9,484 秒，原事实表为 7,887 秒，放大 1,597 秒（约 20.25%）。附件 `call_agg` 的 `COUNT(*)`、`SUM(call_duration)`、`COUNT(a.call_id)`、`COUNT(s.parsed_content)` 和 `ARRAY_AGG` 均面临行放大风险。

## 使用约束与未决项

- 原 SQL 不应直接把未去重 ASR 左连接到通话事实后统计电话数和总时长。先确定每个 `origin_file_url` 的业务取舍规则，再以匹配后唯一键和聚合守恒验证；不能仅凭 `ROW_NUMBER()` 任意取一条。
- 关联 ASR 时应排除空 `origin_file_url`，且空 `call_url` 不应参与等值关联。`parsed_content=''` 是否视为有效原文待业务确认。
- AI 结果 `is_del` 为 `bigint`，应使用 `is_del=0`。是否还需限制 `analysis_status`、通话记录 `is_del`，以及 ASR 增量分区对全量通话快照的覆盖窗口，仍待确认。
- 当前仅验证物理诊断子集的 Join 风险，未把任一候选关联升级为全量 `confirmed` contract。
