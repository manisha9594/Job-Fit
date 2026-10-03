import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from copilot.interview import generate_questions, score_mock_answer
from copilot.jd_intake import extract_jd

REPO = Path(__file__).resolve().parent.parent
JD1 = (REPO / "sample_data" / "sample_jd_1.txt").read_text()
PROFILE = (REPO / "sample_data" / "sample_profile.md").read_text()

GOOD_ANSWER = (
    "At Example Insurance Co I built a RAG support copilot with LangGraph agents, "
    "FastAPI, and pgvector. First I chunked 40k support docs and tuned embeddings, "
    "then I added a prompt evaluation harness. The result was a 35% drop in average "
    "ticket resolution time and hallucinations fell from 12% to 3%."
)
POOR_ANSWER = "I am good at AI stuff."


def test_questions_generated():
    jd = extract_jd(JD1)
    result = generate_questions(jd, PROFILE, n=6)
    assert len(result["questions"]) == 6
    assert all(isinstance(q, str) and q for q in result["questions"])


def test_good_answer_scores_higher():
    jd = extract_jd(JD1)
    q = "Tell me about a RAG system you built."
    good = score_mock_answer(q, GOOD_ANSWER, jd)
    poor = score_mock_answer(q, POOR_ANSWER, jd)
    assert good["score"] > poor["score"]
    assert good["feedback"], "expected feedback items"


def test_empty_answer_raises():
    with pytest.raises(ValueError):
        score_mock_answer("Q?", "   ", extract_jd(JD1))
