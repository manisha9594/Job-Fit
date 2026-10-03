import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from copilot import graph as pipeline

REPO = Path(__file__).resolve().parent.parent
JD1 = (REPO / "sample_data" / "sample_jd_1.txt").read_text()
PROFILE = (REPO / "sample_data" / "sample_profile.md").read_text()


def test_full_pipeline_end_to_end():
    result = pipeline.run_pipeline(JD1, resume_text=PROFILE,
                                   resume_source="test")
    for key in ("jd", "fit", "tailored", "outreach"):
        assert key in result, f"missing pipeline stage {key}"
    assert result["jd"]["company"] == "Northwind Labs"
    assert 0 <= result["fit"]["score"] <= 100
    assert result["tailored"]["bullets"]
    assert result["outreach"]["connection_note_chars"] <= 300


def test_prep_interview_entrypoint():
    result = pipeline.prep_interview(JD1, resume_text=PROFILE, n=4)
    assert len(result["questions"]) == 4
    assert result["jd"]["title"]


def test_mock_interview_entrypoint():
    result = pipeline.mock_interview_turn(
        "Tell me about a RAG system you built.",
        "I built a LangGraph RAG copilot with FastAPI and pgvector; "
        "first I tuned chunking, then evals; hallucinations fell from 12% to 3%.",
        JD1)
    assert result["score"] > 50
