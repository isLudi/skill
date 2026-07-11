# 青橙渠道和年级映射

## 1. 来源

当前过程数据数据中心快照：`resources/raw_sql/data_center_qingcheng_2064.sql`

历史已入库过程数据 raw：`resources/raw_sql/qingcheng_process_data_raw_20260522.sql`

### 1.1 权威渠道契约

- 契约 ID：`qingcheng:channel_mapping:process_2064`
- 适用域：仅限青橙项目部过程数据模型 `2064`。
- 输入字段：`bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.rule_name`。
- 输出维度：`channel_map_1`（一级渠道）与 `channel_map_2`（二级渠道）。
- 权威实现：`resources/raw_sql/data_center_qingcheng_2064.sql` 的 `data` CTE。
- 一致性约束：同一个规则若同时定义一级、二级渠道，两套 CASE 必须同步维护；`%抖音正价退费%` 在两级都必须输出 `抖音复用`，不得出现一级命中而二级为 `null` 的状态。
- 优先级约束：`%抖音正价退费%` 是精确业务规则，必须位于可能覆盖它的宽泛分支之前。
- Text2SQL 契约：`semantic/contracts/dimension_contracts.json` 中的 `qingcheng:dimension:process_channel_level_1` 与 `qingcheng:dimension:process_channel_level_2` 使用相同规则，支持在青橙有效线索单表路径中确定性编译。

## 2. 一级渠道 channel_map_1

按 `f.rule_name` 模糊匹配：

| 匹配规则 | 输出 |
|---|---|
| `%抖音正价退费%` | `抖音复用` |
| `%私域%` | `青橙私域` |
| `%青橙IP%` | `青橙IP` |
| `%青橙公海%` | `青橙公海` |
| `%青橙公域%` | `青橙公域` |
| `%青橙图书%` | `青橙图书` |
| `%青橙本地化%` | `青橙本地化` |
| `%抖音私信%` | `抖音私信` |
| `%进校%` | `进校` |
| `%训练营%` | `青橙训练营` |

## 3. 二级渠道 channel_map_2

按 `f.rule_name` 模糊匹配：

| 匹配规则 | 输出 |
|---|---|
| `%抖音正价退费%` | `抖音复用` |
| `%赠失-星义%` | `IP星义` |
| `%赠失-朱博士%` | `IP朱博士` |
| `%赠失-春春%` | `IP春春` |
| `%赠失-郭艺%` | `IP郭艺` |
| `%赠失-亚飞%` | `IP亚飞` |
| `%私域会话%` | `私域会话` |
| `%私域表单%` | `私域表单` |
| `%私域图书%` | `私域图书` |
| `%私域裂变%` | `私域裂变` |
| `%私域品效%` | `私域品效` |
| `%私域IE%` | `私域IE` |
| `%私域本地化%` | `私域本地化` |
| `%亚飞IP%` | `亚飞IP` |
| `%SEC未加好友%` | `SEC未加好友` |
| `%SEC首期掉海%` | `SEC首期掉海` |
| `%顾问未加好友%` | `顾问未加好友` |
| `%郑州图书%` | `郑州图书` |
| `%武汉图书%` | `武汉图书` |
| `%西安图书%` | `西安图书` |
| `%图书咨询%` | `图书咨询` |
| `%公域学霸%` | `公域学霸` |
| `%南京%` | `南京` |
| `%抖音私信%` | `抖音私信` |
| `%进校9元%` | `进校9元` |
| `%训练营%` | `青橙训练营` |

## 4. 年级 grade_1

按 `f.rule_name` 优先匹配：

| 匹配规则 | 输出 |
|---|---|
| `%高一%` | `高一` |
| `%高二%` | `高二` |
| `%高三%` | `高三` |
| `%初二%` | `初二` |
| `%初三%` | `初三` |

如果以上规则都不命中，使用：

```sql
f.lead_purchase_intention_level2_category_name
```

## 5. 维护注意事项

