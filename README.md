# 🎯 JobFit

An **agentic job-hunting assistant** built with **LangGraph, FastAPI, and
React** — the tool I use every morning of my job search. Paste a job posting
and a pipeline of specialist agents extracts the details, scores the fit
against my resume, tailors bullets, drafts recruiter outreach, and preps me
for interviews. A local SQLite tracker keeps every application organized.

## What it does

```
job posting text ──▶ intake ──▶ fit ──▶ tailor ──▶ outreach
                        │          │
                        │          └─ resume (local, gitignored)
                        └─ title, company, salary, skills, visa language…
```

| Agent / module | What it does |
|---|---|
| **JD intake** | Extracts title, company, location, work type, salary, required skills, and quotes visa/sponsorship/citizenship language **verbatim** |
| **Fit scoring** | Scores the JD 0–100 against the resume: matched skills, gaps, verdict |
| **Resume tailoring** | Rewrites bullets to mirror JD keywords — before/after diff, reframes only, never invents |
| **Outreach** | Drafts a LinkedIn connection note (≤300 chars) + follow-up message |
| **Interview prep** | Generates likely questions from JD + resume; scores mock answers with feedback |
| **Tracker** | SQLite-backed application log with statuses + follow-up reminders |
| **Job sources** | Pull-only listings from free APIs / public feeds (see below) |

## Quickstart

```bash
pip install -r requirements.txt

# CLI demo (works with NO api key — demo mode)
python cli.py pipeline sample_data/sample_jd_1.txt
python cli.py questions sample_data/sample_jd_2.txt
python cli.py jobs remotive --query "python ai engineer"
python cli.py track add --company "Acme" --role "Senior AI Engineer"
python cli.py track list

# API server
uvicorn app:app --reload        # → http://localhost:8000
# Frontend
cd frontend && npm install && npm run dev   # → http://localhost:5174
```

## Demo mode vs live mode

Without any API key the app runs in **demo mode**: deterministic, rule-based
analysis (regex + skill lexicon) that works fully offline — extraction,
scoring, tailoring, and mock-answer grading all function.

For live LLM answers, copy `.env.example` to `.env` and set **one** key
(checked in this order):

| Provider | Env var | Free tier |
|---|---|---|
| Google Gemini | `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| Groq | `GROQ_API_KEY` | https://console.groq.com/keys |
| OpenAI / compatible | `OPENAI_API_KEY` (+ optional `LLM_BASE_URL`) | paid |

## Your resume stays local

Set `RESUME_PATH` (or drop `resume.pdf` / `resume.txt` into `data/`).
`data/` is **gitignored** — the repo only ships a redacted sample profile
(`sample_data/sample_profile.md`), which is used automatically when no resume
is found. Never commit your real resume.

## Job sources

| Source | Auth | Notes |
|---|---|---|
| Remotive | none | remote jobs API |
| Arbeitnow | none | job board API |
| Greenhouse / Lever / Ashby | none | public career-page feeds (pass the board/company slug) |
| Adzuna | free `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | https://developer.adzuna.com |
| USAJobs | free `USAJOBS_API_KEY` | https://developer.usajobs.gov |

**Deliberately excluded: LinkedIn, Indeed, ZipRecruiter.** Their terms
prohibit bots that log in or apply automatically, and they actively detect
them. For those sites, paste a posting into the JD intake and apply yourself.

## Safety & ethics

- **The app never submits applications.** It prepares analysis and drafts;
  the human reviews everything and clicks submit.
- **The app never sends messages** or logs into any account. No credentials
  are stored anywhere.
- **Personal data stays on your machine** (`data/` is gitignored; only the
  redacted sample ships with the repo).

## Tests

```bash
pytest -q
```

35 tests: JD extraction (incl. verbatim visa quotes), fit scoring, tailoring
diffs, outreach templates, interview Q&A scoring, tracker CRUD, source
normalization (mocked HTTP), end-to-end LangGraph pipeline, and API routes.

## Project structure

```
copilot/
  llm.py        # provider factory: Gemini → Groq → OpenAI → demo stub
  skills.py     # shared skill lexicon for matching
  jd_intake.py  # posting → structured fields (demo heuristics / live LLM)
  resume.py     # local resume loading (gitignored data dir)
  fit.py        # JD-vs-resume scoring
  tailor.py     # bullet rewriting + before/after diff
  outreach.py   # connection note + follow-up drafts
  interview.py  # question generation + mock answer scoring
  tracker.py    # SQLite application tracker
  sources.py    # pull-only job connectors
  graph.py      # LangGraph pipeline: intake → fit → tailor → outreach
app.py          # FastAPI service
cli.py          # CLI demo
frontend/       # React + TypeScript (Vite) UI
sample_data/    # redacted sample profile + 2 sample JDs
tests/          # pytest suite
```

## Interview talking points

- **Why multi-agent?** Each stage (extract → score → tailor → draft) has a
  different job; a LangGraph state machine makes the handoffs explicit and
  debuggable instead of one giant prompt.
- **Demo-mode engineering:** the whole pipeline works offline with
  deterministic heuristics, so every behavior is testable — 35 pytest tests
  pin the extraction, scoring, and grading logic.
- **RAG-adjacent skills:** skill-lexicon matching, verbatim evidence quotes
  for visa language (like citation grounding), eval-style mock-answer scoring.
- **Ethics by design:** pull-only sources, no credential storage, no
  auto-apply — automation that respects platform terms.
- **Dogfooding:** "I built the tool I use for my own job hunt — it screens
  postings, flags visa language, and tracks 30+ applications."
