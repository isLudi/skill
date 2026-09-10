#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
refresh.py — 妙搭看板每日刷新流水线（通用模板）

导出 → 聚合构建 data.json → 闸门校验 → git 提交推送 → release 发布 → 轮询。

使用前准备（一次性）：
    1. 把本文件放到看板项目根目录，同目录建 app/（妙搭应用仓库克隆）和 explore/（导出+构建脚本）
    2. 设置环境变量 MIAODA_APP_ID=<app_id>
    3. 在 app/ 里执行过 lark-cli apps +git-credential-init --app-id <app_id> --as user（否则 git 推送弹密码框）

用法：
    D:\anaconda3\python.exe refresh.py --confirm-publish  # 完整刷新并发布
    D:\anaconda3\python.exe refresh.py --no-publish       # 只导出+构建+推送，不发布（调试用）
"""
import argparse, datetime, json, os, shutil, subprocess, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.abspath(__file__))
EXPLORE = os.path.join(ROOT, "explore")
APP = os.path.join(ROOT, "app")
NPM = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "npm")
REAL_GIT = os.environ.get("MIAODA_GIT") or shutil.which("git") or ""
APP_ID = os.environ.get("MIAODA_APP_ID", "")
BRANCH = os.environ.get("MIAODA_BRANCH", "sprint/default")
# data.json 中必须存在且非空的字段（按你的看板改）
REQUIRED_KEYS = ["meta"]

_SENSITIVE_FLAGS = {"--base-token", "--token", "--password", "--secret", "--authorization", "--content", "--text", "--markdown"}


def _redacted_args(args):
    rendered, redact_next = [], False
    for value in args:
        item = str(value)
        if redact_next:
            rendered.append("<redacted>")
            redact_next = False
        elif item in _SENSITIVE_FLAGS:
            rendered.append(item)
            redact_next = True
        elif any(item.startswith(flag + "=") for flag in _SENSITIVE_FLAGS):
            rendered.append(item.split("=", 1)[0] + "=<redacted>")
        else:
            rendered.append(item)
    return " ".join(rendered)


def resolve_lark_cli():
    override = os.environ.get("LARK_CLI", "").strip()
    if override:
        candidate = Path(os.path.expandvars(override)).expanduser()
        if candidate.is_file():
            return str(candidate)
        found = shutil.which(override)
        if found:
            return found
        raise SystemExit("LARK_CLI 指向的 lark-cli 不存在: %s" % override)
    if os.name == "nt":
        candidates = []
        if os.environ.get("APPDATA"):
            npm_root = Path(os.environ["APPDATA"]) / "npm"
            candidates.append(npm_root / "node_modules" / "@larksuite" / "cli" / "bin" / "lark-cli.exe")
            candidates.append(npm_root / "lark-cli.exe")
        candidates.append(Path(sys.executable).resolve().parent / "lark-cli.exe")
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        found = shutil.which("lark-cli.exe")
        if found:
            return found
        raise SystemExit("未找到原生 lark-cli.exe，请设置 LARK_CLI")
    found = shutil.which("lark-cli")
    if found:
        return found
    raise SystemExit("未找到 lark-cli，请设置 LARK_CLI")


def env_with_npm():
    e = dict(os.environ)
    e["PATH"] = NPM + os.pathsep + e.get("PATH", "") if os.path.isdir(NPM) else e.get("PATH", "")
    e["PYTHONIOENCODING"] = "utf-8"
    e["PYTHONUTF8"] = "1"
    return e


def run(cmd, cwd, env, timeout=900):
    print(">> " + _redacted_args(cmd), flush=True)
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       timeout=timeout, shell=False)
    if r.returncode != 0:
        print("---- STDERR ----", r.stderr[-2500:], flush=True)
        raise SystemExit("命令失败 (exit %d): %s" % (r.returncode, cmd))
    return r.stdout


def run_lark(args, cwd, env, timeout=120):
    command = [resolve_lark_cli(), *(str(item) for item in args)]
    return run(command, cwd, env, timeout=timeout)


def check_gate():
    p = os.path.join(APP, "data.json")
    if not os.path.exists(p):
        raise SystemExit("data.json 不存在, 构建失败")
    j = json.load(open(p, encoding="utf-8"))
    for k in REQUIRED_KEYS:
        if k not in j or (isinstance(j[k], (list, dict)) and len(j[k]) == 0):
            raise SystemExit("data.json 缺少或为空字段: %s" % k)
    today = datetime.date.today().isoformat()
    exported = j.get("meta", {}).get("exported_at", "")
    if exported != today:
        raise SystemExit("exported_at=%s 不是今日 %s，终止发布" % (exported, today))
    print("[gate] data.json OK | exported_at=%s" % exported)


def git_commit_push():
    env = env_with_npm()
    run([REAL_GIT, "add", "--", "data.json"], APP, env, timeout=120)
    if not run([REAL_GIT, "status", "--porcelain"], APP, env, timeout=60).strip():
        print("[git] 无变更, 跳过提交/推送")
        return False
    today = datetime.date.today().isoformat()
    run([REAL_GIT, "commit", "-m", "auto: 刷新数据快照 %s" % today], APP, env, timeout=120)
    try:
        run([REAL_GIT, "push", "origin", BRANCH], APP, env, timeout=180)
    except SystemExit:
        if os.environ.get("MIAODA_ALLOW_FORCE_PUSH") != "1":
            raise SystemExit("普通推送失败；不会自动强推。确认远端历史后设置 MIAODA_ALLOW_FORCE_PUSH=1 再重试")
        print("[git] 已显式允许，尝试 force-with-lease")
        run([REAL_GIT, "push", "--force-with-lease", "origin", BRANCH], APP, env, timeout=180)
    return True


def publish():
    env = env_with_npm()
    rid_out = run_lark(["apps", "+release-create", "--app-id", APP_ID,
                        "--branch", BRANCH, "--as", "user"], APP, env, timeout=120)
    rid = json.loads(rid_out)["data"]["release_id"]
    print("[release] 创建 %s, 轮询中..." % rid)
    for i in range(18):
        g = run_lark(["apps", "+release-get", "--app-id", APP_ID,
                      "--release-id", rid, "--as", "user"], APP, env, timeout=60)
        try:
            st = json.loads(g).get("data", {}).get("status")
        except Exception:
            st = "?"
        print("  [%d] status=%s" % (i + 1, st), flush=True)
        if st == "finished":
            print("[release] 发布完成 %s" % rid)
            return
        if st == "failed":
            raise SystemExit("发布失败:\n" + g)
        time.sleep(20)
    raise SystemExit("发布轮询超时(>6min)，请按本机 lark-apps Skill 的 release-get 说明继续只读核验")


def main():
    parser = argparse.ArgumentParser(description="妙搭看板每日刷新流水线")
    parser.add_argument("--no-publish", action="store_true", help="只提交并推送数据，不发起妙搭发布")
    parser.add_argument("--confirm-publish", action="store_true", help="确认本次要发起妙搭发布")
    args = parser.parse_args()
    if not APP_ID:
        raise SystemExit("请先设置环境变量 MIAODA_APP_ID")
    if not REAL_GIT:
        raise SystemExit("未找到 git，请安装 Git 或设置 MIAODA_GIT")
    if not args.no_publish and not args.confirm_publish:
        raise SystemExit("本次会发起妙搭发布；请复核分支后显式传 --confirm-publish，或使用 --no-publish")
    env = env_with_npm()
    print("===== 看板自动刷新 %s =====" % datetime.datetime.now().isoformat(timespec="seconds"))
    # 1. 导出 + 构建（按你的项目实现这两个脚本）
    run([sys.executable, "export_raw.py"], EXPLORE, env, timeout=1200)
    run([sys.executable, "build_data.py"], EXPLORE, env, timeout=300)
    # 2. 同步进应用仓库 + 闸门
    shutil.copy(os.path.join(EXPLORE, "data.json"), os.path.join(APP, "data.json"))
    check_gate()
    # 3. 提交推送 + 发布
    if not git_commit_push():
        print("[skip] 无变更, 无需发布")
        return
    if args.no_publish:
        print("===== 完成(未发布) =====")
        return
    publish()
    print("===== 自动刷新完成 =====")


if __name__ == "__main__":
    main()
