# 数据中心数据集源 SQL（市场顾问部）

## 1. 来源与范围

- 同步日期：2026-07-05
- 来源页面：https://uanalysis.baijia.com/data-center/data-set
- 同步范围：市场顾问部目录下从 `(内部渠道)外呼过程数据` 开始到末尾的 SQL 数据集。
- 维护方式：脚本仅保存数据中心“数据集详情”接口返回的 `executeSql` 源 SQL，不改写业务逻辑。
- SQL 存放：完整源 SQL 存放在 `resources/raw_sql`；本文件只维护数据集到 raw SQL 文件的映射。

## 2. 数据集清单

| 序号 | 数据集名称 | 数据集 ID | fileValue | subjectId | 数据源 ID | 所属路径 | 源 SQL 文件 | 行数 |
|---:|---|---|---|---|---|---|---|---:|
| 1 | `(内部渠道)外呼过程数据` | `menu_set_3730730014856388608` | `2054` | `2044` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/(内部渠道)外呼过程数据 | [data_center_market_2054_20260705.sql](../../resources/raw_sql/data_center_market_2054_20260705.sql) | 732 |
| 2 | `(内部)到课衰减情况` | `menu_set_3748378950886789121` | `2132` | `2121` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/(内部)到课衰减情况 | [data_center_market_2132_20260705.sql](../../resources/raw_sql/data_center_market_2132_20260705.sql) | 432 |
| 3 | `转化数据_市场顾问` | `menu_set_3767103007846227968` | `2253` | `2242` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/转化数据_市场顾问 | [data_center_market_2253_20260705.sql](../../resources/raw_sql/data_center_market_2253_20260705.sql) | 440 |
| 4 | `运营侧个人数据` | `menu_set_3790459879440003073` | `2293` | `2282` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/运营侧个人数据 | [data_center_market_2293_20260705.sql](../../resources/raw_sql/data_center_market_2293_20260705.sql) | 883 |
| 5 | `进量节奏` | `menu_set_3791960320014991360` | `2307` | `2296` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/进量节奏 | [data_center_market_2307_20260705.sql](../../resources/raw_sql/data_center_market_2307_20260705.sql) | 125 |
| 6 | `分二级部门转化` | `menu_set_3793241904433971200` | `2310` | `2299` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/分二级部门转化 | [data_center_market_2310_20260705.sql](../../resources/raw_sql/data_center_market_2310_20260705.sql) | 405 |
| 7 | `分析--分周期转化` | `menu_set_3803169871873413121` | `2344` | `2334` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/分析--分周期转化 | [data_center_market_2344_20260705.sql](../../resources/raw_sql/data_center_market_2344_20260705.sql) | 1227 |
| 8 | `进量测试(市场渠道)` | `menu_set_3803433852106686465` | `2345` | `2335` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/进量测试(市场渠道) | [data_center_market_2345_20260705.sql](../../resources/raw_sql/data_center_market_2345_20260705.sql) | 556 |
| 9 | `退费_科目_产品` | `menu_set_3804597496486080513` | `2349` | `2339` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/退费_科目_产品 | [data_center_market_2349_20260705.sql](../../resources/raw_sql/data_center_market_2349_20260705.sql) | 321 |
| 10 | `多科用户退费占比` | `menu_set_3804644399882543105` | `2350` | `2340` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/多科用户退费占比 | [data_center_market_2350_20260705.sql](../../resources/raw_sql/data_center_market_2350_20260705.sql) | 177 |
| 11 | `退费原因分析` | `menu_set_3804680191438585856` | `2353` | `2343` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/退费原因分析 | [data_center_market_2353_20260705.sql](../../resources/raw_sql/data_center_market_2353_20260705.sql) | 178 |
| 12 | `评优看板` | `menu_set_3822395827668975617` | `2421` | `2411` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/评优看板 | [data_center_market_2421_20260705.sql](../../resources/raw_sql/data_center_market_2421_20260705.sql) | 145 |
| 13 | `每日转化情况` | `menu_set_3823450751436996609` | `2423` | `2413` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/每日转化情况 | [data_center_market_2423_20260705.sql](../../resources/raw_sql/data_center_market_2423_20260705.sql) | 178 |
| 14 | `每日转化数据表` | `menu_set_3823600047361425408` | `2424` | `2414` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/每日转化数据表 | [data_center_market_2424_20260705.sql](../../resources/raw_sql/data_center_market_2424_20260705.sql) | 493 |
| 15 | `前期用户画像` | `menu_set_3833908289888309248` | `2461` | `2451` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/前期用户画像 | [data_center_market_2461_20260705.sql](../../resources/raw_sql/data_center_market_2461_20260705.sql) | 573 |
| 16 | `过程文本数据` | `menu_set_3845530621211140096` | `2533` | `2523` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/过程文本数据 | [data_center_market_2533_20260705.sql](../../resources/raw_sql/data_center_market_2533_20260705.sql) | 598 |
| 17 | `抖音私信- 分时间段` | `menu_set_3861038899901222912` | `2623` | `2613` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/抖音私信- 分时间段 | [data_center_market_2623_20260705.sql](../../resources/raw_sql/data_center_market_2623_20260705.sql) | 559 |
| 18 | `分触达时间段--抖音咨询` | `menu_set_3861085202969292800` | `2625` | `2615` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/分触达时间段--抖音咨询 | [data_center_market_2625_20260705.sql](../../resources/raw_sql/data_center_market_2625_20260705.sql) | 562 |
| 19 | `月度评优` | `menu_set_3862900336085241857` | `2632` | `2622` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/月度评优 | [data_center_market_2632_20260705.sql](../../resources/raw_sql/data_center_market_2632_20260705.sql) | 194 |
| 20 | `每日转化数据表测试` | `menu_set_3864063308345716737` | `2634` | `2624` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/每日转化数据表测试 | [data_center_market_2634_20260705.sql](../../resources/raw_sql/data_center_market_2634_20260705.sql) | 307 |
| 21 | `季度评优` | `menu_set_3865803192573276160` | `2643` | `2633` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/季度评优 | [data_center_market_2643_20260705.sql](../../resources/raw_sql/data_center_market_2643_20260705.sql) | 236 |
| 22 | `半年度评优` | `menu_set_3865812647888924673` | `2644` | `2634` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/半年度评优 | [data_center_market_2644_20260705.sql](../../resources/raw_sql/data_center_market_2644_20260705.sql) | 385 |
| 23 | `前期流量画像-城市` | `menu_set_3874131548178558976` | `2683` | `2673` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/前期流量画像-城市 | [data_center_market_2683_20260705.sql](../../resources/raw_sql/data_center_market_2683_20260705.sql) | 605 |
| 24 | `新人过程转化数据` | `menu_set_3874438523397902337` | `2688` | `2678` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/新人过程转化数据 | [data_center_market_2688_20260705.sql](../../resources/raw_sql/data_center_market_2688_20260705.sql) | 559 |
| 25 | `暑期激励看板` | `menu_set_3881609454571925504` | `2727` | `2717` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/暑期激励看板 | [data_center_market_2727_20260705.sql](../../resources/raw_sql/data_center_market_2727_20260705.sql) | 411 |
| 26 | `转化各学部同比` | `menu_set_3885929973588549633` | `2742` | `2732` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/转化各学部同比 | [data_center_market_2742_20260705.sql](../../resources/raw_sql/data_center_market_2742_20260705.sql) | 183 |
| 27 | `暑期激励v2` | `menu_set_3890437045159682049` | `2751` | `2741` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/暑期激励v2 | [data_center_market_2751_20260705.sql](../../resources/raw_sql/data_center_market_2751_20260705.sql) | 936 |
| 28 | `用户成单画像` | `menu_set_3893424081230045185` | `2774` | `2764` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/用户成单画像 | [data_center_market_2774_20260705.sql](../../resources/raw_sql/data_center_market_2774_20260705.sql) | 683 |
| 29 | `成单用户画像整体数据` | `menu_set_3901633051635220480` | `2809` | `2799` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/成单用户画像整体数据 | [data_center_market_2809_20260705.sql](../../resources/raw_sql/data_center_market_2809_20260705.sql) | 349 |
| 30 | `用户画像成单用户城市标签` | `menu_set_3901731394904186880` | `2812` | `2802` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/用户画像成单用户城市标签 | [data_center_market_2812_20260705.sql](../../resources/raw_sql/data_center_market_2812_20260705.sql) | 317 |
| 31 | `市场渠道用户成单分析` | `menu_set_3911759458547912705` | `2836` | `2824` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/市场渠道用户成单分析 | [data_center_market_2836_20260705.sql](../../resources/raw_sql/data_center_market_2836_20260705.sql) | 455 |
| 32 | `暑期激励v3-月份` | `menu_set_3913265094620393472` | `2842` | `2830` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/暑期激励v3-月份 | [data_center_market_2842_20260705.sql](../../resources/raw_sql/data_center_market_2842_20260705.sql) | 945 |
| 33 | `评优看板测试渠道` | `menu_set_3921966160156524545` | `2856` | `2844` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/评优看板测试渠道 | [data_center_market_2856_20260705.sql](../../resources/raw_sql/data_center_market_2856_20260705.sql) | 1 |
| 34 | `市场渠道用户成单分析2` | `menu_set_3932546397269991424` | `2883` | `2871` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/市场渠道用户成单分析2 | [data_center_market_2883_20260705.sql](../../resources/raw_sql/data_center_market_2883_20260705.sql) | 448 |
| 35 | `市场渠道用户成单分析3` | `menu_set_3933555512801468416` | `2885` | `2873` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/市场渠道用户成单分析3 | [data_center_market_2885_20260705.sql](../../resources/raw_sql/data_center_market_2885_20260705.sql) | 449 |
| 36 | `退费整体数据` | `menu_set_3933610975748915200` | `2886` | `2874` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/退费整体数据 | [data_center_market_2886_20260705.sql](../../resources/raw_sql/data_center_market_2886_20260705.sql) | 340 |
| 37 | `多科用户退费` | `menu_set_3935191825064992768` | `2890` | `2878` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/多科用户退费 | [data_center_market_2890_20260705.sql](../../resources/raw_sql/data_center_market_2890_20260705.sql) | 371 |
| 38 | `koc数据播报` | `menu_set_3954191650309713920` | `2978` | `2966` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/koc数据播报 | [data_center_market_2978_20260705.sql](../../resources/raw_sql/data_center_market_2978_20260705.sql) | 377 |
| 39 | `新老人转化对比` | `menu_set_3975633867349405696` | `3039` | `3027` | `menu_source_817034371567951872` | 通用/SQL数据集/H业务线/市场部/市场顾问部/市场顾问部/新老人转化对比 | [data_center_market_3039_20260705.sql](../../resources/raw_sql/data_center_market_3039_20260705.sql) | 1012 |

## 3. 维护说明

- 若数据中心数据集顺序、名称或 SQL 发生变化，重新运行 `sync-data-center-sql --write` 刷新本文件和对应 raw SQL。
- 若需要解释字段、指标或看板口径，应在读取源 SQL 后再维护 `knowledge/tables`、`knowledge/metrics` 或专题文档；不要只凭数据集名称补口径。
- 青橙与市场顾问业务知识库相互隔离：青橙数据集只写入 `qingcheng-dashboard-sql`，市场顾问数据集只写入 `sql-query-writer-for-dashboard`。
