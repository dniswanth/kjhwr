"""Generate a SYNTHETIC dataset (same schema as Elexon) so the app runs offline. Replace with scripts/ingest.py."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
out = Path(__file__).resolve().parents[1] / "data"
idx = pd.date_range("2025-12-27", "2026-02-05", freq="30min", tz="UTC")
x = np.zeros(len(idx)); 
for i in range(1, len(x)):
    x[i] = 0.995 * x[i - 1] + rng.normal(0, 0.12)
truth = np.clip(7000 + 4200 * x, 300, 16500)
truth = pd.Series(truth, idx)
act = truth["2026-01-01":"2026-02-01 00:00"]
pd.DataFrame({"startTime": act.index.strftime("%Y-%m-%dT%H:%M:%SZ"), "fuelType": "WIND",
              "generation": act.round(0).astype(int).values}).to_csv(out / "actuals.csv.gz", index=False)
rows = []
for p in pd.date_range("2025-12-28", "2026-01-31 23:00", freq="1h", tz="UTC"):
    tg = pd.date_range(p + pd.Timedelta(hours=1), periods=192, freq="30min")
    tg = tg[(tg >= "2026-01-01") & (tg <= "2026-02-01")]
    if len(tg) == 0:
        continue
    n = 192
    err = rng.normal(0, 1, n).cumsum() * 45 + rng.normal(0, 150, n) + 120
    err = err[(tg - (p + pd.Timedelta(hours=1))) // pd.Timedelta("30min")]
    f = np.clip(truth.reindex(tg).values * (1 + 0.03 * rng.normal()) - err, 0, 17000)
    rows.append(pd.DataFrame({"startTime": tg.strftime("%Y-%m-%dT%H:%M:%SZ"),
                              "publishTime": p.strftime("%Y-%m-%dT%H:%M:%SZ"), "generation": f.round(0).astype(int)}))
pd.concat(rows).to_csv(out / "forecasts.csv.gz", index=False)
(out / "meta.json").write_text(json.dumps({"source": "synthetic"}))
print("done")
