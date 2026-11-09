# Vienna Marathon training site

Two pages for Tim's build to the Vienna City Marathon (April 18, 2027), published with GitHub Pages at **https://run.tdubois.com**.
Both read the same `data.json`, so one refresh updates both.

- **`index.html`** — *The Road to Vienna*, the shareable story page at the site's main address (story, race board, race-day photos, headline numbers).
- **`TAD-Training-Dashboard-x6j9szpy.html`** — *Vienna Marathon Build*, the detailed personal dashboard (load, recovery, plan, questions for the coach). It isn't linked from the public page.

## What's in this repo

| File | What it is |
|------|------------|
| `index.html` | The public story page. Its story text and race descriptions are written by hand; its numbers come from `data.json`. |
| `TAD-Training-Dashboard-x6j9szpy.html` | The personal dashboard: layout, styles, charts and the written commentary. |
| `Illness-Check-uk064es3.html` | *Morning illness check*, a gauge of early illness signs from overnight HRV and resting heart rate. Not linked from either page. |
| `illness-1mcyzk90.json` | The illness check's numbers: last night's score, band, per-metric values vs. 7-night baseline, and a 60-night score history. Only the illness check page reads it. |
| `scripts/illness_check.py` | Computes the illness check from Kailo's HRV and resting heart rate answers and rewrites its JSON. |
| `img/` | Race photos used on the story page (resized, metadata stripped). |
| `data.json` | The numbers: runs, weekly mileage, fitness/fatigue, HRV, resting HR, sleep, PBs, marathon-projection trend (`proj`). Both pages read it when they open. |
| `.nojekyll` | An empty file that tells GitHub Pages to serve the page as-is. |
| `README.md` | This file. |

The page loads two things from the internet when it opens: Chart.js (for the charts) and Google Fonts.
Everything else comes from the two files in this repo. (Opening either page straight from your computer won't load `data.json` — browsers block that. It works on the GitHub Pages URL.)

## How the data gets updated

One scheduled Claude task, "Daily running refresh (illness check + dashboard)", runs every morning at 9:13 AM Pacific.
It pulls from the Garmin Personal API first (through Tim's Mac, so the Mac must be awake), with Strava and Kailo as backups,
plus TrainingPeaks (via Chrome) and the TrainingPeaks calendar feed. It does two separate commits:

1. **Illness check:** runs `scripts/illness_check.py` and commits only `illness-1mcyzk90.json`.
2. **Dashboard refresh:** rewrites `data.json` and the dashboard's factual numbers, and commits those.

A failure in one part doesn't block the other. GitHub Pages republishes about a minute after each push. Tim can also ask Claude for a refresh at any time.

### Morning illness check

Uses overnight HRV, resting heart rate and sleeping respiration (blood oxygen too, if Pulse Ox is turned on for sleep).
The page shows the data source from `method.source` in the JSON. The illness part never touches `data.json` or the other pages,
and the dashboard part leaves the illness files alone.

## One-time setup (GitHub Pages)

1. **Settings** → **Pages** (left sidebar).
2. Under **Build and deployment** → **Source**, choose **Deploy from a branch**.
3. Under **Branch**, pick `main` and `/ (root)`, then **Save**.
4. Wait 1–2 minutes. The site is live at https://run.tdubois.com (custom domain set via the `CNAME` file; domain verified in GitHub account settings; HTTPS enforced).

## Privacy note

On a free GitHub plan, Pages only works for **public** repos. That means anyone with the URL
can see the pages, and anyone can view the repo's files, including the HRV, resting heart rate and sleep data.
The dashboard has a `noindex` tag, so search engines are asked not to list it, but the page itself isn't private.
