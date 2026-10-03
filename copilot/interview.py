"""Interview prep: generate likely questions from JD + resume, and score a
mock Q&A turn.

Demo mode uses skill-parameterized question templates and keyword-coverage
scoring. Live mode personalizes via the LLM.
"""
import json
import re

from .llm import get_chat_model, is_demo_mode
from .skills import find_skills

_QUESTION_TEMPLATES = [
    "Walk me through a project where you used {skill}. What was your role and what was the outcome?",
    "Tell me about a time you debugged a hard production issue involving {skill}. What was your process?",
    "What best practices do you follow when working with {skill}, and why?",
    "What's the trickiest tradeoff you've faced with {skill}, and how did you decide?",
    "How would you explain your {skill} work to a non-technical stakeholder?",
]
_GAP_TEMPLATE = ("This role uses {skill}, which isn't on your resume. How would you get "
                 "up to speed, and what related experience can you draw on?")
_RESPONSIBILITY_TEMPLATE = ('The role involves: "{resp}" Tell me about a time you did '
                            "something similar.")
# Lines that read like duties: start with an action verb, long enough to quote.
_RESP_RE = re.compile(
    r"^(?:[-•●*]\s*)?(implement|analy[sz]e|support|develop|build|design|work|participate|"
    r"write|assist|research|lead|own|collaborate|maintain|deliver|drive|manage|create|"
    r"partner|mentor|deploy|integrate|optimi[sz]e|improve)\w*\b.{30,}",
    re.I,
)


def _responsibilities(jd_text: str) -> list[str]:
    out = []
    for line in jd_text.splitlines():
        line = line.strip()
        if _RESP_RE.match(line):
            first = re.split(r"(?<=[.;])\s|,\s+including\s", line.lstrip("-•●* "))[0]
            # Only trim at ", and" when the duty is long — a short line's
            # ", and" is usually a list ("Python, FastAPI, and LangGraph").
            if len(first) > 110 and ", and " in first[40:]:
                first = first[:40] + first[40:].split(", and ", 1)[0]
            out.append(first.rstrip(" ,;") + ("" if first.endswith(".") else "."))
    return out


def _fallback_questions(jd: dict, resume_text: str, n: int = 8,
                        jd_text: str = "") -> list[str]:
    jd_skills = jd.get("required_skills") or []
    resume_skills = set(find_skills(resume_text))
    have = [s for s in jd_skills if s in resume_skills][:3] or find_skills(resume_text)[:3]
    gaps = [s for s in jd_skills if s not in resume_skills][:2]
    role = f"the {jd['title']} role" if jd.get("title") else "this role"

    questions = [f"Tell me about yourself and why you're interested in {role}."]
    questions += [_QUESTION_TEMPLATES[i % len(_QUESTION_TEMPLATES)].format(skill=s)
                  for i, s in enumerate(have)]
    questions += [_GAP_TEMPLATE.format(skill=s) for s in gaps]
    questions += [_RESPONSIBILITY_TEMPLATE.format(resp=r) for r in _responsibilities(jd_text)]
    return questions[:n]


def generate_questions(jd: dict, resume_text: str, n: int = 8,
                       jd_text: str = "") -> dict:
    """Generate likely interview questions (demo or live)."""
    if is_demo_mode():
        questions = _fallback_questions(jd, resume_text, n, jd_text)
    else:
        llm = get_chat_model()
        raw = llm.invoke(
            "Generate {n} likely interview questions for this candidate and role. "
            "Reply with JSON only: {{\"questions\": [...]}}.\n\nRole: {t} at {c}. "
            "Required skills: {s}.\n\nResume:\n\"\"\"{r}\"\"\"".format(
                n=n, t=jd.get("title", ""), c=jd.get("company", ""),
                s=", ".join(jd.get("required_skills") or []),
                r=resume_text[:4000],
            )
        ).content
        try:
            questions = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])["questions"][:n]
        except (ValueError, json.JSONDecodeError, KeyError):
            questions = _fallback_questions(jd, resume_text, n, jd_text)
    return {"questions": questions, "demo_mode": is_demo_mode()}


def score_mock_answer_demo(question: str, answer: str, jd: dict) -> dict:
    """Keyword-coverage heuristic: does the answer touch the JD's skills?"""
    jd_skills = jd.get("required_skills") or []
    q_skills = set(find_skills(question))
    a_skills = set(find_skills(answer))
    hit = sorted(q_skills & a_skills)
    relevant = sorted((q_skills | set(jd_skills[:4])) & a_skills)
    words = len(answer.split())
    structure = bool(re.search(r"\b(first|then|finally|result|outcome|impact)\b", answer, re.I))

    score = 0
    feedback = []
    if relevant:
        score += 40
        feedback.append(f"Good — you referenced: {', '.join(relevant[:4])}.")
    else:
        feedback.append("Try naming the specific tools/skills from the job description.")
    if words >= 60:
        score += 30
    elif words >= 25:
        score += 15
        feedback.append("A bit short — aim for 60+ words with a concrete example.")
    else:
        feedback.append("Too short — use the STAR format: situation, task, action, result.")
    if structure:
        score += 20
    else:
        feedback.append("Add structure: walk through what you did, then the outcome/impact.")
    if re.search(r"\b\d+\b", answer):
        score += 10
        feedback.append("Nice — quantified details strengthen an answer.")
    return {
        "score": min(100, score),
        "skills_mentioned": hit,
        "word_count": words,
        "feedback": feedback,
    }


_MOCK_PROMPT = """You are an interview coach. Score this mock interview answer 0-100
and give 2-3 sentences of concrete feedback. Reply with JSON only:
{{"score": <int>, "feedback": ["..."], "skills_mentioned": [...]}}.

Question: {q}
Job skills: {s}
Answer: \"\"\"{a}\"\"\""""


def score_mock_answer(question: str, answer: str, jd: dict) -> dict:
    """Score one mock Q&A turn (demo or live)."""
    if not answer or not answer.strip():
        raise ValueError("answer must not be empty")
    if is_demo_mode():
        result = score_mock_answer_demo(question, answer, jd)
    else:
        llm = get_chat_model()
        raw = llm.invoke(_MOCK_PROMPT.format(
            q=question, s=", ".join(jd.get("required_skills") or []),
            a=answer[:2000],
        )).content
        try:
            result = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        except (ValueError, json.JSONDecodeError):
            result = score_mock_answer_demo(question, answer, jd)
    result["demo_mode"] = is_demo_mode()
    return result
