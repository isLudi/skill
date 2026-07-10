"""Windows formula recalculation through the installed Microsoft Excel COM API."""

from __future__ import annotations

import gc
import time
from pathlib import Path
from typing import Any

from office.workbook_scan import scan_workbook


def recalc_with_excel(filename: str | Path, timeout: int = 30) -> dict[str, Any]:
    """Open, fully recalculate, save, and scan one workbook with Excel COM."""

    path = Path(filename).resolve()
    if not path.exists():
        return {"backend": "excel_com", "error": f"File {path} does not exist"}

    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        return {
            "backend": "excel_com",
            "error": (
                "Windows Excel recalculation requires pywin32. "
                "Run this skill with D:\\anaconda3\\python.exe or install pywin32 "
                "into the selected Python environment."
            ),
            "detail": str(exc),
        }

    excel = None
    workbook = None
    excel_version = None
    started = time.monotonic()
    pythoncom.CoInitialize()
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.AskToUpdateLinks = False
        excel.EnableEvents = False
        try:
            excel.AutomationSecurity = 3
        except Exception:
            pass

        try:
            workbook = excel.Workbooks.Open(str(path), 0, False)
        except Exception as exc:
            return {
                "backend": "excel_com",
                "error": (
                    "Excel COM could not open the workbook. Excel COM is available, "
                    "so inspect workbook structure, table/filter overlap, file locks, "
                    "or corruption before treating this as a missing dependency."
                ),
                "detail": str(exc),
            }

        excel_version = str(excel.Version)
        excel.Calculation = -4105
        excel.CalculateBeforeSave = True
        calculation_started = time.monotonic()
        excel.CalculateFullRebuild()
        # Some Excel builds report xlPending (2) after a synchronous full
        # rebuild even though cached values are already updated. Only
        # xlCalculating (1) means calculation is actively running.
        while int(excel.CalculationState) == 1:
            if time.monotonic() - calculation_started > timeout:
                return {
                    "backend": "excel_com",
                    "excel_version": excel_version,
                    "error": f"Excel calculation did not finish within {timeout} seconds",
                }
            pythoncom.PumpWaitingMessages()
            time.sleep(0.1)

        workbook.Save()
    except Exception as exc:
        return {
            "backend": "excel_com",
            "excel_version": excel_version,
            "error": "Excel COM recalculation failed",
            "detail": str(exc),
        }
    finally:
        if workbook is not None:
            try:
                workbook.Close(SaveChanges=False)
            except Exception:
                pass
        if excel is not None:
            try:
                excel.Quit()
            except Exception:
                pass
        workbook = None
        excel = None
        gc.collect()
        pythoncom.CoUninitialize()

    result = scan_workbook(path)
    result.update(
        {
            "backend": "excel_com",
            "excel_version": excel_version,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    )
    return result
