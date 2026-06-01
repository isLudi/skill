# Web 查询权限与表可用性指南

## 1. 概述

通过 Playwright Web 自动化执行查询时，使用的是**当前登录账号的 Web UI 权限**。Web 登录通过 CAS 认证后具有用户的完整数据访问范围，覆盖所有知识库已登记的表。

## 2. 表可读性判断

当查询报错或返回异常时，按以下顺序排查：

1. **SQL 语法错误**：字段名拼写、表名前缀、分区过滤、函数兼容性。
2. **部门/行级范围**：是否缺少 `department_name` 限定，或限定范围不当。
3. **Web 登录状态过期**：浏览器 state.json 失效，需重新 login。
4. **平台限流或超时**：复杂查询超时或并发限制。

## 3. 登录状态管理

- **state.json 位置**：`C:\Users\Ludim\.codex\runtime\usql-web-query-operator\state.json`
- **有效期**：通常数小时到一天。CAS Cookie 过期后需重新 login。
- **刷新命令**：通过 `usql_web_query.py login` 重新执行 CAS 自动登录。
- **手动登录**：如果 SSO/MFA 拦截自动登录，使用 `login --manual --headed`。
- **凭证管理**：`BAIJIA_USERNAME` 和 `BAIJIA_PASSWORD` 存储在 `usql_api.env` 中，不写入 Skill 文档。

## 4. NPS 弹窗

百家平台可能在登录后弹出 NPS 满意度调查弹窗，脚本已内置自动关闭逻辑（`dismiss_nps_if_present`）。如果出现新类型的弹窗阻塞脚本，使用 `--headed --debug-artifacts` 排查。
