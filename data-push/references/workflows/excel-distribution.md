# Excel按人切割与私聊分发

脚本 `scripts/excel_split_send.py`：一张总表 → 按列切成 N 份 → 逐个私聊发送。

```bash
Set-Location 'C:\Users\Ludim\.codex\skills\data-push'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
$PY='D:\anaconda3\python.exe'

# ① 切割：按「顾问姓名」拆，每人一个 xlsx，文件名=姓名
& $PY '.\scripts\excel_split_send.py' split --file 底表.xlsx --sheet 顾问分周 --by 顾问姓名 --out out/distribute/

# ② 演练：只打印"谁收到什么"，不真发（重名/查无此人会列清单）
& $PY '.\scripts\excel_split_send.py' send --dir out/distribute/ --dry-run

# ③ 正式发送（文件名带工号如 丁雪04.xlsx 时加 --strip-digits）
& $PY '.\scripts\excel_split_send.py' send --dir out/distribute/ --strip-digits --message "你的数据见附件，请查收：{name}"
```

**规则（安全红线）**：
- 收件人 = 文件名去扩展名，按飞书姓名**唯一精确匹配**；重名/模糊/查无此人一律跳过并列清单，绝不猜着发
- `--dry-run` 必跑；正式发送前把「收件人数 + 跳过名单 + 附言」给用户确认
- 切割后抽查 1~2 个文件确认没串行（切错列会把别人的数据发错人）
- split 会生成 `_mapping.csv`（收件人/行数/文件）用于对账
- 需要授权 `im:message.send_as_user`（一次性）：`lark-cli auth login --scope "im:message.send_as_user"`，scope 授权一次长期有效

---

---

稳定入口：`scripts/excel_split_send.py`；实现：`scripts/lark_delivery/workflows/excel_distribution.py`。群播报的部门、期次、指标规则不应用到Excel分发。新增或更改分发规则先加独立的工作流测试。
