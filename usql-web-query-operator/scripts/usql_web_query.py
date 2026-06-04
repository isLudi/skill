#!/usr/bin/env python3
"""Operate the Baijia SQL取数 web UI through Playwright.

The script intentionally keeps credentials and browser storage outside the
skill directory. It is a POC automation surface: selectors are conservative and
artifacts are stored under the local Codex runtime folder by default.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


QUERY_URL = "https://uanalysis.baijia.com/getDataSql"
RUNTIME_DIR = Path.home() / ".codex" / "runtime" / "usql-web-query-operator"
DEFAULT_STATE = RUNTIME_DIR / "state.json"
DEFAULT_ARTIFACTS = RUNTIME_DIR / "artifacts"
DEFAULT_BROWSER_CHANNEL = "msedge"
DEFAULT_ENV_FILE = Path(r"E:\2000_work\GAOTU\20002_市场顾问部看板维护表格\usql_api.env")


class UsageError(RuntimeError):
    """User-actionable script error."""


@dataclass
class RunSummary:
    ok: bool
    status: str
    message: str
    artifacts_dir: str
    query_id: str | None = None
    result_preview: dict[str, Any] | None = None
    download_path: str | None = None

    def to_json(self) -> str:
        return json.dumps({
            "ok": self.ok,
            "status": self.status,
            "message": self.message,
            "artifacts_dir": self.artifacts_dir,
            "query_id": self.query_id,
            "result_preview": self.result_preview,
            "download_path": self.download_path,
        }, ensure_ascii=False, indent=2)


def import_playwright() -> Any:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise UsageError(
            "Python Playwright is not installed. Install with:\n"
            "D:\\anaconda3\\python.exe -m pip install playwright\n"
            "D:\\anaconda3\\python.exe -m playwright install chromium"
        ) from exc
    return sync_playwright, PlaywrightTimeoutError


def load_env_file(path: Path | None) -> None:
    if not path or not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def ensure_runtime(paths: list[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def read_sql(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise UsageError(f"SQL file is empty: {path}")
    return text


def visible_download_limit(sql: str) -> int | None:
    matches = re.findall(r"\blimit\s+(\d+)\b", sql, flags=re.I)
    if not matches:
        return None
    return int(matches[-1])


def enforce_download_policy_before_run(sql: str, download: bool) -> None:
    limit = visible_download_limit(sql)
    if download and limit is not None and limit > 1000:
        raise UsageError(
            "Download is blocked by local policy: SQL must visibly contain "
            "LIMIT 1000 or lower, or the result page must prove <= 1000 rows."
        )


def safe_artifact_dir(root: Path) -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    path = root / timestamp
    path.mkdir(parents=True, exist_ok=False)
    return path


def launch_browser(playwright: Any, headed: bool, browser_channel: str | None, executable_path: str | None):
    launch_kwargs: dict[str, Any] = {"headless": not headed}
    if executable_path:
        launch_kwargs["executable_path"] = executable_path
    elif browser_channel:
        launch_kwargs["channel"] = browser_channel
    return playwright.chromium.launch(**launch_kwargs)


def launch_context(playwright: Any, state_path: Path, headed: bool, browser_channel: str | None, executable_path: str | None):
    browser = launch_browser(playwright, headed, browser_channel, executable_path)
    context_kwargs: dict[str, Any] = {
        "viewport": {"width": 1600, "height": 1000},
        "accept_downloads": True,
    }
    if state_path.exists():
        context_kwargs["storage_state"] = str(state_path)
    context = browser.new_context(**context_kwargs)
    return browser, context


def fill_login_if_present(page: Any, username: str | None, password: str | None) -> bool:
    if "cas.baijia.com" not in page.url and "login" not in page.url.lower():
        return False

    if not username:
        username = os.environ.get("BAIJIA_USERNAME")
    if not password:
        password = os.environ.get("BAIJIA_PASSWORD")

    if not username:
        username = input("Baijia username: ").strip()
    if not password:
        password = getpass.getpass("Baijia password: ")

    inputs = page.locator("input")
    if inputs.count() < 2:
        raise UsageError("Login page detected, but username/password inputs were not found.")

    inputs.nth(0).fill(username)
    inputs.nth(1).fill(password)
    page.get_by_text("登录", exact=True).click()
    return True


def ensure_authenticated(page: Any, args: argparse.Namespace, context: Any | None = None) -> None:
    page.goto(QUERY_URL, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(1500)
    if "cas.baijia.com" in page.url or "login" in page.url.lower():
        fill_login_if_present(page, getattr(args, "username", None), getattr(args, "password", None))
        page.wait_for_load_state("domcontentloaded", timeout=45_000)
        page.wait_for_timeout(3000)
        if context is not None:
            context.storage_state(path=str(args.state_path))
    if "cas.baijia.com" in page.url or "login" in page.url.lower():
        raise UsageError("Login failed or requires manual verification.")


def dismiss_nps_if_present(page: Any) -> bool:
    """Close the NPS satisfaction survey modal if it is open.

    Returns True if a modal was found and closed.
    """
    close_selectors = [
        page.locator(".nps-modal-close-icon"),
        page.locator("[class*='nps-modal-close']"),
        page.locator(".nps-modal .ant-modal-close"),
    ]
    for locator in close_selectors:
        try:
            if locator.count() > 0:
                locator.first.click(timeout=3000)
                page.wait_for_timeout(500)
                return True
        except Exception:
            continue

    # Fallback: the NPS survey might show a satisfaction/result page with a button.
    skip_selectors = [
        page.locator(".nps-result-button"),
        page.get_by_text("跳过"),
        page.get_by_text("Skip"),
        page.get_by_text("关闭"),
    ]
    for locator in skip_selectors:
        try:
            if locator.count() > 0:
                locator.first.click(timeout=3000)
                page.wait_for_timeout(500)
                return True
        except Exception:
            continue
    return False


def get_sql_frame(page: Any) -> Any:
    """Return a FrameLocator for the /sql/ iframe that contains the editor."""
    return page.frame_locator('iframe[src^="/sql/"]')


def _sql_frame_ready(page: Any) -> bool:
    """Return True when the /sql/ iframe body is present and non-empty."""
    try:
        frame = page.frame_locator('iframe[src^="/sql/"]')
        frame.locator("body").wait_for(state="visible", timeout=30_000)
        return True
    except Exception:
        return False


def wait_for_query_page(page: Any) -> None:
    page.wait_for_load_state("domcontentloaded", timeout=30_000)
    page.wait_for_timeout(1500)
    if "cas.baijia.com" in page.url or "login" in page.url.lower():
        raise UsageError("Still on login page; login state was not established.")

    # Dismiss NPS survey modal before interacting with the page.
    dismiss_nps_if_present(page)
    page.wait_for_timeout(500)

    page.get_by_text("SQL取数", exact=True).click(timeout=15_000)
    page.wait_for_timeout(1000)

    # The SQL editor lives inside an iframe. Wait for it to load.
    dismiss_nps_if_present(page)
    if not _sql_frame_ready(page):
        page.wait_for_timeout(3000)
        _sql_frame_ready(page)


def create_query_tab(page: Any) -> None:
    candidates = [
        page.get_by_text("+", exact=True),
        page.locator(".ant-tabs-nav-add"),
        page.locator("[aria-label='add']"),
        page.locator("button").filter(has_text="+"),
    ]
    for candidate in candidates:
        try:
            if candidate.count() > 0:
                candidate.first.click(timeout=3000)
                page.wait_for_timeout(800)
                return
        except Exception:
            continue


def set_monaco_sql(page: Any, sql: str) -> None:
    """Set SQL text in the CodeMirror editor inside the /sql/ iframe and select all.

    The platform requires SQL text to be selected (highlighted) before execution,
    otherwise it shows "请选中执行的sql！" (Please select the SQL to execute).
    """
    frame = get_sql_frame(page)

    # Method 1: use CodeMirror API via evaluate on the iframe.
    for frame_obj in page.frames:
        if frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
            set_result = frame_obj.evaluate(
                """sql => {
                    const cmEl = document.querySelector('.CodeMirror');
                    if (cmEl && cmEl.CodeMirror) {
                        const cm = cmEl.CodeMirror;
                        cm.setValue(sql);
                        // Select all text — required by the platform before execution.
                        cm.execCommand('selectAll');
                        return true;
                    }
                    return false;
                }""",
                sql,
            )
            if set_result:
                return
            break

    # Method 2: click the CodeMirror editor, paste, and select all.
    editor = frame.locator(".CodeMirror").last
    editor.click(timeout=10_000)
    page.keyboard.press("Control+A")
    page.keyboard.insert_text(sql)
    page.keyboard.press("Control+A")


def click_run(page: Any) -> None:
    # The run button is inside the /sql/ iframe (CodeMirror editor toolbar).
    frame = get_sql_frame(page)
    dismiss_nps_if_present(page)

    selectors = [
        "[aria-label='play-circle']",
        "[aria-label*='play']",
        ".anticon-play-circle",
        ".anticon-caret-right",
        "[title*='运行']",
        "[aria-label*='运行']",
        "button:has-text('运行')",
    ]
    for selector in selectors:
        for scope in (frame, page):
            locator = scope.locator(selector)
            try:
                if locator.count() > 0:
                    locator.first.click(timeout=3000)
                    return
            except Exception:
                continue

    # Fallback: toolbar button near the editor (inside iframe).
    editor_buttons = frame.locator(".antd-pro-src-components-editor-index-editorBtn")
    count = min(editor_buttons.count(), 20)
    for index in range(count):
        item = editor_buttons.nth(index)
        try:
            item.click(timeout=2000)
            return
        except Exception:
            continue

    raise UsageError("Could not find the run button. Rerun with --headed --debug-artifacts.")


def wait_for_status(page: Any, timeout_ms: int):
    deadline = time.monotonic() + timeout_ms / 1000
    last_text = ""
    while time.monotonic() < deadline:
        # Check both outer page and iframe for status text.
        body_text = page.locator("body").inner_text(timeout=5000)
        try:
            frame = get_sql_frame(page)
            iframe_text = frame.locator("body").inner_text(timeout=3000)
        except Exception:
            iframe_text = ""
        combined = body_text + iframe_text
        last_text = combined[-2000:]
        if "Success" in combined:
            return "Success", combined
        if "Failed" in combined:
            return "Failed", combined
        page.wait_for_timeout(2000)
    return "Timeout", last_text


def extract_query_id(text: str) -> str | None:
    match = re.search(r"\b(\d{8,})\b", text)
    return match.group(1) if match else None


def _wait_for_result_panel(page: Any) -> None:
    """Wait for the result panel to render after query success.

    The platform shows "Success" in query history when the query is accepted,
    then streams execution logs asynchronously. After the log finishes, the
    page AUTO-JUMPS to the result view showing the data table + download button.

    We wait for: log loading spinner gone → auto-jump → result table visible.
    """
    frame = get_sql_frame(page)
    # The platform can be slow — wait up to the full query timeout.
    deadline = time.monotonic() + 600.0  # 10 min max

    scroll_script = "el => { el.scrollTop = el.scrollHeight; }"
    prev_url = ""

    while time.monotonic() < deadline:
        # Scroll to keep the bottom (log / result area) visible.
        try:
            frame.locator("body").evaluate(scroll_script)
        except Exception:
            pass

        page.wait_for_timeout(2000)

        for frame_obj in page.frames:
            if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
                continue

            # Detect if the iframe auto-jumped to a result URL.
            cur_url = frame_obj.url
            if cur_url != prev_url:
                prev_url = cur_url

            check = frame_obj.evaluate("""() => {
                // 1. Is the log loading spinner still active?
                const loadingIcons = document.querySelectorAll('.anticon-loading');
                for (const icon of loadingIcons) {
                    if (icon.closest('.antd-pro-src-components-history-infinite-scroll-log-index-logContainer')) {
                        return 'log-loading';
                    }
                }

                // 2. Check for a result data table (not the query-history table).
                const tables = document.querySelectorAll('.ant-table');
                for (const t of tables) {
                    const headers = Array.from(t.querySelectorAll('th')).map(h => h.innerText.trim());
                    if (headers.some(h => h.includes('查询ID') || h.includes('主要内容'))) continue;
                    const rows = t.querySelectorAll('.ant-table-row');
                    if (rows.length > 0) {
                        return 'result-table:' + rows.length + 'rows';
                    }
                }

                // 3. Check for result data text anywhere in the body.
                const bt = document.body.innerText;
                if (bt.includes('row_cnt') || bt.includes('lead_cnt')) return 'result-text';

                // 4. Check for collapsed/expandable result panel.
                const collapses = document.querySelectorAll('.ant-collapse-item');
                if (collapses.length > 0) return 'collapse-panels:' + collapses.length;

                // 5. "结果"/"表格" tabs present?
                if (bt.includes('结果') && bt.includes('表格')) return 'result-tabs';

                return 'waiting';
            }""")

            if check.startswith('result-') or check.startswith('collapse-'):
                page.wait_for_timeout(1000)
                return
            if check == 'log-loading':
                continue

    # Timeout: one last attempt.
    try:
        frame.locator("body").evaluate(scroll_script)
        page.wait_for_timeout(3000)
    except Exception:
        pass


def open_result_table(page: Any) -> None:
    """The result panel auto-appears at the page bottom after query success.

    We just scroll down to ensure it is in view, then click "结果"/"表格" if needed.
    """
    frame = get_sql_frame(page)
    page.wait_for_timeout(500)

    # Scroll to bottom of the iframe to ensure the result panel is visible.
    try:
        frame.locator("body").evaluate("el => el.scrollTop = el.scrollHeight")
        page.wait_for_timeout(500)
    except Exception:
        pass

    # Try clicking "结果" / "表格" sub-tabs if they exist.
    for label in ("结果", "表格"):
        for scope in (frame, page):
            try:
                locator = scope.get_by_text(label, exact=True)
                if locator.count() > 0:
                    locator.last.click(timeout=3000)
                    page.wait_for_timeout(500)
                    break
            except Exception:
                continue


def extract_result_preview(page: Any, max_rows: int = 5) -> dict[str, Any] | None:
    open_result_table(page)
    body_text = page.locator("body").inner_text(timeout=5000)

    # Collect tables from both the iframe and the outer page.
    all_tables = []
    for frame_obj in page.frames:
        try:
            frame_tables = frame_obj.evaluate(
                """maxRows => {
                    function visible(el) {
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                    }
                    return Array.from(document.querySelectorAll('table')).filter(visible).map((table) => {
                        const rows = Array.from(table.querySelectorAll('tr')).filter(visible);
                        const parsed = rows.map((tr) => Array.from(tr.querySelectorAll('th,td')).map((cell) => cell.innerText.trim()));
                        const nonEmpty = parsed.filter((row) => row.some(Boolean));
                        return {
                            headers: nonEmpty[0] || [],
                            rows: nonEmpty.slice(1, maxRows + 1),
                            row_count_visible: Math.max(nonEmpty.length - 1, 0),
                        };
                    });
                }""",
                max_rows,
            )
            all_tables.extend(frame_tables)
        except Exception:
            continue
    ignored_headers = {"查询ID", "查询时间", "主要内容", "引擎", "持续时间", "状态", "下载状态", "操作"}
    candidates = []
    for table in all_tables:
        headers = set(table.get("headers") or [])
        if not headers:
            continue
        if headers & ignored_headers:
            continue
        # Prefer tables that actually have data rows.
        if table.get("rows") and len(table["rows"]) > 0:
            candidates.append(table)
    if not candidates:
        # Fallback: accept any non-history table even if empty.
        for table in all_tables:
            headers = set(table.get("headers") or [])
            if not headers:
                continue
            if headers & ignored_headers:
                continue
            candidates.append(table)
    if not candidates:
        return None
    # Return the last candidate (typically the bottom-most result table).
    result = candidates[-1]
    result["no_more"] = "已无更多" in body_text
    return result


def download_allowed(sql: str, result_preview: dict[str, Any] | None) -> tuple[bool, str]:
    limit = visible_download_limit(sql)
    if limit is not None:
        return (limit <= 1000, f"SQL limit={limit}")
    if result_preview and result_preview.get("no_more") and result_preview.get("row_count_visible", 1001) <= 1000:
        return (True, "result page indicates no more rows and visible rows <= 1000")
    return (False, "no SQL limit and result page did not prove <= 1000 rows")


def click_download_button(page: Any, artifacts_dir: Path):
    """Click the download button and select Excel format from the dropdown.

    The platform shows a dropdown with CSV and Excel options after clicking
    the download icon. We select the Excel (.xlsx) option.
    """
    frame = get_sql_frame(page)

    # Step 1: click the download icon to open the dropdown menu.
    download_selectors = [
        ".anticon-download",
        "[aria-label*='download']",
        "button.ant-btn-link.ant-dropdown-trigger",
    ]
    clicked = False
    for selector in download_selectors:
        for scope in (frame, page):
            locator = scope.locator(selector)
            try:
                if locator.count() > 0:
                    locator.last.click(timeout=5000)
                    clicked = True
                    break
            except Exception:
                continue
        if clicked:
            break

    if not clicked:
        raise UsageError("Could not find the download button.")

    # Step 2: wait for the dropdown menu to appear.
    page.wait_for_timeout(800)

    # Step 3: click the Excel option in the dropdown.
    # The dropdown shows lowercase "csv" and "excel" menu items.
    excel_selectors = [
        frame.get_by_text("excel", exact=True),
        page.get_by_text("excel", exact=True),
        frame.locator(".ant-dropdown-menu-item:has-text('excel')"),
    ]
    excel_clicked = False
    with page.expect_download(timeout=30_000) as download_info:
        for selector in excel_selectors:
            try:
                if selector.count() > 0:
                    selector.last.click(timeout=5000)
                    excel_clicked = True
                    break
            except Exception:
                continue

        if not excel_clicked:
            # Fallback: click the last dropdown menu item (which is "excel").
            for scope in (frame, page):
                menu_items = scope.locator(".ant-dropdown-menu-item")
                try:
                    count = menu_items.count()
                    if count >= 2:
                        menu_items.nth(count - 1).click(timeout=3000)
                        excel_clicked = True
                        break
                except Exception:
                    continue

        if not excel_clicked:
            raise UsageError("Could not find the Excel download option in the dropdown.")

    download = download_info.value
    suggested = download.suggested_filename or "usql_result_download.xlsx"
    target = artifacts_dir / suggested
    download.save_as(str(target))
    return str(target)


def save_debug_artifacts(page: Any, artifacts_dir: Path, prefix: str = "page") -> None:
    page.screenshot(path=str(artifacts_dir / f"{prefix}.png"), full_page=True)
    (artifacts_dir / f"{prefix}.html").write_text(page.content(), encoding="utf-8")


def cmd_doctor(_: argparse.Namespace) -> int:
    try:
        import_playwright()
    except UsageError as exc:
        print(str(exc))
        return 1
    print("Python Playwright is available.")
    print(f"Runtime dir: {RUNTIME_DIR}")
    print(f"Default state: {DEFAULT_STATE}")
    edge_path = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    chrome_path = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    print(f"Edge available: {edge_path.exists()} ({edge_path})")
    print(f"Chrome available: {chrome_path.exists()} ({chrome_path})")
    print(f"Default browser channel: {DEFAULT_BROWSER_CHANNEL}")
    return 0


def cmd_login(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    sync_playwright, _ = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    with sync_playwright() as playwright:
        browser = launch_browser(playwright, args.headed, args.browser_channel, args.executable_path)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()
        page.goto(QUERY_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        if args.manual:
            print("Complete login in the opened browser, then press Enter here.")
            input()
        else:
            fill_login_if_present(page, args.username, args.password)
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
            page.wait_for_timeout(3000)
        context.storage_state(path=str(args.state_path))
        print(f"Saved login state: {args.state_path}")
        browser.close()
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    sql = read_sql(args.sql_file)
    enforce_download_policy_before_run(sql, download=args.download)
    sync_playwright, _ = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            page.goto(QUERY_URL, wait_until="domcontentloaded", timeout=45_000)
            if "cas.baijia.com" in page.url or "login" in page.url.lower():
                raise UsageError("Login state expired. Run the login command again.")
            wait_for_query_page(page)
            if args.new_tab:
                create_query_tab(page)
            set_monaco_sql(page, sql)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "before_run")
            click_run(page)
            status, text = wait_for_status(page, args.timeout_ms)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "after_run")

            # After Success, the result panel renders at the bottom of the page
            # after log-loading completes. Wait for it to appear.
            if status == "Success":
                _wait_for_result_panel(page)
                if args.debug_artifacts:
                    save_debug_artifacts(page, artifacts_dir, "after_result_panel")

            query_id = extract_query_id(text)
            result_preview = extract_result_preview(page) if status == "Success" else None
            download_path = None
            if status == "Success" and args.download:
                allowed, reason = download_allowed(sql, result_preview)
                if not allowed:
                    raise UsageError(f"Download blocked by local policy: {reason}")
                download_path = click_download_button(page, artifacts_dir)
            summary = RunSummary(
                ok=status == "Success",
                status=status,
                message="Query finished." if status in {"Success", "Failed"} else "Timed out waiting for query status.",
                artifacts_dir=str(artifacts_dir),
                query_id=query_id,
                result_preview=result_preview,
                download_path=download_path,
            )
        except Exception as exc:
            if args.debug_artifacts:
                try:
                    save_debug_artifacts(page, artifacts_dir, "error")
                except Exception:
                    pass
            summary = RunSummary(
                ok=False,
                status="Error",
                message=str(exc),
                artifacts_dir=str(artifacts_dir),
            )
        finally:
            browser.close()

    print(summary.to_json())
    return 0 if summary.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check local Playwright availability.")
    doctor.set_defaults(func=cmd_doctor)

    login = subparsers.add_parser("login", help="Authenticate and save browser storage state.")
    login.add_argument("--headed", action="store_true", help="Show browser window.")
    login.add_argument("--manual", action="store_true", help="Let the user complete login manually.")
    login.add_argument("--username", default=os.environ.get("BAIJIA_USERNAME"))
    login.add_argument("--password", default=os.environ.get("BAIJIA_PASSWORD"))
    login.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    login.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    login.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    login.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    login.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    login.set_defaults(func=cmd_login)

    run = subparsers.add_parser("run", help="Run SQL in the web UI.")
    run.add_argument("--sql-file", type=Path, required=True)
    run.add_argument("--headed", action="store_true", help="Show browser window.")
    run.add_argument("--state-path", type=Path, default=DEFAULT_STATE)
    run.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    run.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    run.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL, help="Installed browser channel, e.g. msedge or chrome.")
    run.add_argument("--executable-path", default=None, help="Explicit browser executable path; overrides --browser-channel.")
    run.add_argument("--timeout-ms", type=int, default=10 * 60 * 1000)
    run.add_argument("--new-tab", action=argparse.BooleanOptionalAction, default=True)
    run.add_argument("--download", action="store_true", help="Download the result when local row-limit policy allows it.")
    run.add_argument("--no-download", action="store_false", dest="download")
    run.add_argument("--debug-artifacts", action="store_true", help="Save screenshots and HTML under the runtime artifacts directory.")
    run.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
