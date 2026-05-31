# USQL RestAPI Python 调用规则

## 1. 使用场景

当用户需要排查数据代码、验证 SQL、抽样查数、或希望摆脱“线上平台查询数据 -> 下载数据 -> 提供本地数据集路径”的流程时，优先使用 USQL RestAPI 在 Python 中直接提交 Presto SQL 并读取返回数据。

该接口只用于查询取数，不用于 DDL、DML、删除、写入或高风险全量扫描。生成 SQL 前仍必须遵守本 Skill 的表名、分区、小时、部门范围限定和 `limit` 规则。

## 2. 接口配置

| 项 | 值 |
| --- | --- |
| 方法 | `POST` |
| 线上 host | `bdg-da-gateway.baijia.com` |
| 测试 host | `test-bdg-da-gateway.baijia.com` |
| 已废弃测试地址 | `10.224.194.145:15888` |
| 路径 | `/usql/api/execute` |
| 线上 URL | `http://bdg-da-gateway.baijia.com/usql/api/execute` |
| 测试 URL | `http://test-bdg-da-gateway.baijia.com/usql/api/execute` |
| 请求类型 | JSON POST |

## 3. 本地 env 配置

默认从以下本地 env 文件读取 USQL 接口参数：

```text
E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env
```

该文件是 USQL Python 调用的本地配置入口。后续使用 Python 直接查数、验证 SQL 或排查接口调用时，先读取这个 env 文件；如果文件不存在或缺少字段，再要求用户补充配置，不要把真实 token 写入 Skill 文档。

当前 env 文件应维护以下变量：

```dotenv
USQL_API_METHOD=POST
USQL_API_ENV=online
USQL_API_ONLINE_HOST=bdg-da-gateway.baijia.com
USQL_API_TEST_HOST=test-bdg-da-gateway.baijia.com
USQL_API_PATH=/usql/api/execute
USQL_API_ONLINE_URL=http://bdg-da-gateway.baijia.com/usql/api/execute
USQL_API_TEST_URL=http://test-bdg-da-gateway.baijia.com/usql/api/execute
USQL_API_URL=http://bdg-da-gateway.baijia.com/usql/api/execute
USQL_CONTENT_TYPE="application/json; charset=utf-8"
USQL_APP_ID=<USQL应用ID>
USQL_TOKEN=<USQL授权token>
USQL_TIMEOUT_SECONDS=300
```

维护规则：

- `USQL_TOKEN` 只放在本地 env 文件或进程环境变量中，不写入 Skill、回答、日志或代码仓库。
- `USQL_API_URL` 是实际请求地址；默认使用线上 URL。
- `USQL_API_ENV` 用于说明当前环境，常用值为 `online` 或 `test`。
- 切换测试环境时，将 `USQL_API_URL` 改为 `USQL_API_TEST_URL` 对应值，或在代码中显式传入测试 URL。
- 如果用户指定其他 env 文件，优先使用用户指定路径；否则使用上述默认路径。

## 4. Header

必须传递名为 `token` 的 header。不要把真实 token 写进 Skill、日志、回答或代码仓库；运行时从环境变量、本地 `.env`、用户提供的本地文件或当前脚本变量中读取。

```http
token: <USQL授权token>
Content-Type: application/json; charset=utf-8
```

注意：这里的 `token` 不是 `Authorization: Bearer ...`，而是普通 header 键 `token`。

## 5. Body / Param

请求体必须至少包含 `sql` 和 `appId`。

