"""FastAPI service exposing JobFit.

Read-only where it matters: job sources are pull-only, the tracker is local
SQLite, and nothing here can submit an application anywhere — drafting is as
far as it goes. The human clicks submit.
"""
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

load_dotenv()

from copilot import graph as pipeline
from copilot import interview as interview_mod
from copilot import jd_intake, sources
from copilot.fit import score_fit
from copilot.llm import is_demo_mode, llm_provider
from copilot.outreach import draft_outreach
from copilot.resume import (is_sample, load_resume_text, remove_uploaded_resume,
                            resume_identity, tailored_docx, uploaded_resume_path,
                            save_uploaded_resume, uploaded_resume_name)
from copilot.skills import find_skills
from copilot.tailor import tailor_resume
from copilot.question_bank import full_bank
from copilot.saved import SavedJobs, export_pdf
from copilot.tracker import Tracker

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="JobFit", version="1.0.0")
_tracker = Tracker()
_saved = SavedJobs()


class JDText(BaseModel):
    jd_text: str = Field(..., min_length=20, max_length=30000)


class PipelineRequest(BaseModel):
    jd_text: str = Field(..., min_length=20, max_length=30000)


class MockRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    answer: str = Field(..., min_length=1, max_length=5000)
    jd_text: str = Field(..., min_length=20, max_length=30000)


class BulletEdit(BaseModel):
    original: str
    tailored: str


class TailoredResumeRequest(BaseModel):
    edits: list[BulletEdit]
    company: str = ""


class SavedJobIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    company: str = ""
    url: str = ""
    fit_score: int | None = None
    verdict: str = ""
    top_skills: list[dict] = []
    gaps: list[str] = []
    questions: list[str] = []
    notes: str = ""
    resume: str = ""


class SavedJobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    url: str | None = None
    notes: str | None = None


class ApplicationIn(BaseModel):
    company: str
    role: str
    url: str = ""
    location: str = ""
    date_applied: str | None = None
    status: str = "applied"
    notes: str = ""


class StatusUpdate(BaseModel):
    status: str


@app.get("/health")
def health():
    return {"status": "ok", "demo_mode": is_demo_mode(),
            "llm_provider": llm_provider()}


MAX_RESUME_BYTES = 5 * 1024 * 1024


def _resume_status() -> dict:
    text, source = load_resume_text()
    return {"source": source, "is_sample": is_sample(source),
            "filename": uploaded_resume_name() if source == "uploaded" else None,
            "skills": find_skills(text), "demo_mode": is_demo_mode()}


@app.get("/resume/status")
def resume_status():
    return _resume_status()


@app.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail="Resume must be under 5 MB")
    try:
        save_uploaded_resume(file.filename or "resume.txt", content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _resume_status()


@app.post("/resume/tailored")
def download_tailored_resume(req: TailoredResumeRequest):
    """Your uploaded .docx with the accepted bullet rewrites applied in place —
    same layout and styling, only the bullet text changes."""
    path = uploaded_resume_path()
    if not path or path.suffix.lower() != ".docx":
        raise HTTPException(status_code=422, detail=(
            "Downloading a tailored resume needs a Word (.docx) resume — "
            "upload one in the Resume box."))
    edits = {e.original: e.tailored for e in req.edits if e.tailored.strip() != e.original.strip()}
    content, replaced = tailored_docx(path, edits)
    stem = Path(uploaded_resume_name() or "resume.docx").stem
    suffix = re.sub(r"[^A-Za-z0-9]+", "_", req.company).strip("_")
    name = f"{stem}_tailored{'_' + suffix if suffix else ''}.docx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{name}"',
                 "X-Bullets-Replaced": str(replaced)})


@app.delete("/resume")
def delete_resume():
    remove_uploaded_resume()
    return _resume_status()


