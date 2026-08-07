# 渠道 CASE 映射口径

## 1. 口径名称

市场顾问渠道 CASE 映射口径

## 2. 最新来源

- 0805 版本原始来源：`C:\Users\Ludim\Desktop\CASE.txt`，来源文件 SHA-256 `7ae55aa357ac5f27b23a7f1e82a609c5479ca473667e758667191f42869b3842`
- Skill 最新归档：`resources/raw_sql/market_channel_case_when_0805.sql`
- 0805 与 0726 逐分支融合：保留 0805 的完整顺序，审计新增、删除、条件/输出变化及公共分支移位；不按固定行号切片替换
- 0805 精确执行 CASE：170 个 `WHEN` 分支，109 个去重后的渠道输出值；CASE 文本 SHA-256 `73bc9bdc26c7719640c6a66352f1675743ae1f7655221e197ab87865068f236e`
- 最近共享 CASE 更新日期：2026-08-05；Data Center 定向覆盖补充日期：2026-08-01 至 2026-08-05
- 输出字段：`qudao`

### 0726 → 0805 融合审计

- 0805 相比 0726：新增 30 个分支、删除 16 个既有分支、7 处条件/输出变化，公共分支存在顺序调整；另保留 15 组相邻同输出规则作为审计信息，不以机械合并结果替代线上规则。
- 0805 的 `北京直播江苏`、区域图书、曹忆、锋途 KOC、退款复用及进校相关分支均按原始顺序进入所有完整渠道 CASE 消费者；特异规则继续位于会抢先命中的宽泛规则之前。
- 2054 的完整查询探针证明：相邻安全合并版本在 Doris JDBC 下出现无结果集失败，因此生产数据集继续使用 0805 精确有序 CASE；性能优化仅改已验证的分区过滤、投影、无用 CTE/JOIN 和展示层排序，不改渠道语义。
- 当前 27 个完整 CASE 数据中心目标中 25 个完成新 SQL 保存、读回和新 `SUCCESS`，2886/2890 已读回优化 SQL 但刷新链暂无新执行记录，故不将其标记为上线成功。

### 0524 → 0612 增量变更

- **新增/细分**孟亚飞 1 组与 2 组渠道：`孟亚飞-1组-抖音`、`孟亚飞-1组-B站`、`孟亚飞-1组-百度`、`孟亚飞-2组-百度`、`孟亚飞-2组-抖音`。
- **2026-06-18 口径修正**：业务反馈 `孟亚飞-1组-视频号` 与 `孟亚飞9元` 为同一渠道，0612 CASE 中 `channel_name_2 = '视频号'` 的孟亚飞 1 组分支统一输出 `孟亚飞9元`；后续看板不应再把 `孟亚飞-1组-视频号` 作为独立展示渠道。
- **新增/细分** B 站信息流渠道：`B站信息流-曹忆`、`B站信息流-汤学健`、`B站信息流-亚飞(1元)`。
- **新增** `进校直推`、`信息流-陈瑞春`。
- **移除或合并**一批旧输出值，例如 `周帅-百度数字人`、`孟亚飞百度数字人`、`孟亚飞99-2组`、`信息流-肖晗`、`市场私域小红书`、`正价课判单补录`、`转介绍` 等；旧口径 raw SQL 已清理，不再作为活跃维护入口。

### 0612 → 0723 增量变更

- 新增期次无关规则：

```sql
when rule_name like '%北京直播江苏%'
then '北京直播江苏'
```

- 不得把 `0728期`、年级或其他当期字段写死在渠道 CASE 中；未来期次只要 `rule_name` 包含 `北京直播江苏`，均统一归因为 `北京直播江苏`。
- 该规则必须位于所有宽泛流量池、老师 IP、渠道树条件之前。2026-07-23 在线探针 query `1495639193` 显示，最新可见分区 `dt='20260723' and hour='13'` 中纯值等于 `北京直播江苏` 命中 0 条，而 `like '%北京直播江苏%'` 命中 15 条明细，`sum(lead_count)=14`、`sum(valid_lead_count)=14`；既有 query `1495469885` 显示其中 8 条线索的 `flow_pool_name` 含 `星义物理`，若不前置会先命中 `赵星义`。
- 规则在不同数据集可输出为 `channel_map`、`channel_map_1` 或 `qudao`；展示值统一为 `北京直播江苏`，不因最终字段别名变化。

