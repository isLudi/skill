# SQL取数网页画像

## 已知 URL

- SQL取数页面：`https://uanalysis.baijia.com/getDataSql`
- 数据中心数据集页面：`https://uanalysis.baijia.com/data-center/data-set`
- 自助BI看板页面：`https://uanalysis.baijia.com/dashboard-market`
- Taitan 看板编辑页：`https://udata.baijia.com/taitan/?dashboardId=<dashboard_id>&htmlId=<html_id>`
- 看板菜单 API：`https://uanalysis.baijia.com/uanalysis-intelligence/data/menu/manage`
- 保存的登录态缺失或过期时，会重定向到 CAS 登录页。

## 脚本边界

- `scripts/usql_web_query.py`：负责 SQL取数执行、结果预览、结果下载、临时表上传、数据地图字段同步，以及数据中心数据集源 SQL 同步。
- `scripts/read_dashboard.py`：只负责自助BI看板文件夹/菜单发现，以及看板页面读取。
- 不要把看板扫描或读取命令重新塞回 `usql_web_query.py`。

## 凭据来源

统一凭证文件通过命令行 `--env-file` 或环境变量 `USQL_ENV_FILE` 指定，可以包含 `BAIJIA_USERNAME` 和 `BAIJIA_PASSWORD`。未指定时脚本使用本机兼容回退路径；脚本读取凭证但不会打印值。

## 已知手工流程

1. 打开 SQL取数页面。
2. 如果跳转到 CAS 登录页，输入用户名和密码并点击 `登录`。
3. 在查询页面点击顶部导航 `SQL取数`。
4. 需要时点击 `+` 创建新查询 tab。
5. 写入 SQL 前选择引擎。
   - 默认自动化路径：`Presto`
   - 备选路径：`Doris-Presto` -> `doris内测加速版`，仅在 Presto 结果疑似为空或需要排查引擎差异时使用
6. 将 SQL 粘贴到 CodeMirror 编辑器。
7. 点击编辑器工具栏附近的运行图标。
8. 等待查询历史状态变为 `Success` 或 `Failed`。
9. 成功运行会打开底部结果 tab，名称类似 `查询1377529335`。
10. 在结果 tab 中，通过 `结果` -> `表格` 查看数据。
11. 下载按钮是结果表上方左侧的小下箭头图标。
12. 如果结果可能超过 1000 行，不要下载。

## Selector 策略（2026-06-06 验证）

### 页面结构

`https://uanalysis.baijia.com/getDataSql` 页面把 SQL 编辑器放在一个 **iframe** 中（`<iframe src="/sql/?ts=...">`）。所有编辑器、运行按钮和结果区交互都必须通过 `page.frame_locator('iframe[src^="/sql/"]')` 定位到 iframe 内容。

### 编辑器

平台使用 **CodeMirror**，不是 Monaco。编辑器位于 `/sql/` iframe 内。

- 写入 SQL：通过 `frame_obj.evaluate()` 调用 `document.querySelector('.CodeMirror').CodeMirror.setValue(sql)`。
- 回退方案：点击 `.CodeMirror` -> Ctrl+A -> 粘贴。

### 引擎选择器

引擎选择器也位于 `/sql/` iframe 内，容器是 `.antd-pro-src-components-editor-index-changeModeBox`。

2026-06-30 默认路径：

1. 点击 `.antd-pro-src-components-editor-index-changeModeBox .ant-select-selector`
2. 点击 `Presto`

2026-06-11 验证的 Doris-Presto 备选路径：

1. 点击 `.antd-pro-src-components-editor-index-changeModeBox .ant-select-selector`
2. 点击 `Doris-Presto`
3. 点击 `doris内测加速版`

切换 Doris 后，选择器文本会从 `Presto` 变为内部引擎标签，例如 `PRESTO_817034371362430977`。不要通过等待字面值 `doris内测加速版` 留在选择器中来校验切换结果；页面不会这样展示。

### 运行

首选提交路径：

- 聚焦 CodeMirror。
- 选中当前 SQL。
- 按 `Ctrl+E`。

iframe 编辑器工具栏中的运行按钮回退方案：

- `[aria-label='play-circle']`
- `.anticon-play-circle`
- 编辑器运行区域附近的可见 toolbar button

### NPS 满意度弹窗

页面加载时可能出现 NPS（Net Promoter Score）弹窗。交互前先关闭：

