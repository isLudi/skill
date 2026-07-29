# 数据地图与 Data Center 本地知识同步

## 1. 领域目标

所有业务 Skill 根目录、知识路径、看板文件夹和 Data Center 选择器由 [domain_adapters.json](domain_adapters.json) 注册，并通过 [domain_adapters.md](domain_adapters.md) 的校验器解析。

注册表只负责安全路由，不提供业务口径或写入授权。

## 2. 数据地图字段同步

默认 dry-run：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-datamap-fields --target-skill all
```

确认后本地写入：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-datamap-fields `
  --target-skill all `
  --write
```

单域或单表可使用 `--target-skill market|qingcheng`、`--table <db.table>`。`--no-refresh-datamap` 只使用 runtime 缓存；`--only-missing-cache` 只刷新缺失项。

边界：

- 数据地图只维护表名、字段、类型、分区、物理粒度和候选键。
- 跳过 `temp_table.*`。
- 不根据物理字段推断指标、范围、Join 或渠道语义。
- `--write` 产生变化时必须运行反向索引、catalog、领域 integrity 和完整 Text2SQL 栈；这些门禁不可关闭。

## 3. Data Center 源 SQL 本地同步

默认 dry-run：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-data-center-sql `
  --target-skill all
```

审阅 `DataCenterSyncPlan` 和精确 Hash 后：

```powershell
D:\anaconda3\python.exe scripts\usql_web_query.py sync-data-center-sql `
  --target-skill all `
  --write `
  --expected-plan-sha256 <exact-plan-sha256>
```

常用增量参数为 `--dataset-name`、`--market-start-name`、`--slot-binding` 和 `--retire-model-id`。

写入规则：

- canonical SQL 固定为 `resources/raw_sql/data_center_<domain>_<model_id>.sql`。
- 当前模型和语义槽位记录在目标 Skill 的 current-model registry，由其 semantic 目录独立维护。
- Apply 在独占锁中复核计划 Hash 和文件前置 Hash；跨两域时作为一个事务。
- 任一强制维护步骤失败时恢复业务文件及生成物。
- 本命令只更新本地业务 Skill，不修改远端 Data Center。

## 4. 远端 Data Center

远端替换与创建是两套独立工作流：

- 替换既有数据集：见 [data_center_replacement.md](data_center_replacement.md)。
- 新建数据集并首抽：见 [data_center_creation.md](data_center_creation.md)。

两者都要求独立只读 Plan、精确 Hash、显式 `--confirm-production-write`、保存后回读、立即执行和新的 `SUCCESS`。本地同步 Plan、替换 Plan 和创建 Plan 互不授权。