- CASE 顺序会影响命中结果，新增规则必须检查是否被上游更宽泛的规则吞掉。
- `%抖音正价退费% -> 抖音复用` 是成对渠道契约：`channel_map_1`、`channel_map_2` 和 2064 权威 SQL 必须同时出现；该规则缺失任一级都会使最终 `channel_map_1/channel_map_2 is not null` 门禁丢数。
- 2026-06-25 数据中心 2064 快照已把青橙 IP 二级渠道细分到 `IP星义/IP朱博士/IP春春/IP郭艺/IP亚飞`，不再只保留宽泛的 `%青橙IP%` 二级归类；维护时必须先核对这些高优先级分支是否仍在最前。
- 当前 `channel_map_1` 中 `%私域%` 位于多条私域细分规则之前，但它只生成一级渠道，暂未与 `channel_map_2` 冲突。
- 当前映射只作为青橙过程数据口径，不得默认复用到其他部门。
- 如果 `temp_table.dingxi01_qing_daoke.qudao` 的取值变化，必须同步核对 `channel_map_2`。

## 6. 到课 raw 版本差异

来源：`resources/raw_sql/qingcheng_daoke_raw_20260522.sql`。

该 SQL 使用较窄的渠道映射：

### channel_map_1

| 匹配规则 | 输出 |
|---|---|
| `%私域%` | `青橙私域` |
| `%青橙IP%` | `青橙IP` |
| `%青橙公海%` | `青橙公海` |
| `%青橙图书%` | `青橙图书` |
| `%青橙公域%` | `青橙公域` |
| `%进校%` | `进校` |

### channel_map_2

| 匹配规则 | 输出 |
|---|---|
| `%私域表单%` | `私域表单` |
| `%私域图书%` | `私域图书` |
| `%私域裂变%` | `私域裂变` |
| `%私域品效%` | `私域品效` |
| `%亚飞IP%` | `亚飞IP` |
| `%SEC未加好友%` | `SEC未加好友` |
| `%SEC首期掉海%` | `SEC首期掉海` |
| `%顾问未加好友%` | `顾问未加好友` |
| `%武汉图书%` | `武汉图书` |
| `%西安图书%` | `西安图书` |
| `%公域学霸%` | `公域学霸` |
| `%进校9元%` | `进校9元` |

### grade_1

到课 raw 版本只识别高一、高二、高三、初二、初三，未命中时输出：

```sql
'未知'
```

与过程数据 raw 的差异：过程数据 raw 未命中时回退到 `lead_purchase_intention_level2_category_name`。

## 7. 转化 raw 版本差异

来源：`resources/raw_sql/data_center_qingcheng_2460.sql`。

转化 SQL 中存在两套渠道映射：

1. `dd` 中 `ld.rule_name` 只输出二级渠道 `rule_name` 和年级 `grade_0`。
2. `bb` 中为线索量生成 `channel_map_1`、`channel_map_2` 和 `grade_1`。

### dd.rule_name 二级渠道

| 匹配规则 | 输出 |
|---|---|
| `%私域表单%` | `私域表单` |
| `%私域会话%` | `私域会话` |
| `%私域图书%` | `私域图书` |
| `%私域裂变%` | `私域裂变` |
| `%私域品效%` | `私域品效` |
| `%私域IE%` | `私域IE` |
| `%私域本地化%` | `私域本地化` |
| `%亚飞IP%` | `亚飞IP` |
| `%SEC未加好友%` | `SEC未加好友` |
| `%SEC首期掉海%` | `SEC首期掉海` |
| `%顾问未加好友%` | `顾问未加好友` |
| `%郑州图书%` | `郑州图书` |
| `%武汉图书%` | `武汉图书` |
| `%西安图书%` | `西安图书` |
| `%图书咨询%` | `图书咨询` |
| `%公域学霸%` | `公域学霸` |
| `%公海%` | `公海` |
| `%抖音私信%` | `抖音私信` |
| `%训练营%` | `青橙训练营` |
| `%进校%` | `进校` |
| 未命中 | `未知` |

### bb.channel_map_1

| 匹配规则 | 输出 |
|---|---|
| `%私域%` | `青橙私域` |
| `%IP%` 或 `%亚飞IP%` | `青橙IP` |
| `%公海%` | `青橙公海` |
| `%公域%` | `青橙公域` |
| `%武汉图书%` 或 `%郑州图书%` 或 `%西安图书%` | `青橙图书` |
| `%抖音私信%` | `抖音私信` |
| `%训练营%` | `青橙训练营` |
| `%进校%` | `进校` |
| 未命中 | `未知` |

### bb.channel_map_2

与 `dd.rule_name` 基本一致，但额外包含 `%南京% -> 南京`。

