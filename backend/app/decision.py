"""Core logic: which forecast was the latest one available when the buyer had to decide?"""
import pandas as pd

TZ = "Europe/London"
DEFAULT_CUTOFF = "09:50"  # day-ahead gate closure, UK local time on D-1 (configurable)


def parse_cutoff(hhmm: str) -> pd.Timedelta:
    h, m = hhmm.split(":")
    return pd.Timedelta(hours=int(h), minutes=int(m))


def add_cutoff(f: pd.DataFrame, hhmm: str) -> pd.DataFrame:
    """Attach delivery_date (UK local date of target) and the UTC cutoff instant (D-1 at hhmm UK local)."""
    f = f.copy()
    local = f["startTime"].dt.tz_convert(TZ)
    f["delivery_date"] = local.dt.tz_localize(None).dt.normalize()
    naive = f["delivery_date"] - pd.Timedelta(days=1) + parse_cutoff(hhmm)
    cut = naive.dt.tz_localize(TZ, ambiguous="NaT", nonexistent="shift_forward")
    f["cutoff"] = cut.dt.tz_convert("UTC")
    return f


def latest_available(f: pd.DataFrame, hhmm: str = DEFAULT_CUTOFF) -> pd.DataFrame:
    """For every target half-hour keep the forecast with the greatest publishTime <= cutoff."""
    f = add_cutoff(f, hhmm)
    f = f[f["publishTime"] <= f["cutoff"]]
    f = f.sort_values(["startTime", "publishTime"]).groupby("startTime", as_index=False).last()
    f["horizon_h"] = (f["startTime"] - f["publishTime"]).dt.total_seconds() / 3600
    return f
