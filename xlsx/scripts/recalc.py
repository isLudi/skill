"""
Excel Formula Recalculation Script
Recalculates formulas with Excel COM on Windows and LibreOffice elsewhere.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from office.workbook_scan import scan_workbook

MACRO_DIR_MACOS = "~/Library/Application Support/LibreOffice/4/user/basic/Standard"
MACRO_DIR_LINUX = "~/.config/libreoffice/4/user/basic/Standard"
MACRO_FILENAME = "Module1.xba"

RECALCULATE_MACRO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub RecalculateAndSave()
      ThisComponent.calculateAll()
      ThisComponent.store()
      ThisComponent.close(True)
    End Sub
</script:module>"""


def has_gtimeout():
    try:
        subprocess.run(
            ["gtimeout", "--version"], capture_output=True, timeout=1, check=False
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def setup_libreoffice_macro():
    from office.soffice import get_soffice_env

    macro_dir = os.path.expanduser(
        MACRO_DIR_MACOS if platform.system() == "Darwin" else MACRO_DIR_LINUX
    )
    macro_file = os.path.join(macro_dir, MACRO_FILENAME)

    if (
        os.path.exists(macro_file)
        and "RecalculateAndSave" in Path(macro_file).read_text()
    ):
        return True

    if not os.path.exists(macro_dir):
        subprocess.run(
            ["soffice", "--headless", "--terminate_after_init"],
            capture_output=True,
            timeout=10,
            env=get_soffice_env(),
        )
        os.makedirs(macro_dir, exist_ok=True)

    try:
        Path(macro_file).write_text(RECALCULATE_MACRO)
        return True
    except Exception:
        return False


def recalc(filename, timeout=30):
    """Select the native calculation backend for the current operating system."""

    if platform.system() == "Windows":
        from office.excel_com import recalc_with_excel

        return recalc_with_excel(filename, timeout)
    return recalc_with_libreoffice(filename, timeout)


def recalc_with_libreoffice(filename, timeout=30):
    from office.soffice import get_soffice_env

    if not Path(filename).exists():
        return {"backend": "libreoffice", "error": f"File {filename} does not exist"}

    if shutil.which("soffice") is None:
        return {
            "backend": "libreoffice",
            "error": "LibreOffice soffice was not found on PATH",
        }

    abs_path = str(Path(filename).absolute())

    if not setup_libreoffice_macro():
        return {"backend": "libreoffice", "error": "Failed to setup LibreOffice macro"}

    cmd = [
        "soffice",
        "--headless",
        "--norestore",
        "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application",
        abs_path,
    ]

    if platform.system() == "Linux":
        cmd = ["timeout", str(timeout)] + cmd
    elif platform.system() == "Darwin" and has_gtimeout():
        cmd = ["gtimeout", str(timeout)] + cmd

    result = subprocess.run(cmd, capture_output=True, text=True, env=get_soffice_env())

    if result.returncode != 0 and result.returncode != 124:
        error_msg = result.stderr or "Unknown error during recalculation"
        if "Module1" in error_msg or "RecalculateAndSave" not in error_msg:
            return {
                "backend": "libreoffice",
                "error": "LibreOffice macro not configured properly",
            }
        return {"backend": "libreoffice", "error": error_msg}

    try:
        result = scan_workbook(filename)
        result["backend"] = "libreoffice"
        return result

    except Exception as e:
        return {"backend": "libreoffice", "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print("Usage: python recalc.py <excel_file> [timeout_seconds]")
        print("\nRecalculates formulas with Excel COM on Windows and LibreOffice elsewhere")
        print("\nReturns JSON with error details:")
        print("  - status: 'success' or 'errors_found'")
        print("  - total_errors: Total number of Excel errors found")
        print("  - total_formulas: Number of formulas in the file")
        print("  - error_summary: Breakdown by error type with locations")
        print("    - #VALUE!, #DIV/0!, #REF!, #NAME?, #NULL!, #NUM!, #N/A")
        sys.exit(1)

    filename = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    result = recalc(filename, timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