### 0723 → 0726 合并变更

- 以 0723 版本为合并基线，继续将 `rule_name like '%北京直播江苏%' then '北京直播江苏'` 保持为第一优先级规则。
- 保留孟亚飞 1 组视频号合并口径：符合该分支的记录继续输出 `孟亚飞9元`，不拆成独立的 `孟亚飞-1组-视频号`。
- 从 `D:\Feishu\1.txt` 吸收 16 条区域/KOC/进校新增分支，新增或补齐河南进校、广东/浙江/上海/江苏图书、曹忆、北京直播山东、北京直播河南、锋途KOC、西安直播江苏（抖音/视频号）和西安直播北京。
- 接受 17 处 KOC/进校条件扩展：包括 KOC 人员名单补充曲默晗、孟亚飞数学补充 `rule_name like '%初二%'`、周帅数学补充新高二 SKU、进校名单补充赵艺雅、TMK1元补充禾顺云、进校私域合作补充肖佳兴/姚佳03。
- 按新稿差异删除 34 条旧规则实例；其中北京直播江苏按相同业务条件重新插入最高优先级，因此实际不再保留的是另外 33 条旧业务分支。
- 未吸收超出本次范围的 `赠课失败`、`EM-小红书合作`、`转介绍`、`搜索1元`、`集团私域`、`郭艺`、`B站信息流-赵星义`、`APP` 等新增条件；同时拒绝 7 处与本次区域/KOC/进校无关的输出值变化，继续沿用 0723 输出口径。
- 0726 canonical SQL 的 SHA-256 为 `ae19deefce5c646b51c85e51e7df7f5449161d3f0c3d36dab07723e05ead443d`；完整选择与排除证据见本次 runtime 合并清单。

### 2026-08-01 0728 期退款复用批次定向覆盖

- 业务确认：`20260803期` 中来源三级部门为 `线上商务部`、source 负责人为 `曲默晗` 或 `何木玲`、SKU 以 `0728期-` 开头且包含 `帅师` 或 `孟帝` 的线索，是 0728 期退款后的线索复用，不属于 `KOC-周帅数学` 或 `KOC-孟亚飞数学`。
- 旧 CASE 会因 SKU 和 source 负责人条件命中两个 KOC 分支；修正后统一输出 `退款订单复用`。该分支必须位于所有周帅数学、孟亚飞数学 KOC 分支之前：

```sql
when period_name = '20260803期'
 and third_department_name = '线上商务部'
 and source_manager_name in ('曲默晗', '何木玲')
 and sku_id_name like '0728期-%'
 and (sku_id_name like '%帅师%' or sku_id_name like '%孟帝%')
then '退款订单复用'
```

- 这是按业务事实确认的单批次覆盖，不得移除期次、来源部门、source 负责人或 SKU 四组边界并泛化到其他期次。模型使用别名时仅做等价字段替换，例如 model `2344` 使用 `lf_period_name`/`lf.*`，model `2978` 使用 `lb.period_name`/`lb.*`。
- 修正已写入 22 个当前 Data Center canonical SQL：`2054, 2132, 2253, 2293, 2310, 2344, 2345, 2533, 2688, 2751, 2774, 2809, 2812, 2836, 2842, 2883, 2885, 2886, 2890, 2978, 3039, 3153`。model `2344` 有 3 处同义 CASE，均需保持一致；model `2978` 是 KOC 范围播报，改归 `退款订单复用` 后该批次应从其 KOC-only 输出中排除。
- 修正前精确批次 `sum(lead_count)=1444`，其中 `KOC-周帅数学=1121`、`KOC-孟亚飞数学=323`；1442 计入既有退款池/退款计划匹配，另 2 条未命中该物理池条件，但业务确认整批均为退款复用。修正后 query `1514422403` 验证 1444 全部归入 `退款订单复用`，两个错误 KOC 渠道残留为 0；截至 2026-08-01，`20260728期` 的周帅 KOC 209 尚未调整，2026-08-02 按新的退款池证据另行重分类，见下一节。
- `resources/raw_sql/market_channel_case_when_0805.sql` 是通用共享基线；对上述当前 Data Center 模型做整体 CASE 替换时，必须在共享基线上继续保留本定向覆盖，不能因重新粘贴共享片段而丢失。

### 2026-08-02 20260728 期线上商务部退款复用高优先级覆盖

