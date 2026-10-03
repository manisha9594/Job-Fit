import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from copilot.saved import SavedJobs
from copilot.tracker import Tracker

REPO = Path(__file__).resolve().parent.parent
JD1 = (REPO / "sample_data" / "sample_jd_1.txt").read_text()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "_tracker",
                        Tracker(db_path=tmp_path / "api_test.db"))
    monkeypatch.setattr(app_module, "_saved",
                        SavedJobs(db_path=tmp_path / "api_test.db"))
    return TestClient(app_module.app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["demo_mode"] is True


def test_jd_analyze(client):
    r = client.post("/jd/analyze", json={"jd_text": JD1})
    assert r.status_code == 200
    assert r.json()["company"] == "Northwind Labs"
    assert r.json()["visa_language"]


def test_pipeline(client):
    r = client.post("/pipeline", json={"jd_text": JD1})
    assert r.status_code == 200
    body = r.json()
    assert body["fit"]["score"] >= 0
    assert body["outreach"]["connection_note"]


def test_tracker_crud(client):
    r = client.post("/tracker/applications",
                    json={"company": "Acme", "role": "Senior AI Engineer"})
    assert r.status_code == 201
    app_id = r.json()["id"]

    r = client.get("/tracker/applications")
    assert r.json()["stats"]["total"] == 1

    r = client.patch(f"/tracker/applications/{app_id}",
                     json={"status": "interview"})
    assert r.json()["status"] == "interview"

    r = client.get("/tracker/followups")
    assert r.status_code == 200

    r = client.delete(f"/tracker/applications/{app_id}")
    assert r.json()["deleted"] == app_id


def test_tracker_invalid_status(client):
    r = client.post("/tracker/applications",
                    json={"company": "Acme", "role": "X", "status": "hired"})
    assert r.status_code == 422


def test_pipeline_includes_top_skills_and_questions(client):
    data = client.post("/pipeline", json={"jd_text": JD1}).json()
    assert data["top_skills"] and {"skill", "mentions", "on_resume"} <= set(data["top_skills"][0])
    mentions = [s["mentions"] for s in data["top_skills"]]
    assert mentions == sorted(mentions, reverse=True)
    assert len(data["interview"]["questions"]) >= 4


def test_saved_jobs_crud_and_pdf(client):
    job = {"title": "Software Developer", "company": "Acme & Co", "fit_score": 72,
           "top_skills": [{"skill": "APIs", "mentions": 2, "on_resume": True}],
           "gaps": ["GitLab"], "questions": ["Tell me about yourself."]}
    created = client.post("/saved", json=job)
    assert created.status_code == 201
    job_id = created.json()["id"]
    assert created.json()["top_skills"][0]["skill"] == "APIs"

    r = client.patch(f"/saved/{job_id}", json={"notes": "apply by Friday"})
    assert r.json()["notes"] == "apply by Friday"
    assert len(client.get("/saved").json()["jobs"]) == 1

    pdf = client.get("/saved/export.pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")

    assert client.delete(f"/saved/{job_id}").status_code == 200
    assert client.delete(f"/saved/{job_id}").status_code == 404
    assert client.get("/saved").json()["jobs"] == []


def test_saved_job_requires_title(client):
    assert client.post("/saved", json={"title": ""}).status_code == 422
