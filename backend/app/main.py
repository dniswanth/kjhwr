import re
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .data import load
from .decision import DEFAULT_CUTOFF, TZ, add_cutoff, latest_available
from .metrics import histogram, summarize

app = FastAPI(title="Wind forecast decision support")
CUT = Query(DEFAULT_CUTOFF, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


def _dates():
    a, _, _ = load()
    d = a["startTime"].dt.tz_convert(TZ).dt.tz_localize(None).dt.normalize()
    return d.min(), d.max()


def _table(cutoff: str) -> pd.DataFrame:
    """Latest-available forecast joined with actuals for every target half-hour."""
    a, f, _ = load()
    t = latest_available(f, cutoff).merge(a, on="startTime", how="left")
    t["error"] = t["actual"] - t["forecast"]
    t["local"] = t["startTime"].dt.tz_convert(TZ)
    return t


def _parse(d: str) -> pd.Timestamp:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        raise HTTPException(400, "date must be YYYY-MM-DD")
    return pd.Timestamp(d)


def _clean(df: pd.DataFrame) -> list:
    return df.astype(object).where(df.notna(), None).to_dict("records")


@app.get("/api/meta")
def meta():
    _, _, m = load()
    lo, hi = _dates()
    return {**m, "first_date": lo.strftime("%Y-%m-%d"), "last_date": hi.strftime("%Y-%m-%d"),
            "default_cutoff": DEFAULT_CUTOFF, "timezone": TZ}


@app.get("/api/decision")
def decision(date: str, cutoff: str = CUT):
    """What the buyer sees on D-1: the latest forecast for delivery day `date`, plus actuals if known."""
    day = _parse(date)
    t = _table(cutoff)
    d = t[t["local"].dt.tz_localize(None).dt.normalize() == day].sort_values("startTime")
    if d.empty:
        raise HTTPException(404, "no forecast was available for that delivery date")
    # error band from days *before* the delivery day (no look-ahead); fall back to full period if too little history
    prior = t[(t["local"].dt.tz_localize(None).dt.normalize() < day)]
    hist = prior if prior["actual"].notna().sum() >= 96 else t
    hs = summarize(hist)
    q10, q90 = hs.get("err_q10", 0), hs.get("err_q90", 0)
    d = d.assign(low=(d["forecast"] + q10).clip(lower=0), high=d["forecast"] + q90)
    cut = add_cutoff(d.head(1), cutoff)["cutoff"].iloc[0]
    pts = d[["startTime", "forecast", "actual", "publishTime", "low", "high", "horizon_h"]].copy()
    for c in ("startTime", "publishTime"):
        pts[c] = pts[c].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "date": date,
        "cutoff_utc": cut.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cutoff_local": cut.tz_convert(TZ).strftime("%Y-%m-%d %H:%M"),
        "publish_min": pts["publishTime"].min(), "publish_max": pts["publishTime"].max(),
        "forecast_mwh": round(float(d["forecast"].sum() * 0.5)),
        "conservative_mwh": round(float(d["low"].sum() * 0.5)),
        "actual_mwh": round(float(d["actual"].sum() * 0.5)) if d["actual"].notna().all() else None,
        "band_basis": {"q10": q10, "q90": q90, "n": hs.get("n", 0), "from_prior_days": hist is prior},
        "day_summary": summarize(d),
        "points": _clean(pts.round(1)),
    }


@app.get("/api/accuracy")
def accuracy(start: str, end: str, cutoff: str = CUT):
    s, e = _parse(start), _parse(end)
    t = _table(cutoff)
    ld = t["local"].dt.tz_localize(None).dt.normalize()
    t = t[(ld >= s) & (ld <= e)].dropna(subset=["actual"])
    if t.empty:
        raise HTTPException(404, "no data in range")
    t = t.assign(hour=t["local"].dt.hour, day=t["local"].dt.strftime("%Y-%m-%d"))
    by = lambda col: [{col: k, **summarize(g)} for k, g in t.groupby(col)]
    return {"summary": summarize(t), "by_hour": by("hour"), "by_day": by("day"),
            "histogram": histogram(t["error"]),
            "by_level": [{"level": lv, **summarize(g)} for lv, g in t.groupby(pd.qcut(
                t["actual"], 3, labels=["low wind", "mid wind", "high wind"]), observed=True)]}


@app.get("/api/horizon")
def horizon(start: str, end: str):
    """Error versus lead time, using every published forecast (not just the day-ahead one)."""
    s, e = _parse(start), _parse(end)
    a, f, _ = load()
    m = f.merge(a, on="startTime")
    m["h"] = (m["startTime"] - m["publishTime"]).dt.total_seconds() / 3600
    ld = m["startTime"].dt.tz_convert(TZ).dt.tz_localize(None).dt.normalize()
    m = m[(ld >= s) & (ld <= e) & (m["h"] >= 0)]
    m["bucket"] = (m["h"] // 6 * 6).astype(int)
    return {"rows": [{"from_h": int(k), "to_h": int(k) + 6, **summarize(g)} for k, g in m.groupby("bucket")]}


_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.exists():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = _dist / path
        return FileResponse(f if path and f.is_file() else _dist / "index.html")