- 业务确认：`20260728期` 中来源三级部门为 `线上商务部`，同时满足 `电商退款用户池 + 0728期退款用户计划 + 内部/流量复用 + source负责人曲默晗 + 0728期帅师SKU` 的记录，是线上商务部退款后的线索复用，不属于 `KOC-周帅数学`。旧 CASE 的通用退款分支只覆盖 `直播部/新媒体内容运营部/市场一组/私域运营部`，未包含 `线上商务部`，因此这批记录继续向下命中“曲默晗 + 帅师 SKU”的 KOC 宽泛分支。
- 必须在既有 `20260803期` 定向覆盖以及所有孟亚飞/周帅 KOC 分支之前增加以下精确分支；八组边界不得删减或泛化：

```sql
when period_name = '20260728期'
 and third_department_name = '线上商务部'
 and flow_pool_name = '电商退款用户池'
 and put_plan_name = '0728期退款用户计划'
 and channel_name_1 = '内部'
 and channel_name_2 = '流量复用'
 and source_manager_name = '曲默晗'
 and sku_id_name like '0728期-%帅师%'
then '退款订单复用'
```

- 上线后 query `1517735633` 验证：退款池共 214 个源行/214 个去重线索，`sum(lead_count)=209`、`sum(valid_lead_count)=209`，全部输出 `退款订单复用`。原无年级异常队列中的 1 条 KOL 线索来自 `金榜题火箭班 + 达人-刘(个人)-43-自动创建 + 商务/KOL + 何木玲`，不满足上述退款池边界，仍输出 `KOC-周帅数学`（1 行、1 线索、1 有效量）。
- 修正覆盖 22 个当前 Data Center 模型：`2054, 2132, 2253, 2293, 2310, 2344, 2345, 2533, 2688, 2751, 2774, 2809, 2812, 2836, 2842, 2883, 2885, 2886, 2890, 2978, 3039, 3153`。model `2344` 的 3 处同义 CASE 必须同步；model `2978` 的 `lead_base` 必须同时投影 `put_plan_name` 和 `channel_name_1`，否则下一层 CASE 会因字段不可见导致预览失败。该内部投影不改变 model `2978` 的最终输出字段。
- model `2978` 是 KOC-only 播报：退款池记录改为 `退款订单复用` 后应自然退出 KOC 输出；上文的 1 条 KOL 仍保留在 KOC 范围。既有 `20260803期` 定向覆盖继续保留，本次规则不是对它的替换。
- 22 个模型均完成完整 SQL 预览、保存后哈希回读和新 `SUCCESS` 抽数：`2054->162316119`、`2132->162316123`、`2253->162316125`、`2293->162316126`、`2310->162316132`、`2344->162316171`、`2345->162316217`、`2533->162316281`、`2688->162316316`、`2751->162316345`、`2774->162316357`、`2809->162316378`、`2812->162316386`、`2836->162316391`、`2842->162316400`、`2883->162316415`、`2885->162316734`、`2886->162323233`、`2890->162323239`、`2978->162323250`、`3039->162323253`、`3153->162323255`。

## 3. 适用范围

用于市场顾问相关看板中的渠道归因 CASE 映射。现有历史 SQL 中同类字段包括：

- `channel_map`
- `channel_map_1`
- `qudao`

生成或改写市场顾问转化、线索转化到课、外呼过程、分配计划实际有效量等看板 SQL 时，如果需要“最新渠道 CASE”，优先引用 `resources/raw_sql/market_channel_case_when_0805.sql`，不要直接照抄旧看板中的长 CASE。

### 3.1 模板取数强制同步消费者

- 市场顾问部 8 个既有模板（`5962, 6529, 7689, 7808, 8006, 8101, 8882, 9002`）均必须与 0805 共享渠道 CASE 保持规则顺序、条件和输出值一致；目标别名仅按模板字段做等价适配。
- 当前发布 SQL 以线上模板回读文件和 `knowledge/dashboards/template_query_market_datasets.md` 登记为准。
- 每次更新 `market_channel_case_when_MMDD.sql` 时，必须同时读取上述 8 个线上模板、做规则级差异比较、原位保存并发布同一模板 id、回读 SQL/参数/最终字段；已有申请关系不得因重建模板而失效。
- 当前 2026-08-01/02 两条退款批次规则仍属于指定 Data Center 模型的定向覆盖，不是共享 `market_channel_case_when_0805.sql` 的组成部分；只有业务明确将其提升为共享规则或明确要求模板吸收时，才同步进模板，避免把模型定向条件误当作共享 CASE。

