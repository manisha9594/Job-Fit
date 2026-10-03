"""The copilot pipeline: a LangGraph StateGraph orchestrating the agents.

    jd_text ──▶ intake ──▶ fit ──▶ tailor ──▶ outreach ──▶ done
                  │          │
                  │          └─ resume_text (loaded once, shared)
                  └─ extracted JD dict (title, company, skills, visa language…)

Each node is one specialist agent; state carries the handoffs. run_pipeline
also attaches ranked top skills and interview questions. Mock Q&A is a separate entry point (same LLM dispatch, demo-or-live).
"""
from typing import TypedDict

from langgraph.graph import END, StateGraph

from . import fit as fit_mod
from . import interview as interview_mod
from . import jd_intake
from . import outreach as outreach_mod
from . import tailor as tailor_mod
from .resume import load_resume_text, resume_bullets, resume_identity
from .question_bank import common_questions
from .skills import find_skills, rank_skills

TOP_SKILLS = 8


class CopilotState(TypedDict, total=False):
    jd_text: str
    jd: dict
    resume_text: str
    resume_source: str
    fit: dict
    tailored: dict
    outreach: dict


def _node_intake(state: CopilotState) -> dict:
    return {"jd": jd_intake.extract_jd(state["jd_text"])}


def _node_fit(state: CopilotState) -> dict:
    return {"fit": fit_mod.score_fit(state["jd"], state["resume_text"])}


def _node_tailor(state: CopilotState) -> dict:
    bullets = resume_bullets(state["resume_text"], state.get("resume_source", ""))
    return {"tailored": tailor_mod.tailor_resume(
        state["jd"], state["resume_text"], bullets=bullets, jd_text=state["jd_text"])}


def _node_outreach(state: CopilotState) -> dict:
    return {"outreach": outreach_mod.draft_outreach(
        state["jd"], state["fit"],
        identity=resume_identity(state["resume_text"]),
        resume_text=state["resume_text"],
    )}


def build_pipeline():
    """Compile and return the intake → fit → tailor → outreach graph."""
    g = StateGraph(CopilotState)
    g.add_node("intake", _node_intake)
    g.add_node("fit", _node_fit)
    g.add_node("tailor", _node_tailor)
    g.add_node("outreach", _node_outreach)
    g.set_entry_point("intake")
    g.add_edge("intake", "fit")
    g.add_edge("fit", "tailor")
    g.add_edge("tailor", "outreach")
    g.add_edge("outreach", END)
    return g.compile()


def run_pipeline(jd_text: str, resume_text: str | None = None,
                 resume_source: str | None = None) -> dict:
    """Run the full pipeline. Returns the final state dict."""
    if resume_text is None:
        resume_text, resume_source = load_resume_text()
    graph = build_pipeline()
    result = graph.invoke(
        {"jd_text": jd_text, "resume_text": resume_text,
         "resume_source": resume_source or ""},
        config={"recursion_limit": 25},
    )
    result = dict(result)
    resume_skills = set(find_skills(resume_text))
    result["top_skills"] = [
        {**s, "on_resume": s["skill"] in resume_skills}
        for s in rank_skills(jd_text)[:TOP_SKILLS]
    ]
    result["interview"] = interview_mod.generate_questions(
        result["jd"], resume_text, jd_text=jd_text)
    result["common_questions"] = common_questions(
        [s["skill"] for s in result["top_skills"]] + (result["jd"].get("required_skills") or []))
    return result


def prep_interview(jd_text: str, resume_text: str | None = None, n: int = 6) -> dict:
    """Generate likely interview questions for a JD."""
    jd = jd_intake.extract_jd(jd_text)
    if resume_text is None:
        resume_text, _ = load_resume_text()
    return {"jd": jd,
            **interview_mod.generate_questions(jd, resume_text, n=n)}


def mock_interview_turn(question: str, answer: str, jd_text: str) -> dict:
    """Score one mock Q&A turn."""
    jd = jd_intake.extract_jd(jd_text)
    return interview_mod.score_mock_answer(question, answer, jd)
