# Techjays signal agent: staging site

DRG's staging front end for the **Estimator & Quoting Specialist** signal agent built for Techjays.
The agent watches US job boards for companies hiring estimators or quoting specialists, checks each
job post against the Techjays ICP with evidence, scores it, and writes the SDR call opener and email.

This branch (`staging`) holds the site. `main` intentionally has no site, so no production version exists.

## What the site does

- Team sign-in with a shared access code (stored in the browser after the first entry)
- Live prospect list with status (Qualified, Review, Rejected), score, evidence from the job post,
  who to call, call opener, email, and the fact-check result
- **Download all as CSV** and **CSV of this view** (current filter and search), 25 columns
- **Run agent now** with live progress and the failure reason when a run stops

## Where it runs

- **GitHub Pages (from this `staging` branch, `/docs` folder):**
  `https://dollar-revenue-group.github.io/techjays-signal-agent/`
  Every push to `staging` republishes it within a minute or two.
- **Backup copy served by n8n:** `https://n8n-bkfvq-u78038.vm.elestio.app/webhook/techjays-agent/app`

## How it is wired

| Piece | Where |
|---|---|
| Agent | n8n workflow "Techjays · Estimator & Quoting signal agent" |
| Site API | n8n workflow "Techjays · Staging site API" |
| Prospects | n8n data table `techjays_estimator_prospects` |
| Run log | n8n data table `techjays_agent_runs` |
| Site page | n8n data table `techjays_site_files` (row `index.html`) |

API endpoints (all under `https://n8n-bkfvq-u78038.vm.elestio.app/webhook/techjays-agent/`).
Every call needs `?code=<team access code>`; a wrong code gets HTTP 401.

| Method | Path | Returns |
|---|---|---|
| GET | `prospects` | `{ ok, rows: [...] }` newest first |
| GET | `status` | `{ ok, runs: [...] }` last 5 runs |
| POST | `run` | `{ ok, run_id }`, or `{ ok: false, reason: "already_running" }` |

## Changing the site

1. Edit `docs/index.html` on this branch and open a pull request into `staging`.
2. Merging into `staging` updates GitHub Pages automatically. To refresh the n8n backup copy too:
   ```sh
   N8N_PUBLISH_CODE=<admin code> sh scripts/publish-to-n8n.sh
   ```
   The admin code is not stored in this repo. Ask Jay.

## Optional: Netlify branch deploy (0 credits to create)

If you connect this repo to a Netlify project, `netlify.toml` cancels every production build,
so only the `staging` branch deploy is built (`staging--<site>.netlify.app`).
In Netlify: Project configuration → Build & deploy → Branches and deploy contexts →
Branch deploys: **Let me add individual branches** → `staging`.
Visits to a branch deploy still count as web requests (about 2 credits per 10,000 requests).

## Before going live

- Add the SerpApi and TheirStack API keys to their credentials in n8n.
- Re-enable the agent's weekday 6:30 AM ET schedule trigger once runs succeed.
- Rotate the team access code in the four "Code OK?" checks if it is shared outside the team.