## 4. 主要依赖字段

该 CASE 片段依赖主线索/全链路宽表中的渠道、投放、流量池、规则和部门字段。常见字段包括：

| 字段 | 用途 |
|---|---|
| flow_pool_name | 流量池识别，覆盖直播、图书、私域、自然流、商务等大量规则 |
| rule_name | 规则名识别，覆盖期次、训练营、私域、IP、老师名、价格等规则 |
| put_plan_name | 投放计划识别，覆盖抖音私信、进校、KOC、商务、私域等规则 |
| sku_id_name | 商品/落地页 SKU 识别，覆盖老师 IP、价格、图书、纯课等规则 |
| source_manager_name | source 负责人识别，覆盖抖音私信、进校、KOC、创新、图书等规则 |
| channel_name_1 / channel_name_2 / channel_name_3 | 渠道树识别，覆盖信息流、B站、小红书、商务、公众号、APP 等规则 |
| ad_account_name | 广告账户识别，覆盖信息流老师 IP 和科目规则 |
| page_id_name | 页面名称识别，覆盖 B站信息流、TMK、书商、进校等规则 |
| source_put_plan_name | source 侧投放计划识别，常用于 B站信息流等规则 |
| first_department_name / second_department_name / third_department_name | 部门范围和渠道归属识别 |
| virtual_second_department_name / virtual_fourth_department_name / virtual_fifth_department_name | 虚拟架构识别，常用于私域、菁英、团队规则 |
| channel_provider_name / channel_second_provider_name | 渠道商识别，覆盖小程序、TMK、图书、商务等规则 |
| get_customer_way_name | 获客方式识别，覆盖短视频信息流、KOL 直播等规则 |
| period_name | 期次/多学科拓展排除条件 |
| lead_purchase_intention_name / lead_purchase_intention_level1_category_name / lead_purchase_intention_level2_category_name | 购买意向和品类条件 |
| flow_original_order_activity_price / flow_order_price / flow_orders_income_amount | 价格条件 |
| lead_create_time | 特定时间后规则 |

## 5. 关键渠道规则提示

该 CASE 顺序敏感，前面的规则会覆盖后面的规则。新增已验证的高优先级规则时，应放在会抢先命中的宽泛分支之前；除此之外必须整体保留原有顺序。

### 5.1 超长 CASE 顺序风险

维护超长 `channel_map` / `channel_map_1` / `qudao` CASE 时，必须先检查“更特异规则是否被更宽泛规则提前抢先命中”。同一老师、同一 IP、同一价格体系中，价格、渠道、地域、产品类型越具体的条件应放在越前面。

典型风险：

- `rule_name like '%北京直播江苏%'` 必须先于 `flow_pool_name like '%星义物理%' then '赵星义'`，且不得写死期次。
- 2026-08-01 与 2026-08-02 两条 0728 退款复用定向覆盖都必须先于 `KOC-孟亚飞数学` 和 `KOC-周帅数学` 分支；每条规则各自的期次、部门、流量池/计划、渠道、source 负责人和 SKU 边界必须完整保留，避免误伤真实 KOC 线索。
- `rule_name like '%孟亚飞ip99%'` 应先于 `flow_pool_name like '%孟帝%' ... then '孟亚飞9元'`、`sku_id_name like '%孟亚飞%' then '孟亚飞9元'` 等宽泛规则。
- `B站信息流-亚飞`、`孟亚飞IP99元`、`孟亚飞IP9元`、`孟亚飞常规99元`、`亚飞99元西安直播` 这类相邻口径不能只看最终输出名称，还要检查它们在 CASE 中的相对位置。
- 不能把“当前没有命中目标渠道”直接判断为事实表无数据；应先模拟现有 CASE 的实际命中结果，确认是否被前序分支归到了其他渠道。

推荐排查顺序：

1. 查目标期次临时表或维表是否已维护目标渠道，例如 `temp_table.dingxi01_daoke_1_6_t` 中的 `qici + qudao + grade + begin_time`。
2. 查主事实表目标期次的 `rule_name`、`flow_pool_name`、`put_plan_name`、`sku_id_name`、`channel_name_1/2`、`third_department_name` 分布。
3. 用 `case ... end as current_case_result` 模拟现有 CASE 的实际输出；如果目标记录落到别的渠道，优先调整 CASE 顺序，而不是新增重复分支。
4. 新增或调整规则时，优先使用大小写兼容写法，例如 `lower(rule_name) like '%孟亚飞ip99%'`；不要同时保留后置重复分支，避免读者误以为后置分支可命中。