### 转化最终 channel_1

最终按 `channel_map_2` 归类：

| 匹配规则 | 输出 |
|---|---|
| `%私域%`、`%公域%` | `私域` |
| `%IP%` | `IP` |
| `%图书%` | `图书` |
| `%SEC未加好友%`、`%SEC首期掉海%`、`%公海%`、`%顾问未加好友%` | `公海` |
| `%抖音私信%` | `抖音私信` |
| `%训练营%` | `青橙训练营` |
| `%进校%` | `进校` |
| 未命中 | `未知` |

## 8. 转化成本映射

来源：`resources/raw_sql/data_center_qingcheng_2460.sql`。

| 条件 | `cost_lead` |
|---|---|
| `channel_map_2 = '亚飞IP'` | `120` |
| `channel_map_2 = '武汉图书'` | `20` |
| `channel_map_2 = '抖音私信'` | `130` |
| `channel_map_2 = '进校'` | `70` |
| 其他 | `0` |

成本为硬编码，不来自成本表；更新成本口径时必须同步更新 SQL 和 `knowledge/metrics/qingcheng_conversion_metrics.md`。

## 9. 转化宽表-市场渠道版本（channel_map）

来源：`resources/raw_sql/qingcheng_conversion_wide_table_market_channel_20260611.sql`

**重要**：这是中台市场渠道口径，与第 2~8 节中的青橙过程数据/转化/到课 raw 的 `rule_name` 简单模糊匹配渠道体系完全不同。两者不得混用。

### 9.1 channel_map 映射逻辑

`channel_map` 是一个 100+ 分支的 CASE WHEN，单一输出字段。CASE WHEN 按书写顺序执行，前面命中的分支会覆盖后面可能也命中的条件。

**涉及字段**（按重要性排序）：
`third_department_name`, `flow_pool_name`, `source_manager_name`, `rule_name`, `sku_id_name`, `put_plan_name`, `channel_name_1`, `channel_name_2`, `channel_name_3`, `ad_account_name`, `channel_provider_name`, `first_department_name`, `second_department_name`, `virtual_fourth_department_name`, `virtual_fifth_department_name`, `page_id_name`, `source_put_plan_name`, `channel_second_provider_name`, `lead_purchase_intention_level1_category_name`, `lead_purchase_intention_name`, `flow_original_order_activity_price`, `flow_order_price`, `flow_orders_income_amount`, `get_customer_way_name`, `virtual_second_department_name`, `lead_create_time`, `period_name`.

### 9.2 渠道大类分组

以下按渠道大类对 channel_map 输出值进行分组（大类来源：`temp_table.shenbaoxin_channel_group.channel_group`，以下归类为推断，待人工确认）：

#### 信息流类

| channel_map 输出 | 关键匹配条件 |
|---|---|
| `信息流` | `channel_name_1='信息流'` + 多种排除条件；或 `channel_name_2='B站'` + `third_department_name like '%投放%'`；或 `投放部` + `短视频信息流` + 价格 100 |
| `信息流-周帅` | `third_department_name='投放部'` + `ad_account_name like '%周帅%'` |
| `信息流-肖晗` | `ad_account_name like '%肖晗%'` + `channel_name_1='信息流'` |
| `信息流-亚飞` | `channel_name_1='信息流'` + (`page_id_name like '%亚飞%'` or `ad_account_name like '%亚飞%'`) |
| `信息流-小红书` | `third_department_name='投放部'` + `channel_name_2='小红书'` + `channel_name_1<>'搜索营销'`；或 `source_manager_name='冯银晨'` + `channel_name_2='小红书'` |
| `信息流-抖音私信` | `channel_name_1='信息流'` + (`put_plan_name like '%抖音私信%'` or `put_plan_name like '%初三0元%'` or `put_plan_name like '%高中0元%'`) |
| `信息流-虚拟号挂车` | `source_manager_name in ('宋莹莹','辛世如')` + `channel_name_2='视频号'` |
| `信息流19` | `channel_name_1='信息流获客'` + `flow_original_order_activity_price like '%1990%'` |
| `信息流搜索` | `flow_pool_name='百度搜索引擎'` or `channel_name_1='搜索营销'` |
| `B站信息流` | `channel_name_1='信息流'` + `channel_name_2='B站'` + 未命中名师细分 |
| `B站信息流-亚飞` | `channel_name_1='信息流'` + `channel_name_2='B站'` + 亚飞相关关键词 |
| `B站信息流-郭艺` | `channel_name_1='信息流'` + `channel_name_2='B站'` + `page_id_name like '%郭艺%'` |
| `B站信息流-朱汉祺` | `channel_name_1='信息流'` + `channel_name_2='B站'` + `page_id_name like '%朱博士%'`；或 `短直电商` + `B站` + 商务 + 朱博士 + 自然流 |
| `B站信息流-肖晗` | `channel_name_1='信息流'` + `channel_name_2='B站'` + `page_id_name like '%肖晗%'` |
| `B站信息流-马凯鹏` | `channel_name_1='信息流'` + `channel_name_2='B站'` + 马凯鹏/化学关键词 |
| `B站信息流-陈瑞春` | `channel_name_1='信息流'` + `channel_name_2='B站'` + 陈瑞春/春春关键词 + 语文账户；或价格 2990/2980/1980 + 帅师 + 语文 |
| `B站信息流-周帅` | `channel_name_1='信息流'` + `channel_name_2='B站'` + 帅师/周帅 + 非语文账户；或价格 1980 + 数学账户 |
| `百度星耀` | `put_plan_name` 匹配多位星耀名师 |
| `孟亚飞百度数字人` | 孟亚飞相关流量池 + `channel_name_2='百度'` + `直播部` |
| `周帅-百度数字人` | `third_department_name='直播部'` + `sku_id_name like '%周帅%'` + `channel_name_2 in ('百度','B站')` |

