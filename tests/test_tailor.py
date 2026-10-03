import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from copilot.jd_intake import extract_jd
from copilot.tailor import tailor_resume

REPO = Path(__file__).resolve().parent.parent
JD1 = (REPO / "sample_data" / "sample_jd_1.txt").read_text()
PROFILE = (REPO / "sample_data" / "sample_profile.md").read_text()


def test_tailor_returns_before_after():
    result = tailor_resume(extract_jd(JD1), PROFILE)
    assert result["bullets"], "expected bullets"
    for b in result["bullets"]:
        assert b["original"] and b["tailored"]
        assert isinstance(b["changed"], bool)


def test_demo_never_stuffs_keywords():
    result = tailor_resume(extract_jd(JD1), PROFILE)
    assert result["changed_count"] == 0
    assert all("leveraging" not in b["tailored"] for b in result["bullets"])
    # Each bullet is tagged with the JD skills it already shows.
    assert any(b["relevant_skills"] for b in result["bullets"])


def test_live_applies_only_valid_edits(monkeypatch):
    from types import SimpleNamespace

    from copilot import tailor

    reply = ('{"edits": [{"id": 0, "tailored": "Built a RAG support copilot.", "why": "x"},'
             ' {"id": 999, "tailored": "out of range"}, {"id": 1, "tailored": ""}]}')
    fake = SimpleNamespace(invoke=lambda prompt: SimpleNamespace(content=reply))
    monkeypatch.setattr(tailor, "is_demo_mode", lambda: False)
    monkeypatch.setattr(tailor, "get_chat_model", lambda: fake)

    result = tailor_resume(extract_jd(JD1), PROFILE, bullets=["a b c", "d e f"])
    assert result["changed_count"] == 1
    assert result["bullets"][0]["tailored"] == "Built a RAG support copilot."
    assert result["bullets"][1]["changed"] is False


def test_empty_resume_raises():
    with pytest.raises(ValueError):
        tailor_resume(extract_jd(JD1), "")