近期已验证案例：

```sql
when lower(f.rule_name) like '%孟亚飞ip99%' then '孟亚飞IP99元'
```

该分支需要放在 `孟亚飞9元` 宽泛规则之前。否则 `0529期-孟亚飞ip99元-孟亚飞ip99元-初一/初二`、`0605期-孟亚飞ip99元-孟亚飞ip99元-初二/初三` 会先被归为 `孟亚飞9元`，导致到课表中已维护的 `孟亚飞IP99元` / `孟亚飞ip99元` 渠道无法匹配。

与近期排查相关的抖音私信规则：

```sql
when source_manager_name in ('韩正卿') then '抖音私信'
when channel_name_1 = '信息流'
  and (
      put_plan_name like '%抖音私信%'
      or put_plan_name like '%初三0元%'
      or put_plan_name like '%高中0元%'
  )
then '信息流-抖音私信'
```

因此排查“抖音私信”进量时不能只查 `rule_name like '%抖音私信%'`，还应检查：

- `source_manager_name = '韩正卿'`
- `channel_name_1 = '信息流'`
- `put_plan_name like '%抖音私信%'`
- `put_plan_name like '%初三0元%'`
- `put_plan_name like '%高中0元%'`

## 6. 复用模板

建议在主数据 CTE 中直接派生渠道字段：

```sql
with base as (
    select
        t.lead_id,
        t.user_id,
        t.employee_email_name,
        t.rule_name,
        -- 粘贴 resources/raw_sql/market_channel_case_when_0805.sql
        -- 并按需要将输出别名 qudao 改为 channel_map
        <latest_channel_case_when>
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t
    where t.dt = 'YYYYMMDD'
      and t.hour = 'HH'
      and t.section_assign_employee_first_level_department_name = 'H业务线'
      and t.section_assign_employee_second_level_department_name = '市场部'
)
select *
from base
limit 100;
```

如果目标看板历史字段名为 `channel_map` 或 `channel_map_1`，应只改最终别名：

```sql
else '其他未知流量' end as channel_map
```

除已验证需要前置的精确规则外，不要改动其余 CASE 分支顺序。

## 7. 定期更新流程

当渠道 CASE 来源文件更新后：

1. 从来源文件名提取日期后缀；例如来源为 `D:\Feishu\MMDD.txt`，归档路径必须为 `resources/raw_sql/market_channel_case_when_MMDD.sql`。后续若来源日期变化，最新归档必须同步改为新的 `market_channel_case_when_MMDD.sql`。
2. 将来源文件同步覆盖到对应日期后缀的归档 SQL；如果已有旧日期后缀文件作为最新入口，应重命名或替换为新后缀，并同步更新所有知识库引用。
3. 重新统计行数、`then` 分支数、去重渠道数和关键字段变化。
4. 更新本文件的原始文件、Skill 归档、来源文件最后修改时间、代码规模、关键渠道规则和待确认事项。
5. 将模板 id `7689` 作为强制同步消费者：按 3.1 的流程原位更新、发布、回读、查询验证，并用线上回读 SQL 刷新其模板 raw SQL 和模板清单。
6. 更新 `knowledge/update_log/changelog.md`，按时间正序追加到文件末尾。
7. 依次运行 `scripts/build_reverse_indexes.py`、仓库级 `../scripts/build_text2sql_catalog.py`、`scripts/check_skill_integrity.py` 和仓库级 `../scripts/validate_text2sql_stack.py`。

该文件是 CASE 片段，不是完整 SQL；通常不直接运行 `scripts/validate_sql_rules.py`，除非先包成完整可执行查询。

## 8. 待确认事项

- 渠道 CASE 来源文件是否仍按 `D:\Feishu\MMDD.txt` 命名；如果命名规则变化，应同步更新本知识文档和归档文件命名规则。
- `qudao`、`channel_map`、`channel_map_1` 是否完全等价需按具体看板确认。
- CASE 依赖的部分字段来自宽表，若用于规则表或其他表，需要先确认字段是否存在。
- 部分条件把价格字段当字符串做 `like` 或 `in ('100.0', ...)`，字段真实类型需按目标表确认。
