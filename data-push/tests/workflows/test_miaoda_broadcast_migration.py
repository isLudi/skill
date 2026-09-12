from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_miaoda_broadcast_runbook_has_required_safety_gates():
    text = (ROOT / "references" / "workflows" / "miaoda-broadcast-migration.md").read_text(encoding="utf-8")
    required = [
        "DELIVERY_MODE=dry-run",
        "不存在的幂等键",
        "不降级成纯文本姓名",
        "skipped-in-test-chat",
        "禁止盲目重发",
        "只允许服务端角色",
        "一次点击只创建一个 run_id",
        "blocked_before_real_delivery",
    ]
    assert all(item in text for item in required)


def test_skill_routes_full_stack_broadcast_separately_from_static_dashboard():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "references/workflows/miaoda.md" in skill
    assert "references/workflows/miaoda-broadcast-migration.md" in skill
