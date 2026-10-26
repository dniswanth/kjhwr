import pandas as pd
from backend.app.decision import latest_available
from backend.app.metrics import summarize


def _f(rows):
    df = pd.DataFrame(rows, columns=["startTime", "publishTime", "forecast"])
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    return df


def test_picks_latest_before_cutoff_and_ignores_later():
    f = _f([
        ("2026-01-10 12:00", "2026-01-08 12:00", 1000),
        ("2026-01-10 12:00", "2026-01-09 09:00", 2000),   # latest before 09:50 on D-1
        ("2026-01-10 12:00", "2026-01-09 11:00", 3000),   # published after cutoff -> unusable
    ])
    out = latest_available(f, "09:50")
    assert len(out) == 1 and out["forecast"].iloc[0] == 2000


def test_no_forecast_before_cutoff_drops_target():
    f = _f([("2026-01-10 12:00", "2026-01-09 10:00", 500)])
    assert latest_available(f, "09:50").empty


def test_summarize_sign_convention():
    s = summarize(pd.DataFrame({"actual": [90.0, 110.0], "forecast": [100.0, 100.0]}))
    assert s["mae_mw"] == 10 and s["bias_mw"] == 0
