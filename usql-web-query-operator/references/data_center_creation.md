# 数据中心新建数据集与抽数

本流程把“在某文件夹创建名称为某某的数据集”拆成独立的只读 Plan 与生产 Apply。自然语言只负责确定业务域、目标文件夹、数据集名称和经业务 SQL Skill 审阅的具体 SQL；它本身不授予远端写权限。

## 权限边界

- `plan-data-center-dataset-creation` 只读取菜单和现有数据集，校验文件夹身份与同目录名称唯一性，生成 Hash 绑定计划；不会打开保存接口或创建数据集。
- `apply-data-center-dataset-creation` 是唯一的新建写入口。必须同时提供计划文件、精确 `--expected-plan-sha256` 和 `--confirm-production-write`。
- Creation Plan 与 SQL Replacement Plan 权限互不继承；`sync-data-center-sql --write` 也只写本地知识库。
- 新建前持有 `folder_id + dataset_name` 独占锁，并重新检查文件夹身份和名称冲突。
- 保存后若回读或抽数失败，不自动删除或回滚新数据集；receipt 标记 `manual_attention_required=true`，保留新 ID 供人工处理。

## 计划命令

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py plan-data-center-dataset-creation `
  --domain qingcheng `
  --folder-path "青橙项目部" `
  --dataset-name "新数据集名称" `
  --sql-file C:\path\to\reviewed.sql
```

默认数据源为 `PRESTO数据源（DORIS加速）`，身份 `menu_source_817034371567951872`；可同时用 `--data-source-name` 和 `--data-source-id` 显式覆盖。默认同步日期为当天至 90 天后，默认选择 `0:00` 至 `23:00` 全部整点。也可用 `--schedule-start`、`--schedule-end` 和可重复的 `--schedule-hour` 覆盖。

计划会绑定：

- `domain` 与完整文件夹 `menu_set_*` 身份/路径；
- 新数据集名称和计划时同目录子数据集 ID；
- SQL 文件绝对路径、UTF-8 无 BOM 内容 Hash 与字节数；
- 数据源显示名与稳定 ID；
- 同步开关、日期范围、小时级频率与具体执行时点。

## Apply 命令

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py apply-data-center-dataset-creation `
  --plan-file C:\path\to\data_center_creation_plan_....json `
  --expected-plan-sha256 <reviewed_hash> `
  --confirm-production-write
```

执行顺序固定为：

1. 重读域内文件夹与同目录数据集，阻断文件夹漂移或重名。
2. 从目标文件夹菜单打开“新建数据集”草稿。
3. 设置名称，按显示名选择数据源，完整写入 SQL 并回读编辑器 Hash。
4. 运行预览；请求 SQL Hash 与数据源 ID 必须匹配计划，响应至少返回一个字段元数据。
5. 打开同步任务，设置不超过 90 天的日期范围、小时级频率和计划内整点。
6. 保存；保存请求必须满足 `id=null`、`parentId`、`dataSourceId`、SQL Hash 全部与计划一致。
7. 通过菜单和详情 API 找到唯一的新 `menu_set_*`，回读 SQL、数据源、同步日期、频率和 taskId。
8. 点击“立即执行”，轮询同步历史；只有出现计划执行后新增的 `SUCCESS` 记录才成功。

## Receipt 与完成标准

成功 receipt 位于 `runtime/usql-web-query-operator/data-center/creation/`，包含：

- reviewed Plan Hash；
- 新数据集 ID、名称和完整路径；
- SQL Hash、预览字段数/行数；
- schedule taskId、立即执行响应和最新成功记录；
- 各阶段耗时与 `fully_verified=true`。

保存成功不等于完成。没有新同步记录、状态不是 `SUCCESS`、详情回读不一致或身份不唯一时都必须失败。

## 2026-07-14 验收证据

- 文件夹：`通用/SQL数据集/H业务线/市场部/市场顾问部/青橙项目部`
- 数据集：`Codex自动建数验收_20260714_222621`
- 新 ID：`menu_set_3989072902490079232`
- 预览：2 个字段、1 行
- 新同步记录：`158879234`
- 状态：`SUCCESS`
- 抽数执行耗时：3 秒
- Apply 完整链路耗时：约 27.6 秒
