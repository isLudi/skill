"""Stable paths independent of compatibility entrypoint location."""
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = SKILL_ROOT.parent
WORKSPACE_ROOT = SKILLS_ROOT.parent
CONFIG_ROOT = SKILL_ROOT / "config"
