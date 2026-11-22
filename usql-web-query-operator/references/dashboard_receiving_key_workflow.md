# 青橙接量人力兼容字段切换

适用模型为转化数据 2460。适配器只处理转化数据看板和青橙运营侧看板中既有的「接量人力」公式。每张看板分别核对授权和版本。接量人力在原数据粒度按 `v_lead` 产生顾问或数字零的占位。兼容数据集将同一取值以 `legacy_receiving_key` 文本字段输出，切换后使用 `count(DISTINCT ${legacy_receiving_key}) - 1`。人效保留其既有公式及对接量人力的引用。

1. 数据中心在原分组下增加兼容字段，对账后保存并重抽。运行记录达到新的 `SUCCESS`，回读保存 SQL Hash 和物理字段 ID。兼容回执含 `dataset_id`、`model_id`、`saved_sql_sha256`、`field.paramId`、`latest_run.id`、`fully_verified=true`。回执是数据前置证据，授权由各写入阶段单独校验。
2. `plan-receiving-key-draft` 读取 Data Center 和两个看板版本。读取正式版本时通过 `searchPublishVersionList` 定位唯一有效的全量发布版本，用其 `versionId` 回读编辑配置和所有组件。版本列表、编辑配置和线上布局必须一致。逐模型匹配依赖、物理字段、公式名称及消费者，同时核对草稿与全量发布版只有系统生成的版本身份差异。
3. `apply-receiving-key-draft` 使用精确 Plan SHA 和生产草稿确认。校验所有域、owner、模型、公式和状态后，只更新独立草稿接量公式。保存草稿并回读完整哈希，复核原全量版本。当错误后的状态精确匹配本次草稿写入时，补偿恢复原接量公式并回读。
4. `publish-receiving-key-draft` 使用精确 Plan SHA、Apply 回执 SHA、版本说明和独立发布确认。再次回读兼容字段及抽数、草稿和线上原版本，核对发布载荷稳定后发布一次。随后要求唯一新全量版本的说明匹配，完整回读其语义哈希和接量依赖。发布响应无法确认时，保留回执和已发送状态。
5. 需要让 2460 按规则拆行时，在所有范围内的相关看板验证新公式后，使用最新线上数据集 SQL 作为新基线，单独运行数据中心替换计划和抽数验收。

三个命令均指定 `--state-path`、`--compatibility-receipt`、`--output` 和独立 `--artifacts-dir`。Plan 指定 `--dashboard-id`。Apply 消费 `--plan`、`--plan-sha256`、`--confirm-production-write`。Publish 消费同一 Plan、`--apply-receipt`、`--apply-receipt-sha256`、`--version-description`、`--confirm-publish`。Apply 回执 SHA 使用 JSON 规范化 SHA-256，与 Plan Hash 的序列化规则相同。

`--calculation-mode restore-stock` 用于恢复原接量公式。先恢复并核对上线时的兼容阶段 SQL，以及已重抽成功的同步记录。Plan 绑定当前已发布的接量公式和兼容 SQL 的精确 Hash。Apply 在保存草稿前逐个检查负责该指标的透视表真实取值，Publish 进一步检查线上透视表现值。切换公式同样需要通过这两处实际取值。
