	import { useEffect, useState } from "react";
import { Area, Bar, BarChart, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, fmt } from "./api.js";

const C = { fc: "var(--fc)", ink: "var(--ink)", line: "var(--line)", warn: "var(--warn)" };
const axis = { stroke: "var(--mute)", fontSize: 12 };
const tip = { contentStyle: { background: "var(--panel)", border: "1px solid var(--line)", color: "var(--ink)" } };

const Stat = ({ v, l }) => <div className="stat"><b>{v}</b><span>{l}</span></div>;
const Chart = ({ title, sub, children, h = 300 }) => (
  <section className="chart"><h3>{title}</h3><p>{sub}</p>
    <ResponsiveContainer width="100%" height={h}>{children}</ResponsiveContainer></section>
);

function useData(path, params, deps) {
  const [s, set] = useState({ data: null, error: null });
  useEffect(() => {
    let live = true;
    set({ data: null, error: null });
    api(path, params).then((data) => live && set({ data, error: null })).catch((e) => live && set({ data: null, error: e.message }));
    return () => { live = false; };
  }, deps); // eslint-disable-line
  return s;
}

function Decision({ date, cutoff }) {
  const { data: d, error } = useData("decision", { date, cutoff }, [date, cutoff]);
  if (error) return <p className="err">{error}</p>;
  if (!d) return <p>Loading…</p>;
  const rows = d.points.map((p) => ({ ...p, t: p.startTime.slice(11, 16), base: p.low, span: p.high - p.low }));
  const s = d.day_summary;
  return (<>
    <h2>Delivery day {date}</h2>
    <p className="sub">What you could see at {d.cutoff_local} (UK time) on the day before: the latest wind forecast already published, and what actually happened.</p>
    <div className="stats">
      <Stat v={`${fmt(d.forecast_mwh)} MWh`} l="forecast wind for the day" />
      <Stat v={`${fmt(d.conservative_mwh)} MWh`} l="cautious case (lower edge of band)" />
      <Stat v={d.actual_mwh == null ? "pending" : `${fmt(d.actual_mwh)} MWh`} l="actual wind" />
      <Stat v={s.n ? `${fmt(s.mae_mw)} MW` : "n/a"} l="average miss on this day" />
    </div>
    <Chart title="Wind generation, MW per half-hour" sub={`Forecast published ${d.publish_min.slice(0, 16).replace("T", " ")} UTC. Band covers the middle 80% of past misses (${fmt(d.band_basis.q10)} to +${fmt(d.band_basis.q90)} MW).`} h={380}>
      <ComposedChart data={rows}>
        <CartesianGrid stroke={C.line} strokeDasharray="3 3" />
        <XAxis dataKey="t" {...axis} interval={5} /><YAxis {...axis} width={55} />
        <Tooltip {...tip} formatter={(v, n) => [fmt(v), n]} />
        <Area dataKey="base" stackId="b" stroke="none" fill="transparent" legendType="none" name="band low" />
        <Area dataKey="span" stackId="b" stroke="none" fill="var(--band)" name="expected range" />
        <Line dataKey="forecast" stroke={C.fc} strokeWidth={2.5} dot={false} name="Forecast" />
        <Line dataKey="actual" stroke={C.ink} strokeWidth={2} dot={false} name="Actual" />
        <Legend />
      </ComposedChart>
    </Chart>
    <p className="note">
      {d.band_basis.from_prior_days ? `Band built from ${fmt(d.band_basis.n)} half-hours before this day, so it uses no hindsight.` : "Too little earlier history, so the band uses the whole month."}
      {" "}Wind above the forecast lowers what you must buy; wind below it raises it.
    </p>
  </>);
}

function Accuracy({ start, end, cutoff }) {
  const { data: a, error } = useData("accuracy", { start, end, cutoff }, [start, end, cutoff]);
  if (error) return <p className="err">{error}</p>;
  if (!a) return <p>Loading…</p>;
  const s = a.summary;
  return (<>
    <h2>How accurate is the day-ahead forecast?</h2>
    <p className="sub">Error = actual minus forecast. Negative means the forecast was too high (wind fell short). Measured on the forecast you actually had at the cutoff, {start} to {end}.</p>
    <div className="stats">
      <Stat v={`${fmt(s.mae_mw)} MW`} l="mean absolute error" />
      <Stat v={`${fmt(s.nmae_pct, 1)}%`} l="of average wind output" />
      <Stat v={`${fmt(s.bias_mw)} MW`} l="average bias" />
      <Stat v={`${fmt(s.abs_err_p90)} MW`} l="9 in 10 misses are smaller than this" />
      <Stat v={`${fmt(s.err_q10)} to +${fmt(s.err_q90)}`} l="80% range of error, MW" />
    </div>
    <Chart title="Distribution of forecast error" sub="Half-hours per error size (MW). Left of zero: over-forecast.">
      <BarChart data={a.histogram}><CartesianGrid stroke={C.line} strokeDasharray="3 3" /><XAxis dataKey="mid" {...axis} /><YAxis {...axis} width={45} /><Tooltip {...tip} /><Bar dataKey="count" fill={C.fc} name="half-hours" /></BarChart>
    </Chart>
    <Chart title="Error by hour of the delivery day" sub="Average absolute error (MAE) and bias, MW">
      <BarChart data={a.by_hour}><CartesianGrid stroke={C.line} strokeDasharray="3 3" /><XAxis dataKey="hour" {...axis} /><YAxis {...axis} width={45} /><Tooltip {...tip} /><Legend /><Bar dataKey="mae_mw" fill={C.fc} name="MAE" /><Bar dataKey="bias_mw" fill={C.warn} name="Bias" /></BarChart>
    </Chart>
    <Chart title="Error by day" sub="Average absolute error (MAE) per delivery day, MW">
      <BarChart data={a.by_day}><CartesianGrid stroke={C.line} strokeDasharray="3 3" /><XAxis dataKey="day" {...axis} tickFormatter={(v) => v.slice(8)} /><YAxis {...axis} width={45} /><Tooltip {...tip} /><Bar dataKey="mae_mw" fill={C.fc} name="MAE" /></BarChart>
    </Chart>
    <Chart title="Error by wind level" sub="Terciles of actual output. Does the forecast struggle when it is very windy or calm?" h={240}>
      <BarChart data={a.by_level}><CartesianGrid stroke={C.line} strokeDasharray="3 3" /><XAxis dataKey="level" {...axis} /><YAxis {...axis} width={45} /><Tooltip {...tip} /><Legend /><Bar dataKey="mae_mw" fill={C.fc} name="MAE" /><Bar dataKey="bias_mw" fill={C.warn} name="Bias" /></BarChart>
    </Chart>
  </>);
}

