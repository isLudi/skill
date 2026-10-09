"""Isolated OWA Light login, bounded OES mail discovery and attachment reads."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlencode, urljoin, urlsplit

from _shared.browser import launch_browser
from _shared.config import OES_DATA_ROOT
from _shared.errors import UsageError
from .board import SHANGHAI
from .session import load_credentials, _within

MAIL_URL = "https://mail.gaotu.cn/owa/"
MAIL_RUNTIME_DIR = OES_DATA_ROOT / "oes-outlook"
DEFAULT_MAIL_STATE = MAIL_RUNTIME_DIR / "state.json"
DEFAULT_SENDER = "gtkt-lvyue"
DEFAULT_SUBJECT = "业绩数据明细导出"


@dataclass(frozen=True)
class ExportMail:
    item_id: str = field(repr=False)
    sender: str
    subject: str
    received_at: datetime

    @property
    def identity_hash(self) -> str:
        return hashlib.sha256(self.item_id.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Attachment:
    filename: str
    url: str = field(repr=False)


@dataclass
class OutlookSession:
    browser: Any
    context: Any
    page: Any
    login_performed: bool

    def close(self) -> None:
        self.browser.close()


def _authenticated(page: Any) -> bool:
    url = urlsplit(page.url)
    return url.hostname == "mail.gaotu.cn" and url.path == "/owa/" and page.locator("#lnkNavMail").count() == 1


def _save_state(context: Any, path: Path) -> None:
    temporary = path.with_suffix(".tmp")
    context.storage_state(path=str(temporary))
    temporary.replace(path)


def open_outlook_session(playwright: Any, args: Any) -> OutlookSession:
    """Refresh FBA once when necessary, using only the exact OES env section."""
    state_path = args.mail_state_path
    if not _within(state_path, MAIL_RUNTIME_DIR):
        raise UsageError(f"Outlook state must stay under its isolated runtime directory: {MAIL_RUNTIME_DIR}")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    credentials = load_credentials(args.env_file)
    account_hash = hashlib.sha256(credentials.username.casefold().encode("utf-8")).hexdigest()
    binding = state_path.with_suffix(".account")
    reuse = state_path.is_file() and binding.is_file() and binding.read_text(encoding="utf-8").strip() == account_hash
    browser = launch_browser(playwright, args.headed, args.browser_channel, args.executable_path)
    try:
        kwargs = {"accept_downloads": True, "viewport": {"width": 1600, "height": 1000}}
        context = browser.new_context(**kwargs, **({"storage_state": str(state_path)} if reuse else {}))
        page = context.new_page()
        page.goto(MAIL_URL, wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_function("() => document.querySelector('#lnkNavMail') || document.querySelector('#username')", timeout=15_000)
        login_performed = False
        if not _authenticated(page):
            if urlsplit(page.url).hostname != "mail.gaotu.cn" or "/owa/auth/" not in urlsplit(page.url).path:
                raise UsageError("Outlook authentication or page layout changed; expected the OWA Light mailbox or login form.")
            if page.locator("#username").count() != 1 or page.locator("#password").count() != 1:
                raise UsageError("Outlook requires interactive verification or its login form changed.")
            if reuse:
                context.close()
                context = browser.new_context(**kwargs)
                page = context.new_page()
                page.goto(MAIL_URL, wait_until="domcontentloaded", timeout=45_000)
            page.locator("#username").fill(credentials.username)
            page.locator("#password").fill(credentials.password)
            # This is an observed form field, scoped to this login request; no mailbox preference is edited.
            downlevel = page.locator("input[name=forcedownlevel]")
            if downlevel.count() == 1:
                downlevel.evaluate("e => e.value = '1'")
            submit = page.locator(".signinbutton")
            if submit.count() != 1:
                raise UsageError("Outlook sign-in button changed; no credentials were submitted.")
            submit.click(timeout=15_000)
            page.wait_for_load_state("domcontentloaded", timeout=45_000)
            if not _authenticated(page):
                raise UsageError("Outlook login was rejected or requires verification; no automatic credential retry was made.")
            login_performed = True
        _save_state(context, state_path)
        binding.write_text(account_hash + "\n", encoding="utf-8")
        return OutlookSession(browser, context, page, login_performed)
    except Exception:
        browser.close()
        raise


def parse_received_time(value: str) -> datetime:
    normalized = " ".join(value.replace("\u00a0", " ").split())
    try:
        return datetime.strptime(normalized, "%Y/%m/%d %H:%M").replace(tzinfo=SHANGHAI).astimezone(timezone.utc)
    except ValueError as exc:
        raise UsageError("Outlook received-time format changed; refusing to guess the mail's age.") from exc


def parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise UsageError("Mail timestamps must be ISO-8601 and include a timezone offset.") from exc
    if parsed.tzinfo is None:
        raise UsageError("Mail timestamps must include a timezone offset, for example +08:00.")
    return parsed.astimezone(timezone.utc)


def list_export_mails(session: OutlookSession, *, sender: str, subject_contains: str, scan_pages: int) -> list[ExportMail]:
    page = session.page
    page.goto(MAIL_URL, wait_until="domcontentloaded", timeout=45_000)
    if not _authenticated(page):
        raise UsageError("Outlook state expired during mail polling; resume after restoring the mailbox session.")
    result: list[ExportMail] = []
    seen: set[str] = set()
    for _ in range(scan_pages):
        # Start at each checkbox's nearest row, avoiding outer tables that contain the entire inbox.
        rows = page.locator("input[name=chkmsg]").evaluate_all(
            """els => els.map(e => {
              const tr = e.closest('tr'); const link = tr.querySelector('a[onclick*=onClkRdMsg]');
              return {id:e.value, subject:link?.innerText.trim(), cells:[...tr.cells].map(c=>c.innerText.trim())};
            })"""
        )
        for row in rows:
            cells = row.get("cells", [])
            if len(cells) != 8:
                raise UsageError("Outlook inbox column layout changed; mail discovery stopped.")
            if cells[4].casefold() != sender.casefold() or subject_contains not in (row.get("subject") or ""):
                continue
            item_id = row.get("id")
            if not item_id or item_id in seen:
                continue
            seen.add(item_id)
            result.append(ExportMail(item_id, cells[4], row["subject"], parse_received_time(cells[6])))
        next_page = page.locator("#lnkNxtPgHdr")
        if next_page.count() != 1 or "noHv" in (next_page.get_attribute("class") or ""):
            break
        next_page.click(timeout=15_000)
        page.wait_for_load_state("domcontentloaded", timeout=45_000)
    return result


def matching_mails(mails: list[ExportMail], *, received_after: datetime, received_before: datetime | None = None,
                   excluded_hashes: set[str] | None = None, exact_subject: str | None = None) -> list[ExportMail]:
    # OWA Light exposes arrival timestamps at minute precision. The pre-export baseline closes that minute's gap.
    lower_bound = received_after.replace(second=0, microsecond=0)
    return [m for m in mails if m.received_at >= lower_bound
            and (received_before is None or m.received_at <= received_before)
            and m.identity_hash not in (excluded_hashes or set())
            and (exact_subject is None or m.subject == exact_subject)]


def parse_mail_count(text: str) -> int:
    match = re.search(r"数据总(?:条数总数|条数|数)\s*[:：]\s*(\d[\d,，]*)", text)
    if not match:
        raise UsageError("OES export mail has no recognized data count; attachment delivery is unverified.")
    value = match.group(1)
    if ("," in value or "，" in value) and not re.fullmatch(r"\d{1,3}(?:[,，]\d{3})+", value):
        raise UsageError("OES export mail has an invalid thousands-separated count.")
    return int(value.replace(",", "").replace("，", ""))


def read_export_mail(session: OutlookSession, mail: ExportMail) -> tuple[int, list[Attachment]]:
    page = session.page
    page.goto(MAIL_URL + "?" + urlencode({"ae": "Item", "t": "IPM.Note", "id": mail.item_id}),
              wait_until="domcontentloaded", timeout=45_000)
    if not _authenticated(page) or page.title() != mail.subject + " - Outlook":
        raise UsageError("Outlook did not open the exact selected export mail.")
    text = page.locator("body").inner_text()
    count = parse_mail_count(text)
    links = page.locator("a[id='lnkAtmt'][href]").evaluate_all(
        "els => els.map(e => ({text:e.innerText, href:e.getAttribute('href')}))"
    )
    attachments: list[Attachment] = []
    for link in links:
        name = re.match(r"^(.+?\.xlsx)\b", link["text"].replace("\u200e", "").strip(), re.IGNORECASE)
        if name:
            url = urljoin(MAIL_URL, link["href"])
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.hostname != "mail.gaotu.cn" or parsed.path != "/owa/attachment.ashx":
                raise UsageError("Outlook attachment URL is outside the observed same-origin download endpoint.")
            attachments.append(Attachment(name.group(1), url))
    if len(attachments) != 1:
        raise UsageError("Expected exactly one native OES .xlsx attachment in the selected export mail.")
    return count, attachments


def download_attachment(session: OutlookSession, attachment: Attachment) -> bytes:
    response = session.context.request.get(attachment.url, timeout=120_000, max_redirects=0)
    if not response.ok:
        raise UsageError(f"Outlook attachment download failed with HTTP {response.status}; no export was resubmitted.")
    data = response.body()
    if not data.startswith(b"PK\x03\x04"):
        raise UsageError("Outlook returned no XLSX bytes (possibly an expired login page).")
    return data
