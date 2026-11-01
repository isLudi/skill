"""An empty book conversion report needs a complete same-revision source proof."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_qingcheng_process_source as source
import preview_qingcheng_transformation as preview
import run_qingcheng_transformation as runner

PERIOD = "20261023期"


def fake_export(monkeypatch, *, witness_rev=42, witness_period=PERIOD, complete=True):
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        output = Path(args[args.index("--output") + 1])
        conditions = json.loads(args[args.index("--filter-json") + 1])["conditions"]
        witness = conditions == [["期次", "==", PERIOD]]
        rows = ([{"record_id": "rec_witness", "记录键": "key", "期次": witness_period,
                  "分区日期": "20261024", "分区小时": "12"}] if witness else [])
        output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        manifest = {"base_token": source.BASE_TOKEN, "table_id": source.TABLE_ID,
                    "records_count": len(rows), "rev": witness_rev if witness else 42,
                    "has_more": False if witness else not complete}
        output.with_suffix(".manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return "{}"
    monkeypatch.setattr(source, "run_lark", run)
    return calls


def test_empty_books_use_current_period_witness_at_same_revision(monkeypatch, tmp_path):
    calls = fake_export(monkeypatch)
    manifest = source.fetch("partner_books", PERIOD, tmp_path / "source.ndjson", allow_empty=True)
    assert manifest["empty_scope_verified"] is True
    assert manifest["records_count"] == 0 and manifest["snapshot"] == ["20261024", "12"]
    assert manifest["rev"] == 42 and manifest["has_more"] is False
    assert len(calls) == 2


@pytest.mark.parametrize("kwargs", [{"witness_rev": 43}, {"witness_period": "20261016期"}, {"complete": False}])
def test_partial_changed_or_old_period_evidence_blocks(monkeypatch, tmp_path, kwargs):
    fake_export(monkeypatch, **kwargs)
    with pytest.raises(ValueError):
        source.fetch("partner_books", PERIOD, tmp_path / "source.ndjson", allow_empty=True)


@pytest.mark.parametrize("channel,options", [("partner_books", {}), ("public_pool", {"allow_empty": True})])
def test_other_process_reports_keep_strict_empty_guard(monkeypatch, tmp_path, channel, options):
    fake_export(monkeypatch)
    with pytest.raises(ValueError, match="Missing or duplicate"):
        source.fetch(channel, PERIOD, tmp_path / "source.ndjson", **options)


def test_empty_book_revision_probe_requires_opt_in(monkeypatch, tmp_path):
    fake_export(monkeypatch)
    assert source.probe_revision("partner_books", PERIOD, tmp_path / "probe.ndjson", allow_empty=True) == 42
    with pytest.raises(ValueError, match="revision probe"):
        source.probe_revision("partner_books", PERIOD, tmp_path / "strict.ndjson")


@pytest.mark.parametrize("proof,finance", [(True,False),(False,False),(True,True)])
def test_only_proven_empty_book_source_can_render_no_data(monkeypatch, tmp_path, proof, finance):
    config = json.loads(preview.DEFAULT_CONFIG.read_text(encoding="utf-8"))
    config["channels"] = [entry for entry in config["channels"] if entry["id"] == "partner_books"]
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    for name in ("process", "conversion"):
        path = tmp_path / f"{name}.ndjson"
        rows = []
        if name == "conversion" and finance:
            rows = [{"record_id":"rec_finance","记录键":f"{PERIOD}|conversion_finance_only|武汉图书|lead|user|account",
                     "期次":PERIOD,"一级渠道":"图书","渠道":"武汉图书","年级":"高一","主管":"主管甲","顾问账号":"account",
                     "分区日期":"20261024","分区小时":"12","收款":6600,"退费":0,"净收款":6600,
                     "当期收款":0,"当期退费":0,"当期净收款":0}]
        path.write_text("".join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows), encoding="utf-8")
        manifest = {"has_more": False, "records_count": 0, "rev": 42,
                    "period": PERIOD, "channel": "partner_books", "snapshot": ["20261024", "12"]}
        if name == "process" and proof:
            manifest["empty_scope_verified"] = True
        manifest['records_count'] = len(rows)
        path.with_suffix(".manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(preview, "_table_image", lambda *args, **kwargs: None)
    args = (tmp_path / "process.ndjson", tmp_path / "conversion.ndjson", tmp_path / "preview", config_path)
    if not proof:
        with pytest.raises(ValueError, match="snapshots"):
            preview.build(*args, channels=("partner_books",), period=PERIOD, levels=("consultant", "dept"))
        return
    result = preview.build(*args, channels=("partner_books",), period=PERIOD, levels=("consultant", "dept"))
    book = result["results"]["partner_books"]
    assert book["process_rows"] == 0 and book["conversion_rows"] == int(finance)
    assert all(level["rows"] == 0 for level in book["levels"].values())
    assert preview.FALLBACK_REMINDER in book["levels"]["consultant"]["message"]
    assert book["levels"]["dept"]["reminders"] == []
    assert result["process_snapshot"] == "20261024 12:00"
    assert all((tmp_path / "preview" / level["png"]).is_file() for level in book["levels"].values())
    if finance:
        assert book['levels']['consultant']['empty_source_finance_summary']['收款'] == '6600'
        assert book['join_coverage']['consultant_level']['orphan_income'] == 6600


@pytest.mark.parametrize('status,old_binding', [(6,False),(3,False),(7,False),(6,True)])
def test_empty_report_cannot_send_during_replacement_or_with_old_binding(monkeypatch,tmp_path,status,old_binding):
    from types import SimpleNamespace
    batch=runner._batch()
    upstream=batch['upstream']
    row={'id':123,'taskId':67397,'status':status,'startTime':'2026-10-24 14:01:14',
         'runConfig':json.dumps({'projectId':308,'execFileId':upstream['exec_file_id']-1 if old_binding else upstream['exec_file_id']})}
    # A queued future schedule cannot have changed the Base yet.
    future={'id':124,'taskId':67397,'status':0,'startTime':None,'dispatchTime':None}
    (tmp_path/'history.json').write_text(json.dumps({'executions':[row,future]}),encoding='utf-8')
    def run(command,**kwargs):
        assert kwargs['env']['PYTHONUTF8']=='1' and kwargs['env']['PYTHONIOENCODING']=='utf-8'
        assert command[command.index('--task-name')+1]=='qing2lark_zhuanhua'
        return SimpleNamespace(returncode=0,stdout=json.dumps({'artifact_dir':str(tmp_path)}))
    monkeypatch.setattr(runner.subprocess,'run',run)
    if status==6 and not old_binding:
        assert runner._conversion_upstream_ready(batch)==123
    else:
        with pytest.raises(ValueError,match='producer is running'):
            runner._conversion_upstream_ready(batch)
