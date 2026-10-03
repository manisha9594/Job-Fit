import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from copilot.fit import score_fit
from copilot.jd_intake import extract_jd

REPO = Path(__file__).resolve().parent.parent
JD1 = (REPO / "sample_data" / "sample_jd_1.txt").read_text()
PROFILE = (REPO / "sample_data" / "sample_profile.md").read_text()


def test_fit_score_range_and_verdict():
    jd = extract_jd(JD1)
    fit = score_fit(jd, PROFILE)
    assert 0 <= fit["score"] <= 100
    assert fit["verdict"] in ("strong fit", "good fit", "stretch", "weak fit")
    # Alex Morgan's profile matches this JD well
    assert fit["score"] >= 50


def test_matched_and_gaps_partition():
    jd = extract_jd(JD1)
    fit = score_fit(jd, PROFILE)
    assert "Python" in fit["matched_skills"]
    assert set(fit["matched_skills"]).isdisjoint(set(fit["gap_skills"]))
    assert len(fit["matched_skills"]) + len(fit["gap_skills"]) == fit["jd_skill_count"]


def test_weak_profile_scores_lower():
    jd = extract_jd(JD1)
    weak = "I am a junior accountant. I know Excel and bookkeeping."
    assert score_fit(jd, weak)["score"] < score_fit(jd, PROFILE)["score"]


def test_empty_resume_raises():
    with pytest.raises(ValueError):
        score_fit(extract_jd(JD1), "  ")
