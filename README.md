# Work Search

**A private tool that finds data work in public hiring feeds, ranks it by rules I can read, and runs a daily outreach routine.**

Live page: https://alexcorvin.io/work/work-search

This repository holds the case study. The tool itself stays private, because it stores my contacts, drafts and resume.

## The problem

Looking for data science work took hours a day, and much of that time went to postings I could not use.

- **Job boards hide what is new.** They rank postings by their own logic, so a role posted this morning can sit below one that has been open for months.
- **Keyword search misses the right roles.** Roles that combine several skills, such as analysis, visualization and language models, rarely match a single search term.
- **Most postings were roles I could not take.** I live in Spain and work US or EU hours, and more than half of open postings are onsite or limited to a country I do not live in.
- **Some postings are not real openings.** Roles that have been open for months, or reposted again and again, waste time that should go to live ones.
- **Applications with no person behind them go unanswered.** Sending an application through a portal, with no one at the organization knowing my name, rarely led to a reply.

I needed a way to see every new and relevant posting within a day of it going up, decide quickly which ones were worth my time, and make writing to the people who hire a daily habit instead of an afterthought.

## How I solved it

I built a tool that runs on my own computer every morning and does the searching for me.

1. **It reads the source instead of the boards.** Most organizations publish their open roles through a hiring platform that offers a public feed. The tool reads the feeds of 70 organizations on nine hiring platforms, such as Greenhouse, Lever and Ashby, along with six remote job boards. It sees a posting within a day of it going up and notices when one is taken down.
2. **It removes what I cannot do before scoring anything.** A posting has to be remote in the US, the EU or worldwide, or based in Spain. Everything else is dropped first, which removes more than half of what is open.
3. **It scores every posting by written rules.** Points come from the title, the skills named in the description, the kind of organization and contract work, and every point comes with a written reason. No language model takes part in scoring, so the same posting always receives the same score, and when I disagree with a score I change one line in a settings file.
4. **It labels stale postings without hiding them.** Postings that have been open for months, have been reposted, leave out their pay or say almost nothing specific receive a ghost-risk label, so I can decide for myself.
5. **It builds outreach into the day.** A daily checklist asks for five messages, three applications and two proposals. A board tracks every lead from first contact to interview and shows who is due a follow-up. A draft screen writes a short note to a named person, and plain code flags stock phrases and any number that is not in my resume.
6. **It protects personal data.** Before anything goes to a language model, my name and contact details are replaced with placeholders, and the prompt is not built if any personal detail remains. The tool never applies or sends anything by itself.
7. **It runs and checks itself.** A scheduled macOS job refreshes the feeds at 7:00, the app catches up after a missed day, and 178 automated tests run in about two seconds without a network connection.

## Results

From the tool's own database on 30 October 2026:

- **1,103 open postings narrow to 41 worth reviewing.** The location gate removes 623 of them, or 56%, and four score high enough to apply right away.
- **About 66 new postings arrive each day, and one or two are worth a look.** In the first full week, 464 new postings came in and 12 scored 50 or more. A day of searching became a list I can read in a few minutes.
- **Job boards supply 76% of the matches, even with a penalty.** The mission-driven organizations the tool was built around post few data roles at a time.
- **About one in five open postings carries some ghost risk.** 107 are labeled some risk and 117 high risk.
- **The tool has not yet shown whether it changes reply rates.** That needs several more weeks of use.

## What this repository contains

The case study page and the scripts that build it. The figures come from totals in the tool's database, and the screenshots come from a demo database of invented data.

```
scripts/build.py                totals from the database, then the page
scripts/demo_seed.py            invented demo database for the screenshots
scripts/screenshots.mjs         screenshots of the app with Playwright
src/page.template.html          page source, with a data placeholder
data/summary.json               the published totals
docs/index.html                 built page
docs/img/                       screenshots of the app with demo data
embed/squarespace-snippet.html  iframe embed with auto-height
```

### Data

`data/summary.json` holds every number on the page. It is built from the tool's SQLite database, opened read-only, and contains only totals: postings by day, by score band, by kind of source and by ghost label. No posting titles, organizations, contacts, messages or resume text are read.

The first day, 23 October 2026, included setup runs while sources were being added, so the weekly figures start on 24 October.

### Screenshots

The screenshots in `docs/img/` show the app running against a separate demo database, never the real one. Every organization, posting and person in them is invented. The scores and ghost labels come from the app's own rules, because the seed script runs the app's rescoring and ghost check on the demo postings.

```bash
python scripts/demo_seed.py     # writes demo/demo.db (ignored by git)
cd ../work-search && WORKSEARCH_DB=../work-search-case-study/demo/demo.db WORKSEARCH_NO_CATCHUP=1 \
  python3 -m uvicorn worksearch.api:app --host 127.0.0.1 --port 8765
node scripts/screenshots.mjs    # needs Playwright with Chromium
```

`WORKSEARCH_NO_CATCHUP` stops the app from refreshing when it starts, so it fetches nothing. The Prepare to apply screen is not shown, because it reads my real resume.

### Run it

```bash
python scripts/build.py                  # reads ../work-search/data/work_search.db
python scripts/build.py --from-summary   # rebuilds the page from data/summary.json alone
```

Only the Python standard library is needed.

### Embedding

`docs/index.html` and its screenshots in `docs/img/` make up the whole page. To place it inside another page, use `embed/squarespace-snippet.html`. The page reports its height to the parent page, so the frame resizes to fit.

## Built with

Python, FastAPI and SQLite for collection, scoring and the API; Vue and TypeScript for the screens; a macOS launchd job for the daily run.

Design and engineering: Alex Corvin.