#### 市场私域类

| channel_map 输出 | 关键匹配条件 |
|---|---|
| `市场私域视频号` | `flow_pool_name in ('高途学习规划','智辉老师讲规划')` |
| `市场私域入群` | `channel_name_1='市场私域'` + 郑州学习顾问部/罗江博团队；或 `period_name like '%多学科拓展%'` + `third_department_name like '%私域运营%'`；或 `rule_name like '%训练营%'` + `rule_name like '%市场私域%'` |
| `市场私域图书` | `third_department_name like '%私域%'` + `rule_name like '%私域%'` + `rule_name like '%图书%'` |
| `市场私域品效` | `third_department_name like '%私域%'` + `rule_name like '%品效%'` |
| `市场私域公域组` | `third_department_name like '%私域%'` + `rule_name like '%公域学霸%'` |
| `市场私域IE` | `third_department_name like '%私域%'` + `rule_name like '%IE%'` |
| `市场私域裂变` | `third_department_name like '%私域%'` + `rule_name like '%裂变%'` |
| `市场私域低价单` | `third_department_name='私域运营部'` + 排除训练营/复用/未加好友/内部换量；或 `channel_name_1='市场私域'` + `flow_original_order_activity_price='0.0'` + 排除公导私/公转私/激活/咨询/训练营/罗江博/郑州；或 `flow_pool_name like '%市场部-微信私域%'`等 |
| `市场私域待支付` | `put_plan_name like '%私域-信息流%'`；或 `flow_pool_name like '%待支付%'` |
| `市场私域未加好友` | `put_plan_name like '%未加好友%'`；或 `flow_pool_name like '%未加好友%'` |
| `市场私域首期掉海` | `flow_pool_name like '%内部换量%'` |
| `市场私域公导私` | `flow_pool_name like '%市场部-公转私%'` |
| `市场私域代运营` | `put_plan_name like '%迪九学%'` |
| `市场私域小红书` | `third_department_name='私域运营部'` + `channel_name_1='信息流获客'` |
| `市场私域高三复读` | `put_plan_name like '%高三复读%'` |

#### 名师/IP 类（直播部为主）

