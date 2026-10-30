"""Fill a separate demo database for screenshots of the Work Search app.

Every organization, posting and person here is made up. Scores and ghost labels come from the
app's own rules (rescore and the ghost check), so the screens show how the tool really behaves.

Usage:
  python scripts/demo_seed.py            # writes demo/demo.db, never the real database
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT.parent / "work-search"
DEMO_DB = ROOT / "demo" / "demo.db"
sys.path.insert(0, str(APP))

from worksearch import board, jobs  # noqa: E402
from worksearch.db import connect, set_setting  # noqa: E402

COMPANIES = [
    ("Riverbend Policy Lab", "greenhouse", "riverbend", "research"),
    ("Open Harbor Data", "lever", "openharbor", "civic"),
    ("Northfield Health Institute", "ashby", "northfield", "research"),
    ("Tidewater Climate Trust", "greenhouse", "tidewater", "nonprofit"),
    ("Ledger & Lens", "lever", "ledgerlens", "journalism"),
    ("Fieldnote Studio", "pinpoint", "fieldnote", "studio"),
    ("Quarry Analytics", "ashby", "quarry", "tools"),
    ("Remote Roles Weekly", "remotive", "rrw", "board"),
]

DESC = {
    "viz": "You'll build data visualization and dashboards in Python, pandas, SQL and D3 for a public data program. "
           "You'll work with the research team and our product manager on open data releases.",
    "rag": "Build retrieval-augmented tools with embeddings and a vector database, and evaluate language model answers. "
           "Python, SQL and data storytelling for public policy research.",
    "analyst": "Survey analysis, evaluation and statistical analysis in Python and R programming for a health policy team. "
               "Some public sector reporting.",
    "news": "Join the newsroom graphics desk. D3, Svelte and JavaScript for data journalism, with a focus on climate.",
    "generic": "Support the team with reporting and spreadsheets.",
    "sales": "Own the pipeline and close new accounts.",
    "us_only": "Python and SQL for evaluation work. Candidates must reside in the United States.",
}

# Most real postings run longer than this and name a team, which the ghost check looks for.
# Add a standard paragraph to every description except the deliberately thin one.
TEAM = (" You'll join the Public Data team and report to the Director of Research. We publish our methods and code, "
        "and we review each other's work before anything goes out. The salary range is $95,000 to $120,000, and we "
        "offer flexible hours, a learning budget and four weeks of leave. We welcome applicants from every background "
        "and we'll make any adjustments you need during the interviews. Tell us about one project you're proud of, "
        "what you'd do differently now, and how you'd explain it to someone outside the field.")
DESC = {k: v + ("" if k == "generic" else TEAM) for k, v in DESC.items()}

# (company, title, location, description, employment, days since posted)
POSTINGS = [
    (0, "Data Scientist, Public Data", "Remote - Worldwide", "viz", "full_time", 2),
    (2, "Applied Scientist, Language Models", "Remote (EU)", "rag", "contract", 1),
    (4, "Data Journalist", "Madrid, Spain", "news", "full_time", 3),
    (1, "Data Visualization Developer", "Remote - US", "viz", "full_time", 5),
    (3, "Research Data Analyst", "Remote - Worldwide", "analyst", "contract", 9),
    (2, "Research Associate, Evaluation", "Remote - US", "us_only", "full_time", 12),
    (6, "Analytics Engineer", "Remote (EU)", "viz", "full_time", 60),
    (7, "Senior Data Analyst", "Remote - Worldwide", "analyst", "full_time", 120),
    (5, "Information Designer", "Lisbon, Portugal", "news", "full_time", 4),
    (0, "Policy Analyst", "Washington, DC", "analyst", "full_time", 6),
    (6, "Account Executive", "Remote - Worldwide", "sales", "full_time", 8),
    (7, "Operations Coordinator", "Remote - Worldwide", "generic", "full_time", 30),
    (1, "GIS Specialist", "Remote", "analyst", "part_time", 15),
    (3, "Machine Learning Engineer", "Remote - Worldwide", "rag", "full_time", 95),
]

PEOPLE = [
    # name, type (job, client, contract or network, as in the app), stage, role, next step, days until next date, linked posting (index into POSTINGS)
    ("Maya Lindqvist", "job", "lead", "Data lead, Riverbend Policy Lab", "Send a short note about the public data role", 0, 0),
    ("Tomás Ferreira", "job", "contacted", "Graphics editor, Ledger & Lens", "Follow up on the data journalist role", 0, 2),
    ("Priya Natarajan", "network", "conversation", "Head of research, Northfield Health Institute", "Prepare for Thursday's call", 2, 1),
    ("Open Harbor Data", "job", "applied", "Data Visualization Developer", "Check for a reply", 4, 3),
    ("Jonah Abernathy", "client", "lead", "Founder, Fieldnote Studio", "Ask about contract work", 1, None),
    ("Elena Varga", "network", "contacted", "Program director, Tidewater Climate Trust", "Follow up next week", 6, 4),
    ("Samuel Osei", "job", "interview", "Engineering manager, Quarry Analytics", "Send thank-you note", 0, 6),
]


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    DEMO_DB.parent.mkdir(parents=True, exist_ok=True)
    if DEMO_DB.exists():
        DEMO_DB.unlink()
    conn = connect(DEMO_DB)
    now = datetime.now(timezone.utc).replace(microsecond=0)

    for name, ats, token, cat in COMPANIES:
        conn.execute("INSERT INTO companies (name, ats, token, category, active, last_checked_at) VALUES (?,?,?,?,1,?)",
                     (name, ats, token, cat, iso(now)))
    ids = [r[0] for r in conn.execute("SELECT id FROM companies ORDER BY id")]

    for i, (c, title, loc, d, emp, age) in enumerate(POSTINGS):
        posted = now - timedelta(days=age)
        seen = max(posted, now - timedelta(days=min(age, 6)))
        conn.execute(
            """INSERT INTO jobs (company_id, external_id, title, url, location_raw, employment_type, description_text,
               posted_at, first_seen_at, last_seen_at, employer) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (ids[c], f"demo-{i}", title, f"https://example.com/jobs/{i}", loc, emp, DESC[d],
             iso(posted), iso(seen), iso(now), COMPANIES[c][0] if COMPANIES[c][3] != "board" else "Example Employer"))
    conn.commit()
    jobs.rescore(conn)

    job_ids = [r[0] for r in conn.execute("SELECT id FROM jobs ORDER BY id")]
    today = date.today()
    for name, kind, stage, role, step, days, posting in PEOPLE:
        board.create_card(conn, {
            "name": name, "type": kind, "stage": stage, "role": role, "next_step": step,
            "next_date": (today + timedelta(days=days)).isoformat(),
            "job_id": job_ids[posting] if posting is not None else None,
        })

    # A week of checklist counts, ending today with the day half done.
    week = {"messages": [5, 4, 5, 6, 5, 3, 2], "apply": [3, 2, 3, 3, 1, 2, 1], "proposals": [2, 1, 2, 0, 2, 1, 0],
            "followups": [1, 1, 1, 1, 0, 1, 1], "plan": [1, 1, 1, 1, 1, 1, 1], "visible": [1, 0, 1, 1, 0, 1, 0]}
    for back in range(7):
        day = (today - timedelta(days=6 - back)).isoformat()
        for task, counts in week.items():
            if counts[back]:
                board.set_count(conn, day, task, counts[back])
    # A normal morning: the scheduled refresh ran at 7:00 and every feed answered.
    ran = iso(now.replace(hour=6, minute=0, second=0) if now.hour >= 6 else now)
    set_setting(conn, "last_refresh", {"at": ran, "started": ran, "companies": len(COMPANIES), "failed": [],
                                       "jobs": len(POSTINGS), "new": 3, "closed": 0})
    set_setting(conn, "last_run", {"at": ran, "source": "scheduled", "ok": True, "error": None, "failed": 0})
    conn.commit()
    print(f"Wrote {DEMO_DB} with {len(job_ids)} postings and {len(PEOPLE)} cards.")
    for r in conn.execute("SELECT title, score, ghost_risk FROM jobs ORDER BY score DESC"):
        print(f"  {r[1]:>3}  ghost {r[2]:>3}  {r[0]}")


if __name__ == "__main__":
    main()
