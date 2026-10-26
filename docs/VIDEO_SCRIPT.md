# Video script (max 10 min total)

## Part 1: Client pitch (about 4:30)
1. **0:00 Problem (30s).** You buy tomorrow's power today at about 09:50. Wind is the biggest swing factor. Which forecast did you really have, and how wrong is it?
2. **0:30 Tomorrow's forecast page (90s).** Pick a delivery day. Show the forecast at cutoff (publish time visible), the shaded 80% range, actuals overlaid. Read the cards: forecast MWh vs cautious MWh. Say: "plan to buy the gap between demand and the cautious case if you are risk-averse."
3. **2:00 Accuracy page (90s).** MAE, % of output, bias, "9 in 10 misses below X MW". Error histogram. Hour-of-day and wind-level breakdowns: where the forecast is weakest.
4. **3:30 Lead time page (30s).** Newer forecasts are better, but you can only use what existed at cutoff.
5. **4:00 Close (30s).** Cutoff is adjustable. Next steps: add demand and solar, probabilistic forecasts, price link.

## Part 2: Tech review (about 4:30)
1. **0:00 Architecture (60s).** React (Vite, Recharts) to FastAPI to pandas over cached CSVs in `data/`. One Docker image; FastAPI serves the built UI. Vercel/Heroku configs included.
2. **1:00 Core logic (90s).** `decision.py`: attach D-1 cutoff in Europe/London, drop forecasts published after it, keep latest per startTime. Show `test_decision.py`.
3. **2:30 Metrics + API (60s).** Error = actual - forecast. Endpoints: meta, decision, accuracy, horizon. Band uses prior days only (no look-ahead).
4. **3:30 Ingest + practices (60s).** `scripts/ingest.py`, pinned deps, tests, Docker. Limits: national wind only, cutoff assumption, outturn revisions. AI assistance disclosed in README.
