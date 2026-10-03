"""Outreach drafts: LinkedIn connection note + follow-up message.

Demo mode fills proven templates with the JD + fit summary. Live mode asks
the LLM to personalize, keeping the same tight structure. Nothing is ever
sent by the app — drafts are for the user to review and send.
"""
import json

from .llm import get_chat_model, is_demo_mode

# The recipient is unknown, so drafts greet a placeholder the user fills in.
GREETING = "Hi [Name],"
MAX_NOTE = 300  # LinkedIn connection-note limit


def _role_phrase(jd: dict) -> str:
    role = f"the {jd['title']} role" if jd.get("title") else "your open role"
    return f"{role} at {jd['company']}" if jd.get("company") else role


def _intro(identity: dict) -> str:
    headline = identity.get("headline") or "software engineer"
    years = identity.get("years")
    article = "an" if headline[:1].lower() in "aeiou" else "a"
    return f"{article} {headline}" + (f" with {years}+ years of experience" if years else "")


def _note(text: str) -> str:
    return text if len(text) <= MAX_NOTE else text[:MAX_NOTE - 1].rsplit(" ", 1)[0] + "…"


def outreach_demo(jd: dict, fit: dict, identity: dict) -> dict:
    skills = (fit.get("matched_skills") or [])[:3]
    skill_text = ", ".join(skills)
    sign = (identity.get("name") or "").split(" ")[0]

    connection_note = _note(
        f"{GREETING} I came across {_role_phrase(jd)} and it lines up well with "
        f"my background — I'm {_intro(identity)}"
        + (f", working hands-on with {skill_text}" if skills else "")
        + ". Would love to connect."
    )
    followup = (
        f"{GREETING} thanks for connecting! I've applied for {_role_phrase(jd)}. "
        + (f"My recent work centres on {skill_text}, which maps closely to what the "
           f"role describes. " if skills else "")
        + "If you're open to it, I'd appreciate a quick chat about the team and what "
          "success looks like in the role."
        + (f"\n\nThanks,\n{sign}" if sign else "")
    )
    return {
        "connection_note": connection_note,
        "connection_note_chars": len(connection_note),
        "followup_message": followup,
        "angle": f"lead with {skill_text}" if skills else "no strong skill overlap found",
    }


_OUTREACH_PROMPT = """Write two short LinkedIn outreach drafts from a job seeker to someone
at the hiring company (a recruiter or engineer — name unknown).
Rules:
- Start both with exactly "{greeting}" (the user fills in the name).
- Use ONLY facts from the candidate summary below. Never invent employers,
  metrics, years, or skills.
- connection_note: under 280 characters, names the role (and company if known).
- followup_message: warm, 3-4 sentences, specific to the role's needs; no
  visa or location talk; sign off with the candidate's first name.
- Plain, professional tone; no buzzwords or exclamation-mark overload.
Reply with JSON only: {{"connection_note": "...", "followup_message": "...", "angle": "<one line: what to lead with>"}}.

Candidate: {name}, {intro}
Candidate's skills that match the job: {skills}
Role: {role}
Job's top skills: {jd_skills}
Resume excerpt:
\"\"\"{resume}\"\"\"
"""


def outreach_live(jd: dict, fit: dict, identity: dict, resume_text: str = "") -> dict:
    llm = get_chat_model()
    raw = llm.invoke(_OUTREACH_PROMPT.format(
        greeting=GREETING,
        name=identity.get("name") or "the candidate",
        intro=_intro(identity),
        skills=", ".join((fit.get("matched_skills") or [])[:5]) or "none",
        role=_role_phrase(jd),
        jd_skills=", ".join((jd.get("required_skills") or [])[:8]),
        resume=resume_text[:2500],
    )).content
    try:
        data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        note = _note(data.get("connection_note", ""))
        if not note:
            raise ValueError("empty note")
        return {
            "connection_note": note,
            "connection_note_chars": len(note),
            "followup_message": data.get("followup_message", ""),
            "angle": data.get("angle", ""),
        }
    except (ValueError, json.JSONDecodeError):
        return outreach_demo(jd, fit, identity)


def draft_outreach(jd: dict, fit: dict, identity: dict | None = None,
                   resume_text: str = "") -> dict:
    """Draft outreach copy (demo or live). Never sends anything."""
    identity = identity or {}
    if is_demo_mode():
        result = outreach_demo(jd, fit, identity)
    else:
        result = outreach_live(jd, fit, identity, resume_text)
    result["demo_mode"] = is_demo_mode()
    return result
