# Tiangong2 数据开发任务只读探查

## 适用范围

使用 `scripts/tiangong2_task.py` 对 `https://tiangong2.baijia.com/develop/task` 做只读身份核验、项目枚举和“数据开发”文件夹递归探查。该入口用于盘点任务树、当前编辑器代码、版本、调度、资源绑定和项目质量清单，并在 runtime 生成脱敏源码快照与静态分类报告。

本功能不运行任务，不点击保存、提交、运行、调试、发布或回滚，不创建、重命名、移动或删除文件夹/任务，也不调用任何写接口。

## 账号与登录态隔离

`usql_api.env` 中存在两组同名键，普通 dotenv 读取会把两个账号混在一起。Tiangong2 入口必须只读取以下精确注释区段：

```text
# tiangong2 Web Query (Playwright) credentials
BAIJIA_USERNAME=...
BAIJIA_PASSWORD=...
```

- 不得使用 `# USQL Web Query (Playwright) credentials` 下的值。
- 读取由 `_shared.env.read_env_section` 完成，值直接传入登录函数，不依赖进程里已有的同名环境变量。
- 独立状态文件固定在 `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\tiangong2-task\state.json`；不得复用 USQL 的 `state.json` 或 Data Map 状态。
- 每次命令先读取 `getAuth` 并将当前 `name` 与精确区段的用户名比对。身份不匹配时丢弃当前 context、用无状态 context 重新登录并再次核验；仍不匹配则失败。
- 密码、Cookie、角色详情、请求头和登录 HTML 不进入 Skill 或探查报告。

## 命令

### 只读列出项目

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py list-projects
```

该命令核验独立身份并返回当前账号可访问的项目 ID/名称。它不会读取任务代码。

### 递归探查精确文件夹

```powershell
D:\anaconda3\python.exe scripts\tiangong2_task.py explore `
  --project-id 308 `
  --folder "关赛楠" `
  --folder "申宝鑫" `
  --include-version-code
```

- `--project-id` 必须绑定一个当前账号可访问的精确项目。
- 每个 `--folder` 必须是“数据开发”下的唯一直接子文件夹；重名、缺失或重复参数会失败。
- 遍历会递归读取全部下级目录和任务，不按名称、任务类型或数量静默截断。
- 当前代码总是读取；版本列表总是读取。`--include-version-code` 额外读取每个版本的代码，用于当前/最新发布版本 Hash 比对和完整版本快照。
- 当前支持页面公开的 DATA_SYNC、SPARK、PYTHON、SHELL、KYUUBI 类型；遇到未登记类型会失败并要求更新只读适配器，不做猜测性请求。

## 只读接口白名单

客户端没有通用 URL 调用入口，只允许以下读取面：

- Base GET：`cas/getAuth`、`menu/listProjects`
- form POST：`menu/listMenus`、`constant/taskTypeNameCodeMapping`、`dataDevelop/getTask`、`dataDevelop/getPython`、`dataDevelop/getShell`、`dataDevelop/getSpark`、`dataDevelop/getKyuubi`、`DS/getDSConfig`、`ver/listVersions`、`ver/getCode`
- JSON POST：`task/getScheduleConfig`、`resource/task/list`、`quality/list`

POST 仅表示页面读取接口采用 POST 传参，不构成远端写入。注册表会拒绝包含 save/new/create/update/delete/run/start/submit/publish 等写操作段的 endpoint；测试必须证明非白名单请求在网络调用前失败。

## Runtime 工件

默认在下列目录创建带时间戳和唯一后缀的运行目录：

```text
C:\Users\Ludim\.codex\runtime\usql-web-query-operator\tiangong2-task\explorations\
```

每次成功探查包含：

- `manifest.json`：范围、任务数、只读声明、文件 Hash；
- `inventory.json`：项目、目录、任务元数据、调度、资源、版本、质量匹配和静态分析；
- `analysis.json`：不含源码正文的任务分类与数据流索引；
- `summary.md`：面向人工审阅的分类报告；
- `sources/`：当前源码脱敏副本；
- `versions/`：仅在 `--include-version-code` 时生成的版本源码脱敏副本。

输出路径必须位于 Tiangong2 专用 runtime；指向 Skill、知识库或其他目录会在浏览器前失败。探查结果不会自动写入任何业务 Skill 知识库。

## 源码脱敏与静态分析

- 源码在落盘前识别 password/passwd/pwd/token/secret/api key/access key/private key、URL 参数、CLI 参数和飞书 webhook 等字面量；报告只记录规则与命中次数，不保存值。
- `original_sha256` 绑定远端原文，`redacted_sha256` 绑定实际落盘副本。Python/Shell 当前与发布版本按原文 Hash 比较；Kyuubi/Spark 会先去除版本接口额外附加的 `sql:`、SQL 参数和运行参数 UI 包装，再比较规范化正文，同时仍保留两侧原始 Hash。
- 静态分析只做词法/AST 读取：任务类型、Python import、SQL 操作、读写/创建/删除表、创建/删除 database 或 schema、外部主机、Shell 命令、系统集成、调度字段和版本 Hash。
- “存在 DROP/CREATE/INSERT、外部 POST 或硬编码敏感值”是代码风险信号，不表示本次执行过这些语句。
- 动态 SQL、运行时分支、外部 API 实际响应和调度运行结果不会被执行验证；报告必须保留这一解释边界。

## 完整性与失败语义

- 当前源码、精确项目或精确文件夹缺失会使整个命令失败，不生成“已完成”结论。
- 单个任务没有调度、资源或版本时可记录为未配置；接口异常会进入该任务 warnings。
- 未登记任务类型、身份错配、输出越界或写接口漂移必须失败。
- 不允许为了“补齐内容”点击运行/调试/提交/发布，也不读取或复用另一个账号的登录态。

## 维护验证

修改该入口至少运行：

```powershell
D:\anaconda3\python.exe -m pytest tests\test_tiangong2_*.py -q
D:\anaconda3\python.exe scripts\build_command_reference.py --check
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\Ludim\.codex\skills\usql-web-query-operator
```

页面新增任务类型或读取接口时，先用 runtime-only 探针确认请求方法、Content-Type、参数和返回结构，再将最小读取接口加入白名单与单测。不得从前端 bundle 中发现一个接口名后直接放宽到通用请求。