@app.post("/jd/analyze")
def analyze_jd(req: JDText):
    try:
        return jd_intake.extract_jd(req.jd_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/pipeline")
def run_full_pipeline(req: PipelineRequest):
    """Intake → fit → tailor → outreach in one call."""
    try:
        return pipeline.run_pipeline(req.jd_text)
    except Exception as exc:  # noqa: BLE001 — map everything to a clean 500
        log.exception("pipeline failed")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc


@app.post("/fit")
def fit_only(req: JDText):
    jd = jd_intake.extract_jd(req.jd_text)
    resume_text, _ = load_resume_text()
    return {"jd": jd, "fit": score_fit(jd, resume_text)}


@app.post("/tailor")
def tailor_only(req: JDText):
    jd = jd_intake.extract_jd(req.jd_text)
    resume_text, _ = load_resume_text()
    return {"jd": jd, "tailored": tailor_resume(jd, resume_text)}


@app.post("/outreach")
def outreach_only(req: JDText):
    jd = jd_intake.extract_jd(req.jd_text)
    resume_text, _ = load_resume_text()
    fit = score_fit(jd, resume_text)
    return {"jd": jd, "outreach": draft_outreach(
        jd, fit, identity=resume_identity(resume_text), resume_text=resume_text)}


@app.get("/questions/bank")
def question_bank():
    """Most-asked interview questions: behavioral + technical by skill."""
    return full_bank()


@app.post("/interview/questions")
def interview_questions(req: JDText):
    try:
        return pipeline.prep_interview(req.jd_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/interview/mock")
def interview_mock(req: MockRequest):
    try:
        return pipeline.mock_interview_turn(req.question, req.answer, req.jd_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/jobs/search")
def jobs_search(source: str = "remotive", query: str = "", limit: int = 20,
                board: str = "", company: str = ""):
    """Pull-only job listings. Never logs in, never applies."""
    try:
        kwargs: dict = {"limit": limit}
        if source in ("remotive",):
            kwargs["query"] = query
        elif source == "adzuna":
            kwargs.update(app_id=os.getenv("ADZUNA_APP_ID", ""),
                          app_key=os.getenv("ADZUNA_APP_KEY", ""),
                          query=query)
        elif source == "usajobs":
            kwargs.update(api_key=os.getenv("USAJOBS_API_KEY", ""),
                          keyword=query or "software engineer")
        elif source in ("greenhouse", "ashby"):
            if not board:
                raise HTTPException(status_code=422,
                                    detail=f"{source} needs ?board=<board-slug>")
            kwargs["board_token" if source == "greenhouse" else "board"] = board
        elif source == "lever":
            if not company:
                raise HTTPException(status_code=422,
                                    detail="lever needs ?company=<lever-slug>")
            kwargs["company"] = company
        return {"source": source, "jobs": sources.search(source, **kwargs)}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        log.exception("job source fetch failed")
        raise HTTPException(status_code=502, detail=f"Source fetch failed: {exc}") from exc


@app.post("/tracker/applications", status_code=201)
def tracker_add(app_in: ApplicationIn):
    try:
        return _tracker.add(**app_in.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/tracker/applications")
def tracker_list(status: str | None = None):
    try:
        return {"applications": _tracker.list(status=status),
                "stats": _tracker.stats()}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.patch("/tracker/applications/{app_id}")
def tracker_update(app_id: int, upd: StatusUpdate):
    row = _tracker.update_status(app_id, upd.status)
    if row is None:
        raise HTTPException(status_code=404, detail="application not found")
    return row


@app.delete("/tracker/applications/{app_id}")
def tracker_delete(app_id: int):
    if not _tracker.delete(app_id):
        raise HTTPException(status_code=404, detail="application not found")
    return {"deleted": app_id}


@app.get("/tracker/followups")
def tracker_followups(days: int = 7):
    return {"due": _tracker.due_followups(days=days)}


# --- Saved job analyses -----------------------------------------------------

@app.get("/saved")
def saved_list():
    return {"jobs": _saved.list()}


@app.post("/saved", status_code=201)
def saved_add(job: SavedJobIn):
    return _saved.add(job.model_dump())


@app.patch("/saved/{job_id}")
def saved_update(job_id: int, fields: SavedJobUpdate):
    job = _saved.update(job_id, fields.model_dump())
    if not job:
        raise HTTPException(status_code=404, detail="saved job not found")
    return job


@app.delete("/saved/{job_id}")
def saved_delete(job_id: int):
    if not _saved.delete(job_id):
        raise HTTPException(status_code=404, detail="saved job not found")
    return {"deleted": job_id}


@app.get("/saved/export.pdf")
def saved_export_pdf():
    return Response(
        content=export_pdf(_saved.list()), media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="saved-jobs.pdf"'})
