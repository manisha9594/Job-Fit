"""JobFit — agentic job-hunting assistant.

Modules:
    llm        LLM factory (Gemini / Groq / OpenAI / offline demo stub)
    skills     shared skill lexicon for JD/resume matching
    jd_intake  extract structured fields from a job posting
    resume     load the user's resume text (local, gitignored)
    fit        score a JD against the resume
    tailor     rewrite resume bullets against JD keywords (+ diff)
    outreach   draft LinkedIn connection note + follow-up
    interview  interview question generation + mock Q&A scoring
    tracker    SQLite application tracker
    sources    read-only job-listing connectors (free APIs / public feeds)
    graph      LangGraph pipeline orchestrating intake → fit → tailor → outreach
"""
