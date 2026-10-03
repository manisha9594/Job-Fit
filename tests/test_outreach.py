import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from copilot.fit import score_fit
from copilot.jd_intake import extract_jd
from copilot.outreach import draft_outreach

REPO = Path(__file__).resolve().parent.parent
JD1 = (REPO / "sample_data" / "sample_jd_1.txt").read_text()
PROFILE = (REPO / "sample_data" / "sample_profile.md").read_text()


IDENTITY = {"name": "Alex Morgan", "headline": "Senior Python AI Engineer", "years": 10}


def test_connection_note_length_and_content():
    jd = extract_jd(JD1)
    fit = score_fit(jd, PROFILE)
    out = draft_outreach(jd, fit, identity=IDENTITY)
    assert out["connection_note_chars"] <= 300
    assert "Northwind Labs" in out["connection_note"]
    # Greets the recipient (placeholder), never the candidate themselves.
    assert out["connection_note"].startswith("Hi [Name],")
    assert "Alex" not in out["connection_note"]
    assert out["followup_message"].rstrip().endswith("Alex")


def test_outreach_uses_resume_identity_not_hardcoded_persona():
    jd = extract_jd(JD1)
    fit = score_fit(jd, PROFILE)
    ident = {"name": "Sam Lee", "headline": "Full Stack Engineer", "years": 8}
    note = draft_outreach(jd, fit, identity=ident)["connection_note"]
    assert "Full Stack Engineer with 8+ years" in note
    assert "Python AI" not in note


def test_partial_jd_wording():
    out = draft_outreach({"title": "", "company": ""}, {"matched_skills": []}, identity={})
    assert "the  role" not in out["connection_note"]
    assert "this role role" not in out["connection_note"]


def test_followup_has_no_location_or_visa_talk():
    jd = extract_jd(JD1)
    fit = score_fit(jd, PROFILE)
    out = draft_outreach(jd, fit, identity=IDENTITY)
    msg = out["followup_message"].lower()
    assert "visa" not in msg and "sponsorship" not in msg
    assert out["followup_message"]