- 关闭图标：`.nps-modal-close-icon` 或 `.nps-modal-close-icon > svg`
- 跳过按钮：`.nps-result-button`
- 必须在操作编辑器或 SQL tab 前关闭。

### 状态检测

点击运行前，记录查询历史表和已打开结果 tab 中已有的 query id。提交后，只有当状态/结果属于新的 query id，或查询历史行 SQL 文本与本次提交 SQL fingerprint 匹配时，才认为它是当前运行。

不要只依赖整页里的 `Success` 文本。旧的成功结果 tab 可能仍然打开，不能当作当前运行结果。

失败明细来源：

- Ant notification/message/alert 文本。
- 打开失败行的 `日志` 后读取 `log_area`。
- 只有没有结构化来源时，才使用整页关键词回退。

### 结果提取

成功运行会打开底部结果 tab，名称类似 `查询1388196115`。只有当本次运行后出现新的 `查询<id>` tab，且页面展示 `结果` / `表格` 以及结果表、结果字段文本或下载图标时，结果区才算当前结果。

`已无更多` 可以证明结果页较小，但检测结果区是否存在不依赖它。

### 下载

下载优先使用结果下载 API 的 CSV；只有 API 不可用时才使用 iframe 结果区中的下箭头图标。已验证流程：

1. 调用结果下载检查接口和 CSV 下载接口，并在写盘前校验返回字节。
2. 如果 API 不可用，点击结果区 `.anticon-download` 或带下载语义的 icon。
3. 如果点击后出现下拉菜单，选择 `excel` / `Excel` / `xlsx`；如果图标直接触发浏览器下载，则保存后校验。
4. CSV 若实际为对象存储 XML 列表/错误页，或 Excel 在查询有数据时只有表头、表头列不完整，判定为无效制品，不得返回成功。
5. `run --download` 识别到上述无效制品时，自动用同一 concrete SQL 创建临时 Template Query、下载 CSV，并执行 `offline -> delete`。summary 的 `download_fallback` 保留原因、临时模板/查询 ID、行数和清理结果。

已验证 xlsx 文件名模式类似 `task_<query_id>_<timestamp>.xlsx`。

### 临时表上传

2026-06-15 验证：

临时表 UI 也位于 `/sql/` iframe 内。稳定自动化路径：

1. 点击左侧 tab 文本 `临时表`。
2. 点击 `.anticon-cloud-upload`。
3. 点击菜单项 `建表向导`。
4. 第 1 步选择 radio `excel` 或 `csv`，再点击 `下一步`。
5. 第 2 步使用当前 `.ant-modal` 下隐藏的 `input[type=file]`；Excel 上传时 accept 会显示 `.xls, .xlsx`。当首行是字段名时，保持 `头行作为字段名行` 选中。
6. 等待上传文件名出现，再点击 `下一步`。
7. 第 3 步选择 `新建表` 或 `复用现有表`。
   - `复用现有表` 使用 Ant Design 可搜索 select：点击 `.ant-select-selector`，填写 `.ant-select-selection-search-input`，再点击可见的 `.ant-select-item-option-content` 精确表名。
   - 选中已有表后，要显式选择 `覆盖` 或 `追加`；页面可能默认回到 `追加`。
8. 点击 `下一步` 进入字段映射。所有字段默认勾选。
9. 点击 `开始导入`。
10. 等待 `导入历史`，解析顶部匹配行。`状态=成功` 加上 `临时表名` 和 `数据量` 是上传成功信号。

`E:\1900_work\GAOTU\19003_青橙项目部看板维护表格\qing_team_jg.xlsx` 的已观察校验结果：

| 导入时间 | 文件类型 | 源文件 | 临时表名 | 数据量 | 状态 |
|---|---|---|---|---:|---|
| 2026-06-15 12:48:22 | excel | qing_team_jg2026061512480017.xlsx | dingxi01_qing_team_jg | 916 | 成功 |

### 手工表 registry

2026-06-17 验证：

- 本地手工表目录记录在 `references/manual_temp_table_registry.json`。
- registry 存储平台临时表名、文件到表映射、置信度和本地校验规则。
- `upload-temp-table` 默认读取 registry，并可为高置信度条目推断 `--target-table`。
- `check-manual-table` 执行无浏览器的映射和 workbook 校验预检查。
- 标记为 `review_required_*` 的条目，必须在人工确认后显式传入 `--target-table` 才能上传。

