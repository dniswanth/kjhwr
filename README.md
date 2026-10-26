# Wind forecast desk (day-ahead buying support)

Web app for a GB energy buyer: shows the latest national wind forecast available at the day-ahead decision time and quantifies its accuracy. Data: Elexon BMRS `FUELHH` (actuals, `fuelType=WIND`) and `WINDFOR` (forecasts), January 2026.

**Live app:** _add Vercel/Heroku link here_

> **AI disclosure:** this project was built with assistance from Claude (Anthropic), which generated the initial code, tests and docs. All code should be reviewed by the author before submission.

> **Data status:** data/ contains real Elexon data for January 2026, loaded with scripts/ingest.py. scripts/make_synthetic.py is a fallback for offline demos only.

## Key idea
For each target half-hour, use the forecast with the greatest `publishTime` at or before the cutoff on D-1 (default 09:50 UK time, adjustable in the UI). Error = actual - forecast.

## Files
| Path | Purpose |
|---|---|
| `backend/app/decision.py` | Latest-forecast-at-cutoff selection (timezone aware) |
| `backend/app/metrics.py` | Bias, MAE, RMSE, percentiles, histogram |
| `backend/app/data.py` | Loads cached CSVs |
| `backend/app/main.py` | FastAPI endpoints (`/api/meta`, `/decision`, `/accuracy`, `/horizon`); serves the built UI |
| `backend/tests/` | pytest unit tests |
| `frontend/` | React + Vite + Recharts UI |
| `scripts/ingest.py` | Pulls real data from the Elexon API into `data/` |
| `scripts/make_synthetic.py` | Generates the synthetic sample data |
| `data/` | `actuals.csv.gz`, `forecasts.csv.gz`, `meta.json` |
| `Dockerfile`, `docker-compose.yml`, `heroku.yml` | Container build and Heroku deploy |
| `vercel.json`, `api/index.py` | Vercel deploy |
| `docs/VIDEO_SCRIPT.md` | Script for the two-part demo video |

## Run
```bash
# Docker
docker compose up --build        # http://localhost:8080
If port 8080 is busy, change the left-hand number in docker-compose.yml.

# Or locally
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload            # API on :8000
cd frontend && npm install && npm run dev        # UI on :5173 (proxies /api)

pytest backend                                    # tests
python scripts/ingest.py                          # load real Elexon data
```

## Deploy
- **Heroku:** `heroku create && heroku stack:set container && git push heroku main`
- **Vercel:** `vercel --prod` (uses `vercel.json`; data files are bundled with the function)

## Assumptions and limits
- National wind only; no demand, solar or price data.
- Cutoff default 09:50 UK local on D-1 is an assumption; verify the gate closure of your auction.
- `ingest.py` keeps forecasts up to 96 h ahead to limit file size.
