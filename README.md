# techjays-signal-agent

DRG's signal agent for Techjays (estimator & quoting hiring signal).

- **`staging` branch:** the team site (`docs/`), published with GitHub Pages.
- **`main` branch:** the free job scraper that feeds the agent. GitHub only runs scheduled jobs from the default branch, so it lives here.

## Free job scraper

`scraper/scrape.py` uses [JobSpy](https://pypi.org/project/python-jobspy/) to collect US estimator and quoting posts
from Indeed (and a few LinkedIn searches) from the last 72 hours, sends them to n8n, then starts an agent run.
`.github/workflows/scrape-jobs.yml` runs it every weekday at 11:00 UTC, or on demand from the Actions tab
("Scrape estimator jobs (free)" → Run workflow).

It needs three repository secrets (Settings → Secrets and variables → Actions → New repository secret):

| Secret | Value |
|---|---|
| `N8N_BASE` | `https://n8n-bkfvq-u78038.vm.elestio.app/webhook/techjays-agent` |
| `N8N_INGEST_CODE` | the ingest code (ask Jay) |
| `N8N_TEAM_CODE` | the team access code (ask Jay) |

JobSpy scrapes the job boards' public pages, which their terms of service do not allow. Expect occasional blocks
(LinkedIn returns 429 on bursts); one failed search does not stop the run.
