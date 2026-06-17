# Manual Temporary Table Registry

Updated: 2026-06-17

This registry records local Excel manual tables and their standard temporary
table names on the SQL取数 platform. The machine-readable source is
`references/manual_temp_table_registry.json`; upload scripts read that file.

## Mapping Policy

- `platform_exact_name`: local filename stem matches an observed platform temp
  table after the `dingxi01_` prefix is added.
- `platform_verified_import_history`: mapping is backed by a successful import
  row observed through the platform.
- `platform_inferred_semantic` / `platform_inferred_abbreviation`: mapping is
  inferred from the local business name and the observed platform table list.
- `review_required_*`: the script can report the candidate table but will not
  auto-target it unless the caller passes `--target-table` explicitly.

## Market Consultant Tables

| Local file | Standard temp table | Status | Auto target | Main checks |
|---|---|---|---|---|
| `ceshiqudao_pingyou.xlsx` | `dingxi01_ceshiqudao_pingyou` | exact | yes | required columns |
| `cost.xlsx` | `dingxi01_cost` | exact | yes | required columns |
| `daoke_1_6_t.xlsx` | `dingxi01_daoke_1_6_t` | exact | yes | required columns; qudao/grade coverage needs SQL-side check |
| `jiagou_db.xlsx` | `dingxi01_jiagou_db` | exact | yes | lowercase prefixes; duplicate `qici + employee_email_name`; `xiaozu` variant names |
| `jiagou_zx.xlsx` | `dingxi01_jiagou_zx` | exact | yes | lowercase prefixes; `jingli` cannot be blank or `-`; infer missing manager suggestions |
| `jinliang_goal.xlsx` | `dingxi01_jinliang_goal` | exact | yes | required columns |
| `leads_goal.xlsx` | `dingxi01_goal` candidate | review required | no | platform has no `dingxi01_leads_goal`; confirm before overwrite |
| `pingyou_jg.xlsx` | `dingxi01_pingyou_jg` | exact | yes | one consultant should not map to multiple supervisor/group values |
| `plan_id.xlsx` | `dingxi01_plan_id` | exact | yes | required columns |

## Qingcheng Tables

| Local file | Standard temp table | Status | Auto target | Main checks |
|---|---|---|---|---|
| `daoke_t_one_six_qing.xlsx` | `dingxi01_qing_daoke` | inferred semantic | yes | required columns; no blank headers; qudao/grade coverage needs SQL-side check |
| `qing_qi_moth.xlsx` | `dingxi01_qing_qi_moth` | exact | yes | required columns |
| `qing_qici_goal.xlsx` | `dingxi01_qing_goal` | inferred semantic | yes | required columns |
| `qing_team_goal_qi.xlsx` | `dingxi01_qing_team_g_qi` | inferred abbreviation | yes | required columns |
| `qing_team_goal_moth.xlsx` | `dingxi01_qing_team_goal` | inferred semantic | yes | required columns |
| `qing_team_jg.xlsx` | `dingxi01_qing_team_jg` | verified import history | yes | qici required; `dazu` cannot be `0`; lowercase email prefixes |
| `qing_team_moth_jg.xlsx` | `dingxi01_month_jg` candidate | review required | no | platform name lacks qing/team prefix; confirm before overwrite |

## Local Data Rules

- Lowercase prefix rules check the first ASCII letter in configured columns.
  Chinese names and non-letter prefixes are not flagged by this local check.
- Name variant checks group names by removing trailing digits and prefer the
  variant with a numeric suffix when both plain and suffixed forms exist.
- Missing `jiagou_zx.jingli` values are not filled by the upload command. The
  validator reports rows where `xiaozu` has a unique existing `jingli`
  candidate, so the workbook can be reviewed before a manual edit.
- Coverage of `qudao` and `grade` against current-period inbound-course data is
  not knowable from the Excel file alone. The validator emits an informational
  reminder; a SQL-side comparison is still required before critical uploads.
