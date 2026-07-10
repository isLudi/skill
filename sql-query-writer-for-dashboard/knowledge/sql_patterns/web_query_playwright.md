# Web 查询执行流程（Playwright 自动化）

## 1. 使用场景

当用户要求执行 SQL 并获取结果用于分析时，通过 **Playwright 浏览器自动化** 模拟登录百家 SQL 取数平台，执行查询并下载 xlsx 文件，然后用 pandas 进行分析。

## 2. 执行流程

```
用户需求 → 生成 Presto SQL → Playwright 自动登录 → 注入 SQL 并全选 → 
点击执行 → 等待日志加载完成 → 结果自动展示 → 下载 xlsx → pandas 分析
```

## 3. 凭证与状态

| 项目 | 位置 |
|---|---|
| 百家登录账号 | `--env-file` 或 `USQL_ENV_FILE` 指向文件中的 `BAIJIA_USERNAME` |
| 百家登录密码 | `--env-file` 或 `USQL_ENV_FILE` 指向文件中的 `BAIJIA_PASSWORD` |
| 浏览器登录状态 | `C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json` |
| 脚本入口 | `c:\Users\Ludim\.codex\skills\usql-web-query-operator\scripts\usql_web_query.py` |

## 4. 命令速查

```powershell
# 检查 Playwright 依赖
D:\anaconda3\python.exe c:\Users\Ludim\.codex\skills\usql-web-query-operator\scripts\usql_web_query.py doctor

# 首次登录或 state 过期时，刷新登录状态
$env:USQL_ENV_FILE='<本机 usql_api.env 绝对路径>'
D:\anaconda3\python.exe C:\Users\Ludim\.codex\skills\usql-web-query-operator\scripts\usql_web_query.py login --headed
# 具体命令参考: c:\Users\Ludim\.codex\skills\usql-web-query-operator\SKILL.md

# 执行查询（headless 不显示浏览器）
D:\anaconda3\python.exe c:\Users\Ludim\.codex\skills\usql-web-query-operator\scripts\usql_web_query.py run --sql-file <sql_file>

# 执行查询并下载结果
D:\anaconda3\python.exe c:\Users\Ludim\.codex\skills\usql-web-query-operator\scripts\usql_web_query.py run --sql-file <sql_file> --download

# 调试模式（显示浏览器窗口 + 保存截图）
D:\anaconda3\python.exe c:\Users\Ludim\.codex\skills\usql-web-query-operator\scripts\usql_web_query.py run --sql-file <sql_file> --headed --debug-artifacts
```

## 5. 执行规则

### 执行前
- SQL 必须遵守本 Skill 的所有规则（完整表名、dt/hour 分区、部门限定、limit）。
- 下载前 SQL 必须包含 `limit <= 1000`，否则脚本会在 pre-run 阶段拦截。
- 探索型查询默认不加 `--download`，先看 `result_preview` 再决定。

### 执行后
- `result_preview` 包含表头和前几行数据预览（JSON）。
- `download_path` 指向下载的 xlsx 文件路径。
- 使用 pandas 读取 xlsx 进行分析：

```python
import pandas as pd
df = pd.read_excel(download_path)
```

## 6. 查询执行的技术细节

### 页面架构
- 外层页面：`https://uanalysis.baijia.com/getDataSql`
- SQL 编辑器在 iframe 内：`iframe[src^="/sql/"]`
- 编辑器类型：**CodeMirror**（不是 Monaco）
- 运行按钮：`[aria-label='play-circle']`
- SQL 必须先全选才能执行：`cm.setValue(sql)` + `cm.execCommand('selectAll')`

### 查询生命周期
1. **click_run** → 查询提交
2. **wait_for_status** → 查询被接受，history 显示 "Success"
3. **日志加载** → 页面底部出现 log 面板，loading spinner 持续旋转
4. **日志完成** → spinner 消失，页面自动跳转到结果视图
5. **结果展示** → 底部出现结果表格
6. **下载** → 点击 download icon → 弹出 csv/excel 下拉菜单 → 选择 excel

### 已知限制
- 查询执行通过非 HTTP 协议（WebSocket 或内部通道），Playwright 只能轮询 DOM 状态。
- 日志加载时间不可控，`_wait_for_result_panel` 默认等待 2-10 分钟。
- Headless 模式可能影响结果面板的渲染触发，建议使用 `--headed`。

## 7. 注意事项

- Playwright Web 路径使用用户完整账号权限，表覆盖完整。
- 查询速度较慢（依赖浏览器交互和平台查询等待），复杂查询可能需要数分钟。
- 登录状态有时效性，过期后需重新执行 `login` 命令。
