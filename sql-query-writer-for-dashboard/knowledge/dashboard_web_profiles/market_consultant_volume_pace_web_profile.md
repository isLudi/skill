# 市场顾问-进量节奏 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- dashboard_id：`dashboard_3791961955008733184`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3791961955008733184&sourceType=1`
- profile 时间：2026-06-01 09:33:00
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\dashboard_profiles\market_consultant_20260601\市场顾问-进量节奏\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 1 |
| `value_unit_count` | 1 |
| `data_ready_unit_count` | 1 |
| `analytic_unit_count` | 1 |
| `analytic_data_ready_unit_count` | 1 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

无全局筛选器结构。

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 分渠道进量节奏 | unit_3903063829110960129 | u_pivot | 2307 进量节奏 | page=200<br>download=0 | data_ready | task=1378412941,1378412942<br>rows=132<br>total=132 |

## 5. 分析单元字段结构

### 分渠道进量节奏

- unit_id：`unit_3903063829110960129`；类型：`u_pivot`；模型：`2307` / 进量节奏
- 刷新：data_ready；task_ids：`1378412941,1378412942`；行数：132；序列：0 / 0 点
- 维度/表头字段：渠道小类（id=361904）、年级（id=398440）、接量人力（id=customized_975776757062987777）、已分配（id=8346823364339712）、分配目标（id=8343155372615682）、进量比例（id=customized_975776757360783360）、有效分配（id=8346823364339713）、有效留存（id=customized_975776757163651073）、group_period_name（id=321701）、qudao（id=361904）、jingli（id=361906）
- 指标/序列字段：接量人力、已分配、分配目标、进量比例、有效分配、有效留存

## 6. 维护注意事项

- `u_text`、`u_material` 等非分析单元可能返回空数据，这是展示素材，不按刷新失败处理。
- 生成 SQL 或排查指标时，应回到对应 `knowledge/dashboards/*.md` 和 `knowledge/metrics/*.md` 确认业务口径；本文件只说明 Web BI 当前配置结构。
- 看板筛选器存在动态默认值时，应优先读取本文件中的字段 ID、默认值样例和作用单元，再按业务需求替换。
