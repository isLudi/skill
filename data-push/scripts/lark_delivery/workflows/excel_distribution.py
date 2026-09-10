#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
excel_split_send.py — 按列切割 Excel 并逐个私聊分发（飞书）

用法：
  # 1) 切割：按「顾问姓名」列把 xlsx 拆成每人一个文件
  D:\anaconda3\python.exe excel_split_send.py split --file 底表.xlsx --sheet 顾问分周 --by 顾问姓名 --out out/

  # 2) 演练发送（不真发，只打印会对谁发什么）
  D:\anaconda3\python.exe excel_split_send.py send --dir out/ --dry-run

  # 3) 正式发送：文件名（去扩展名）= 收件人姓名，逐个私聊
  D:\anaconda3\python.exe excel_split_send.py send --dir out/ --message "你的周报数据见附件，查收：{name}"

依赖：lark-cli 已登录且已授予 im:message.send_as_user（见 SKILL.md 前置条件）。
"""
import argparse, json, os, re, sys

from ..common.runtime import run_lark

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def sanitize(name):
    return re.sub(r'[\\/:*?"<>|]', "_", str(name)).strip() or "空值"


def cmd_split(a):
    import pandas as pd
    df = pd.read_excel(a.file, sheet_name=a.sheet if a.sheet else 0)
    if a.by not in df.columns:
        raise SystemExit("列 '%s' 不存在，可选列：%s" % (a.by, list(df.columns)))
    os.makedirs(a.out, exist_ok=True)
    mapping = []
    for val, grp in df.groupby(df[a.by].fillna("空值"), dropna=False):
        fn = sanitize(val) + ".xlsx"
        grp.to_excel(os.path.join(a.out, fn), index=False)
        mapping.append({"收件人": val, "行数": len(grp), "文件": fn})
        print("  %-12s %5d 行 -> %s" % (val, len(grp), fn))
    pd.DataFrame(mapping).to_csv(os.path.join(a.out, "_mapping.csv"),
                                 index=False, encoding="utf-8-sig")
    print("切割完成：%d 个文件 -> %s" % (len(mapping), a.out))


def resolve_user(name):
    """按姓名找 open_id，只接受唯一精确匹配。"""
    out = run_lark(["contact", "+search-user", "--query", name, "--as", "user"])
    users = json.loads(out).get("data", {}).get("users", [])
    exact = [u for u in users if u.get("localized_name") == name]
    if len(exact) == 1:
        return exact[0]["open_id"], None
    if not exact:
        if not users:
            return None, "无匹配"
        if len(users) == 1:
            return None, "仅模糊命中(%s)，未自动匹配" % users[0].get("localized_name")
        return None, "有 %d 个模糊命中但无精确匹配" % len(users)
    return None, "重名 %d 人" % len(exact)


def cmd_send(a):
    files = sorted(f for f in os.listdir(a.dir)
                   if f.endswith(".xlsx") and not f.startswith("_"))
    if not files:
        raise SystemExit("目录里没有可发送的 xlsx：" + a.dir)
    ok, skip, fail = 0, [], []
    for f in files:
        name = os.path.splitext(f)[0]
        match_name = re.sub(r"\d+$", "", name) if a.strip_digits else name
        oid, err = resolve_user(match_name)
        if err:
            skip.append((name, err))
            print("[skip] %s: %s" % (name, err))
            continue
        if a.dry_run:
            print("[dry-run] %s -> %s (%s)" % (f, name, oid))
            ok += 1
            continue
        try:
            run_lark(["im", "+messages-send", "--user-id", oid,
                      "--file", f, "--as", "user"], cwd=os.path.abspath(a.dir), timeout=300)
            if a.message:
                run_lark(["im", "+messages-send", "--user-id", oid,
                          "--markdown", a.message.replace("{name}", name), "--as", "user"])
            print("[ok] 已发 %s (%s)" % (name, f))
            ok += 1
        except Exception as e:
            fail.append((name, str(e)[:120]))
            print("[fail] %s: %s" % (name, str(e)[:120]))
    print("\n汇总：成功 %d，跳过 %d，失败 %d" % (ok, len(skip), len(fail)))
    if skip:
        print("跳过名单（需人工核对）：%s" % "、".join(n for n, _ in skip))
    if fail:
        print("失败名单：%s" % "、".join(n for n, _ in fail))
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="按列切割 Excel 并飞书私聊分发")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("--file", required=True)
    s.add_argument("--sheet", default=None)
    s.add_argument("--by", required=True, help="切割依据列名，如 顾问姓名")
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_split)
    s = sub.add_parser("send")
    s.add_argument("--dir", required=True)
    s.add_argument("--message", default=None, help="随文件附言，{name} 会替换为收件人姓名")
    s.add_argument("--strip-digits", action="store_true",
                   help="匹配飞书姓名前去掉文件名末尾数字（如 丁雪04.xlsx 按 丁雪 匹配）")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_send)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