## 数据地图字段 API

2026-06-17 验证：

- 页面 URL：`https://tiangong2.baijia.com/dataMap/dataMapNew`
- Runtime 登录态/缓存：`C:\Users\Ludim\.codex\runtime\data-map\state.json` 和 `datamap_table_catalog.json`
- 表搜索：POST `https://tiangong2.baijia.com/md-admin/api/tableV2/searchTableList`，body 为 `{"topicIds":[],"searchContent":"<db.table>","pageNo":1,"pageSize":10}`
- 表信息：POST `https://tiangong2.baijia.com/md-admin/api/tableV2/getTableInfo`，body 为 `{"tableId":<id>}`
- 普通字段：POST `https://tiangong2.baijia.com/md-admin/api/tableV2/normalColumns`，body 为 `{"tableId":<id>,"pageNo":1,"pageSize":500}`
- 分区字段：POST `https://tiangong2.baijia.com/md-admin/api/tableV2/partitionColumns`，body 为 `{"tableId":<id>,"pageNo":1,"pageSize":500}`
- DDL：POST `https://tiangong2.baijia.com/md-admin/api/tableV2/getDdl`，body 为 `{"tableId":<id>}`

该流程使用 `usql_web_query.py sync-datamap-fields`。只有加 `--write` 后才写治理过的 skill markdown/docs；cookie 和 schema cache 始终保存在 runtime 下。

## 数据中心数据集源 SQL API

2026-06-17 验证：

- 页面 URL：`https://uanalysis.baijia.com/data-center/data-set`
- 共享登录态：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
- Runtime 摘要目录：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\data-center\`
- 数据集菜单：POST `https://uanalysis.baijia.com/uanalysis-intelligence/data/menu/manage`，body 为 `{"menuType":"DATA_SET"}`
- 数据集详情：POST `https://uanalysis.baijia.com/uanalysis-intelligence/data/set/detail`，body 为 `{"id":"menu_set_<id>"}`。必须使用菜单节点 ID，不是 `fileValue` 或 `subjectId`。
- 详情响应中的 `executeSql` 是数据中心编辑页左下角 SQL 语句的完整源 SQL；`dataSourceId`、`subjectId`、`openExternal` 等字段可作为数据集元数据记录。

## 数据中心新建数据集页面与请求

2026-07-14 已在 `青橙项目部` 文件夹完成无保存采证，并完成一次生产验收：

- 文件夹菜单“新建数据集”只打开草稿页，不立即创建远端对象；路由为 `/data-center/edit-data-set?parentId=<menu_set_folder_id>`。
- 草稿保存接口为 `POST /uanalysis-data/data/set/saveAndUpdate`。新建 payload 必须满足 `id=null`，并携带 `parentId`、`name`、`menuType=DATA_SET`、`dataSourceId`、完整 `executeSql`、预览生成的 `dataParamList` 和 `schedule`。
- 当前默认数据源 `PRESTO数据源（DORIS加速）` 的已验证身份为 `menu_source_817034371567951872`；Plan 同时绑定显示名与身份，预览/保存请求必须与两者一致。
- 同步日期组件允许从当天开始，范围不得超过 90 天；小时级 `timeUnit=1`，每小时一次必须显式选择 `0:00` 到 `23:00` 共 24 项。
- 保存响应的 `data` 返回新 `menu_set_*` 身份。完成标准不是保存，而是详情 API 回读名称/目录/SQL/数据源/同步配置一致，随后 `executeOnce` 成功并出现新的 `SUCCESS` 同步记录。
- 已验证创建数据集 `Codex自动建数验收_20260714_222621`（`menu_set_3989072902490079232`）：预览 2 字段/1 行；新同步记录 `158879234` 于 `2026-07-14 22:28:10` 完成，状态 `SUCCESS`，执行耗时 3 秒。
- 打开 `https://uanalysis.baijia.com/data-center/data-set?selectId=<menu_set_id>` 可以在 UI 中选中指定数据集，但脚本同步源 SQL 时优先使用详情接口，避免触发数据预览执行。

2026-07-14 生产替换链路采证：

