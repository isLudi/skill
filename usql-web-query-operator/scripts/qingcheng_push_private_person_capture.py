from __future__ import annotations

import sys

from read_dashboard.cli import main
from read_dashboard.push_targets import build_capture_argv


if __name__ == "__main__":
    raise SystemExit(main(build_capture_argv("private_person", sys.argv[1:])))
