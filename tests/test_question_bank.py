import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from copilot.question_bank import BEHAVIORAL, TECHNICAL, common_questions, full_bank
from copilot.skills import SKILL_VARIANTS


def test_every_bank_skill_is_detectable():
    # A bank entry is only reachable if find_skills can produce that name.
    canonical = set(SKILL_VARIANTS.values()) | {"Go"}
    assert set(TECHNICAL) <= canonical, set(TECHNICAL) - canonical


def test_common_questions_follow_skill_order_and_skip_unknown():
    out = common_questions(["SQL", "Nonexistent", "C#", "SQL"], per_skill=2)
    assert [t["skill"] for t in out["technical"]] == ["SQL", "C#"]
    assert all(len(t["questions"]) == 2 for t in out["technical"])
    assert out["behavioral"] == BEHAVIORAL


def test_full_bank_has_everything():
    assert len(full_bank()["technical"]) == len(TECHNICAL)