- 编辑页路由为 `https://uanalysis.baijia.com/data-center/edit-data-set?selectId=<menu_set_id>`，但生产执行不能直接深链进入：必须先打开详情页再点击“编辑”，让前端绑定当前数据集。SQL 编辑器为 `.CodeMirror`，运行控件为 `[aria-label="play-circle"]`。
- CodeMirror 可见早于 SQL 异步注入完成；必须持续读取编辑器，直到内容 Hash 等于详情 API 的当前 SQL Hash，超时仍不一致才按漂移阻断。不能把空编辑器当成真实 SQL，也不能跳过 Hash 门禁。
- 预览运行：POST `/uanalysis-intelligence/data/set/execute`；请求带 `dataSourceId`、完整 `executeSql`、`dataParamList` 和 `isCash`。
- 保存前检查：POST `/uanalysis-intelligence/data/menu/changeFileConfirm`，body 为 `{"id":"<menu_set_id>"}`。
- 保存：POST `/uanalysis-intelligence/data/set/saveAndUpdate`；请求绑定 `id`、名称、数据源、完整 SQL、字段元数据和原同步配置。
- 同步历史：POST `/uanalysis-intelligence/data/set/schedules/list`，body 为 `{"taskId":"<comma-separated task ids>","pageNo":1,"pageSize":10}`；返回记录字段为 `id/startTime/endTime/elapsed/status`。
- 立即执行：POST `/uanalysis-intelligence/data/set/schedules/executeOnce`，body 为 `{"id":"<comma-separated task ids>"}`。
- 生产完成必须同时满足：保存后详情 SQL Hash 与计划一致、出现不属于执行前基线的新同步记录、该新记录 `status=SUCCESS`。仅保存成功或仅收到立即执行响应均不算完成。

目标范围规则：

- 青橙项目部：目录路径以 `市场顾问部/青橙项目部/<数据集名>` 结尾的 SQL 数据集全部同步到 `qingcheng-dashboard-sql`。
- 市场顾问部：目录路径以 `市场顾问部/市场顾问部/<数据集名>` 结尾的 SQL 数据集，从 `(内部渠道)外呼过程数据` 开始同步到末尾，写入 `sql-query-writer-for-dashboard`。
- 同步命令是 `usql_web_query.py sync-data-center-sql`。默认 dry-run；只有加 `--write` 后才写 raw SQL、数据集清单和 changelog，并运行目标 skill 的索引与完整性检查。

## 未确认问题

- 页面是否能在下载前稳定暴露总行数。
- 平台是否会在部分会话中阻断自动登录，并要求手工 SSO/MFA；当前自动 CAS 登录在 headless 下可用。
- 打开特定看板后的 dashboard 查询/结果 API 仍需继续生成画像。文件夹名和 dashboard ID 可由 `read_dashboard.py scan-folder` 获取，它会向看板菜单 API POST `{"menuType":"HOME_AND_DASHBOARD"}`。

## 看板画像 API

2026-06-01 验证：

- 直接看板 URL：`https://uanalysis.baijia.com/dashboard-market?id=<dashboard_id>&sourceType=1`
- 看板配置：POST `https://uanalysis.baijia.com/uanalysis-intelligence/config/dashBoard`，body 为 `{"dashboardId":"<dashboard_id>","isConfig":false}`
- 单元明细：POST `https://uanalysis.baijia.com/uanalysis-intelligence/value/unit/consumer/detail`，body 为 `{"id":"<unit_id>","isConfig":false}`
- 公共筛选器明细：POST `https://uanalysis.baijia.com/uanalysis-intelligence/value/public/unit/relation/detail`，body 为 `{"id":"<public_filter_relation_id>","isConfig":false}`
- 单元取值 / 刷新验证：POST `https://uanalysis.baijia.com/uanalysis-intelligence/value/unit`，带目标 `unit_id`、空筛选列表和 page 对象。表格/透视表单元返回 `title`、`data`、`totalData`、`page`、`taskIds`；图表单元可能返回 `xAxis`、`series`、`taskIds`，不一定返回表格 `data`。

该流程使用 `read_dashboard.py profile-dashboard`、`profile-folder` 或 `profile-all`。默认 `--profile-mode config` 只读取配置和 unit detail，不调用 `value/unit`；这也是知识同步的生产默认。实时数据健康检查使用独立命令 `check-dashboard-values --profile <config-profile.json>`。

`check-dashboard-values` 的默认保护：

