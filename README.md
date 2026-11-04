# Vienna Marathon training site

Two pages for Tim's build to the Vienna City Marathon (April 18, 2027), published with GitHub Pages.
Both read the same `data.json`, so one refresh updates both.

- **`index.html`** — *Vienna Marathon Build*, the detailed personal dashboard (load, recovery, plan, questions for the coach).
- **`road-to-vienna.html`** — *The Road to Vienna*, the shareable story page (story, race board, race-day photos, headline numbers).

## What's in this repo

| File | What it is |
|------|------------|
| `index.html` | The personal dashboard: layout, styles, charts and the written commentary. |
| `road-to-vienna.html` | The public story page. Its story text and race descriptions are written by hand; its numbers come from `data.json`. |
| `img/` | Race photos used on the story page (resized, metadata stripped). |
| `data.json` | The numbers: runs, weekly mileage, fitness/fatigue, HRV, resting HR, sleep, PBs, marathon-projection trend (`proj`). Both pages read it when they open. |
| `.nojekyll` | An empty file that tells GitHub Pages to serve the page as-is. |
| `README.md` | This file. |

The page loads two things from the internet when it opens: Chart.js (for the charts) and Google Fonts.
Everything else comes from the two files in this repo. (Opening `index.html` straight from your computer won't load `data.json` — browsers block that. It works on the GitHub Pages URL.)

## How the data gets updated

Updates happen on demand, not on a schedule. When Tim asks Claude to refresh the dashboard, Claude:
pulls the latest data from Strava, Garmin (via Kailo) and TrainingPeaks; rewrites `data.json`
(and edits the commentary in `index.html` when it needs to change); and commits the change to this repo. GitHub Pages republishes the page about a minute later, at the same URL.

## One-time setup (GitHub Pages)

1. **Settings** → **Pages** (left sidebar).
2. Under **Build and deployment** → **Source**, choose **Deploy from a branch**.
3. Under **Branch**, pick `main` and `/ (root)`, then **Save**.
4. Wait 1–2 minutes. The page is live at `https://<your-username>.github.io/<repo-name>/`.

## Privacy note

On a free GitHub plan, Pages only works for **public** repos. That means anyone with the URL
can see the page, and anyone can view the repo's files, including the HRV, resting heart rate and sleep data.
The page has a `noindex` tag, so search engines are asked not to list it, but the page itself isn't private.