| channel_map 输出 | 关键匹配条件 |
|---|---|
| `肖晗` | 流量池/SKU/投放计划含肖晗 + `third_department_name='直播部'` |
| `郭艺` | 汤哥/海淀名师高阶 + 小艺 SKU；或 海淀高阶名师/海淀老师高阶/小艺 + 直播部/新媒体/市场一组 |
| `陈瑞春` | `third_department_name='直播部'` + 春春/瑞春 SKU/规则；或 `source_manager_name='刘福云'` + 春春/瑞春 |
| `朱博士29` | 朱博士/双博士/教育规划流量池 + 直播部 + 排除多学科拓展/张杰/马凯鹏IP；或 `put_plan_name like '%朱博士说教育%'` |
| `朱博士99` | `third_department_name='直播部'` + 朱博士99/朱汉祺99 SKU/规则 |
| `朱博士9元` | 直播部 + 朱博士/朱汉祺 + 9 元 + 排除 29 元/急/礼盒29 |
| `马凯鹏29` | 朱博士讲英语 + 马凯鹏IP SKU + 直播部 |
| `马凯鹏99` | 马总/减法化学马老师/总裁讲化学/高分讲堂 + 排除多学科拓展 + 99 SKU + 直播部 |
| `马凯鹏29` | 马总/减法化学马老师/总裁讲化学/高分讲堂 + 排除多学科拓展 + 非99 SKU + 直播部 |
| `孟亚飞99-1组` | 孟帝/孟老师/中考数学冲刺/8升9数学/孟亚飞讲数学等流量池 + 排除多学科拓展 + 排除 KOL + 直播部 + 99 规则 |
| `孟亚飞99-2组` | `third_department_name='图书营销部'` + 孟亚飞99/亚飞 SKU |
| `孟亚飞9元` | 孟帝系列流量池 + 排除多学科拓展 + 排除 KOL + 直播部（非 99 非百度分支） |
| `孟亚飞199` | `third_department_name='直播部'` + `sku_id_name like '%孟亚飞%'` + `sku_id_name like '%199%'` |
| `张杰` | 北大杰哥/张小杰流量池 + 直播部；或 教育规划 + 张杰规则 + 直播部 |
| `汤老师` | 汤哥/汤老师流量池 + 直播部/新媒体内容运营部 |
| `曹忆` | 曹忆/dudu/中考决胜天团/具象思维/在逃发面馒头 + 直播部/新媒体；或 初阶化学规划/启迪-初阶老师 + 直播部/新媒体/市场一组 |
| `曹忆9.9纯课` | 中考百日冲刺 + 直播部 |
| `何峥峥` | 峥峥流量池 + 直播部 |
| `王汐子` | 汐子流量池 + 排除亚飞 SKU + 直播部 |

#### KOC 类

| channel_map 输出 | 关键匹配条件 |
|---|---|
| `KOC-书课包` | `source_manager_name in (孙晗01,方俊结01,...)` + `sku_id_name like '%原型题%'` |
| `KOC-孟亚飞数学` | KOC 负责人 + 孟帝/dudu/市场初二/亚飞/初二高阳/菁英初三等 SKU 或流量池='中考加油'+孟帝 |
| `KOC-周帅数学` | KOC 负责人 + 帅师/周帅 SKU/规则 或流量池='中考加油'+帅师 |
| `KOC-肖晗` | KOC 负责人 + 肖晗 SKU/规则 或流量池='中考加油'+肖晗 |
| `KOC-5元朱汉祺` | KOC 负责人 + 朱汉祺/朱博士/29元 + 价格条件 |
| `KOC-5元纯课` | KOC 负责人 + 排除朱汉祺/朱博士/周帅/29元 |
| `KOC-周帅` | KOC 负责人 + 周帅 SKU；或自然流 + KOC 负责人 + 周帅 SKU |
| `KOC-赠课后退款` | `source_manager_name='方俊结01'` + `put_plan_name like '%赠课后退款%'` |
| `KOC赠课失败` | `put_plan_name like '%赠课失败%'` + `third_department_name='线上商务部'` |
| `KOC分层测试` | `put_plan_name like '%B类%'` or `put_plan_name like '%b类%'` or `channel_second_provider_name like '%KOC当期%'` |
| `自孵化KOC-5元纯课` | `third_department_name in ('品牌效能部','KOC孵化部')` + `channel_name_2 in ('抖音','视频号','快手','KOL')`；或自然流 + 赵语诗/崔文轩/孙培尧 |
| `自孵化KOC-赠课失败` | `third_department_name='KOC孵化部'` + 电商退款 + 失败 |
| `自孵化KOC-退款订单复用` | `third_department_name='KOC孵化部'` + 电商退款 + 退 |
| `品宣组KOC` | `put_plan_name like '%周司鹏%'` |

#### 进校类