- 单次请求超时 `15000 ms`，最多 `2` 次，退避 `500 ms`。
- 单看板总预算 `90000 ms`；预算耗尽后其余 unit 标记 `not_run_dashboard_timeout`，不得继续串行等待。
- 失败写入 runtime-only cache，TTL `900` 秒；TTL 内重复检查返回 `skipped_cached_failure`，不再次调用慢接口。
- 输出独立 `DashboardValueHealth` Artifact，并通过 `source_profile_sha256` 绑定 config profile；健康失败不污染配置完整性，也不被解释为业务指标错误。

需要向后兼容的一体化画像时显式使用 `--profile-mode full`。不要把 full 模式恢复为 `profile-all` 默认。

## Taitan 编辑页指标公式 API

2026-06-24 验证：

- 编辑页 URL：`https://udata.baijia.com/taitan/?dashboardId=<dashboard_id>&htmlId=<html_id>`
- 共享登录态：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
- 生产命令：`D:\anaconda3\python.exe scripts\read_dashboard.py profile-edit-dashboard --edit-url "<edit_url>"`
- 默认读取版本：`draft`，可用 `--version-id <version>` 覆盖。
- 输出位置：runtime artifact 目录，默认文件名为 `<dashboard_id>_edit_metrics_profile.json`。
- 批处理：`profile-edit-folder` / `profile-edit-all` 先扫描菜单，再用隔离 subprocess 有限并发执行同一只读命令。默认 `max_workers=2`，硬上限 4；使用 staging 文件和 `profile_sha256` 区分 `unchanged` / `updated` / `incomplete`，完整缓存 24 小时内可 resume。

只读接口：

- 编辑页配置：POST `https://udata.baijia.com/uanalysis-intelligence/config/dashBoard`，body 为 `{"dashboardId":"<dashboard_id>","isConfig":true,"versionId":"draft"}`。
- 透视表单元配置：POST `https://udata.baijia.com/uanalysis-intelligence/value/unit/detail`，body 为 `{"id":"<unit_id>","dashboardId":"<dashboard_id>","versionId":"draft"}`。该接口会返回 `unitDimensionList`、`unitColumnDimensionList`、`unitMeasureList`、`unitAideMeasureList`、`unitFilterList`，比 view page 的 `consumer/detail` 更适合读取编辑页字段配置。
- 公共筛选器关系：POST `https://udata.baijia.com/uanalysis-intelligence/value/public/unit/relation/detail`，body 为 `{"id":"<public_filter_relation_id>","isConfig":true,"versionId":"draft"}`。
- 维度详情：POST `https://udata.baijia.com/uanalysis-intelligence/model/detail/dim`，body 为 `{"id":"<field_id>","modelType":2}`。
- 普通指标详情：POST `https://udata.baijia.com/uanalysis-intelligence/model/detail/metric`，body 为 `{"id":"<metric_id>","modelType":2}`。
- 自定义指标公式：POST `https://udata.baijia.com/uanalysis-intelligence/model/customized/column/list`，body 为 `{"id":"customized_<id>"}`。响应中的 `formula` 和 `dependencyIndicators` 是自定义指标计算公式和依赖来源。
- 数据集字段树：POST `https://udata.baijia.com/uanalysis-intelligence/model/subject/paramList`，body 为 `{"modelType":2,"dashboardId":"<dashboard_id>","subjectId":<subject_id>,"selected":[...]}`。`subjectId` 可从公共筛选器关系、透视表 `dashboardModel` 或自定义指标详情中推断；识别不到时仍保留透视表字段采集结果，但若 pivot 同时没有可解析的 `applicationModelId/modelId`，画像完整性必须为 `incomplete`。

输出结构重点：

- `pivot_units[]`：每个透视表的单元 ID、名称、模型、组件信息和字段列表。
- `pivot_units[].fields[]`：实际配置字段，包含 `group`、`show_name`、`field_id`、`business_name`、`formula`、`detail`、`dependencies`。
- 普通指标的 `formula` 来自字段配置中的聚合定义，例如 `sum(<metric_id>)`；自定义指标的 `formula` 来自 `model/customized/column/list`，例如 `sum(${is_friend_lead})/sum(${v_lead})`。
- `text_notes[]`：从富文本组件和文本单元中提取的指标说明、口径说明。
- `dataset_fields[]`：可识别 `subjectId` 时补充的数据集字段树摘要；如只需要实际使用字段，可加 `--skip-dataset-fields`。
- `binding_validation`：检查每个已配置 pivot 的 unit/component/model-or-dataset identity、selected field、formula、component-filter 与 dataset 反向引用；启用字段树时再核对已选字段和公式依赖。空白/非数据组件不计入失败。
- `profile_sha256`：只覆盖可编辑状态；Taitan 每次打开可能变化的 `html_id` 作为路由元数据保留，但不参与状态 Hash。组件、布局、公式、筛选器和数据集变化仍必须改变 Hash。

