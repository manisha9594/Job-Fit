"""JD intake: extract structured fields from a raw job posting.

Demo mode uses deterministic heuristics (regex + keyword lexicon) so the
pipeline works fully offline. Live mode asks the LLM for JSON and falls back
to heuristics for any missing field.
"""
import json
import re

from .llm import get_chat_model, is_demo_mode
from .skills import find_skills

SALARY_RE = re.compile(
    r"\$\s?[\d,]+(?:\.\d+)?\s?[Kk]?"
    r"(?:\s*(?:-|–|—|to)\s*\$?\s?[\d,]+(?:\.\d+)?\s?[Kk]?)?"
    r"(?:\s*(?:/|per)\s*(?:year|yr|hour|hr|month))?"
)
WORK_TYPE_RES = {
    "remote": re.compile(r"\bremote\b", re.I),
    "hybrid": re.compile(r"\bhybrid\b", re.I),
    "on-site": re.compile(r"\bon[-\s]?site\b|\bin[-\s]?office\b|\bin[-\s]?person\b", re.I),
}
# Sentences matching these are quoted VERBATIM — mirrors real screening work.
VISA_RE = re.compile(
    r"sponsorship|H-?1B|visa\b|OPT\b|authorized to work|work authorization|"
    r"U\.?S\.?\s*citizen|citizenship|security clearance|ITAR|public trust|"
    r"must be (?:a |an )?u\.?s\.? (?:citizen|national)",
    re.I,
)
TITLE_HINTS = ("engineer", "developer", "scientist", "architect", "manager",
               "analyst", "designer", "lead", "principal", "staff")
SECTION_HEADING_RE = re.compile(
    r"(key\s+)?(responsibilities|requirements|qualifications|what you('ll| will) do|"
    r"about (the )?(role|job|us|company)|what success looks like|benefits|"
    r"skills|duties|overview|job description)\s*:?$",
    re.I,
)
# Level words only count next to a role noun, so "nontechnical staff" or
# "senior team members" don't set seniority.
SENIORITY_RE = re.compile(
    r"\b(principal|staff|senior|sr\.?|lead|junior|jr\.?|entry[-\s]level|mid[-\s]level|graduate)"
    r"\s+(?:[\w/+#.-]+\s+){0,2}?"
    r"(engineer|developer|scientist|architect|analyst|designer|programmer|consultant|role|position)s?\b",
    re.I,
)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def extract_demo(jd_text: str) -> dict:
    """Rule-based extraction. Deterministic; no LLM needed."""
    text = jd_text.strip()
    sentences = _sentences(text)

    salary_m = SALARY_RE.search(text)
    work_types = [wt for wt, rx in WORK_TYPE_RES.items() if rx.search(text)]
    visa_quotes = [s for s in sentences if VISA_RE.search(s)]

    # Title: first non-empty line mentioning a role keyword, else first line.
    title = ""
    for line in text.splitlines()[:6]:
        line = line.strip(" -*•\t")
        if line and any(h in line.lower() for h in TITLE_HINTS) and len(line) < 120:
            title = line
            break
    if not title:
        # Fall back to the first line that isn't a section heading, e.g. when
        # only the "Key Responsibilities" part of a posting was pasted.
        for line in text.splitlines()[:6]:
            line = line.strip(" -*•\t")
            if line and not SECTION_HEADING_RE.match(line) and len(line) < 80:
                title = line
                break

    # Company: line right after the title, if it looks like a company name.
    company = ""
    lines = [ln.strip(" -*•\t") for ln in text.splitlines() if ln.strip()]
    if title in lines:
        idx = lines.index(title)
        if idx + 1 < len(lines) and len(lines[idx + 1]) < 80:
            nxt = lines[idx + 1]
            if not any(h in nxt.lower() for h in TITLE_HINTS):
                company = nxt

    return {
        "title": title,
        "company": company,
        "location": _guess_location(text),
        "work_type": work_types[0] if work_types else "unknown",
        "work_type_signals": work_types,
        "salary": salary_m.group(0).strip() if salary_m else "",
        "required_skills": find_skills(text),
        "visa_language": visa_quotes[:5],
        "seniority_hint": _seniority(text),
        "char_count": len(text),
    }


def _guess_location(text: str) -> str:
    m = re.search(
        r"\b([A-Z][a-zA-Z .'-]+,\s*[A-Z]{2})\b", text[:800]
    )
    if m:
        return m.group(1)
    if re.search(r"\bremote\b", text, re.I):
        return "Remote"
    return ""


def _seniority(text: str) -> str:
    m = SENIORITY_RE.search(text)
    if not m:
        return "unknown"
    level = re.sub(r"[-\s]+", "-", m.group(1).lower().rstrip("."))
    return {"sr": "senior", "jr": "junior", "entry-level": "entry",
            "mid-level": "mid"}.get(level, level)


_LIVE_PROMPT = """Extract structured fields from this job posting. Reply with JSON only,
using exactly these keys: title, company, location, work_type (one of
remote/hybrid/on-site/unknown), salary (string, "" if none),
required_skills (array of strings), visa_language (array — VERBATIM quotes of
any sentence about visas, sponsorship, citizenship, work authorization, or
clearances; [] if none), seniority_hint.

Job posting:
\"\"\"{jd}\"\"\""""


def extract_live(jd_text: str) -> dict:
    llm = get_chat_model()
    raw = llm.invoke(_LIVE_PROMPT.format(jd=jd_text[:8000])).content
    try:
        data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError):
        return extract_demo(jd_text)
    demo = extract_demo(jd_text)
    # Fill any gaps the LLM left with heuristic results; never invent.
    for key in ("title", "company", "location", "salary"):
        if not data.get(key):
            data[key] = demo[key]
    if not data.get("required_skills"):
        data["required_skills"] = demo["required_skills"]
    if "visa_language" not in data:
        data["visa_language"] = demo["visa_language"]
    return data


def extract_jd(jd_text: str) -> dict:
    """Extract structured fields from a job posting (demo or live)."""
    if not jd_text or not jd_text.strip():
        raise ValueError("jd_text must not be empty")
    if is_demo_mode():
        result = extract_demo(jd_text)
    else:
        result = extract_live(jd_text)
    result["demo_mode"] = is_demo_mode()
    return result
