"""Free job discovery for the Techjays estimator & quoting signal agent.

Scrapes recent US job posts with JobSpy (Indeed first, then LinkedIn),
keeps only estimator / quoting titles, and sends them to the agent in n8n.
Then it asks n8n to start an agent run, which verifies, scores and writes
outreach for each post.

Environment variables (set as GitHub Actions secrets):
  N8N_BASE        e.g. https://n8n-bkfvq-u78038.vm.elestio.app/webhook/techjays-agent
  N8N_INGEST_CODE code for the /ingest endpoint
  N8N_TEAM_CODE   team access code, used to start the run (optional)
  HOURS_OLD       how far back to look, default 72
"""
import json
import os
import re
import sys
import time
from urllib.parse import urlparse

import requests
from jobspy import scrape_jobs

BASE = os.environ.get("N8N_BASE", "").rstrip("/")
INGEST_CODE = os.environ.get("N8N_INGEST_CODE", "")
TEAM_CODE = os.environ.get("N8N_TEAM_CODE", "")
HOURS_OLD = int(os.environ.get("HOURS_OLD", "72"))

# Indeed: the main free source. Broad terms, the title filter below narrows them.
INDEED_TERMS = [
    "CNC estimator",
    "machining estimator",
    "manufacturing estimator",
    "fabrication estimator",
    "sheet metal estimator",
    "quoting specialist",
    "quote specialist",
    "cost estimator manufacturing",
    "steel estimator",
    "mechanical estimator",
    "HVAC estimator",
    "electrical estimator",
]
# LinkedIn rate-limits bursts, so keep it small.
LINKEDIN_TERMS = ["manufacturing estimator", "quoting specialist", "mechanical estimator"]

INCLUDE = re.compile(r"\b(estimator|estimating|quoting|quote specialist|quote coordinator|quotation)\b", re.I)
EXCLUDE = re.compile(r"\b(insurance|claims?|auto|damage|body ?shop|collision|appraiser|adjuster|real estate|mortgage|software|tax|payroll|medical|dental|healthcare|intern|internship|restoration)\b", re.I)


def clean(v):
    if v is None:
        return ""
    s = str(v)
    return "" if s.lower() in ("nan", "none", "nat") else s


def domain(url):
    try:
        host = urlparse(clean(url)).hostname or ""
        return host[4:] if host.startswith("www.") else host
    except ValueError:
        return ""


def run_search(site, term, wanted):
    kwargs = dict(
        site_name=[site],
        search_term=term,
        location="United States",
        results_wanted=wanted,
        hours_old=HOURS_OLD,
        country_indeed="USA",
        description_format="markdown",
        verbose=0,
    )
    if site == "linkedin":
        kwargs["fetch_description"] = True
    for attempt in (1, 2):
        try:
            return scrape_jobs(**kwargs)
        except Exception as e:  # one bad search should not stop the run
            print(f"[{site}] '{term}' attempt {attempt} failed: {e}", file=sys.stderr)
            time.sleep(20 if site == "linkedin" else 5)
    return None


def collect():
    jobs, seen = [], set()
    plan = [("indeed", t, 60) for t in INDEED_TERMS] + [("linkedin", t, 25) for t in LINKEDIN_TERMS]
    for site, term, wanted in plan:
        df = run_search(site, term, wanted)
        n_new = 0
        if df is not None and len(df):
            for r in df.to_dict("records"):
                title, company = clean(r.get("title")), clean(r.get("company"))
                if not title or not company or not INCLUDE.search(title) or EXCLUDE.search(title):
                    continue
                key = (company.lower(), title.lower())
                if key in seen:
                    continue
                seen.add(key)
                jobs.append({
                    "source": "JobSpy (" + clean(r.get("site")).title() + ")",
                    "job_title": title,
                    "company": company,
                    "location": clean(r.get("location")),
                    "posted_date": clean(r.get("date_posted"))[:10],
                    "boards": clean(r.get("site")).title(),
                    "job_url": clean(r.get("job_url_direct")) or clean(r.get("job_url")),
                    "description": clean(r.get("description"))[:12000],
                    "company_domain": domain(r.get("company_url_direct")),
                    "employees_text": clean(r.get("company_num_employees")),
                    "company_industry": clean(r.get("company_industry")),
                    "schedule": clean(r.get("job_type")),
                })
                n_new += 1
        print(f"[{site}] '{term}': kept {n_new}")
        time.sleep(8 if site == "linkedin" else 2)
    return jobs


def send(jobs):
    sent = 0
    for i in range(0, len(jobs), 50):
        batch = jobs[i:i + 50]
        r = requests.post(f"{BASE}/ingest", params={"code": INGEST_CODE}, json={"jobs": batch}, timeout=120)
        print(f"ingest batch {i // 50 + 1}: HTTP {r.status_code} {r.text[:200]}")
        r.raise_for_status()
        sent += json.loads(r.text).get("received", 0)
    return sent


def main():
    if not BASE or not INGEST_CODE:
        sys.exit("Set N8N_BASE and N8N_INGEST_CODE.")
    jobs = collect()
    print(f"Total estimator/quoting posts kept: {len(jobs)}")
    if not jobs:
        print("Nothing new to send.")
        return
    print(f"n8n received {send(jobs)} posts")
    if TEAM_CODE:
        r = requests.post(f"{BASE}/run", params={"code": TEAM_CODE}, data="", headers={"Content-Type": "text/plain"}, timeout=60)
        print(f"start agent run: HTTP {r.status_code} {r.text[:200]}")


if __name__ == "__main__":
    main()
