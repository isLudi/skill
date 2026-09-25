from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "deliver_query_result.py"
SPEC = spec_from_file_location("deliver_query_result", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_csv_identifier_columns_stay_text(tmp_path):
    source = tmp_path / "result.csv"
    source.write_text(
        "订单号,用户编号,业务线,归属人ID,收款金额\n"
        "426972749136140264,7501113837,7,285063,3.00\n",
        encoding="utf-8-sig",
    )

    frame = MODULE.read_table(source)

    for column in ("订单号", "用户编号", "业务线", "归属人ID"):
        assert MODULE.dtype_name(frame[column]) == "object"
    assert frame.loc[0, "订单号"] == "426972749136140264"
    assert MODULE.dtype_name(frame["收款金额"]) == "float64"


def test_non_midnight_transaction_time_stays_text(tmp_path):
    source = tmp_path / "result.csv"
    source.write_text("交易时间,交易流水日\n2026-04-04 04:09:12,2026-04-04\n", encoding="utf-8-sig")

    sheet = MODULE.frame_to_sheet(MODULE.read_table(source), "业绩明细")

    assert sheet["dtypes"]["交易时间"] == "object"
    assert sheet["data"][0][0] == "2026-04-04 04:09:12"
    assert sheet["dtypes"]["交易流水日"] == "object"
