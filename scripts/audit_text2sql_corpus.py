"""Parse every concrete retained SQL artifact with the pinned Presto parser."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = REPO_ROOT / "_shared" / "text2sql_core"
sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.corpus import audit_raw_sql  # noqa: E402


def main() -> int:
    result = audit_raw_sql(REPO_ROOT, CORE_ROOT / "config" / "corpus_exceptions.json")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

