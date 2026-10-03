"""Resume tailoring: rewrite resume bullets to fit a JD.

Live mode: the LLM rewrites the bullets it can honestly strengthen for the JD
(reframing and emphasis only — never new experience, tools or metrics).
Demo mode can't rewrite prose, so it returns bullets unchanged, tagged with
the JD skills each one already shows, for the user to edit by hand.
Output is a before/after list the user reviews before downloading.
"""
import json
import re

from .llm import get_chat_model, is_demo_mode
from .skills import find_skills

MAX_BULLETS = 8
BULLET_RE = r"^([•●◦○■▪‣\-\*]|\d+[.)])\s+"


def _split_bullets(resume_text: str, limit: int | None = MAX_BULLETS) -> list[str]:
    bullets = []
    current = None  # bullet being built; wrapped lines are joined onto it
    for line in resume_text.splitlines():
        s = line.strip()
        if re.match(BULLET_RE, s):
            if current and len(current) > 25:
                bullets.append(current)
            current = re.sub(BULLET_RE, "", s)
        # Wrapped line: indented (markdown/txt), or — as PDF text has no
        # indentation — any non-heading line while the bullet is unfinished.
        elif current is not None and s and (
            line[:1].isspace()
            or (not s.isupper() and not current.rstrip().endswith((".", "!", "?")))
        ):
            current += " " + s
        else:
            if current and len(current) > 25:
                bullets.append(current)
            current = None
    if current and len(current) > 25:
        bullets.append(current)
    # Fallback: long sentences if no bullet formatting found.
    if len(bullets) < 3:
        for s in re.split(r"(?<=[.!])\s+", resume_text):
            s = s.strip()
            if len(s) > 60 and not s.startswith("#"):
                bullets.append(s)
            if limit and len(bullets) >= limit:
                break
    return bullets[:limit] if limit else bullets


MAX_TAILOR = 80  # bullets sent to the LLM in one call


def _relevant(bullet: str, jd_skills: list[str]) -> list[str]:
    have = set(find_skills(bullet))
    return [s for s in jd_skills if s in have]


def _unchanged(bullets: list[str], jd_skills: list[str]) -> list[dict]:
    return [{"original": b, "tailored": b, "changed": False,
             "relevant_skills": _relevant(b, jd_skills)} for b in bullets]


_TAILOR_PROMPT = """You are an expert resume writer tailoring a resume to one job.
Rewrite ONLY the bullets that can be honestly strengthened for this job.

Hard rules:
- Never invent experience, employers, tools, technologies, numbers or results.
  A bullet may name a job keyword ONLY if the original bullet already describes
  that work (e.g. "built REST services" may become "built REST APIs").
- Keep every metric and fact from the original. Keep the same tense.
- Start with a strong action verb; lead with what matters most to this job.
- One sentence, at most ~35 words. No first person.
- If a bullet is unrelated to the job or already strong, leave it out.

Job title: {title}
Job's key skills (most important first): {keywords}
Job responsibilities / requirements:
\"\"\"{jd}\"\"\"

Resume bullets (id: text):
{bullets}

Reply with JSON only:
{{"edits": [{{"id": <id>, "tailored": "<rewritten bullet>", "why": "<few words>"}}]}}"""


def tailor_live(jd: dict, bullets: list[str], jd_text: str = "") -> list[dict]:
    jd_skills = jd.get("required_skills") or []
    out = _unchanged(bullets, jd_skills)
    llm = get_chat_model()
    raw = llm.invoke(_TAILOR_PROMPT.format(
        title=jd.get("title") or "(not given)",
        keywords=", ".join(jd_skills) or "(see text)",
        jd=jd_text[:5000],
        bullets="\n".join(f"{i}: {b}" for i, b in enumerate(bullets[:MAX_TAILOR])),
    )).content
    try:
        data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        for edit in data.get("edits", []):
            i = int(edit.get("id", -1))
            new = (edit.get("tailored") or "").strip()
            if 0 <= i < len(out) and new and new != out[i]["original"]:
                out[i].update(tailored=new, changed=True, why=edit.get("why", ""))
    except (ValueError, TypeError, json.JSONDecodeError, AttributeError):
        pass  # unparseable reply: everything stays unchanged
    return out


def tailor_resume(jd: dict, resume_text: str, bullets: list[str] | None = None,
                  jd_text: str = "") -> dict:
    """Return before/after bullets (demo or live)."""
    if not resume_text or not resume_text.strip():
        raise ValueError("resume_text must not be empty")
    if bullets is None:
        bullets = _split_bullets(resume_text, limit=None)
    if is_demo_mode():
        result = _unchanged(bullets, jd.get("required_skills") or [])
    else:
        result = tailor_live(jd, bullets, jd_text)
    return {
        "bullets": result,
        "changed_count": sum(1 for b in result if b["changed"]),
        "demo_mode": is_demo_mode(),
    }
