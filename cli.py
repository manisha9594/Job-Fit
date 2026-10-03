"""CLI demo. Everything works with no API key (demo mode).

Usage:
    python cli.py analyze sample_data/sample_jd_1.txt
    python cli.py pipeline sample_data/sample_jd_1.txt
    python cli.py questions sample_data/sample_jd_1.txt
    python cli.py mock sample_data/sample_jd_1.txt "Tell me about yourself" "My answer..."
    python cli.py jobs remotive --query "python ai engineer"
    python cli.py track add --company "Acme" --role "Senior AI Engineer"
    python cli.py track list
    python cli.py track due

    # API server
    uvicorn app:app --reload
"""
import argparse
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from copilot import graph as pipeline
from copilot.llm import is_demo_mode, llm_provider
from copilot.resume import load_resume_text
from copilot.sources import search as source_search
from copilot.tracker import Tracker


def _read_jd(path: str) -> str:
    with open(path) as f:
        return f.read()


def cmd_analyze(args):
    from copilot.jd_intake import extract_jd
    print(json.dumps(extract_jd(_read_jd(args.jd_file)), indent=2))


def cmd_pipeline(args):
    result = pipeline.run_pipeline(_read_jd(args.jd_file))
    jd, fit = result["jd"], result["fit"]
    print(f"Role: {jd['title']} @ {jd['company']} ({jd['location']}, {jd['work_type']})")
    print(f"Salary: {jd['salary'] or 'not listed'}")
    print(f"Fit: {fit['score']}/100 — {fit['verdict']}")
    print(f"Matched: {', '.join(fit['matched_skills'][:8]) or '—'}")
    print(f"Gaps: {', '.join(fit['gap_skills'][:8]) or '—'}")
    if jd["visa_language"]:
        print("Visa language:")
        for q in jd["visa_language"]:
            print(f"  - {q[:160]}")
    print(f"\nTailored bullets changed: {result['tailored']['changed_count']}")
    print(f"\nConnection note ({result['outreach']['connection_note_chars']} chars):")
    print(result["outreach"]["connection_note"])


def cmd_questions(args):
    result = pipeline.prep_interview(_read_jd(args.jd_file))
    for i, q in enumerate(result["questions"], 1):
        print(f"{i}. {q}")


def cmd_mock(args):
    result = pipeline.mock_interview_turn(args.question, args.answer,
                                          _read_jd(args.jd_file))
    print(f"Score: {result['score']}/100")
    for fb in result["feedback"]:
        print(f" - {fb}")


def cmd_jobs(args):
    kwargs = {}
    if args.source == "remotive":
        kwargs["query"] = args.query
    elif args.source == "adzuna":
        kwargs.update(app_id=os.getenv("ADZUNA_APP_ID", ""),
                      app_key=os.getenv("ADZUNA_APP_KEY", ""), query=args.query)
    elif args.source == "usajobs":
        kwargs.update(api_key=os.getenv("USAJOBS_API_KEY", ""),
                      keyword=args.query or "software engineer")
    elif args.source in ("greenhouse", "ashby"):
        kwargs["board" if args.source == "ashby" else "board_token"] = args.board
    elif args.source == "lever":
        kwargs["company"] = args.company
    try:
        jobs = source_search(args.source, **kwargs)
    except Exception as exc:  # noqa: BLE001
        print(f"Source fetch failed: {exc}")
        sys.exit(1)
    for j in jobs[: args.limit]:
        print(f"- {j['title']} @ {j['company']} [{j['location']}] ({j['source']})")
        print(f"  {j['url']}")
    print(f"\n{len(jobs)} listings (read-only; apply manually)")


def cmd_track(args):
    t = Tracker()
    if args.track_cmd == "add":
        row = t.add(args.company, args.role, url=args.url, location=args.location,
                    notes=args.notes)
        print(f"Added #{row['id']}: {row['company']} — {row['role']} ({row['status']})")
    elif args.track_cmd == "list":
        rows = t.list(status=args.status)
        for r in rows:
            print(f"#{r['id']} {r['company']} — {r['role']} | {r['status']} | {r['date_applied']}")
        print(f"\n{len(rows)} applications")
    elif args.track_cmd == "due":
        rows = t.due_followups(days=args.days)
        for r in rows:
            print(f"#{r['id']} {r['company']} — {r['role']} (applied {r['date_applied']})")
        print(f"\n{len(rows)} follow-ups due")


def main() -> None:
    print(f"Mode: {'DEMO (no API key)' if is_demo_mode() else 'LIVE (' + llm_provider() + ')'}")
    _, rsrc = load_resume_text()
    print(f"Resume: {rsrc}\n")

    p = argparse.ArgumentParser(prog="copilot")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("analyze"); s.add_argument("jd_file"); s.set_defaults(f=cmd_analyze)
    s = sub.add_parser("pipeline"); s.add_argument("jd_file"); s.set_defaults(f=cmd_pipeline)
    s = sub.add_parser("questions"); s.add_argument("jd_file"); s.set_defaults(f=cmd_questions)
    s = sub.add_parser("mock"); s.add_argument("jd_file"); s.add_argument("question")
    s.add_argument("answer"); s.set_defaults(f=cmd_mock)

    s = sub.add_parser("jobs"); s.add_argument("source", default="remotive", nargs="?")
    s.add_argument("--query", default=""); s.add_argument("--limit", type=int, default=10)
    s.add_argument("--board", default=""); s.add_argument("--company", default="")
    s.set_defaults(f=cmd_jobs)

    s = sub.add_parser("track"); t = s.add_subparsers(dest="track_cmd", required=True)
    a = t.add_parser("add"); a.add_argument("--company", required=True)
    a.add_argument("--role", required=True); a.add_argument("--url", default="")
    a.add_argument("--location", default=""); a.add_argument("--notes", default="")
    l = t.add_parser("list"); l.add_argument("--status", default=None)
    d = t.add_parser("due"); d.add_argument("--days", type=int, default=7)
    s.set_defaults(f=cmd_track)

    args = p.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
