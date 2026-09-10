"""Offline structural validation; no authentication, API or scheduler calls."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import re
import sys

from lark_delivery.paths import SKILL_ROOT
from lark_delivery.core import catalog
from lark_delivery.core.registry import adapter_for


def validate(root=SKILL_ROOT):
    root = Path(root).resolve()
    errors = []
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    if not re.search(r"^name: data-push$", skill, re.M) or root.name != "data-push":
        errors.append("Skill directory/name mismatch")
    count = 0
    for path in (root / "scripts").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(root).as_posix()
        count += 1
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{relative}: {exc}")
            continue
        if len(text.splitlines()) > 650:
            errors.append(f"{relative}: oversized module; split along an interface boundary")
        if relative == "scripts/lark_delivery/legacy/market_group.py" and len(text.splitlines()) > 180:
            errors.append("Compatibility facade is growing into an implementation again")
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if "/common/" in relative and any(word in module.split(".") for word in ("domains", "legacy")):
                    errors.append(f"{relative}: common must not import business/legacy code")
                if "/domains/" in relative and "legacy" in module.split("."):
                    errors.append(f"{relative}: current domain must not depend on legacy")
                if "/core/" in relative and path.name != "registry.py" and "domains" in module.split("."):
                    errors.append(f"{relative}: only registry may select a department adapter")
    for path in root.rglob("*.md"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "\ufffd" in text:
            errors.append(f"{path.relative_to(root)}: replacement character")
        for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
            target = target.strip("<>").split("#", 1)[0]
            if not target or re.match(r"[a-z]+://", target):
                continue
            if not (path.parent / target).resolve().exists():
                errors.append(f"{path.relative_to(root)}: missing link {target}")
    for key in catalog.registry(root / "config")["channels"]:
        try:
            definition = catalog.load_channel(key, root / "config")
            adapter_for(definition)
            entry = root / "scripts/channels" / (key + ".py")
            if not entry.exists() or f'bound_channel="{key}"' not in entry.read_text(encoding="utf-8"):
                errors.append(f"Missing/mismatched channel entrypoint: {key}")
        except (ValueError, KeyError) as exc:
            errors.append(f"{key}: {exc}")
    return {"ok": not errors, "python_files": count, "errors": errors, "remote_mutations": 0}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)
