from backend.app.data import load
a, f, m = load()
mg = f.merge(a, on="startTime")
mg["h"] = (mg.startTime - mg.publishTime).dt.total_seconds() / 3600
print("source:", m)
print("mean actual MW:", round(a.actual.mean()), " max:", a.actual.max())
print("\nmean actual vs forecast by lead time (12h buckets):")
print(mg.groupby(mg.h // 12 * 12)[["actual", "forecast"]].mean().round())
print("\nforecasts for 2026-01-15 12:00 UTC:")
print(mg[mg.startTime == "2026-01-15 12:00:00+00:00"].sort_values("publishTime").tail(5))