| channel_map 输出 | 关键匹配条件 |
|---|---|
| `进校私域合作` | 私域运营部 + 指定 source_manager 列表；或 flow_pool_name 匹配多个进校合作方（南通欣创/人人通科技/济南梦航等）；或 家校共育/保持热爱/青松/悟之道 + 非0元；或 李宁24 + 0转低；或 私域运营部 + 价格 100/900/300 或 0.0+指定负责人；或 `flow_pool_name like '公导私'`；或 `flow_pool_name like '%0转低转正%'` |
| `进校社群` | 包青青等进校负责人 + 社群 |
| `进校TMK1元` | 包青青等 + TMK + 1元落地页 |
| `进校TMK9元` | 包青青等 + TMK + 9元落地页 |
| `进校书商` | 包青青等 + 书商 |
| `进校直播` | 包青青等 + 直播/综合+18 |
| `进校APP合作` | `put_plan_name like '%益企发1元%'` or `put_plan_name like '%腾瑞教育1元%'` |

#### 创新/商务类

| channel_map 输出 | 关键匹配条件 |
|---|---|
| `创新商务` | 耿文超等创新负责人 + 排除公众号/特定流量池/社群/小红书/外部图书/沃德丰/智慧城/育甲/周长磊 |
| `创新商务入群` | 国培教育/易喆教育/钟情/中望达/晨硕/彩石 0元入群；或 0元入群-进校 + 线上商务部 |
| `创新QQ` | qq0元 + 线上商务部 |
| `创新社群` | 耿文超等 + 社群；或 天津智慧双子 |
| `创新直推` | 耿文超等 + 直推 |
| `创新书商` | 耿文超等 + 书商 |
| `创新TMK1元` | 耿文超等 + TMK + 1元 |
| `创新TMK9元` | 耿文超等 + TMK + 9元 |
| `创新直播` | 耿文超等 + 直播/进校 |
| `创新APP` | `flow_pool_name like '%周长磊%'` |
| `商务低价` | `source_manager_name='陈晓菁04'` + 排除开拓/九学；或 包青青等进校负责人 + 大量排除条件 |
| `商务0元` | 青岛寻知/禾兴信息流量池；或 济南格乐 + 表单 |

#### 图书类

| channel_map 输出 | 关键匹配条件 |
|---|---|
| `西安图书直播间-直播` | 图书营销部或直播部 + 真题 SKU |
| `西安图书直播间-挂链` | 图书营销部（非真题）或直播部（秒懂/图书赠送） |
| `武汉图书直播间` | `source_manager_name='王春宵'` |
| `北京图书直播间` | 高中视频书/高中教辅书/朵拉老师流量池 |
| `图书唐成刚` | `channel_provider_name like '%唐成刚%'` or `flow_pool_name='高途云集图书专营店-自然流'` |
| `图书任炯旭` | `flow_pool_name like '%高途图书产品学部%'` |
| `图书KOC达人` | `source_manager_name in ('高曼曼01','杨思怡','宋向函')` |
| `图书挂车` | `source_manager_name in ('陈甜06','梁晓敏')` |
| `外部图书慧敏` | `put_plan_name like '%外部图书供量%'` or `flow_pool_name='高途旗舰店—线索—yuxinru'`；或 沃德丰/智慧城/育甲 |
| `押题卷` | `third_department_name='图书营销部'` + `rule_name like '%点睛卷%'` |
| `点睛卷` | `third_department_name like '%城市定制%'` |

#### 其他渠道