function Horizon({ start, end }) {
  const { data: h, error } = useData("horizon", { start, end }, [start, end]);
  if (error) return <p className="err">{error}</p>;
  if (!h) return <p>Loading…</p>;
  const rows = h.rows.map((r) => ({ ...r, label: `${r.from_h}–${r.to_h}h` }));
  return (<>
    <h2>Does waiting for a newer forecast help?</h2>
    <p className="sub">Error grouped by how far ahead the forecast was published.</p>
    <Chart title="Error by lead time" sub="MAE and RMSE in MW, across every published forecast">
      <BarChart data={rows}><CartesianGrid stroke={C.line} strokeDasharray="3 3" /><XAxis dataKey="label" {...axis} /><YAxis {...axis} width={45} /><Tooltip {...tip} /><Legend /><Bar dataKey="mae_mw" fill={C.fc} name="MAE" /><Bar dataKey="rmse_mw" fill={C.ink} name="RMSE" /></BarChart>
    </Chart>
  </>);
}

function Method({ meta }) {
  return (<div className="prose">
    <h2>How this works</h2>
    <h3>Which forecast counts</h3>
    <p>Elexon publishes many wind forecasts for the same half-hour. For each target half-hour we keep the forecast with the latest publish time that is still at or before the cutoff on the previous day ({meta.default_cutoff} UK time by default). Anything published later could not have informed the purchase.</p>
    <h3>Error definition</h3>
    <p>Error = actual minus forecast, in MW. We report bias, MAE, RMSE, MAE as a share of average output, and percentiles of the error, because a buyer cares about the tails.</p>
    <h3>Expected range</h3>
    <p>The band on the decision page applies the 10th and 90th percentile of past errors to the forecast. It is built only from days before the delivery day.</p>
    <h3>Limits</h3>
    <ul>
      <li>National wind only. Demand, solar and prices are not included.</li>
      <li>The cutoff is a setting. Confirm the gate closure of the auction you use.</li>
      <li>Actual generation (FUELHH) is outturn data and can be revised.</li>
      <li>Forecast error is not constant: it depends on wind level and weather regime, so treat the range as a guide.</li>
    </ul>
  </div>);
}

export default function App() {
  const [meta, setMeta] = useState(null);
  const [tab, setTab] = useState("decision");
  const [date, setDate] = useState("2026-01-15");
  const [cutoff, setCutoff] = useState("09:50");
  useEffect(() => { api("meta").then((m) => { setMeta(m); setCutoff(m.default_cutoff); }); }, []);
  if (!meta) return <p style={{ padding: 30 }}>Loading…</p>;
  const tabs = [["decision", "Tomorrow's forecast"], ["accuracy", "Forecast accuracy"], ["horizon", "Lead time"], ["method", "Method"]];
  return (
    <div className="app">
      <aside>
        <div><h1>Wind forecast desk</h1><p>Day-ahead buying, GB national wind</p></div>
        <nav aria-label="Sections">
          {tabs.map(([k, l]) => <button key={k} aria-current={tab === k ? "page" : undefined} onClick={() => setTab(k)}>{l}</button>)}
        </nav>
        <label>Delivery day
          <input type="date" value={date} min="2026-01-01" max="2026-01-31" onChange={(e) => e.target.value && setDate(e.target.value)} /></label>
        <label>Decision cutoff on the day before (UK time)
          <input type="time" value={cutoff} onChange={(e) => e.target.value && setCutoff(e.target.value)} /></label>
        <p>Data: Elexon BMRS, FUELHH actuals and WINDFOR forecasts, January 2026.</p>
      </aside>
      <main>
        {meta.source !== "elexon" && <div className="banner" role="status">Sample data. These numbers are synthetic until the Elexon data is loaded.</div>}
        {tab === "decision" && <Decision date={date} cutoff={cutoff} />}
        {tab === "accuracy" && <Accuracy start="2026-01-01" end="2026-01-31" cutoff={cutoff} />}
        {tab === "horizon" && <Horizon start="2026-01-01" end="2026-01-31" />}
        {tab === "method" && <Method meta={meta} />}
      </main>
    </div>
  );
}
