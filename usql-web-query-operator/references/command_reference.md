# 命令索引

两个稳定入口：

- `scripts\usql_web_query.py`：SQL取数、模板、临时表、数据地图和 Data Center。
- `scripts\read_dashboard.py`：看板扫描、画像、设计、草稿 Apply、独立 Publish 和构建 Saga。

## `usql_web_query.py`

| 命令 | 作用 | 详细说明 |
|---|---|---|
| `doctor` / `login` | 依赖和登录态 | [sql_query_execution.md](sql_query_execution.md) |
| `run` | SQL 执行、错误、预览、小结果下载 | [sql_query_execution.md](sql_query_execution.md)、[query_plan_contract.md](query_plan_contract.md) |
| `fetch-template-sql` | 读取“我创建的”模板 SQL | [template_query.md](template_query.md) |
| `fetch-market-template-sql` | 读取模板市场 SQL | [template_query.md](template_query.md) |
| `template-download` | 大结果临时模板下载并强制清理 | [template_query.md](template_query.md) |
| `check-manual-table` | 手工表本地预检 | [manual_temp_table_registry.md](manual_temp_table_registry.md) |
| `upload-temp-table` | 上传到已明确目标临时表 | [manual_temp_table_registry.md](manual_temp_table_registry.md) |
| `sync-datamap-fields` | 物理字段本地同步 | [data_knowledge_sync.md](data_knowledge_sync.md) |
| `sync-data-center-sql` | canonical SQL 本地同步 | [data_knowledge_sync.md](data_knowledge_sync.md) |
| `plan/apply-data-center-sql-replacement` | 远端既有数据集替换 | [data_center_replacement.md](data_center_replacement.md) |
| `plan/apply-data-center-dataset-creation` | 远端数据集创建与首抽 | [data_center_creation.md](data_center_creation.md) |

## `read_dashboard.py`

| 命令 | 作用 | 详细说明 |
|---|---|---|
| `scan-folder` | 看板文件夹和 ID 发现 | [platform_profile.md](platform_profile.md) |
| `profile-dashboard/folder/all` | config-only 画像；默认 runtime | [platform_profile.md](platform_profile.md) |
| `check-dashboard-values` | 独立实时取值健康检查 | [platform_profile.md](platform_profile.md) |
| `profile-edit-dashboard/folder/all` | 编辑页字段、公式和绑定只读画像 | [platform_profile.md](platform_profile.md) |
| `design-dashboard` / `plan-dashboard-change` | 本地 Design 和 Diff | [dashboard_change_workflow.md](dashboard_change_workflow.md) |
| `apply/publish-dashboard-change` | 九类 allowlisted 草稿操作和独立发布 | [dashboard_change_workflow.md](dashboard_change_workflow.md) |
| `plan/apply/publish-dashboard-build` | P4C 创建 Saga | [dashboard_build_workflow.md](dashboard_build_workflow.md) |
| `inspect-write-capabilities` | 离线检查 capability registry | [dashboard_write_capabilities.md](dashboard_write_capabilities.md) |
| `capture-write-evidence` | 精确沙箱取证 | [dashboard_write_capabilities.md](dashboard_write_capabilities.md) |
| `verify-sandbox-write-adapters` | 沙箱连续写入和恢复验证 | [dashboard_write_capabilities.md](dashboard_write_capabilities.md) |
| `rebind-pivot-fields-sandbox` | 沙箱复制重建透视表 unit | [dashboard_change_workflow.md](dashboard_change_workflow.md) |
| `edit-public-filters` | Legacy 只读 dry-run | [platform_profile.md](platform_profile.md) |

参数以各入口的 `--help` 为准。任何文档示例都不能替代当前 CLI 参数校验、Hash、确认和 capability registry。
