import json
import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[2] / "data"))


@lru_cache(maxsize=1)
def load():
    a = pd.read_csv(DATA_DIR / "actuals.csv.gz", parse_dates=["startTime"])
    f = pd.read_csv(DATA_DIR / "forecasts.csv.gz", parse_dates=["startTime", "publishTime"])
    for df, cols in ((a, ["startTime"]), (f, ["startTime", "publishTime"])):
        for c in cols:
            df[c] = pd.to_datetime(df[c], utc=True)
    a = a.rename(columns={"generation": "actual"})[["startTime", "actual"]].drop_duplicates("startTime")
    f = f.rename(columns={"generation": "forecast"})[["startTime", "publishTime", "forecast"]]
    meta_path = DATA_DIR / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"source": "unknown"}
    return a, f, meta
