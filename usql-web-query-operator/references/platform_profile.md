# SQL取数网页 Profile

## 已知 URL

- SQL取数页面：`https://uanalysis.baijia.com/getDataSql`
- 自助BI看板页面：`https://uanalysis.baijia.com/dashboard-market`
- 看板菜单 API：`https://uanalysis.baijia.com/uanalysis-intelligence/data/menu/manage`
- 保存的登录态缺失或过期时，会重定向到 CAS 登录页。

## 脚本边界

- `scripts/usql_web_query.py`：只负责 SQL取数执行、结果预览和结果下载。
- `scripts/read_dashboard.py`：只负责自助BI看板文件夹/菜单发现，以及看板页面读取。
- 不要把看板扫描或读取命令重新塞回 `usql_web_query.py`。

## 凭据来源

本地 env 文件 `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env` 可以包含 `BAIJIA_USERNAME` 和 `BAIJIA_PASSWORD`。脚本会读取该文件，但不会打印值。

## 已知手工流程

1. 打开 SQL取数页面。
2. 如果跳转到 CAS 登录页，输入用户名和密码并点击 `登录`。
3. 在查询页面点击顶部导航 `SQL取数`。
4. 需要时点击 `+` 创建新查询 tab。
5. 写入 SQL 前选择引擎。
   - 默认自动化路径：`Doris-Presto` -> `doris内测加速版`
   - 基线路径：`Presto`
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
- fallback：点击 `.CodeMirror` -> Ctrl+A -> 粘贴。

### 引擎选择器

引擎选择器也位于 `/sql/` iframe 内，容器是 `.antd-pro-src-components-editor-index-changeModeBox`。

2026-06-11 验证的路径：

1. 点击 `.antd-pro-src-components-editor-index-changeModeBox .ant-select-selector`
2. 点击 `Doris-Presto`
3. 点击 `doris内测加速版`

切换 Doris 后，选择器文本会从 `Presto` 变为内部引擎标签，例如 `PRESTO_817034371362430977`。不要通过等待字面值 `doris内测加速版` 留在选择器中来校验切换结果；页面不会这样展示。

### 运行

首选提交路径：

- 聚焦 CodeMirror。
- 选中当前 SQL。
- 按 `Ctrl+E`。

iframe 编辑器工具栏中的运行按钮 fallback：

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
- 只有没有结构化来源时，才使用整页关键词 fallback。

### 结果提取

成功运行会打开底部结果 tab，名称类似 `查询1388196115`。只有当本次运行后出现新的 `查询<id>` tab，且页面展示 `结果` / `表格` 以及结果表、结果字段文本或下载图标时，结果区才算当前结果。

`已无更多` 可以证明结果页较小，但检测结果区是否存在不依赖它。

### 下载

下载按钮是 iframe 结果区中的下箭头图标。已验证流程：

1. 点击结果区 `.anticon-download` 或带下载语义的 icon。
2. 如果点击后出现下拉菜单，选择 `excel` / `Excel` / `xlsx`。
3. 如果图标直接触发浏览器下载，则直接保存该文件。

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

`E:\2000_work\GAOTU\20003_青橙项目部看板维护表格\qing_team_jg.xlsx` 的已观察校验结果：

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

## 未确认问题

- 页面是否能在下载前稳定暴露总行数。
- 平台是否会在部分会话中阻断自动登录，并要求手工 SSO/MFA；当前自动 CAS 登录在 headless 下可用。
- 打开特定看板后的 dashboard 查询/结果 API 仍需继续 profile。文件夹名和 dashboard ID 可由 `read_dashboard.py scan-folder` 获取，它会向看板菜单 API POST `{"menuType":"HOME_AND_DASHBOARD"}`。

## 看板 Profile API

2026-06-01 验证：

- 直接看板 URL：`https://uanalysis.baijia.com/dashboard-market?id=<dashboard_id>&sourceType=1`
- 看板配置：POST `https://uanalysis.baijia.com/uanalysis-intelligence/config/dashBoard`，body 为 `{"dashboardId":"<dashboard_id>","isConfig":false}`
- 单元明细：POST `https://uanalysis.baijia.com/uanalysis-intelligence/value/unit/consumer/detail`，body 为 `{"id":"<unit_id>","isConfig":false}`
- 公共筛选器明细：POST `https://uanalysis.baijia.com/uanalysis-intelligence/value/public/unit/relation/detail`，body 为 `{"id":"<public_filter_relation_id>","isConfig":false}`
- 单元取值 / 刷新验证：POST `https://uanalysis.baijia.com/uanalysis-intelligence/value/unit`，带目标 `unit_id`、空筛选列表和 page 对象。表格/透视表单元返回 `title`、`data`、`totalData`、`page`、`taskIds`；图表单元可能返回 `xAxis`、`series`、`taskIds`，不一定返回表格 `data`。

该流程使用 `read_dashboard.py profile-dashboard` 或 `profile-folder`。不要把这些 dashboard API 加进 `usql_web_query.py`。

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