| channel_map 输出 | 关键匹配条件 |
|---|---|
| `APP` | `channel_name_2 in ('APP','M站','PC')` + 排除途途 |
| `短信` | `channel_name_1='商务'` + `channel_name_2='短信'` |
| `小程序` | `channel_provider_name='宿迁伯岳'` |
| `公众号` | `channel_name_2='公众号'` |
| `抖音私信` | `source_manager_name='韩正卿'` |
| `转介绍` | `channel_name_1='转介绍'` |
| `集团私域` | `first_department_name='市场部'` + 排除站内获客 + 排除APP；或 增长组/公众号/微信生态部 + 排除 APP |
| `人工外呼` | `source_manager_name='高文羽'` + 排除唐山TMK/郑州 |
| `人工外呼-AI` | 高文羽 + `lead_purchase_intention_name='AI定制'` |
| `唐山TMK` | `channel_provider_name like '%唐山TMK%'` |
| `郑州TMK-2组` | 高文羽 + 郑州 channel_provider |
| `小红书` | `third_department_name='线上商务部'` + `channel_name_2='小红书'` |
| `小红书投放` | 信息流获客 + 小红书 + 王慧敏13/张琳02/王樱琦01；或 `flow_pool_name like '%小红书班课%'` |
| `AI直播` | `rule_name like '%99元智学%'`；或 `put_plan_name like '%AI名师%'` |
| `正价课判单补录` | `flow_pool_name='正价课判单补录'` |
| `退款订单复用` | 直播部/新媒体/市场一组/私域运营部 + 退 + 电商退款用户池 |
| `赠课失败` | 直播部/新媒体/市场一组/私域运营部 + 失败 + 电商退款用户池 |
| `公导私报名失败` | `put_plan_name like '%公导私%'` + `put_plan_name like '%未购课%'` |
| `语数英` | `rule_name like '%语数英%'` + `third_department_name='新媒体内容运营部'` |
| `原子` | `flow_pool_name like '%原子初三%'` or `flow_pool_name like '%原子系统%'`；或 `flow_pool_name like '%市场部-原子合作%'` |
| `菁英市场流量` | `source_manager_name in ('方宇02','李月林')` |
| `市场二部KOC` | `second_department_name='市场二部'` + `get_customer_way_name='KOL直播'` |
| `市场四部` | `second_department_name='市场四部'` |
| `途途APP` | `flow_pool_name like '%途途教室%'` or `first_department_name like 'TUTU'` |
| `途途商务` | `first_department_name like '%KM%'` + 排除天津智慧双子；或 `first_department_name='TT业务线'` + `third_department_name like '%商务招生%'` |
| `途途信息流私信` | `put_plan_name='美玲测试'` |
| `途途私域` | `rule_name like '%途途私域%'` or (私域规则 + `first_department_name='TT'`) |
| `青少私域` | `flow_pool_name like '%青少-私域%'` |
| `文旅进校` | `second_department_name='战略客户部'` |
| `其他未知流量` | ELSE 兜底 |

### 9.3 已知风险

- **AND/OR 优先级**：多处使用 `A or B and C` 而未加括号，SQL 中 AND 优先级高于 OR，可能导致 `A or (B and C)` 与预期 `(A or B) and C` 不同。例如：
  - `put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部'` 实际按 `'%刘家晋讲图文%' or ('%孟帝数学%' and '直播部')` 计算。
  - 曹忆分支：`flow_pool_name like '%库洛米%' and lead_purchase_intention_level1_category_name <> '规划系统'` 和其他 `flow_pool_name like '%xxx%'` 在同一 OR 链，可能导致库洛米匹配范围异常。
- **分支顺序敏感**：多处 `third_department_name='直播部'` 分支分散在不同位置，前面更宽泛的条件可能吞掉后面更精确的匹配。例如 `sku_id_name like '%孟亚飞%'` 被放在相对靠后的位置，但前面孟亚飞相关的流量池匹配可能已经命中。
- **硬编码人名**：大量使用具体员工邮箱名（如 `孙晗01`、`方俊结01`、`包青青` 等），人员变动时需同步更新 SQL。
- **硬编码日期**：`lead_create_time >= '2026-04-15 00:00:00'` 在 KOC-孟亚飞数学分支中硬编码了日期阈值。
- **硬编码价格**：多处使用 `flow_original_order_activity_price` 的具体取值（`'0.0'`、`'100.0'`、`'1100'`、`'1990'`、`'2990'` 等）作为匹配条件，价格策略变化时需更新。
- **与青橙其他渠道体系隔离**：本映射为市场渠道口径，不得与过程数据/转化/到课 raw 中的 `rule_name` 简单渠道映射混用。

### 9.4 年级映射

本 SQL 的年级映射在 `zhuanhua` CTE 中，而非在 data 层：

```sql
case
    when rule_name like '%初二%' then '初二'
    when rule_name like '%初三%' then '初三'
    when rule_name like '%高一%' then '高一'
    when rule_name like '%高二%' then '高二'
    when rule_name like '%高三%' then '高三'
    else lead_purchase_intention_level2_category_name
end as lead_purchase_intention_level2_category_name
```

与过程数据 raw 版本一致：优先 rule_name 匹配年级，兜底 `lead_purchase_intention_level2_category_name`。