边界：

- `profile-edit-dashboard` 只用于了解指标含义、字段配置和公式，不修改看板。
- 不调用保存、发布、删除、新建、更新接口，也不点击 `保存并发布`、`保存到草稿箱` 等按钮。
- UI selector 或坐标点击只允许作为 selector 漂移排查的临时验证；生产脚本优先走只读 API。

## P3A/P3B 看板变更链路

2026-07-11 起，Text2SQL 下游看板设计和修改使用独立的 `profile-edit-dashboard → design-dashboard → plan-dashboard-change → apply-dashboard-change → publish-dashboard-change` 链路。完整 Artifact、Hash、stable-ID、单 relation 原子性和阻断规则见 `references/dashboard_change_workflow.md`。

当前生产验证过的 P3B 写入面只有公共筛选器动态默认项：`relation_id + filter_id + field_id` 三者必须同时精确匹配。组件、布局和公式可以画像与 Diff，但 operator 不调用未经验证的写接口。

`apply-dashboard-change` 只写 draft；`publish-dashboard-change` 必须在独立进程中消费成功 ApplyReceipt 并显式确认。新链路不允许同一次命令 apply + publish。

## Legacy 公共筛选器只读检查与历史 API

2026-07-04 已验证：

`edit-public-filters` 仅保留历史序号式计划的 dry-run 检查。新的 Text2SQL 看板变更使用上一节 P3 链路；legacy 写入与发布参数会在浏览器启动前拒绝。

- 计划命令：`D:\anaconda3\python.exe scripts\read_dashboard.py edit-public-filters --target-set qingcheng-required`，默认只 dry-run。
- 默认目标文件夹：`青橙播报`。
- 内置目标 `qingcheng-required` 覆盖 6 个看板：`主管_过程数据播报-青橙`、`私域-渠道团队`、`私域--伙伴推送`、`图书_SEC伙伴_青橙`、`主管_过程数据-青橙`、`公域--伙伴推送`。
- 默认修改规则：第 1 个全局筛选器设为动态筛选 `第一项`（`dynamicsFilterValue="1"`），第 2 个全局筛选器设为动态筛选 `第二项`（`dynamicsFilterValue="2"`）。可用 `--first-value`、`--second-value` 覆盖。
- 如果某个看板没有第 2 个筛选器，默认跳过该项并记录 skipped；需要严格要求两个筛选器都存在时加 `--strict-filter-count`。
- 公共筛选器更新：POST `https://udata.baijia.com/uanalysis-intelligence/config/update/public/relation/unit`，body 为公共筛选器 relation detail，附加 `dashboardId`、`versionId="draft"` 和当前 `htmlId`。
- 发布前警告检查：POST `https://udata.baijia.com/uanalysis-intelligence/version/dashboard/publishWarn`，body 为 `{"id":"<dashboard_id>"}`。
- 保存并发布：POST `https://udata.baijia.com/uanalysis-intelligence/version/dashboard/saveAndPublish`，body 使用编辑页 `config/dashBoard` 的 `dashboardHtmlJson`、`jsPackages`、`clientInfo`、`ownerList` 等元数据，`isGrayscale=0` 表示全量发布，`versionDescription` 必填。
- 验证路径：更新后回读 `value/public/unit/relation/detail`，确认第 1/第 2 个筛选器的 `dynamicsFilter=true` 且 `dynamicsFilterValue` 符合计划；发布后检查 `saveAndPublish` 返回 `status=success`。

边界：

- 该命令只能生成只读计划，不调用更新或发布接口；`--apply`、`--publish`、`--confirm-publish` 均被拒绝。
- 下列更新与发布 API 记录仅作为已验证平台能力和 P3 adapter 依据，不再授权 legacy 命令调用。
- 调试产物写入 runtime artifact 目录，不写入业务 SQL skill。

## 冒烟测试 SQL

用下面 SQL 验证网页执行。它聚合成一行输出，不需要下载：

