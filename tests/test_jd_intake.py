import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from copilot.jd_intake import extract_jd

REPO = Path(__file__).resolve().parent.parent
JD1 = (REPO / "sample_data" / "sample_jd_1.txt").read_text()
JD2 = (REPO / "sample_data" / "sample_jd_2.txt").read_text()


def test_extract_title_company_salary_jd1():
    jd = extract_jd(JD1)
    assert "Senior AI Engineer" in jd["title"]
    assert jd["company"] == "Northwind Labs"
    assert "$170,000" in jd["salary"] and "$220,000" in jd["salary"]


def test_extract_skills_jd1():
    jd = extract_jd(JD1)
    for skill in ("Python", "FastAPI", "LangChain", "LangGraph", "RAG",
                  "Agentic AI", "Multi-Agent Systems", "AWS", "Docker",
                  "React", "TypeScript"):
        assert skill in jd["required_skills"], f"missing {skill}"


def test_visa_language_quoted_verbatim_jd1():
    jd = extract_jd(JD1)
    assert jd["visa_language"], "expected visa language in JD1"
    joined = " ".join(jd["visa_language"])
    assert "unable to sponsor" in joined
    assert "authorized to work in the United States" in joined


def test_no_visa_language_jd2():
    jd = extract_jd(JD2)
    assert jd["visa_language"] == []
    assert "Fabrikam Health" in jd["company"]
    assert jd["work_type"] == "remote"


def test_empty_jd_raises():
    with pytest.raises(ValueError):
        extract_jd("   ")


def test_demo_mode_flag_present():
    assert extract_jd(JD1)["demo_mode"] is True  # no API key in test env
