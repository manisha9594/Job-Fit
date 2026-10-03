import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from copilot.tracker import Tracker


@pytest.fixture()
def tracker(tmp_path):
    return Tracker(db_path=tmp_path / "test.db")


def test_add_and_get(tracker):
    row = tracker.add("Acme", "Senior AI Engineer", url="https://x.test/1",
                      location="Remote")
    assert row["id"] >= 1
    assert row["company"] == "Acme" and row["status"] == "applied"
    assert tracker.get(row["id"])["role"] == "Senior AI Engineer"


def test_list_and_stats(tracker):
    tracker.add("Acme", "Role A")
    tracker.add("Beta", "Role B")
    tracker.update_status(1, "interview")
    rows = tracker.list()
    assert len(rows) == 2
    assert tracker.stats() == {
        "total": 2,
        "by_status": {"applied": 1, "screening": 0, "interview": 1,
                      "offer": 0, "rejected": 0, "withdrawn": 0},
    }
    assert len(tracker.list(status="applied")) == 1


def test_invalid_status_rejected(tracker):
    with pytest.raises(ValueError):
        tracker.add("Acme", "Role", status="hired")
    with pytest.raises(ValueError):
        tracker.update_status(1, "hired")


def test_due_followups(tracker):
    tracker.add("Old Co", "Role", date_applied="2020-01-01")
    tracker.add("New Co", "Role", date_applied="2999-01-01")
    due = tracker.due_followups(days=7)
    assert [r["company"] for r in due] == ["Old Co"]


def test_delete(tracker):
    row = tracker.add("Acme", "Role")
    assert tracker.delete(row["id"]) is True
    assert tracker.get(row["id"]) is None
    assert tracker.delete(9999) is False
