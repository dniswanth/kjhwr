import numpy as np
import pandas as pd


def _r(x, n=1):
    return None if x is None or pd.isna(x) else round(float(x), n)


def summarize(df: pd.DataFrame) -> dict:
    """df needs columns actual, forecast. error = actual - forecast (negative = over-forecast)."""
    d = df.dropna(subset=["actual", "forecast"])
    if d.empty:
        return {"n": 0}
    e = d["actual"] - d["forecast"]
    ae = e.abs()
    q = e.quantile([0.05, 0.10, 0.50, 0.90, 0.95])
    return {
        "n": int(len(d)),
        "mean_actual_mw": _r(d["actual"].mean()),
        "bias_mw": _r(e.mean()),
        "mae_mw": _r(ae.mean()),
        "rmse_mw": _r(np.sqrt((e ** 2).mean())),
        "nmae_pct": _r(100 * ae.mean() / d["actual"].mean(), 2),
        "abs_err_p50": _r(ae.quantile(0.5)),
        "abs_err_p90": _r(ae.quantile(0.9)),
        "abs_err_p95": _r(ae.quantile(0.95)),
        "err_q05": _r(q[0.05]), "err_q10": _r(q[0.10]), "err_q50": _r(q[0.50]),
        "err_q90": _r(q[0.90]), "err_q95": _r(q[0.95]),
    }


def histogram(e: pd.Series, bins: int = 24) -> list:
    e = e.dropna()
    if e.empty:
        return []
    lim = max(abs(e.quantile(0.01)), abs(e.quantile(0.99)), 1)
    counts, edges = np.histogram(e.clip(-lim, lim), bins=bins, range=(-lim, lim))
    return [{"from": _r(edges[i], 0), "to": _r(edges[i + 1], 0), "mid": _r((edges[i] + edges[i + 1]) / 2, 0),
             "count": int(c)} for i, c in enumerate(counts)]
