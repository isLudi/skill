# 数据中心数据集源 SQL（市场顾问部）

## 1. 来源与范围

- 同步日期：2026-06-24
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：市场顾问部目录下从 `(内部渠道)外呼过程数据` 开始到末尾的 SQL 数据集。
- 维护方式：脚本仅保存数据中心“数据集详情”接口返回的 `executeSql` 源 SQL，不改写业务逻辑。
- SQL 存放：完整源 SQL 存放在 `resources/raw_sql`；本文件只维护数据集到 raw SQL 文件的映射。
- 去重规则：若数据中心最新 SQL 与既有 canonical raw SQL 完全一致，本清单直接指向 canonical 文件，不再额外保留同内容的 `data_center_market_*` 副本。

## 2. 数据集清单

| 序号 | 数据集名称 | 数据集 ID | fileValue | subjectId | 数据源 ID | 所属路径 | 源 SQL 文件 | 行数 |
|---:|---|---|---|---|---|---|---|---:|
| 1 | `(内部渠道)外呼过程数据` | `menu_set_3730730014856388608` | `2054` | `2044` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/(内部渠道)外呼过程数据 | [data_center_market_2054_20260624.sql](../../resources/raw_sql/data_center_market_2054_20260624.sql) | 732 |
| 2 | `(内部)到课衰减情况` | `menu_set_3748378950886789121` | `2132` | `2121` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/(内部)到课衰减情况 | [data_center_market_2132_20260624.sql](../../resources/raw_sql/data_center_market_2132_20260624.sql) | 508 |
| 3 | `转化数据_市场顾问` | `menu_set_3767103007846227968` | `2253` | `2242` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/转化数据_市场顾问 | [data_center_market_2253_20260624.sql](../../resources/raw_sql/data_center_market_2253_20260624.sql) | 413 |
| 4 | `运营侧个人数据` | `menu_set_3790459879440003073` | `2293` | `2282` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/运营侧个人数据 | [data_center_market_2293_20260624.sql](../../resources/raw_sql/data_center_market_2293_20260624.sql) | 835 |
| 5 | `进量节奏` | `menu_set_3791960320014991360` | `2307` | `2296` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/进量节奏 | [lead_assign_plan_actual_valid_count.sql](../../resources/raw_sql/lead_assign_plan_actual_valid_count.sql) | 96 |
| 6 | `分二级部门转化` | `menu_set_3793241904433971200` | `2310` | `2299` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/分二级部门转化 | [data_center_market_2310_20260624.sql](../../resources/raw_sql/data_center_market_2310_20260624.sql) | 392 |
| 7 | `分析--分周期转化` | `menu_set_3803169871873413121` | `2344` | `2334` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/分析--分周期转化 | [data_center_market_2344_20260624.sql](../../resources/raw_sql/data_center_market_2344_20260624.sql) | 435 |
| 8 | `进量测试(市场渠道)` | `menu_set_3803433852106686465` | `2345` | `2335` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/进量测试(市场渠道) | [data_center_market_2345_20260624.sql](../../resources/raw_sql/data_center_market_2345_20260624.sql) | 556 |
| 9 | `退费_科目_产品` | `menu_set_3804597496486080513` | `2349` | `2339` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/退费_科目_产品 | [refund_subject_product.sql](../../resources/raw_sql/refund_subject_product.sql) | 194 |
| 10 | `多科用户退费占比` | `menu_set_3804644399882543105` | `2350` | `2340` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/多科用户退费占比 | [refund_multi_subject_user_ratio.sql](../../resources/raw_sql/refund_multi_subject_user_ratio.sql) | 177 |
| 11 | `退费原因分析` | `menu_set_3804680191438585856` | `2353` | `2343` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/退费原因分析 | [refund_reason_analysis.sql](../../resources/raw_sql/refund_reason_analysis.sql) | 178 |
| 12 | `评优看板` | `menu_set_3822395827668975617` | `2421` | `2411` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/评优看板 | [consultant_sales_ranking_evaluation_period_clean.sql](../../resources/raw_sql/consultant_sales_ranking_evaluation_period_clean.sql) | 145 |
| 13 | `每日转化情况` | `menu_set_3823450751436996609` | `2423` | `2413` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/每日转化情况 | [data_center_market_2423_20260624.sql](../../resources/raw_sql/data_center_market_2423_20260624.sql) | 178 |
| 14 | `每日转化数据表` | `menu_set_3823600047361425408` | `2424` | `2414` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/每日转化数据表 | [data_center_market_2424_20260624.sql](../../resources/raw_sql/data_center_market_2424_20260624.sql) | 493 |
| 15 | `前期用户画像` | `menu_set_3833908289888309248` | `2461` | `2451` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/前期用户画像 | [data_center_market_2461_20260624.sql](../../resources/raw_sql/data_center_market_2461_20260624.sql) | 573 |
| 16 | `过程文本数据` | `menu_set_3845530621211140096` | `2533` | `2523` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/过程文本数据 | [data_center_market_2533_20260624.sql](../../resources/raw_sql/data_center_market_2533_20260624.sql) | 598 |
| 17 | `抖音私信- 分时间段` | `menu_set_3861038899901222912` | `2623` | `2613` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/抖音私信- 分时间段 | [data_center_market_2623_20260624.sql](../../resources/raw_sql/data_center_market_2623_20260624.sql) | 559 |
| 18 | `分触达时间段--抖音咨询` | `menu_set_3861085202969292800` | `2625` | `2615` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/分触达时间段--抖音咨询 | [data_center_market_2625_20260624.sql](../../resources/raw_sql/data_center_market_2625_20260624.sql) | 562 |
| 19 | `月度评优` | `menu_set_3862900336085241857` | `2632` | `2622` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/月度评优 | [consultant_sales_ranking_evaluation_month_clean.sql](../../resources/raw_sql/consultant_sales_ranking_evaluation_month_clean.sql) | 194 |
| 20 | `每日转化数据表测试` | `menu_set_3864063308345716737` | `2634` | `2624` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/每日转化数据表测试 | [data_center_market_2634_20260624.sql](../../resources/raw_sql/data_center_market_2634_20260624.sql) | 307 |
| 21 | `季度评优` | `menu_set_3865803192573276160` | `2643` | `2633` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/季度评优 | [consultant_sales_ranking_evaluation_quarter_clean.sql](../../resources/raw_sql/consultant_sales_ranking_evaluation_quarter_clean.sql) | 236 |
| 22 | `半年度评优` | `menu_set_3865812647888924673` | `2644` | `2634` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/半年度评优 | [consultant_sales_ranking_evaluation_year_clean.sql](../../resources/raw_sql/consultant_sales_ranking_evaluation_year_clean.sql) | 387 |
| 23 | `前期流量画像-城市` | `menu_set_3874131548178558976` | `2683` | `2673` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/前期流量画像-城市 | [traffic_profile.sql](../../resources/raw_sql/traffic_profile.sql) | 605 |
| 24 | `新人过程转化数据` | `menu_set_3874438523397902337` | `2688` | `2678` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/新人过程转化数据 | [data_center_market_2688_20260624.sql](../../resources/raw_sql/data_center_market_2688_20260624.sql) | 559 |
| 25 | `暑期激励看板` | `menu_set_3881609454571925504` | `2727` | `2717` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/暑期激励看板 | [consultant_sales_department_tenure.sql](../../resources/raw_sql/consultant_sales_department_tenure.sql) | 411 |
| 26 | `转化各学部同比` | `menu_set_3885929973588549633` | `2742` | `2732` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/转化各学部同比 | [consultant_sales_department_tenure_period_20260424.sql](../../resources/raw_sql/consultant_sales_department_tenure_period_20260424.sql) | 183 |
| 27 | `暑期激励v2` | `menu_set_3890437045159682049` | `2751` | `2741` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/暑期激励v2 | [data_center_market_2751_20260624.sql](../../resources/raw_sql/data_center_market_2751_20260624.sql) | 914 |
| 28 | `用户成单画像` | `menu_set_3893424081230045185` | `2774` | `2764` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/用户成单画像 | [data_center_market_2774_20260624.sql](../../resources/raw_sql/data_center_market_2774_20260624.sql) | 683 |
| 29 | `成单用户画像整体数据` | `menu_set_3901633051635220480` | `2809` | `2799` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/成单用户画像整体数据 | [market_channel_conversion_profile_overall_dataset_fixed.sql](../../resources/raw_sql/market_channel_conversion_profile_overall_dataset_fixed.sql) | 349 |
| 30 | `用户画像成单用户城市标签` | `menu_set_3901731394904186880` | `2812` | `2802` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/用户画像成单用户城市标签 | [data_center_market_2812_20260624.sql](../../resources/raw_sql/data_center_market_2812_20260624.sql) | 317 |
| 31 | `市场渠道用户成单分析` | `menu_set_3911759458547912705` | `2836` | `2824` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/市场渠道用户成单分析 | [data_center_market_2836_20260624.sql](../../resources/raw_sql/data_center_market_2836_20260624.sql) | 455 |
| 32 | `暑期激励v3-月份` | `menu_set_3913265094620393472` | `2842` | `2830` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/暑期激励v3-月份 | [data_center_market_2842_20260624.sql](../../resources/raw_sql/data_center_market_2842_20260624.sql) | 945 |
| 33 | `评优看板测试渠道` | `menu_set_3921966160156524545` | `2856` | `2844` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/评优看板测试渠道 | [data_center_market_2856_20260624.sql](../../resources/raw_sql/data_center_market_2856_20260624.sql) | 1 |
| 34 | `市场渠道用户成单分析2` | `menu_set_3932546397269991424` | `2883` | `2871` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/市场渠道用户成单分析2 | [market_channel_conversion_profile_deep_stage_dataset.sql](../../resources/raw_sql/market_channel_conversion_profile_deep_stage_dataset.sql) | 448 |
| 35 | `市场渠道用户成单分析3` | `menu_set_3933555512801468416` | `2885` | `2873` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/市场渠道用户成单分析3 | [data_center_market_2885_20260624.sql](../../resources/raw_sql/data_center_market_2885_20260624.sql) | 449 |
| 36 | `退费整体数据` | `menu_set_3933610975748915200` | `2886` | `2874` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/退费整体数据 | [data_center_market_2886_20260624.sql](../../resources/raw_sql/data_center_market_2886_20260624.sql) | 307 |
| 37 | `多科用户退费` | `menu_set_3935191825064992768` | `2890` | `2878` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/多科用户退费 | [refund_rate_multidim.sql](../../resources/raw_sql/refund_rate_multidim.sql) | 336 |
| 38 | `koc数据播报` | `menu_set_3954191650309713920` | `2978` | `2966` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/koc数据播报 | [data_center_market_2978_20260624.sql](../../resources/raw_sql/data_center_market_2978_20260624.sql) | 377 |

## 3. 维护说明

- 若数据中心数据集顺序、名称或 SQL 发生变化，重新运行 `sync-data-center-sql --write` 刷新本文件和对应 raw SQL。
- 刷新后需要再次做 raw SQL 去重：同一 fileValue 的旧日期快照直接删除；与 canonical SQL 完全一致的数据集行改指向 canonical 文件。
- 若需要解释字段、指标或看板口径，应在读取源 SQL 后再维护 `knowledge/tables`、`knowledge/metrics` 或专题文档；不要只凭数据集名称补口径。
- 青橙与市场顾问业务知识库相互隔离：青橙数据集只写入 `qingcheng-dashboard-sql`，市场顾问数据集只写入 `sql-query-writer-for-dashboard`。