```json
{
  "sql": "select * from 完整库名.表名 where dt = 'YYYYMMDD' limit 20",
  "appId": "<USQL应用ID>"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `sql` | string | 是 | Presto SQL。中文、单引号、双引号需要按 Python 字符串规则正确转义；多行 SQL 推荐使用三引号。 |
| `appId` | string | 是 | USQL 应用 ID。示例脚本 `D:\Feishu\虚拟.txt` 已验证可用的 `appId` 为 `7611237847427072`。 |

## 6. 成功响应

HTTP 状态码为 `200` 只代表请求到达服务端；业务成功必须判断响应 JSON 中的 `code == 0`。

成功响应结构：

```json
{
  "code": 0,
  "data": [
    {
      "field_name": "field_value"
    }
  ],
  "msg": "操作成功",
  "pager": null
}
```

成功状态判定：

- `HTTP status == 200`
- `response["code"] == 0`
- `response["msg"] == "操作成功"`
- `response["data"]` 通常是 list；空结果也可能是成功查询，需结合 SQL 条件判断。

已验证案例：

- 2026-05-24 使用 `D:\Feishu\虚拟.txt` 中的线上 URL、`token`、`appId=7611237847427072` 执行完整市场顾问虚拟架构 SQL，返回 `code=0`、`msg=操作成功`、`data` 共 682 行。
- 使用最小 SQL `select 1 as smoke_test`，返回 `{"code":0,"data":[{"smoke_test":"1"}],"msg":"操作成功"}`。

## 7. 异常规则

| 异常文本 | 排查方向 |
| --- | --- |
| `token 为空` | 检查 header 是否传递 `token`，不要放进 body。 |
| `token 错误` | 检查 token 是否过期、复制错误、使用了错误环境的 token。 |
| `appId 不存在或SQL错误` | 检查 body 是否传递 `appId`，以及 SQL 是否有语法、表权限或字段问题。 |
| `Error -1 (00000) :` | SQL 执行错误。按 Presto SQL 规则排查字段、表名、分区、函数、权限和数据类型。 |

排查顺序：

1. 先用 `select 1 as smoke_test` 验证 URL、token、appId 是否可用。
2. 再执行目标 SQL 的小范围版本，例如增加单日、单小时、部门限定和 `limit`。
3. 如果 smoke test 成功但目标 SQL 失败，优先按 SQL 执行错误处理，不要先怀疑 token。
4. 如果接口返回 HTTP 错误或无法连接，确认 host、网络、代理、测试/线上环境是否正确。

## 8. USQL 权限边界探查规则

公司数据库权限管理严格。USQL RestAPI 可用只代表接口可调用，不代表当前账号具备所有表、字段、部门、业务线或行级范围权限。后续通过 API 探查数据时，必须把“接口连通”“表可读”“字段可读”“部门/范围可见”拆开判断和记录。

适用场景：

- 判断某张表是否能通过 USQL RestAPI 查询。
- 判断同一张表中哪些字段或派生查询会被权限拦截。
- 判断有表权限时，部门、业务线、期次、项目等行级范围限制在哪里。
- 为后续申请更多表、字段或部门范围权限准备证据。
- 将已确认的权限边界沉淀到本 Skill 知识库，减少后续无效 SQL 尝试。

探查顺序：

1. 先执行 `select 1 as smoke_test`，确认 URL、token、appId 和网络可用。
2. 对候选表执行最小安全读：`select 1 from <完整库名.表名> where <安全分区/日期条件> limit 1`。
3. 如果最小读成功，再做小范围 `count(*)`、样例行和关键字段 distinct/top values 检查。
4. 如果表可读但业务结果为空，继续用更小粒度检查区分“确实无数据”和“部门/行级权限不可见”。
5. 对部门或范围字段逐个验证，例如 `department_name`、`*_department_name`、`period_mapping_*`、`qici`、`dt/hour`、业务线字段等。不要一次堆叠大量条件导致错误不可定位。
6. 如果某些字段加入后报错，记录字段级权限或平台解析风险；如果拆成独立列可通过，记录误拦截写法。
7. 不要盲扫全库或暴力枚举部门。只探查用户指定、知识库已有或用户明确批准的候选表和范围。

结果分类：

| 分类 | 含义 | 处理方式 |
| --- | --- | --- |
| API 不通 | smoke test 失败 | 优先检查 env、token、appId、URL、网络 |
| 表无权限 | 最小 `select 1 from table ... limit 1` 失败且错误指向权限 | 记录表名和错误特征，建议申请表权限 |
| 字段无权限 | 表可读，但加入某字段后失败 | 记录字段名，建议申请字段权限或换字段 |
| 行级/部门范围受限 | 表可读，但指定部门/业务线/期次不可见或返回空 | 记录可见范围和不可见范围，建议申请对应范围权限 |
| SQL 语义错误 | 字段不存在、函数不兼容、类型错误 | 按 SQL 修复处理，不归因于权限 |
| 权限解析误拦截 | 特定字符串拼接或调试写法触发平台误判 | 改写 SQL，并沉淀误拦截规则 |
| 空结果但可读 | 查询成功返回空 `data` | 结合分区、范围、事实表产出判断是否真实无数据 |

权限边界记录模板：

```markdown
## USQL 权限边界：<表名或主题>

