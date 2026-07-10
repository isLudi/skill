"""Build or verify P2 manifests, contract indexes, and the shared physical catalog."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = REPO_ROOT / "_shared" / "text2sql_core"
sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.builder import build_outputs, check_outputs, write_outputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated files are missing or stale")
    args = parser.parse_args()
    outputs = build_outputs(REPO_ROOT)
    if args.check:
        failures = check_outputs(outputs)
        if failures:
            for failure in failures:
                print(f"[FAIL] {failure}")
            return 1
        print(f"Text2SQL catalog check passed ({len(outputs)} generated files).")
        return 0
    write_outputs(outputs)
    for path in outputs:
        print(path.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