```sql
select
    count(*) as row_cnt,
    count(distinct lead_id) as lead_cnt,
    count(distinct user_id) as user_cnt,
    sum(lead_count) as total_lead,
    sum(valid_lead_count) as total_valid
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
where dt = '20260531'
  and hour = '11'
  and section_assign_employee_first_level_department_name = 'H业务线'
  and section_assign_employee_second_level_department_name = '市场部'
  and section_assign_employee_third_level_department_name = '市场顾问部'
```

2026-05-31 手工观察输出：

| row_cnt | lead_cnt | user_cnt | total_lead | total_valid |
|---:|---:|---:|---:|---:|
| 1430177 | 1349091 | 1232028 | 1310953 | 1242942 |

## 模板取数已保存 SQL 接口

2026-06-19 已验证：

- 页面 URL：`https://uanalysis.baijia.com/templateGetData/templateQueries/myTemplate/myCreate`
- 共享登录态：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
- 运行时输出目录：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\`
- 我创建的模板列表接口：`POST https://uanalysis.baijia.com/uanalysis-template/template/createList`
- 请求体结构：`{"name":"<可选模板名>","status":2,"pager":{"pageSize":100,"pageNo":1}}`
- 返回行包含 `sqlDetail` 字段，对应页面“查看模板 -> 查看SQL”展示的同一份 SQL。
- 生产命令：`D:\anaconda3\python.exe scripts\usql_web_query.py fetch-template-sql --template-name "<模板名称>"`
- 该命令是只读的，只读取已保存模板 SQL，不会创建模板、执行 SQL 或下载结果。

## 模板市场 SQL 接口

2026-06-27 已验证：

- 页面 URL：`https://uanalysis.baijia.com/templateGetData/templateMarket`
- 共享登录态：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
- 运行时输出目录：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\template-query\`
- 模板市场搜索接口：`POST https://uanalysis.baijia.com/uanalysis-template/market/search`
- 请求体结构：`{"name":"<可选模板名>","pager":{"pageSize":100,"pageNo":1}}`
- 返回行包含 `id`、`name`、`creator`、`publishTime`、`sqlDetail` 等字段，其中 `sqlDetail` 对应页面“查看模板 -> 模板SQL -> 查看SQL”展示的 SQL。
- 生产命令：`D:\anaconda3\python.exe scripts\usql_web_query.py fetch-market-template-sql --template-name "<模板名称>"`
- 该命令是只读的，只读取模板市场已发布模板 SQL，不会创建模板、执行 SQL、下载结果或修改模板。

## 模板取数临时下载流程

2026-06-21 已验证：

- 创建模板页面 URL：`https://uanalysis.baijia.com/templateGetData/templateQueries/createTemplate`
- 创建查询后的页面 URL：`https://uanalysis.baijia.com/templateGetData/templateQueries/myQuery`
- 模板生命周期接口：
  - `POST https://uanalysis.baijia.com/uanalysis-template/template/sqlParser`
  - `POST https://uanalysis.baijia.com/uanalysis-template/template/saveAndUpdate`
  - `POST https://uanalysis.baijia.com/uanalysis-template/template/publish`
  - `POST https://uanalysis.baijia.com/uanalysis-template/template/offline`
  - `POST https://uanalysis.baijia.com/uanalysis-template/template/delete`
- 查询生命周期接口：
  - `POST https://uanalysis.baijia.com/uanalysis-template/query/detail`
  - `POST https://uanalysis.baijia.com/uanalysis-template/query/create`
  - `POST https://uanalysis.baijia.com/uanalysis-template/query/list`
  - `GET https://uanalysis.baijia.com/uanalysis-template/query/log?queryId=<id>`
  - `POST https://uanalysis.baijia.com/uanalysis-template/query/result`
  - `GET https://uanalysis.baijia.com/uanalysis-template/query/download?queryId=<id>&type=1|2`
- 下载类型映射：
  - `type=1`：`csv`
  - `type=2`：Excel 制品，实测文件名为 `*.xlsx`
- 下载制品必须与 `query/result` 的行数/列元数据交叉校验；`type=2` 返回表头空或列不完整工作簿时自动改取 `type=1`，固定 `.xlsx` 输出路径同步改为 `.csv`。
- 生产命令：`D:\anaconda3\python.exe scripts\usql_web_query.py template-download --sql-file C:\path\to\query.sql`
- 当前已验证的清理顺序为 `publish -> query -> download -> offline -> delete`。查询历史记录不在清理范围内。
