"""Pull real Jan-2026 data from Elexon Insights (BMRS) and write data/*.csv.gz.
Usage: python scripts/ingest.py   (needs internet; no API key required)
NOTE: parameter names follow the public Insights API docs; if a 400 comes back, check
https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream and adjust PARAMS."""
import json
import sys
from pathlib import Path
import pandas as pd
import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
OUT = Path(__file__).resolve().parents[1] / "data"
MAX_HORIZON_H = 96  # keep the file small; day-ahead decisions only need ~14-40h


def stream(ds: str, start: str, end: str, step_days: int = 5, **extra) -> pd.DataFrame:
    parts = []
    for s in pd.date_range(start, end, freq=f"{step_days}D"):
        e = min(s + pd.Timedelta(days=step_days), pd.Timestamp(end))
        params = {"publishDateTimeFrom": s.strftime("%Y-%m-%dT%H:%MZ"),
                  "publishDateTimeTo": e.strftime("%Y-%m-%dT%H:%MZ"), "format": "json", **extra}
        r = requests.get(f"{BASE}/{ds}/stream", params=params, timeout=120)
        r.raise_for_status()
        parts.append(pd.DataFrame(r.json()))
        print(ds, s.date(), len(parts[-1]), file=sys.stderr)
    return pd.concat(parts, ignore_index=True)


if __name__ == "__main__":
    act = stream("FUELHH", "2026-01-01", "2026-02-01")
    act = act[act["fuelType"] == "WIND"][["startTime", "fuelType", "generation"]].drop_duplicates("startTime")
    fc = stream("WINDFOR", "2025-12-25", "2026-02-01")[["startTime", "publishTime", "generation"]]
    fc = fc.drop_duplicates(["startTime", "publishTime"])
    h = (pd.to_datetime(fc["startTime"], utc=True) - pd.to_datetime(fc["publishTime"], utc=True)).dt.total_seconds() / 3600
    fc = fc[(h >= 0) & (h <= MAX_HORIZON_H)]
    act.to_csv(OUT / "actuals.csv.gz", index=False)
    fc.to_csv(OUT / "forecasts.csv.gz", index=False)
    (OUT / "meta.json").write_text(json.dumps({"source": "elexon"}))
    print("wrote", len(act), "actuals,", len(fc), "forecasts")