- 测试日期：YYYY-MM-DD
- API 环境：online/test
- 表名：<完整库名.表名>
- 测试范围：dt/hour/日期/部门/业务线/期次
- 最小读结果：成功 / 失败 / 空结果
- 可见字段：<字段列表或摘要>
- 受限字段：<字段列表或无>
- 可见范围：<部门/业务线/期次/项目>
- 不可见或待申请范围：<范围>
- 错误特征：<脱敏后的错误摘要，不含 token>
- 权限申请建议：<表权限/字段权限/部门范围/业务线范围>
- 后续 SQL 注意事项：<必须过滤条件、误拦截写法、limit/分区要求>
```

沉淀规则：

- 表级发现写入对应 `knowledge/tables/<table>.md` 的备注或权限边界段落。
- 通用 API 行为、错误分类和探查流程写入本文档。
- 重要更新追加到 `knowledge/update_log/changelog.md`。
- 不得写入真实 token、账号、cookie、env 原文或敏感响应全文。

## 9. Python 标准库调用模板

该模板不依赖 `requests`，适合在本地 Python 环境直接运行。

```python
import json
import os
import urllib.request
from pathlib import Path


USQL_ONLINE_URL = "http://bdg-da-gateway.baijia.com/usql/api/execute"
USQL_TEST_URL = "http://test-bdg-da-gateway.baijia.com/usql/api/execute"
DEFAULT_USQL_ENV_PATH = Path(r"E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env")


def load_env_file(env_path: str | Path = DEFAULT_USQL_ENV_PATH) -> dict[str, str]:
    env_path = Path(env_path)
    config: dict[str, str] = {}
    if not env_path.exists():
        return config

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        config[key] = value
        os.environ.setdefault(key, value)
    return config


def query_usql(
    sql: str,
    app_id: str | None = None,
    token: str | None = None,
    url: str | None = None,
    env_path: str | Path = DEFAULT_USQL_ENV_PATH,
    timeout: int | None = None,
) -> dict:
    load_env_file(env_path)
    token = token or os.environ["USQL_TOKEN"]
    app_id = app_id or os.environ["USQL_APP_ID"]
    url = url or os.environ.get("USQL_API_URL", USQL_ONLINE_URL)
    timeout = timeout or int(os.environ.get("USQL_TIMEOUT_SECONDS", "300"))
    payload = {
        "sql": sql,
        "appId": app_id,
    }
    headers = {
        "token": token,
        "Content-Type": os.environ.get("USQL_CONTENT_TYPE", "application/json; charset=utf-8"),
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))

    if result.get("code") != 0:
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    sql = "select 1 as smoke_test"
    result = query_usql(sql)
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

如果需要转成 DataFrame，可在调用成功后执行：

```python
import pandas as pd

rows = result.get("data") or []
df = pd.DataFrame(rows)
```

## 10. 生成或修复代码时的要求

- 默认使用线上 URL，除非用户明确要求测试环境。
- 不要在新代码中硬编码真实 token；默认读取 `E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env`，也可以读取用户指定的本地配置文件。
- SQL 必须按 UTF-8 发送：`json.dumps(payload, ensure_ascii=False).encode("utf-8")`。
- 对响应必须同时检查 HTTP 状态和业务 `code`。
- 输出结果时优先输出 `code`、`msg`、`row_count`、`columns`、少量样例行。但是，当用户要求探查数据错误时，需要打印全量结果集进行比对，根据输出数据集结果找到错误原因。
- 如果用户只是要验证接口连通性，先执行 `select 1 as smoke_test`。
- 如果用户要求“直接查数”，先生成遵守 Skill 规则的 Presto SQL，再通过本接口执行。
- 如果用户要求“权限边界探查”，按第 8 节拆分接口、表、字段、部门/行级范围，不要把所有失败都简单归因于 token 或 SQL 错误。
