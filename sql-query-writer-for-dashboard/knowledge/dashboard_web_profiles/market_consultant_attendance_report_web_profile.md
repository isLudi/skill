# 市场顾问部_行课报表 Web BI 结构快照

> 本文件记录自助 BI 页面结构、筛选器、组件单元、字段/指标和刷新验证结果。它补充 Web 前端配置，不替代历史 SQL 业务口径。
> 为避免沉淀结果明细，知识库只保存结构、字段、任务 ID 和行数/序列计数，不保存返回数据行。

## 1. 来源

- dashboard_id：`dashboard_3748410696516800512`
- 打开入口：`https://uanalysis.baijia.com/dashboard-market?id=dashboard_3748410696516800512&sourceType=1`
- profile 时间：2026-06-01 09:30:16
- 原始结构 profile：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\dashboard_profiles\market_consultant_20260601\市场顾问部_行课报表\profile.json`
- 页面渲染：成功

## 2. 刷新验证

| 项目 | 数值 |
|---|---:|
| `unit_count` | 5 |
| `value_unit_count` | 4 |
| `data_ready_unit_count` | 3 |
| `analytic_unit_count` | 3 |
| `analytic_data_ready_unit_count` | 3 |
| `error_count` | 0 |
| `all_analytic_units_ready` | True |

## 3. 全局筛选器

| 筛选器 | 字段/展示名 | field_id | 默认/动态值样例 | 作用单元数 |
|---|---|---|---|---|
| 期次 | qici | 289670 | 20260529期 | 3 |
| 线索渠道 | channel_map_1 | 289671 | 进校0元、训练营、未知、线索复用 | 3 |
| 年级 | grade_1 | 289672 |  | 3 |
| 规则 | rule_name | 374265 |  | 3 |

## 4. 组件和单元

| 单元 | unit_id | 类型 | 模型 | 分页/下载 | 刷新状态 | task_id / 行数 |
|---|---|---|---|---|---|---|
| 标题图 | unit_3748416372584517632 | u_material | 1 主题分析 |  | loaded_empty | rows=0 |
| 全局筛选器 | public_filter_relation_3748432894568730625 | public_filter_relation |  |  | filter_relation |  |
| 渠道年级行课 | unit_3748421949431779328 | u_pivot | 2132 (内部)到课衰减情况 | page=100<br>download=True | data_ready | task=1378411104,1378411103<br>rows=10<br>total=10 |
| 主管行课 | unit_3748425123565043713 | u_pivot | 2132 (内部)到课衰减情况 | page=100<br>download=True | data_ready | task=1378411113,1378411112<br>rows=23<br>total=23 |
| 伙伴行课 | unit_3748430264775114753 | u_pivot | 2132 (内部)到课衰减情况 | page=100<br>download=True | data_ready | task=1378411123,1378411122<br>rows=100<br>total=262 |

## 5. 分析单元字段结构

### 渠道年级行课

- unit_id：`unit_3748421949431779328`；类型：`u_pivot`；模型：`2132` / (内部)到课衰减情况
- 刷新：data_ready；task_ids：`1378411104,1378411103`；行数：10；序列：0 / 0 点
- 维度/表头字段：线索渠道（id=289671）、年级（id=289672）、部门（id=289674）、应出勤人数（id=8172915650029568）、课1（id=customized_963548566671110145）、课2（id=customized_963548566922768385）、课3（id=customized_963548567178620928）、课4（id=customized_963548567426084865）、课5（id=customized_963548567677743105）、课6（id=customized_963548567937789953）、课1有效（id=customized_963548566796939265）、课2有效（id=customized_963548567044403200）、课3有效（id=customized_963548567304450048）、课4有效（id=customized_963548567551913985）、课5有效（id=customized_963548567803572225）、课6有效（id=customized_963548568067813376）
- 指标/序列字段：应出勤人数、课1、课2、课3、课4、课5、课6、课1有效、课2有效、课3有效、课4有效、课5有效、课6有效

### 主管行课

- unit_id：`unit_3748425123565043713`；类型：`u_pivot`；模型：`2132` / (内部)到课衰减情况
- 刷新：data_ready；task_ids：`1378411113,1378411112`；行数：23；序列：0 / 0 点
- 维度/表头字段：主管（id=289673）、应出勤人数（id=8172915650029568）、课1（id=customized_963548566671110145）、课2（id=customized_963548566922768385）、课3（id=customized_963548567178620928）、课4（id=customized_963548567426084865）、课5（id=customized_963548567677743105）、课6（id=customized_963548567937789953）、课1有效（id=customized_963548566796939265）、课2有效（id=customized_963548567044403200）、课3有效（id=customized_963548567304450048）、课4有效（id=customized_963548567551913985）、课5有效（id=customized_963548567803572225）、课6有效（id=customized_963548568067813376）、department（id=289674）
- 指标/序列字段：应出勤人数、课1、课2、课3、课4、课5、课6、课1有效、课2有效、课3有效、课4有效、课5有效、课6有效

### 伙伴行课

- unit_id：`unit_3748430264775114753`；类型：`u_pivot`；模型：`2132` / (内部)到课衰减情况
- 刷新：data_ready；task_ids：`1378411123,1378411122`；行数：100；序列：0 / 0 点
- 维度/表头字段：主管（id=289673）、顾问（id=289698）、渠道（id=289671）、应出勤人数（id=8172915650029568）、课1（id=customized_963548566671110145）、课2（id=customized_963548566922768385）、课3（id=customized_963548567178620928）、课4（id=customized_963548567426084865）、课5（id=customized_963548567677743105）、课6（id=customized_963548567937789953）、课1有效（id=customized_963548566796939265）、课2有效（id=customized_963548567044403200）、课3有效（id=customized_963548567304450048）、课4有效（id=customized_963548567551913985）、课5有效（id=customized_963548567803572225）、课6有效（id=customized_963548568067813376）、xiaozu（id=289673）、channel_map_1（id=289671）
- 指标/序列字段：应出勤人数、课1、课2、课3、课4、课5、课6、课1有效、课2有效、课3有效、课4有效、课5有效、课6有效

## 6. 维护注意事项

- `u_text`、`u_material` 等非分析单元可能返回空数据，这是展示素材，不按刷新失败处理。
- 生成 SQL 或排查指标时，应回到对应 `knowledge/dashboards/*.md` 和 `knowledge/metrics/*.md` 确认业务口径；本文件只说明 Web BI 当前配置结构。
- 看板筛选器存在动态默认值时，应优先读取本文件中的字段 ID、默认值样例和作用单元，再按业务需求替换。
