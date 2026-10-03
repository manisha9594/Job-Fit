import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import copilot.sources as sources


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _patch_get(monkeypatch, payload):
    monkeypatch.setattr(sources.httpx, "get",
                        lambda *a, **k: FakeResponse(payload))


def test_remotive_normalization(monkeypatch):
    _patch_get(monkeypatch, {"jobs": [{
        "title": "Senior AI Engineer", "company_name": "Acme",
        "candidate_required_location": "Remote, USA",
        "url": "https://remotive.test/1", "description": "Python + LLMs",
        "publication_date": "2026-10-01"}]})
    jobs = sources.fetch_remotive(query="python", limit=5)
    assert len(jobs) == 1
    j = jobs[0]
    assert (j["title"], j["company"], j["source"]) == (
        "Senior AI Engineer", "Acme", "remotive")
    assert j["url"].startswith("https://")


def test_greenhouse_normalization(monkeypatch):
    _patch_get(monkeypatch, {"jobs": [{
        "title": "AI Engineer", "absolute_url": "https://boards.test/1",
        "location": {"name": "Remote"}, "updated_at": "2026-09-30"}]})
    jobs = sources.fetch_greenhouse("acme")
    assert jobs[0]["company"] == "acme"
    assert jobs[0]["location"] == "Remote"
    assert jobs[0]["source"] == "greenhouse"


def test_adzuna_requires_keys():
    with pytest.raises(ValueError):
        sources.fetch_adzuna("", "", query="python")


def test_unknown_source():
    with pytest.raises(ValueError):
        sources.search("linkedin")
