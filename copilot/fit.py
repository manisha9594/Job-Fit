"""Fit scoring: score a JD against the resume.

Demo mode: deterministic skill-overlap scoring. Live mode: the LLM grades the
match and must return JSON; demo heuristics fill any gaps.
"""
import json
import re

from .llm import get_chat_model, is_demo_mode
from .skills import SKILL_PRIORITY, find_skills

MIN_SKILLS_FOR_VERDICT = 3


def _years_mentioned(text: str, skill: str) -> int | None:
    esc = re.escape(skill)
    # e.g. "5+ years ... Python" or "Python ... 5 years"
    pat1 = r"(\d+)\+?\s*(?:years?|yrs?)[^.]{0,80}?" + esc
    pat2 = esc + r"[^.]{0,80}?(\d+)\+?\s*(?:years?|yrs?)"
    m = re.search(pat1, text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(pat2, text, re.I)
    return int(m.group(1)) if m else None


def score_demo(jd: dict, resume_text: str) -> dict:
    jd_skills = jd.get("required_skills") or []
    resume_skills = find_skills(resume_text)

    matched = [s for s in jd_skills if s in resume_skills]
    gaps = [s for s in jd_skills if s not in resume_skills]

    # Priority skills weigh more: each matched priority skill = 2 pts, else 1.
    points = sum(2 if s in SKILL_PRIORITY[:12] else 1 for s in matched)
    possible = sum(2 if s in SKILL_PRIORITY[:12] else 1 for s in jd_skills) or 1
    score = round(100 * points / possible)

    detail = []
    for s in jd_skills:
        detail.append({
            "skill": s,
            "matched": s in resume_skills,
            "jd_years": _years_mentioned(json.dumps(jd), s),
        })

    # A 1-for-1 skill match isn't a "strong fit" — too little signal to judge.
    verdict = (
        "not enough skills in posting to judge" if len(jd_skills) < MIN_SKILLS_FOR_VERDICT else
        "strong fit" if score >= 75 else
        "good fit" if score >= 50 else
        "stretch" if score >= 30 else "weak fit"
    )
    return {
        "score": score,
        "verdict": verdict,
        "matched_skills": matched,
        "gap_skills": gaps,
        "skill_detail": detail,
        "jd_skill_count": len(jd_skills),
    }


_FIT_PROMPT = """Score how well this candidate fits the job. Reply with JSON only,
keys: score (0-100 integer), verdict (one of: strong fit, good fit, stretch,
weak fit), matched_skills (array), gap_skills (array), rationale (1-2 sentences).

Job required skills: {jd_skills}
Job title: {title} at {company}

Candidate resume:
\"\"\"{resume}\"\"\""""


def score_live(jd: dict, resume_text: str) -> dict:
    llm = get_chat_model()
    raw = llm.invoke(_FIT_PROMPT.format(
        jd_skills=", ".join(jd.get("required_skills") or []),
        title=jd.get("title", ""),
        company=jd.get("company", ""),
        resume=resume_text[:6000],
    )).content
    try:
        data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        data["score"] = max(0, min(100, int(data.get("score", 0))))
        return data
    except (ValueError, json.JSONDecodeError, KeyError, TypeError):
        return score_demo(jd, resume_text)


def score_fit(jd: dict, resume_text: str) -> dict:
    """Score a JD dict against resume text (demo or live)."""
    if not resume_text or not resume_text.strip():
        raise ValueError("resume_text must not be empty")
    result = score_live(jd, resume_text) if not is_demo_mode() else score_demo(jd, resume_text)
    result["demo_mode"] = is_demo_mode()
    return result
