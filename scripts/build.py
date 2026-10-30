"""Build the Work Search case study page from the app's database.

Reads only totals: counts of postings by day, by score band, by source type and by ghost label.
It never reads contacts, messages, resumes, cards or employer names, and it opens the database
read-only. The totals go to data/summary.json, which is safe to publish.

Usage:
  python scripts/build.py                      # reads ../work-search/data/work_search.db
  python scripts/build.py --db path/to.db
  python scripts/build.py --from-summary       # rebuild the page from data/summary.json only
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT.parent / "work-search" / "data" / "work_search.db"
SUMMARY = ROOT / "data" / "summary.json"
TEMPLATE = ROOT / "src" / "page.template.html"
SITE_OUT = ROOT / "docs" / "index.html"

# The first day includes setup runs, while sources were being added and removed.
# Daily figures start the day after.
STEADY_FROM = "2026-10-24"

APPLY_NOW, REVIEW = 70, 50
GHOST = [(50, "High risk"), (25, "Some risk"), (0, "Low risk")]
GATE_RULES = ("Location", "Excluded")
SOURCE_TYPES = {"board": "Job boards", "research": "Research", "civic": "Civic tech", "nonprofit": "Nonprofits",
                "tools": "Data tools", "journalism": "Journalism", "studio": "Studios", "foundation": "Foundations"}


def one(conn, sql, *args):
    return conn.execute(sql, args).fetchone()[0]


def summarize(db: Path) -> dict:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    open_ = "closed_at IS NULL"
    gated = f"score = 0 AND coalesce(json_extract(score_reasons, '$[0].rule'), '') IN {GATE_RULES}"
    s = {
        "as_of": one(conn, "SELECT max(last_checked_at) FROM companies")[:10],
        "first_day": one(conn, "SELECT min(first_seen_at) FROM jobs")[:10],
        "steady_from": STEADY_FROM,
        "organizations": one(conn, "SELECT count(*) FROM companies WHERE active = 1 AND category != 'board'"),
        "boards": one(conn, "SELECT count(*) FROM companies WHERE active = 1 AND category = 'board'"),
        # Hiring platforms used by the organizations. The job boards are counted separately.
        "platforms": one(conn, "SELECT count(DISTINCT ats) FROM companies WHERE active = 1 AND category != 'board'"),
        "seen": one(conn, "SELECT count(*) FROM jobs"),
        "funnel": {
            "open": one(conn, f"SELECT count(*) FROM jobs WHERE {open_}"),
            "past_gate": one(conn, f"SELECT count(*) FROM jobs WHERE {open_} AND NOT ({gated})"),
            "some_fit": one(conn, f"SELECT count(*) FROM jobs WHERE {open_} AND score >= 30"),
            "review": one(conn, f"SELECT count(*) FROM jobs WHERE {open_} AND score >= {REVIEW}"),
            "apply_now": one(conn, f"SELECT count(*) FROM jobs WHERE {open_} AND score >= {APPLY_NOW}"),
        },
        "gate_location": one(conn, f"SELECT count(*) FROM jobs WHERE {open_} AND score = 0 AND json_extract(score_reasons, '$[0].rule') = 'Location'"),
        "days": [
            {"day": d, "new": n, "review": r, "apply_now": a, "closed": c}
            for d, n, r, a, c in conn.execute(f"""
                SELECT d,
                       sum(kind = 'new'), sum(kind = 'new' AND score >= {REVIEW}), sum(kind = 'new' AND score >= {APPLY_NOW}),
                       sum(kind = 'closed')
                FROM (SELECT substr(first_seen_at, 1, 10) d, 'new' kind, score FROM jobs
                      UNION ALL SELECT substr(closed_at, 1, 10), 'closed', score FROM jobs WHERE closed_at IS NOT NULL)
                WHERE d >= ? GROUP BY d ORDER BY d""", (STEADY_FROM,))
        ],
        "by_source": [
            {"type": SOURCE_TYPES.get(cat, cat), "open": n, "review": r}
            for cat, n, r in conn.execute(f"""
                SELECT c.category, count(*), sum(j.score >= {REVIEW})
                FROM jobs j JOIN companies c ON c.id = j.company_id
                WHERE j.{open_} GROUP BY c.category ORDER BY count(*) DESC""")
        ],
        "ghost": [],
    }
    risks = [r for (r,) in conn.execute(f"SELECT coalesce(ghost_risk, 0) FROM jobs WHERE {open_}")]
    for i, (floor, label) in enumerate(GHOST):
        ceiling = GHOST[i - 1][0] if i else 101
        s["ghost"].append({"label": label, "count": sum(floor <= r < ceiling for r in risks)})
    s["ghost"].reverse()
    conn.close()
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--from-summary", action="store_true")
    a = ap.parse_args()

    if a.from_summary:
        s = json.loads(SUMMARY.read_text())
    else:
        s = summarize(a.db)
        SUMMARY.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY.write_text(json.dumps(s, indent=1) + "\n")

    days = s["days"]
    week = {k: sum(d[k] for d in days) for k in ["new", "review", "apply_now", "closed"]}
    s["week"] = {**week, "days": len(days)}
    s["built"] = date.today().isoformat()
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", json.dumps(s, separators=(",", ":")))
    SITE_OUT.parent.mkdir(parents=True, exist_ok=True)
    SITE_OUT.write_text(html, encoding="utf-8")
    print(json.dumps({k: v for k, v in s.items() if k not in ("days",)}, indent=1))
    print(f"Wrote {SITE_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
