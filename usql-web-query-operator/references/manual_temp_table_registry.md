# 手工临时表 Registry

更新日期：2026-07-20

本文档记录本地 Excel 手工表与 SQL取数平台标准临时表名之间的对应关系。机器可读源文件是 `references/manual_temp_table_registry.json`，上传脚本读取 JSON 文件，本 Markdown 供人工阅读。

## 映射策略

- `platform_exact_name`：本地文件名 stem 加上 `dingxi01_` 前缀后，能精确匹配已观察到的平台临时表。
- `platform_verified_import_history`：映射有平台成功导入历史行作为证据。
- `platform_inferred_semantic` / `platform_inferred_abbreviation`：根据本地业务名和已观察到的平台表列表推断。
- `review_required_*`：脚本可以报告候选表，但不会自动作为上传目标；调用方必须显式传入 `--target-table`。

## 市场顾问部手工表

| 本地文件 | 标准临时表 | 状态 | 可自动作为目标表 | 主要检查 |
|---|---|---|---|---|
| `ceshiqudao_pingyou.xlsx` | `dingxi01_ceshiqudao_pingyou` | 精确匹配 | 是 | 必填列 |
| `cost.xlsx` | `dingxi01_cost` | 精确匹配 | 是 | 必填列 |
| `daoke_1_6_t.xlsx` | `dingxi01_daoke_1_6_t` | 精确匹配 | 是 | 必填列；`qudao`/`grade` 覆盖需要 SQL 侧检查 |
| `jiagou_db.xlsx` | `dingxi01_jiagou_db` | 精确匹配 | 是 | prefix 小写；`qici + employee_email_name` 不能重复；`xiaozu` 名称变体 |
| `jiagou_zx.xlsx` | `dingxi01_jiagou_zx` | 精确匹配 | 是 | prefix 小写；`jingli` 不能为空或 `-`；推断缺失经理建议 |
| `jinliang_goal.xlsx` | `dingxi01_jinliang_goal` | 精确匹配 | 是 | 必填列 |
| `leads_goal.xlsx` | `dingxi01_goal` candidate | 需要复核 | 否 | 平台没有 `dingxi01_leads_goal`；覆盖前需确认 |
| `pingyou_jg.xlsx` | `dingxi01_pingyou_jg` | 精确匹配 | 是 | 一个顾问不应对应多个主管/分组值 |
| `plan_id.xlsx` | `dingxi01_plan_id` | 精确匹配 | 是 | 必填列 |

## 青橙项目部手工表

| 本地文件 | 标准临时表 | 状态 | 可自动作为目标表 | 主要检查 |
|---|---|---|---|---|
| `qing_daoke.xlsx`（兼容旧名 `daoke_t_one_six_qing.xlsx`） | `dingxi01_qing_daoke` | 语义推断 | 是 | 必填列；不能有空表头；`qudao`/`grade` 覆盖需要 SQL 侧检查 |
| `qing_qi_moth.xlsx` | `dingxi01_qing_qi_moth` | 精确匹配 | 是 | 必填列 |
| `qing_goal.xlsx`（兼容旧名 `qing_qici_goal.xlsx`） | `dingxi01_qing_goal` | 语义推断 | 是 | 必填列 |
| `qing_team_goal_qi.xlsx` | `dingxi01_qing_team_g_qi` | 缩写推断 | 是 | 必填列 |
| `qing_team_goal_moth.xlsx` | `dingxi01_qing_team_goal` | 语义推断 | 是 | 必填列 |
| `qing_team_jg.xlsx` | `dingxi01_qing_team_jg` | 导入历史已验证 | 是 | 必须有 `qici`；`dazu` 不能为 `0`；email prefix 小写 |
| `qing_team_moth_jg.xlsx` | `dingxi01_month_jg` candidate | 需要复核 | 否 | 平台名缺少 qing/team 前缀；覆盖前需确认 |

## 本地数据规则

- 小写 prefix 规则检查配置列中的第一个 ASCII 字母。中文名和非字母前缀不会被该本地检查标记。
- 名称变体检查会按“移除尾部数字”后的基础名称分组；当同时存在普通名称和带数字后缀名称时，优先建议使用带数字后缀的规范值。
- `jiagou_zx.jingli` 缺失值不会由上传命令自动回填。validator 会报告那些 `xiaozu` 能唯一推断出已有 `jingli` 候选值的行，供上传前人工审核。
- `qudao` 和 `grade` 是否覆盖当前期进量课程，无法仅从 Excel 文件判断。validator 会输出提示；关键上传前仍需要 SQL 侧比对。
